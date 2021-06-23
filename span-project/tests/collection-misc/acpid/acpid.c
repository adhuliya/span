/*
 *  AD: Downloaded https://sourceforge.net/projects/acpid/
 *  acpid.c - ACPI daemon
 *
 *  Portions Copyright (C) 2000 Andrew Henroid
 *  Portions Copyright (C) 2001 Sun Microsystems
 *  Portions Copyright (C) 2004 Tim Hockin (thockin@hockin.org)
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <getopt.h>
#include <time.h>
#include <sys/poll.h>
#include <grp.h>
#include <syslog.h>

#include "acpid.h"
#include "ud_socket.h"

static int handle_cmdline(int *argc, char ***argv);
static void close_fds(void);
static int daemonize(void);
static int open_log(void);
static int create_pidfile(void);
static void clean_exit(int sig);
static void clean_exit_with_status(int status);
static void reload_conf(int sig);
static char *read_line(int fd);

/* global debug level */
int acpid_debug;

/* do we log event info? */
int logevents;

/* the number of non-root clients that are connected */
int non_root_clients;

static const char *progname;
static const char *confdir = ACPID_CONFDIR;
static const char *eventfile = ACPID_EVENTFILE;
static const char *socketfile = ACPID_SOCKETFILE;
static const char *lockfile = ACPID_LOCKFILE;
static int nosocket;
static const char *socketgroup;
static mode_t socketmode = ACPID_SOCKETMODE;
static int foreground;
static const char *pidfile = ACPID_PIDFILE;
static int clientmax = ACPID_CLIENTMAX;

int
main(int argc, char **argv)
{
	int event_fd;
	int sock_fd = -1; /* init to avoid a compiler warning */

	/* learn who we really are */
	progname = (const char *)strrchr(argv[0], '/');
	progname = progname ? (progname + 1) : argv[0];

	/* handle the commandline  */
	handle_cmdline(&argc, &argv);

	/* close any extra file descriptors */
	close_fds();

	/* actually open the event file */
	event_fd = open(eventfile, O_RDONLY);
	if (event_fd < 0) {
		fprintf(stderr, "%s: can't open %s: %s\n", progname, 
			eventfile, strerror(errno));
		exit(EXIT_FAILURE);
	}
	fcntl(event_fd, F_SETFD, FD_CLOEXEC);

/*
 * if there is data, and the kernel is NOT broken, this eats 1 byte.  We
 * can't have that.  This is ifdef'ed out on the assumption that old kernels
 * are out of popular use, by now.
 */
#ifdef TEST_FOR_BAD_KERNELS
	/*
	 * Older kernels did not support read() properly or poll() at all
	 * Check that the kernel supports the proper semantics, or die.
	 *
	 * Good kernels will respect O_NONBLOCK and return -1.  Bad kernels
	 * will ignore O_NONBLOCK and return 0.  Really bad kernels will block
	 * and overflow the buffer.  Can't deal with the really bad ones.
	 */
	{
		int fl;
		char buf;

		fl = fcntl(event_fd, F_GETFL);
		fcntl(event_fd, F_SETFL, fl | O_NONBLOCK);
		if (read(event_fd, &buf, 1) == 0) {
			fprintf(stderr, 
				"%s: this kernel does not support proper "
				"event file handling.\n"
				"Please get the patch from "
				"http://acpid.sourceforge.net\n", 
				progname);
			exit(EXIT_FAILURE);
		}
		fcntl(event_fd, F_SETFL, fl);
	}
#endif

	/* open our socket */
	if (!nosocket) {
		sock_fd = ud_create_socket(socketfile);
		if (sock_fd < 0) {
			fprintf(stderr, "%s: can't open socket %s: %s\n",
				progname, socketfile, strerror(errno));
			exit(EXIT_FAILURE);
		}
		fcntl(sock_fd, F_SETFD, FD_CLOEXEC);
		chmod(socketfile, socketmode);
		if (socketgroup) {
			struct group *gr;
			struct stat buf;
			gr = getgrnam(socketgroup);
			if (!gr) {
				fprintf(stderr, "%s: group %s does not exist\n",
					progname, socketgroup);
				exit(EXIT_FAILURE);
			}
			if (stat(socketfile, &buf) < 0) {
				fprintf(stderr, "%s: can't stat %s\n",
					progname, socketfile);
				exit(EXIT_FAILURE);
			}
			if (chown(socketfile, buf.st_uid, gr->gr_gid) < 0) {
				fprintf(stderr, "%s: chown(): %s\n",
					progname, strerror(errno));
				exit(EXIT_FAILURE);
			}
		}
	}

	/* if we're running in foreground, we don't daemonize */
	if (!foreground) {
		if (daemonize() < 0)
			exit(EXIT_FAILURE);
	}

	/* open the log */
	if (open_log() < 0) {
		exit(EXIT_FAILURE);
	}
	acpid_log(LOG_INFO, "starting up\n");

	/* trap key signals */
	signal(SIGHUP, reload_conf);
	signal(SIGINT, clean_exit);
	signal(SIGQUIT, clean_exit);
	signal(SIGTERM, clean_exit);
	signal(SIGPIPE, SIG_IGN);

	/* read in our configuration */
	if (acpid_read_conf(confdir)) {
		exit(EXIT_FAILURE);
	}

	/* create our pidfile */
	if (create_pidfile() < 0) {
		exit(EXIT_FAILURE);
	}

	/* main loop */
	acpid_log(LOG_INFO, "waiting for events: event logging is %s\n",
	    logevents ? "on" : "off");
	while (1) {
		struct pollfd ar[2];
		int r;
		int fds = 0;

		/* poll for the socket and the event file */
		ar[0].fd = event_fd; ar[0].events = POLLIN; fds++;
		if (!nosocket) {
			ar[1].fd = sock_fd; ar[1].events = POLLIN; fds++;
		}
		r = poll(ar, fds, -1);

		if (r < 0 && errno == EINTR) {
			continue;
		} else if (r < 0) {
			acpid_log(LOG_ERR, "poll(): %s\n", strerror(errno));
			continue;
		}

		/* house keeping */
		acpid_close_dead_clients();

		/* was it an event? */
		if (ar[0].revents) {
			char *event;
			struct stat trash;
			int fexists;

			/* check for existence of a lockfile */
			fexists = (stat(lockfile, &trash) == 0);

			/* this shouldn't happen */
			if (!ar[0].revents & POLLIN) {
				acpid_log(LOG_DEBUG,
				    "odd, poll set flags 0x%x\n",
				    ar[0].revents);
				continue;
			}

			/* read an event */
			event = read_line(event_fd);

			/* if we're locked, don't process the event */
			if (fexists) {
				if (logevents) {
					acpid_log(LOG_INFO,
					    "lockfile present, not processing "
					    "event \"%s\"\n", event);
				}
				continue;
			}

			/* handle the event */
			if (event) {
				if (logevents) {
					acpid_log(LOG_INFO,
					    "received event \"%s\"\n", event);
				}
				acpid_handle_event(event);
				if (logevents) {
					acpid_log(LOG_INFO,
					    "completed event \"%s\"\n", event);
				}
			} else if (errno == EPIPE) {
				acpid_log(LOG_WARNING,
				    "events file connection closed\n");
				break;
			} else {
				static int nerrs;
				if (++nerrs >= ACPID_MAX_ERRS) {
					acpid_log(LOG_ERR,
					    "too many errors reading "
					    "events file - aborting\n");
					break;
				}
			}
		}

		/* was it a new connection? */
		if (!nosocket && ar[1].revents) {
			int cli_fd;
			struct ucred creds;
			char buf[32];
			static int accept_errors;

			/* this shouldn't happen */
			if (!ar[1].revents & POLLIN) {
				acpid_log(LOG_DEBUG,
				    "odd, poll set flags 0x%x\n",
				    ar[1].revents);
				continue;
			}

			/* accept and add to our lists */
			cli_fd = ud_accept(sock_fd, &creds);
			if (cli_fd < 0) {
				acpid_log(LOG_ERR, "can't accept client: %s\n",
				    strerror(errno));
				accept_errors++;
				if (accept_errors >= 5) {
					acpid_log(LOG_ERR, "giving up\n");
					clean_exit_with_status(EXIT_FAILURE);
				}
				continue;
			}
			accept_errors = 0;
			if (creds.uid != 0 && non_root_clients >= clientmax) {
				close(cli_fd);
				acpid_log(LOG_ERR,
				    "too many non-root clients\n");
				continue;
			}
			if (creds.uid != 0) {
				non_root_clients++;
			}
			fcntl(cli_fd, F_SETFD, FD_CLOEXEC);
			snprintf(buf, sizeof(buf)-1, "%d[%d:%d]",
				creds.pid, creds.uid, creds.gid);
			acpid_add_client(cli_fd, buf);
		}
	}

	clean_exit_with_status(EXIT_SUCCESS);

	return 0;
}

/*
 * Parse command line arguments
 */
static int
handle_cmdline(int *argc, char ***argv)
{
	struct option opts[] = {
		{"confdir", 1, 0, 'c'},
		{"clientmax", 1, 0, 'C'},
		{"debug", 0, 0, 'd'},
		{"eventfile", 1, 0, 'e'},
		{"foreground", 0, 0, 'f'},
		{"logevents", 0, 0, 'l'},
		{"socketgroup", 1, 0, 'g'},
		{"socketmode", 1, 0, 'm'},
		{"socketfile", 1, 0, 's'},
		{"nosocket", 1, 0, 'S'},
		{"pidfile", 1, 0, 'p'},
		{"lockfile", 1, 0, 'L'},
		{"version", 0, 0, 'v'},
		{"help", 0, 0, 'h'},
		{NULL, 0, 0, 0},
	};
	const char *opts_help[] = {
		"Set the configuration directory.",	/* confdir */
		"Set the limit on non-root socket connections.",/* clientmax */
		"Increase debugging level (implies -f).",/* debug */
		"Use the specified file for events.",	/* eventfile */
		"Run in the foreground.",		/* foreground */
		"Log all event activity.",		/* logevents */
		"Set the group on the socket file.",	/* socketgroup */
		"Set the permissions on the socket file.",/* socketmode */
		"Use the specified socket file.",	/* socketfile */
		"Do not listen on a UNIX socket (overrides -s).",/* nosocket */
		"Use the specified PID file.",		/* pidfile */
		"Use the specified lockfile to stop processing.", /* pidfile */
		"Print version information.",		/* version */
		"Print this message.",			/* help */
	};
	struct option *opt;
	const char **hlp;
	int max, size;

	for (;;) {
		int i;
		i = getopt_long(*argc, *argv,
		    "c:C:de:flg:m:s:Sp:L:vh", opts, NULL);
		if (i == -1) {
			break;
		}
		switch (i) {
		case 'c':
			confdir = optarg;
			break;
		case 'C':
			clientmax = strtol(optarg, NULL, 0);
			break;
		case 'd':
			foreground = 1;
			acpid_debug++;
			break;
		case 'e':
			eventfile = optarg;
			break;
		case 'f':
			foreground = 1;
			break;
		case 'l':
			logevents = 1;
			break;
		case 'g':
			socketgroup = optarg;
			break;
		case 'm':
			socketmode = strtol(optarg, NULL, 8);
			break;
		case 's':
			socketfile = optarg;
			break;
		case 'S':
			nosocket = 1;
			break;
		case 'p':
			pidfile = optarg;
			break;
		case 'L':
			lockfile = optarg;
			break;
		case 'v':
			printf(PACKAGE "-" VERSION "\n");
			exit(EXIT_SUCCESS);
		case 'h':
		default:
			fprintf(stderr, "Usage: %s [OPTIONS]\n", progname);
			max = 0;
			for (opt = opts; opt->name; opt++) {
				size = strlen(opt->name);
				if (size > max)
					max = size;
			}
			for (opt = opts, hlp = opts_help;
			     opt->name;
			     opt++, hlp++)
			{
				fprintf(stderr, "  -%c, --%s",
					opt->val, opt->name);
				size = strlen(opt->name);
				for (; size < max; size++)
					fprintf(stderr, " ");
				fprintf(stderr, "  %s\n", *hlp);
			}
			exit(EXIT_FAILURE);
			break;
		}
	}

	*argc -= optind;
	*argv += optind;

	return 0;
}

static void
close_fds(void)
{
	int fd, max;
	max = sysconf(_SC_OPEN_MAX);
	for (fd = 3; fd < max; fd++)
		close(fd);
}

static int
daemonize(void)
{
	switch(fork()) {
	case -1:
		fprintf(stderr, "%s: fork: %s\n", progname, strerror(errno));
		return -1;
	case 0:
		/* child */
		break;
	default:
		/* parent */
		exit(EXIT_SUCCESS);
	}

	/* disconnect */
	setsid();
	umask(0);

	/* get outta the way */
	if (chdir("/") < 0) {
		fprintf(stderr, "%s: chdir(\"/\"): %s\n", progname,
		        strerror(errno));
		return -1;
	}

	return 0;
}

static int
open_log(void)
{
	int nullfd;
	int log_opts;

	/* open /dev/null */
	nullfd = open("/dev/null", O_RDWR);
	if (nullfd < 0) {
		fprintf(stderr, "%s: can't open %s: %s\n", progname, 
			"/dev/null", strerror(errno));
		return -1;
	}

	log_opts = LOG_CONS|LOG_NDELAY;
	if (acpid_debug) {
		log_opts |= LOG_PERROR;
	}
	openlog(PACKAGE, log_opts, LOG_DAEMON);

	/* set up stdin, stdout, stderr to /dev/null */
	if (dup2(nullfd, STDIN_FILENO) != STDIN_FILENO) {
		fprintf(stderr, "%s: dup2: %s\n", progname, strerror(errno));
		return -1;
	}
	if (!acpid_debug && dup2(nullfd, STDOUT_FILENO) != STDOUT_FILENO) {
		fprintf(stderr, "%s: dup2: %s\n", progname, strerror(errno));
		return -1;
	}
	if (!acpid_debug && dup2(nullfd, STDERR_FILENO) != STDERR_FILENO) {
		fprintf(stderr, "%s: dup2: %s\n", progname, strerror(errno));
		return -1;
	}

	close(nullfd);

	return 0;
}

static int
create_pidfile(void)
{
	int fd;

	/* JIC */
	unlink(pidfile);

	/* open the pidfile */
	fd = open(pidfile, O_WRONLY|O_CREAT|O_EXCL, 0644);
	if (fd >= 0) {
		FILE *f;

		/* write our pid to it */
		f = fdopen(fd, "w");
		if (f != NULL) {
			fprintf(f, "%d\n", getpid());
			fclose(f);
			/* leave the fd open */
			return 0;
		}
		close(fd);
	}

	/* something went wrong */
	acpid_log(LOG_ERR, "can't create pidfile %s: %s\n",
		    pidfile, strerror(errno));
	return -1;
}

static void
clean_exit_with_status(int status)
{
	acpid_cleanup_rules(1);
	acpid_log(LOG_NOTICE, "exiting\n");
	unlink(pidfile);
	exit(status);
}

static void
clean_exit(int sig __attribute__((unused)))
{
	clean_exit_with_status(EXIT_SUCCESS);
}

static void
reload_conf(int sig __attribute__((unused)))
{
	acpid_log(LOG_NOTICE, "reloading configuration\n");
	acpid_cleanup_rules(0);
	acpid_read_conf(confdir);
}

int
#ifdef __GNUC__
__attribute__((format(printf, 2, 3)))
#endif
acpid_log(int level, const char *fmt, ...)
{
	va_list args;

	va_start(args, fmt);
	vsyslog(level, fmt, args);
	va_end(args);

	return 0;
}

/* 
 * This depends on fixes in linux ACPI after 2.4.8
 */
#define MAX_BUFLEN	1024
static char *
read_line(int fd)
{
	static char *buf;
	int buflen = 64;
	int i = 0;
	int r;
	int searching = 1;

	while (searching) {
		buf = realloc(buf, buflen);
		if (!buf) {
			acpid_log(LOG_ERR, "malloc(%d): %s\n",
				buflen, strerror(errno));
			return NULL;
		}
		memset(buf+i, 0, buflen-i);

		while (i < buflen) {
			r = read(fd, buf+i, 1);
			if (r < 0 && errno != EINTR) {
				/* we should do something with the data */
				acpid_log(LOG_ERR, "read(): %s\n",
					strerror(errno));
				return NULL;
			} else if (r == 0) {
				/* signal this in an almost standard way */
				errno = EPIPE;
				return NULL;
			} else if (r == 1) {
				/* scan for a newline */
				if (buf[i] == '\n') {
					searching = 0;
					buf[i] = '\0';
					break;
				}
				i++;
			}
		}
		if (buflen >= MAX_BUFLEN) {
			break;
		} 
		buflen *= 2;
	}

	return buf;
}
