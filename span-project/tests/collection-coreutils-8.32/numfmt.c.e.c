# 1 "numfmt.c"
# 1 "<built-in>" 1
# 1 "<built-in>" 3
# 341 "<built-in>" 3
# 1 "<command line>" 1
# 1 "<built-in>" 2
# 1 "numfmt.c" 2
# 17 "numfmt.c"
# 1 "../lib/config.h" 1
# 18 "numfmt.c" 2
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/float.h" 1 3
# 19 "numfmt.c" 2
# 1 "/usr/include/getopt.h" 1 3 4
# 24 "/usr/include/getopt.h" 3 4
# 1 "/usr/include/features.h" 1 3 4
# 402 "/usr/include/features.h" 3 4
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 403 "/usr/include/features.h" 2 3 4
# 424 "/usr/include/features.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/sys/cdefs.h" 1 3 4
# 427 "/usr/include/x86_64-linux-gnu/sys/cdefs.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 428 "/usr/include/x86_64-linux-gnu/sys/cdefs.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/long-double.h" 1 3 4
# 429 "/usr/include/x86_64-linux-gnu/sys/cdefs.h" 2 3 4
# 425 "/usr/include/features.h" 2 3 4
# 448 "/usr/include/features.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/gnu/stubs.h" 1 3 4
# 10 "/usr/include/x86_64-linux-gnu/gnu/stubs.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/gnu/stubs-64.h" 1 3 4
# 11 "/usr/include/x86_64-linux-gnu/gnu/stubs.h" 2 3 4
# 449 "/usr/include/features.h" 2 3 4
# 25 "/usr/include/getopt.h" 2 3 4
# 35 "/usr/include/getopt.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/getopt_core.h" 1 3 4
# 36 "/usr/include/x86_64-linux-gnu/bits/getopt_core.h" 3 4
extern char *optarg;
# 50 "/usr/include/x86_64-linux-gnu/bits/getopt_core.h" 3 4
extern int optind;




extern int opterr;



extern int optopt;
# 91 "/usr/include/x86_64-linux-gnu/bits/getopt_core.h" 3 4
extern int getopt (int ___argc, char *const *___argv, const char *__shortopts)
       __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
# 36 "/usr/include/getopt.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/getopt_ext.h" 1 3 4
# 50 "/usr/include/x86_64-linux-gnu/bits/getopt_ext.h" 3 4
struct option
{
  const char *name;


  int has_arg;
  int *flag;
  int val;
};







extern int getopt_long (int ___argc, char *const *___argv,
   const char *__shortopts,
          const struct option *__longopts, int *__longind)
       __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
extern int getopt_long_only (int ___argc, char *const *___argv,
        const char *__shortopts,
               const struct option *__longopts, int *__longind)
       __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
# 37 "/usr/include/getopt.h" 2 3 4
# 20 "numfmt.c" 2
# 1 "../lib/stdio.h" 1
# 21 "../lib/stdio.h" 3
# 43 "../lib/stdio.h" 3
# 1 "/usr/include/stdio.h" 1 3 4
# 27 "/usr/include/stdio.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/libc-header-start.h" 1 3 4
# 28 "/usr/include/stdio.h" 2 3 4





# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 46 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 3 4
typedef long unsigned int size_t;
# 34 "/usr/include/stdio.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types.h" 1 3 4
# 27 "/usr/include/x86_64-linux-gnu/bits/types.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 28 "/usr/include/x86_64-linux-gnu/bits/types.h" 2 3 4


typedef unsigned char __u_char;
typedef unsigned short int __u_short;
typedef unsigned int __u_int;
typedef unsigned long int __u_long;


typedef signed char __int8_t;
typedef unsigned char __uint8_t;
typedef signed short int __int16_t;
typedef unsigned short int __uint16_t;
typedef signed int __int32_t;
typedef unsigned int __uint32_t;

typedef signed long int __int64_t;
typedef unsigned long int __uint64_t;







typedef long int __quad_t;
typedef unsigned long int __u_quad_t;







typedef long int __intmax_t;
typedef unsigned long int __uintmax_t;
# 130 "/usr/include/x86_64-linux-gnu/bits/types.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/typesizes.h" 1 3 4
# 131 "/usr/include/x86_64-linux-gnu/bits/types.h" 2 3 4


typedef unsigned long int __dev_t;
typedef unsigned int __uid_t;
typedef unsigned int __gid_t;
typedef unsigned long int __ino_t;
typedef unsigned long int __ino64_t;
typedef unsigned int __mode_t;
typedef unsigned long int __nlink_t;
typedef long int __off_t;
typedef long int __off64_t;
typedef int __pid_t;
typedef struct { int __val[2]; } __fsid_t;
typedef long int __clock_t;
typedef unsigned long int __rlim_t;
typedef unsigned long int __rlim64_t;
typedef unsigned int __id_t;
typedef long int __time_t;
typedef unsigned int __useconds_t;
typedef long int __suseconds_t;

typedef int __daddr_t;
typedef int __key_t;


typedef int __clockid_t;


typedef void * __timer_t;


typedef long int __blksize_t;




typedef long int __blkcnt_t;
typedef long int __blkcnt64_t;


typedef unsigned long int __fsblkcnt_t;
typedef unsigned long int __fsblkcnt64_t;


typedef unsigned long int __fsfilcnt_t;
typedef unsigned long int __fsfilcnt64_t;


typedef long int __fsword_t;

typedef long int __ssize_t;


typedef long int __syscall_slong_t;

typedef unsigned long int __syscall_ulong_t;



typedef __off64_t __loff_t;
typedef char *__caddr_t;


typedef long int __intptr_t;


typedef unsigned int __socklen_t;




typedef int __sig_atomic_t;
# 36 "/usr/include/stdio.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/__FILE.h" 1 3 4



struct _IO_FILE;
typedef struct _IO_FILE __FILE;
# 37 "/usr/include/stdio.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/FILE.h" 1 3 4



struct _IO_FILE;


typedef struct _IO_FILE FILE;
# 38 "/usr/include/stdio.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/libio.h" 1 3 4
# 35 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/_G_config.h" 1 3 4
# 19 "/usr/include/x86_64-linux-gnu/bits/_G_config.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 20 "/usr/include/x86_64-linux-gnu/bits/_G_config.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types/__mbstate_t.h" 1 3 4
# 13 "/usr/include/x86_64-linux-gnu/bits/types/__mbstate_t.h" 3 4
typedef struct
{
  int __count;
  union
  {
    unsigned int __wch;
    char __wchb[4];
  } __value;
} __mbstate_t;
# 22 "/usr/include/x86_64-linux-gnu/bits/_G_config.h" 2 3 4




typedef struct
{
  __off_t __pos;
  __mbstate_t __state;
} _G_fpos_t;
typedef struct
{
  __off64_t __pos;
  __mbstate_t __state;
} _G_fpos64_t;
# 36 "/usr/include/x86_64-linux-gnu/bits/libio.h" 2 3 4
# 53 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdarg.h" 1 3 4
# 14 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdarg.h" 3 4
typedef __builtin_va_list va_list;
# 32 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdarg.h" 3 4
typedef __builtin_va_list __gnuc_va_list;
# 54 "/usr/include/x86_64-linux-gnu/bits/libio.h" 2 3 4
# 149 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
struct _IO_jump_t; struct _IO_FILE;




typedef void _IO_lock_t;





struct _IO_marker {
  struct _IO_marker *_next;
  struct _IO_FILE *_sbuf;



  int _pos;
# 177 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
};


enum __codecvt_result
{
  __codecvt_ok,
  __codecvt_partial,
  __codecvt_error,
  __codecvt_noconv
};
# 245 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
struct _IO_FILE {
  int _flags;




  char* _IO_read_ptr;
  char* _IO_read_end;
  char* _IO_read_base;
  char* _IO_write_base;
  char* _IO_write_ptr;
  char* _IO_write_end;
  char* _IO_buf_base;
  char* _IO_buf_end;

  char *_IO_save_base;
  char *_IO_backup_base;
  char *_IO_save_end;

  struct _IO_marker *_markers;

  struct _IO_FILE *_chain;

  int _fileno;



  int _flags2;

  __off_t _old_offset;



  unsigned short _cur_column;
  signed char _vtable_offset;
  char _shortbuf[1];



  _IO_lock_t *_lock;
# 293 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
  __off64_t _offset;







  void *__pad1;
  void *__pad2;
  void *__pad3;
  void *__pad4;

  size_t __pad5;
  int _mode;

  char _unused2[15 * sizeof (int) - 4 * sizeof (void *) - sizeof (size_t)];

};


typedef struct _IO_FILE _IO_FILE;


struct _IO_FILE_plus;

extern struct _IO_FILE_plus _IO_2_1_stdin_;
extern struct _IO_FILE_plus _IO_2_1_stdout_;
extern struct _IO_FILE_plus _IO_2_1_stderr_;
# 337 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
typedef __ssize_t __io_read_fn (void *__cookie, char *__buf, size_t __nbytes);







typedef __ssize_t __io_write_fn (void *__cookie, const char *__buf,
     size_t __n);







typedef int __io_seek_fn (void *__cookie, __off64_t *__pos, int __w);


typedef int __io_close_fn (void *__cookie);




typedef __io_read_fn cookie_read_function_t;
typedef __io_write_fn cookie_write_function_t;
typedef __io_seek_fn cookie_seek_function_t;
typedef __io_close_fn cookie_close_function_t;


typedef struct
{
  __io_read_fn *read;
  __io_write_fn *write;
  __io_seek_fn *seek;
  __io_close_fn *close;
} _IO_cookie_io_functions_t;
typedef _IO_cookie_io_functions_t cookie_io_functions_t;

struct _IO_cookie_file;


extern void _IO_cookie_init (struct _IO_cookie_file *__cfile, int __read_write,
        void *__cookie, _IO_cookie_io_functions_t __fns);







extern int __underflow (_IO_FILE *);
extern int __uflow (_IO_FILE *);
extern int __overflow (_IO_FILE *, int);
# 433 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
extern int _IO_getc (_IO_FILE *__fp);
extern int _IO_putc (int __c, _IO_FILE *__fp);
extern int _IO_feof (_IO_FILE *__fp) __attribute__ ((__nothrow__ ));
extern int _IO_ferror (_IO_FILE *__fp) __attribute__ ((__nothrow__ ));

extern int _IO_peekc_locked (_IO_FILE *__fp);





extern void _IO_flockfile (_IO_FILE *) __attribute__ ((__nothrow__ ));
extern void _IO_funlockfile (_IO_FILE *) __attribute__ ((__nothrow__ ));
extern int _IO_ftrylockfile (_IO_FILE *) __attribute__ ((__nothrow__ ));
# 462 "/usr/include/x86_64-linux-gnu/bits/libio.h" 3 4
extern int _IO_vfscanf (_IO_FILE * __restrict, const char * __restrict,
   __gnuc_va_list, int *__restrict);
extern int _IO_vfprintf (_IO_FILE *__restrict, const char *__restrict,
    __gnuc_va_list);
extern __ssize_t _IO_padn (_IO_FILE *, int, __ssize_t);
extern size_t _IO_sgetn (_IO_FILE *, void *, size_t);

extern __off64_t _IO_seekoff (_IO_FILE *, __off64_t, int, int);
extern __off64_t _IO_seekpos (_IO_FILE *, __off64_t, int);

extern void _IO_free_backup_area (_IO_FILE *) __attribute__ ((__nothrow__ ));
# 42 "/usr/include/stdio.h" 2 3 4




typedef __gnuc_va_list va_list;
# 57 "/usr/include/stdio.h" 3 4
typedef __off_t off_t;






typedef __off64_t off64_t;






typedef __ssize_t ssize_t;






typedef _G_fpos_t fpos_t;




typedef _G_fpos64_t fpos64_t;
# 131 "/usr/include/stdio.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/stdio_lim.h" 1 3 4
# 132 "/usr/include/stdio.h" 2 3 4



extern struct _IO_FILE *stdin;
extern struct _IO_FILE *stdout;
extern struct _IO_FILE *stderr;






extern int remove (const char *__filename) __attribute__ ((__nothrow__ ));

extern int rename (const char *__old, const char *__new) __attribute__ ((__nothrow__ ));



extern int renameat (int __oldfd, const char *__old, int __newfd,
       const char *__new) __attribute__ ((__nothrow__ ));







extern FILE *tmpfile (void) ;
# 169 "/usr/include/stdio.h" 3 4
extern FILE *tmpfile64 (void) ;



extern char *tmpnam (char *__s) __attribute__ ((__nothrow__ )) ;




extern char *tmpnam_r (char *__s) __attribute__ ((__nothrow__ )) ;
# 190 "/usr/include/stdio.h" 3 4
extern char *tempnam (const char *__dir, const char *__pfx)
     __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) ;







extern int fclose (FILE *__stream);




extern int fflush (FILE *__stream);
# 213 "/usr/include/stdio.h" 3 4
extern int fflush_unlocked (FILE *__stream);
# 223 "/usr/include/stdio.h" 3 4
extern int fcloseall (void);
# 232 "/usr/include/stdio.h" 3 4
extern FILE *fopen (const char *__restrict __filename,
      const char *__restrict __modes) ;




extern FILE *freopen (const char *__restrict __filename,
        const char *__restrict __modes,
        FILE *__restrict __stream) ;
# 256 "/usr/include/stdio.h" 3 4
extern FILE *fopen64 (const char *__restrict __filename,
        const char *__restrict __modes) ;
extern FILE *freopen64 (const char *__restrict __filename,
   const char *__restrict __modes,
   FILE *__restrict __stream) ;




extern FILE *fdopen (int __fd, const char *__modes) __attribute__ ((__nothrow__ )) ;





extern FILE *fopencookie (void *__restrict __magic_cookie,
     const char *__restrict __modes,
     _IO_cookie_io_functions_t __io_funcs) __attribute__ ((__nothrow__ )) ;




extern FILE *fmemopen (void *__s, size_t __len, const char *__modes)
  __attribute__ ((__nothrow__ )) ;




extern FILE *open_memstream (char **__bufloc, size_t *__sizeloc) __attribute__ ((__nothrow__ )) ;





extern void setbuf (FILE *__restrict __stream, char *__restrict __buf) __attribute__ ((__nothrow__ ));



extern int setvbuf (FILE *__restrict __stream, char *__restrict __buf,
      int __modes, size_t __n) __attribute__ ((__nothrow__ ));




extern void setbuffer (FILE *__restrict __stream, char *__restrict __buf,
         size_t __size) __attribute__ ((__nothrow__ ));


extern void setlinebuf (FILE *__stream) __attribute__ ((__nothrow__ ));







extern int fprintf (FILE *__restrict __stream,
      const char *__restrict __format, ...);




extern int printf (const char *__restrict __format, ...);

extern int sprintf (char *__restrict __s,
      const char *__restrict __format, ...) __attribute__ ((__nothrow__));





extern int vfprintf (FILE *__restrict __s, const char *__restrict __format,
       __gnuc_va_list __arg);




extern int vprintf (const char *__restrict __format, __gnuc_va_list __arg);

extern int vsprintf (char *__restrict __s, const char *__restrict __format,
       __gnuc_va_list __arg) __attribute__ ((__nothrow__));



extern int snprintf (char *__restrict __s, size_t __maxlen,
       const char *__restrict __format, ...)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 3, 4)));

extern int vsnprintf (char *__restrict __s, size_t __maxlen,
        const char *__restrict __format, __gnuc_va_list __arg)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 3, 0)));





extern int vasprintf (char **__restrict __ptr, const char *__restrict __f,
        __gnuc_va_list __arg)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 2, 0))) ;
extern int __asprintf (char **__restrict __ptr,
         const char *__restrict __fmt, ...)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 2, 3))) ;
extern int asprintf (char **__restrict __ptr,
       const char *__restrict __fmt, ...)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 2, 3))) ;




extern int vdprintf (int __fd, const char *__restrict __fmt,
       __gnuc_va_list __arg)
     __attribute__ ((__format__ (__printf__, 2, 0)));
extern int dprintf (int __fd, const char *__restrict __fmt, ...)
     __attribute__ ((__format__ (__printf__, 2, 3)));







extern int fscanf (FILE *__restrict __stream,
     const char *__restrict __format, ...) ;




extern int scanf (const char *__restrict __format, ...) ;

extern int sscanf (const char *__restrict __s,
     const char *__restrict __format, ...) __attribute__ ((__nothrow__ ));
# 420 "/usr/include/stdio.h" 3 4
extern int vfscanf (FILE *__restrict __s, const char *__restrict __format,
      __gnuc_va_list __arg)
     __attribute__ ((__format__ (__scanf__, 2, 0))) ;





extern int vscanf (const char *__restrict __format, __gnuc_va_list __arg)
     __attribute__ ((__format__ (__scanf__, 1, 0))) ;


extern int vsscanf (const char *__restrict __s,
      const char *__restrict __format, __gnuc_va_list __arg)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format__ (__scanf__, 2, 0)));
# 477 "/usr/include/stdio.h" 3 4
extern int fgetc (FILE *__stream);
extern int getc (FILE *__stream);





extern int getchar (void);
# 495 "/usr/include/stdio.h" 3 4
extern int getc_unlocked (FILE *__stream);
extern int getchar_unlocked (void);
# 506 "/usr/include/stdio.h" 3 4
extern int fgetc_unlocked (FILE *__stream);
# 517 "/usr/include/stdio.h" 3 4
extern int fputc (int __c, FILE *__stream);
extern int putc (int __c, FILE *__stream);





extern int putchar (int __c);
# 537 "/usr/include/stdio.h" 3 4
extern int fputc_unlocked (int __c, FILE *__stream);







extern int putc_unlocked (int __c, FILE *__stream);
extern int putchar_unlocked (int __c);






extern int getw (FILE *__stream);


extern int putw (int __w, FILE *__stream);







extern char *fgets (char *__restrict __s, int __n, FILE *__restrict __stream)
          ;
# 587 "/usr/include/stdio.h" 3 4
extern char *fgets_unlocked (char *__restrict __s, int __n,
        FILE *__restrict __stream) ;
# 603 "/usr/include/stdio.h" 3 4
extern __ssize_t __getdelim (char **__restrict __lineptr,
          size_t *__restrict __n, int __delimiter,
          FILE *__restrict __stream) ;
extern __ssize_t getdelim (char **__restrict __lineptr,
        size_t *__restrict __n, int __delimiter,
        FILE *__restrict __stream) ;







extern __ssize_t getline (char **__restrict __lineptr,
       size_t *__restrict __n,
       FILE *__restrict __stream) ;







extern int fputs (const char *__restrict __s, FILE *__restrict __stream);





extern int puts (const char *__s);






extern int ungetc (int __c, FILE *__stream);






extern size_t fread (void *__restrict __ptr, size_t __size,
       size_t __n, FILE *__restrict __stream) ;




extern size_t fwrite (const void *__restrict __ptr, size_t __size,
        size_t __n, FILE *__restrict __s);
# 662 "/usr/include/stdio.h" 3 4
extern int fputs_unlocked (const char *__restrict __s,
      FILE *__restrict __stream);
# 673 "/usr/include/stdio.h" 3 4
extern size_t fread_unlocked (void *__restrict __ptr, size_t __size,
         size_t __n, FILE *__restrict __stream) ;
extern size_t fwrite_unlocked (const void *__restrict __ptr, size_t __size,
          size_t __n, FILE *__restrict __stream);







extern int fseek (FILE *__stream, long int __off, int __whence);




extern long int ftell (FILE *__stream) ;




extern void rewind (FILE *__stream);
# 707 "/usr/include/stdio.h" 3 4
extern int fseeko (FILE *__stream, __off_t __off, int __whence);




extern __off_t ftello (FILE *__stream) ;
# 731 "/usr/include/stdio.h" 3 4
extern int fgetpos (FILE *__restrict __stream, fpos_t *__restrict __pos);




extern int fsetpos (FILE *__stream, const fpos_t *__pos);
# 750 "/usr/include/stdio.h" 3 4
extern int fseeko64 (FILE *__stream, __off64_t __off, int __whence);
extern __off64_t ftello64 (FILE *__stream) ;
extern int fgetpos64 (FILE *__restrict __stream, fpos64_t *__restrict __pos);
extern int fsetpos64 (FILE *__stream, const fpos64_t *__pos);



extern void clearerr (FILE *__stream) __attribute__ ((__nothrow__ ));

extern int feof (FILE *__stream) __attribute__ ((__nothrow__ )) ;

extern int ferror (FILE *__stream) __attribute__ ((__nothrow__ )) ;



extern void clearerr_unlocked (FILE *__stream) __attribute__ ((__nothrow__ ));
extern int feof_unlocked (FILE *__stream) __attribute__ ((__nothrow__ )) ;
extern int ferror_unlocked (FILE *__stream) __attribute__ ((__nothrow__ )) ;







extern void perror (const char *__s);






# 1 "/usr/include/x86_64-linux-gnu/bits/sys_errlist.h" 1 3 4
# 26 "/usr/include/x86_64-linux-gnu/bits/sys_errlist.h" 3 4
extern int sys_nerr;
extern const char *const sys_errlist[];


extern int _sys_nerr;
extern const char *const _sys_errlist[];
# 782 "/usr/include/stdio.h" 2 3 4




extern int fileno (FILE *__stream) __attribute__ ((__nothrow__ )) ;




extern int fileno_unlocked (FILE *__stream) __attribute__ ((__nothrow__ )) ;
# 800 "/usr/include/stdio.h" 3 4
extern FILE *popen (const char *__command, const char *__modes) ;





extern int pclose (FILE *__stream);





extern char *ctermid (char *__s) __attribute__ ((__nothrow__ ));





extern char *cuserid (char *__s);




struct obstack;


extern int obstack_printf (struct obstack *__restrict __obstack,
      const char *__restrict __format, ...)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 2, 3)));
extern int obstack_vprintf (struct obstack *__restrict __obstack,
       const char *__restrict __format,
       __gnuc_va_list __args)
     __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 2, 0)));







extern void flockfile (FILE *__stream) __attribute__ ((__nothrow__ ));



extern int ftrylockfile (FILE *__stream) __attribute__ ((__nothrow__ )) ;


extern void funlockfile (FILE *__stream) __attribute__ ((__nothrow__ ));
# 44 "../lib/stdio.h" 2 3
# 53 "../lib/stdio.h" 3
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 35 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 3
typedef long int ptrdiff_t;
# 74 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 3
typedef int wchar_t;
# 102 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 3
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/__stddef_max_align_t.h" 1 3
# 19 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/__stddef_max_align_t.h" 3
typedef struct {
  long long __clang_max_align_nonce1
      __attribute__((__aligned__(__alignof__(long long))));
  long double __clang_max_align_nonce2
      __attribute__((__aligned__(__alignof__(long double))));
} max_align_t;
# 103 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 2 3
# 54 "../lib/stdio.h" 2 3




# 1 "../lib/sys/types.h" 1 3
# 21 "../lib/sys/types.h" 3
# 39 "../lib/sys/types.h" 3
# 1 "/usr/include/x86_64-linux-gnu/sys/types.h" 1 3 4
# 33 "/usr/include/x86_64-linux-gnu/sys/types.h" 3 4
typedef __u_char u_char;
typedef __u_short u_short;
typedef __u_int u_int;
typedef __u_long u_long;
typedef __quad_t quad_t;
typedef __u_quad_t u_quad_t;
typedef __fsid_t fsid_t;




typedef __loff_t loff_t;



typedef __ino_t ino_t;






typedef __ino64_t ino64_t;




typedef __dev_t dev_t;




typedef __gid_t gid_t;




typedef __mode_t mode_t;




typedef __nlink_t nlink_t;




typedef __uid_t uid_t;
# 98 "/usr/include/x86_64-linux-gnu/sys/types.h" 3 4
typedef __pid_t pid_t;





typedef __id_t id_t;
# 115 "/usr/include/x86_64-linux-gnu/sys/types.h" 3 4
typedef __daddr_t daddr_t;
typedef __caddr_t caddr_t;





typedef __key_t key_t;





# 1 "/usr/include/x86_64-linux-gnu/bits/types/clock_t.h" 1 3 4






typedef __clock_t clock_t;
# 128 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types/clockid_t.h" 1 3 4






typedef __clockid_t clockid_t;
# 130 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/time_t.h" 1 3 4






typedef __time_t time_t;
# 131 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/timer_t.h" 1 3 4






typedef __timer_t timer_t;
# 132 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4



typedef __useconds_t useconds_t;



typedef __suseconds_t suseconds_t;






# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 146 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4



typedef unsigned long int ulong;
typedef unsigned short int ushort;
typedef unsigned int uint;





# 1 "/usr/include/x86_64-linux-gnu/bits/stdint-intn.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/stdint-intn.h" 3 4
typedef __int8_t int8_t;
typedef __int16_t int16_t;
typedef __int32_t int32_t;
typedef __int64_t int64_t;
# 157 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4
# 178 "/usr/include/x86_64-linux-gnu/sys/types.h" 3 4
typedef unsigned int u_int8_t __attribute__ ((__mode__ (__QI__)));
typedef unsigned int u_int16_t __attribute__ ((__mode__ (__HI__)));
typedef unsigned int u_int32_t __attribute__ ((__mode__ (__SI__)));
typedef unsigned int u_int64_t __attribute__ ((__mode__ (__DI__)));

typedef int register_t __attribute__ ((__mode__ (__word__)));
# 194 "/usr/include/x86_64-linux-gnu/sys/types.h" 3 4
# 1 "/usr/include/endian.h" 1 3 4
# 36 "/usr/include/endian.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/endian.h" 1 3 4
# 37 "/usr/include/endian.h" 2 3 4
# 60 "/usr/include/endian.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/byteswap.h" 1 3 4
# 28 "/usr/include/x86_64-linux-gnu/bits/byteswap.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 29 "/usr/include/x86_64-linux-gnu/bits/byteswap.h" 2 3 4






# 1 "/usr/include/x86_64-linux-gnu/bits/byteswap-16.h" 1 3 4
# 36 "/usr/include/x86_64-linux-gnu/bits/byteswap.h" 2 3 4
# 61 "/usr/include/endian.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/uintn-identity.h" 1 3 4
# 32 "/usr/include/x86_64-linux-gnu/bits/uintn-identity.h" 3 4
static __inline __uint16_t
__uint16_identity (__uint16_t __x)
{
  return __x;
}

static __inline __uint32_t
__uint32_identity (__uint32_t __x)
{
  return __x;
}

static __inline __uint64_t
__uint64_identity (__uint64_t __x)
{
  return __x;
}
# 62 "/usr/include/endian.h" 2 3 4
# 195 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4


# 1 "../lib/sys/select.h" 1 3 4
# 20 "../lib/sys/select.h" 3
# 77 "../lib/sys/select.h" 3
# 1 "../lib/sys/types.h" 1 3
# 21 "../lib/sys/types.h" 3
# 39 "../lib/sys/types.h" 3
# 1 "/usr/include/x86_64-linux-gnu/sys/types.h" 1 3 4
# 40 "../lib/sys/types.h" 2 3
# 78 "../lib/sys/select.h" 2 3
# 100 "../lib/sys/select.h" 3
# 1 "/usr/include/x86_64-linux-gnu/sys/select.h" 1 3 4
# 30 "/usr/include/x86_64-linux-gnu/sys/select.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/select.h" 1 3 4
# 22 "/usr/include/x86_64-linux-gnu/bits/select.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/bits/select.h" 2 3 4
# 31 "/usr/include/x86_64-linux-gnu/sys/select.h" 2 3 4


# 1 "/usr/include/x86_64-linux-gnu/bits/types/sigset_t.h" 1 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/types/__sigset_t.h" 1 3 4




typedef struct
{
  unsigned long int __val[(1024 / (8 * sizeof (unsigned long int)))];
} __sigset_t;
# 5 "/usr/include/x86_64-linux-gnu/bits/types/sigset_t.h" 2 3 4


typedef __sigset_t sigset_t;
# 34 "/usr/include/x86_64-linux-gnu/sys/select.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/types/struct_timeval.h" 1 3 4







struct timeval
{
  __time_t tv_sec;
  __suseconds_t tv_usec;
};
# 38 "/usr/include/x86_64-linux-gnu/sys/select.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types/struct_timespec.h" 1 3 4








struct timespec
{
  __time_t tv_sec;
  __syscall_slong_t tv_nsec;
};
# 40 "/usr/include/x86_64-linux-gnu/sys/select.h" 2 3 4
# 49 "/usr/include/x86_64-linux-gnu/sys/select.h" 3 4
typedef long int __fd_mask;
# 59 "/usr/include/x86_64-linux-gnu/sys/select.h" 3 4
typedef struct
  {



    __fd_mask fds_bits[1024 / (8 * (int) sizeof (__fd_mask))];





  } fd_set;






typedef __fd_mask fd_mask;
# 101 "/usr/include/x86_64-linux-gnu/sys/select.h" 3 4
extern int select (int __nfds, fd_set *__restrict __readfds,
     fd_set *__restrict __writefds,
     fd_set *__restrict __exceptfds,
     struct timeval *__restrict __timeout);
# 113 "/usr/include/x86_64-linux-gnu/sys/select.h" 3 4
extern int pselect (int __nfds, fd_set *__restrict __readfds,
      fd_set *__restrict __writefds,
      fd_set *__restrict __exceptfds,
      const struct timespec *__restrict __timeout,
      const __sigset_t *__restrict __sigmask);
# 101 "../lib/sys/select.h" 2 3
# 745 "../lib/sys/select.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 198 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4







# 1 "/usr/include/x86_64-linux-gnu/sys/sysmacros.h" 1 3 4
# 41 "/usr/include/x86_64-linux-gnu/sys/sysmacros.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/sysmacros.h" 1 3 4
# 42 "/usr/include/x86_64-linux-gnu/sys/sysmacros.h" 2 3 4
# 73 "/usr/include/x86_64-linux-gnu/sys/sysmacros.h" 3 4
extern unsigned int gnu_dev_major (__dev_t __dev) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
extern unsigned int gnu_dev_minor (__dev_t __dev) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
extern __dev_t gnu_dev_makedev (unsigned int __major, unsigned int __minor) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
# 206 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4






typedef __blksize_t blksize_t;






typedef __blkcnt_t blkcnt_t;



typedef __fsblkcnt_t fsblkcnt_t;



typedef __fsfilcnt_t fsfilcnt_t;
# 246 "/usr/include/x86_64-linux-gnu/sys/types.h" 3 4
typedef __blkcnt64_t blkcnt64_t;
typedef __fsblkcnt64_t fsblkcnt64_t;
typedef __fsfilcnt64_t fsfilcnt64_t;






# 1 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/thread-shared-types.h" 1 3 4
# 77 "/usr/include/x86_64-linux-gnu/bits/thread-shared-types.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes-arch.h" 1 3 4
# 21 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes-arch.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 22 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes-arch.h" 2 3 4
# 65 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes-arch.h" 3 4
struct __pthread_rwlock_arch_t
{
  unsigned int __readers;
  unsigned int __writers;
  unsigned int __wrphase_futex;
  unsigned int __writers_futex;
  unsigned int __pad3;
  unsigned int __pad4;

  int __cur_writer;
  int __shared;
  signed char __rwelision;




  unsigned char __pad1[7];


  unsigned long int __pad2;


  unsigned int __flags;
# 99 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes-arch.h" 3 4
};
# 78 "/usr/include/x86_64-linux-gnu/bits/thread-shared-types.h" 2 3 4




typedef struct __pthread_internal_list
{
  struct __pthread_internal_list *__prev;
  struct __pthread_internal_list *__next;
} __pthread_list_t;
# 118 "/usr/include/x86_64-linux-gnu/bits/thread-shared-types.h" 3 4
struct __pthread_mutex_s
{
  int __lock ;
  unsigned int __count;
  int __owner;

  unsigned int __nusers;
# 148 "/usr/include/x86_64-linux-gnu/bits/thread-shared-types.h" 3 4
  int __kind;





  short __spins; short __elision;
  __pthread_list_t __list;
# 166 "/usr/include/x86_64-linux-gnu/bits/thread-shared-types.h" 3 4
};




struct __pthread_cond_s
{
  __extension__ union
  {
    __extension__ unsigned long long int __wseq;
    struct
    {
      unsigned int __low;
      unsigned int __high;
    } __wseq32;
  };
  __extension__ union
  {
    __extension__ unsigned long long int __g1_start;
    struct
    {
      unsigned int __low;
      unsigned int __high;
    } __g1_start32;
  };
  unsigned int __g_refs[2] ;
  unsigned int __g_size[2];
  unsigned int __g1_orig_size;
  unsigned int __wrefs;
  unsigned int __g_signals[2];
};
# 24 "/usr/include/x86_64-linux-gnu/bits/pthreadtypes.h" 2 3 4



typedef unsigned long int pthread_t;




typedef union
{
  char __size[4];
  int __align;
} pthread_mutexattr_t;




typedef union
{
  char __size[4];
  int __align;
} pthread_condattr_t;



typedef unsigned int pthread_key_t;



typedef int pthread_once_t;


union pthread_attr_t
{
  char __size[56];
  long int __align;
};

typedef union pthread_attr_t pthread_attr_t;




typedef union
{
  struct __pthread_mutex_s __data;
  char __size[40];
  long int __align;
} pthread_mutex_t;


typedef union
{
  struct __pthread_cond_s __data;
  char __size[48];
  __extension__ long long int __align;
} pthread_cond_t;





typedef union
{
  struct __pthread_rwlock_arch_t __data;
  char __size[56];
  long int __align;
} pthread_rwlock_t;

typedef union
{
  char __size[8];
  long int __align;
} pthread_rwlockattr_t;





typedef volatile int pthread_spinlock_t;




typedef union
{
  char __size[32];
  long int __align;
} pthread_barrier_t;

typedef union
{
  char __size[4];
  int __align;
} pthread_barrierattr_t;
# 255 "/usr/include/x86_64-linux-gnu/sys/types.h" 2 3 4
# 40 "../lib/sys/types.h" 2 3
# 59 "../lib/stdio.h" 2 3
# 672 "../lib/stdio.h" 3
extern int rpl_fclose (FILE *stream) __attribute__ ((__nonnull__ (1)));
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 697 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 718 "../lib/stdio.h" 3
extern int rpl_fflush (FILE *gl_stream);
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 742 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 761 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 781 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 815 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 847 "../lib/stdio.h" 3
extern int fpurge (FILE *gl_stream) __attribute__ ((__nonnull__ (1)));

extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 869 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 888 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 910 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 933 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 961 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1011 "../lib/stdio.h" 3
extern int rpl_fseek (FILE *fp, long offset, int whence) __attribute__ ((__nonnull__ (1)));

extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 1034 "../lib/stdio.h" 3
extern int rpl_fseeko (FILE *fp, off_t offset, int whence) __attribute__ ((__nonnull__ (1)));

extern int _gl_cxxalias_dummy;







extern int _gl_cxxalias_dummy;
# 1080 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1103 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1140 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;
# 1168 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;
# 1181 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1197 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1233 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 1273 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 1445 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1470 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1486 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1502 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1518 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1542 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1572 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1610 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1638 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1716 "../lib/stdio.h" 3
extern int rpl_asprintf (char **result, const char *format, ...) __attribute__ ((__format__ (__printf__, 2, 3))) __attribute__ ((__nonnull__ (1, 2)));



extern int _gl_cxxalias_dummy;
# 1732 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;




extern int rpl_vasprintf (char **result, const char *format, va_list args) __attribute__ ((__format__ (__printf__, 2, 0))) __attribute__ ((__nonnull__ (1, 2)));



extern int _gl_cxxalias_dummy;
# 1753 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;
# 1798 "../lib/stdio.h" 3
extern int rpl_vfprintf (FILE *__restrict fp, const char *__restrict format, va_list args) __attribute__ ((__format__ (__printf__, 2, 0))) __attribute__ ((__nonnull__ (1, 2)));
# 1810 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;
# 1822 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;
# 1865 "../lib/stdio.h" 3
extern int rpl_vprintf (const char *__restrict format, va_list args) __attribute__ ((__format__ (__printf__, 1, 0))) __attribute__ ((__nonnull__ (1)));







extern int _gl_cxxalias_dummy;
# 1882 "../lib/stdio.h" 3
extern int _gl_cxxalias_dummy;
# 21 "numfmt.c" 2
# 1 "../lib/sys/types.h" 1
# 21 "../lib/sys/types.h" 3
# 22 "numfmt.c" 2
# 1 "../lib/langinfo.h" 1
# 27 "../lib/langinfo.h" 3





# 1 "/usr/include/langinfo.h" 1 3 4
# 23 "/usr/include/langinfo.h" 3 4
# 1 "/usr/include/nl_types.h" 1 3 4
# 33 "/usr/include/nl_types.h" 3 4
typedef void *nl_catd;


typedef int nl_item;





extern nl_catd catopen (const char *__cat_name, int __flag) __attribute__ ((__nonnull__ (1)));



extern char *catgets (nl_catd __catalog, int __set, int __number,
        const char *__string) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int catclose (nl_catd __catalog) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 24 "/usr/include/langinfo.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/locale.h" 1 3 4
# 26 "/usr/include/langinfo.h" 2 3 4
# 41 "/usr/include/langinfo.h" 3 4
enum
{



  ABDAY_1 = (((2) << 16) | (0)),

  ABDAY_2,

  ABDAY_3,

  ABDAY_4,

  ABDAY_5,

  ABDAY_6,

  ABDAY_7,



  DAY_1,

  DAY_2,

  DAY_3,

  DAY_4,

  DAY_5,

  DAY_6,

  DAY_7,




  ABMON_1,

  ABMON_2,

  ABMON_3,

  ABMON_4,

  ABMON_5,

  ABMON_6,

  ABMON_7,

  ABMON_8,

  ABMON_9,

  ABMON_10,

  ABMON_11,

  ABMON_12,




  MON_1,

  MON_2,

  MON_3,

  MON_4,

  MON_5,

  MON_6,

  MON_7,

  MON_8,

  MON_9,

  MON_10,

  MON_11,

  MON_12,


  AM_STR,

  PM_STR,


  D_T_FMT,

  D_FMT,

  T_FMT,

  T_FMT_AMPM,


  ERA,

  __ERA_YEAR,



  ERA_D_FMT,

  ALT_DIGITS,

  ERA_D_T_FMT,

  ERA_T_FMT,


  _NL_TIME_ERA_NUM_ENTRIES,
  _NL_TIME_ERA_ENTRIES,

  _NL_WABDAY_1,
  _NL_WABDAY_2,
  _NL_WABDAY_3,
  _NL_WABDAY_4,
  _NL_WABDAY_5,
  _NL_WABDAY_6,
  _NL_WABDAY_7,


  _NL_WDAY_1,
  _NL_WDAY_2,
  _NL_WDAY_3,
  _NL_WDAY_4,
  _NL_WDAY_5,
  _NL_WDAY_6,
  _NL_WDAY_7,



  _NL_WABMON_1,
  _NL_WABMON_2,
  _NL_WABMON_3,
  _NL_WABMON_4,
  _NL_WABMON_5,
  _NL_WABMON_6,
  _NL_WABMON_7,
  _NL_WABMON_8,
  _NL_WABMON_9,
  _NL_WABMON_10,
  _NL_WABMON_11,
  _NL_WABMON_12,



  _NL_WMON_1,
  _NL_WMON_2,
  _NL_WMON_3,
  _NL_WMON_4,
  _NL_WMON_5,
  _NL_WMON_6,
  _NL_WMON_7,
  _NL_WMON_8,
  _NL_WMON_9,
  _NL_WMON_10,
  _NL_WMON_11,
  _NL_WMON_12,

  _NL_WAM_STR,
  _NL_WPM_STR,

  _NL_WD_T_FMT,
  _NL_WD_FMT,
  _NL_WT_FMT,
  _NL_WT_FMT_AMPM,

  _NL_WERA_YEAR,
  _NL_WERA_D_FMT,
  _NL_WALT_DIGITS,
  _NL_WERA_D_T_FMT,
  _NL_WERA_T_FMT,

  _NL_TIME_WEEK_NDAYS,
  _NL_TIME_WEEK_1STDAY,
  _NL_TIME_WEEK_1STWEEK,
  _NL_TIME_FIRST_WEEKDAY,
  _NL_TIME_FIRST_WORKDAY,
  _NL_TIME_CAL_DIRECTION,
  _NL_TIME_TIMEZONE,

  _DATE_FMT,

  _NL_W_DATE_FMT,

  _NL_TIME_CODESET,



  __ALTMON_1,
  __ALTMON_2,
  __ALTMON_3,
  __ALTMON_4,
  __ALTMON_5,
  __ALTMON_6,
  __ALTMON_7,
  __ALTMON_8,
  __ALTMON_9,
  __ALTMON_10,
  __ALTMON_11,
  __ALTMON_12,
# 269 "/usr/include/langinfo.h" 3 4
  _NL_WALTMON_1,
  _NL_WALTMON_2,
  _NL_WALTMON_3,
  _NL_WALTMON_4,
  _NL_WALTMON_5,
  _NL_WALTMON_6,
  _NL_WALTMON_7,
  _NL_WALTMON_8,
  _NL_WALTMON_9,
  _NL_WALTMON_10,
  _NL_WALTMON_11,
  _NL_WALTMON_12,



  _NL_ABALTMON_1,
  _NL_ABALTMON_2,
  _NL_ABALTMON_3,
  _NL_ABALTMON_4,
  _NL_ABALTMON_5,
  _NL_ABALTMON_6,
  _NL_ABALTMON_7,
  _NL_ABALTMON_8,
  _NL_ABALTMON_9,
  _NL_ABALTMON_10,
  _NL_ABALTMON_11,
  _NL_ABALTMON_12,



  _NL_WABALTMON_1,
  _NL_WABALTMON_2,
  _NL_WABALTMON_3,
  _NL_WABALTMON_4,
  _NL_WABALTMON_5,
  _NL_WABALTMON_6,
  _NL_WABALTMON_7,
  _NL_WABALTMON_8,
  _NL_WABALTMON_9,
  _NL_WABALTMON_10,
  _NL_WABALTMON_11,
  _NL_WABALTMON_12,

  _NL_NUM_LC_TIME,




  _NL_COLLATE_NRULES = (((3) << 16) | (0)),
  _NL_COLLATE_RULESETS,
  _NL_COLLATE_TABLEMB,
  _NL_COLLATE_WEIGHTMB,
  _NL_COLLATE_EXTRAMB,
  _NL_COLLATE_INDIRECTMB,
  _NL_COLLATE_GAP1,
  _NL_COLLATE_GAP2,
  _NL_COLLATE_GAP3,
  _NL_COLLATE_TABLEWC,
  _NL_COLLATE_WEIGHTWC,
  _NL_COLLATE_EXTRAWC,
  _NL_COLLATE_INDIRECTWC,
  _NL_COLLATE_SYMB_HASH_SIZEMB,
  _NL_COLLATE_SYMB_TABLEMB,
  _NL_COLLATE_SYMB_EXTRAMB,
  _NL_COLLATE_COLLSEQMB,
  _NL_COLLATE_COLLSEQWC,
  _NL_COLLATE_CODESET,
  _NL_NUM_LC_COLLATE,




  _NL_CTYPE_CLASS = (((0) << 16) | (0)),
  _NL_CTYPE_TOUPPER,
  _NL_CTYPE_GAP1,
  _NL_CTYPE_TOLOWER,
  _NL_CTYPE_GAP2,
  _NL_CTYPE_CLASS32,
  _NL_CTYPE_GAP3,
  _NL_CTYPE_GAP4,
  _NL_CTYPE_GAP5,
  _NL_CTYPE_GAP6,
  _NL_CTYPE_CLASS_NAMES,
  _NL_CTYPE_MAP_NAMES,
  _NL_CTYPE_WIDTH,
  _NL_CTYPE_MB_CUR_MAX,
  _NL_CTYPE_CODESET_NAME,
  CODESET = _NL_CTYPE_CODESET_NAME,

  _NL_CTYPE_TOUPPER32,
  _NL_CTYPE_TOLOWER32,
  _NL_CTYPE_CLASS_OFFSET,
  _NL_CTYPE_MAP_OFFSET,
  _NL_CTYPE_INDIGITS_MB_LEN,
  _NL_CTYPE_INDIGITS0_MB,
  _NL_CTYPE_INDIGITS1_MB,
  _NL_CTYPE_INDIGITS2_MB,
  _NL_CTYPE_INDIGITS3_MB,
  _NL_CTYPE_INDIGITS4_MB,
  _NL_CTYPE_INDIGITS5_MB,
  _NL_CTYPE_INDIGITS6_MB,
  _NL_CTYPE_INDIGITS7_MB,
  _NL_CTYPE_INDIGITS8_MB,
  _NL_CTYPE_INDIGITS9_MB,
  _NL_CTYPE_INDIGITS_WC_LEN,
  _NL_CTYPE_INDIGITS0_WC,
  _NL_CTYPE_INDIGITS1_WC,
  _NL_CTYPE_INDIGITS2_WC,
  _NL_CTYPE_INDIGITS3_WC,
  _NL_CTYPE_INDIGITS4_WC,
  _NL_CTYPE_INDIGITS5_WC,
  _NL_CTYPE_INDIGITS6_WC,
  _NL_CTYPE_INDIGITS7_WC,
  _NL_CTYPE_INDIGITS8_WC,
  _NL_CTYPE_INDIGITS9_WC,
  _NL_CTYPE_OUTDIGIT0_MB,
  _NL_CTYPE_OUTDIGIT1_MB,
  _NL_CTYPE_OUTDIGIT2_MB,
  _NL_CTYPE_OUTDIGIT3_MB,
  _NL_CTYPE_OUTDIGIT4_MB,
  _NL_CTYPE_OUTDIGIT5_MB,
  _NL_CTYPE_OUTDIGIT6_MB,
  _NL_CTYPE_OUTDIGIT7_MB,
  _NL_CTYPE_OUTDIGIT8_MB,
  _NL_CTYPE_OUTDIGIT9_MB,
  _NL_CTYPE_OUTDIGIT0_WC,
  _NL_CTYPE_OUTDIGIT1_WC,
  _NL_CTYPE_OUTDIGIT2_WC,
  _NL_CTYPE_OUTDIGIT3_WC,
  _NL_CTYPE_OUTDIGIT4_WC,
  _NL_CTYPE_OUTDIGIT5_WC,
  _NL_CTYPE_OUTDIGIT6_WC,
  _NL_CTYPE_OUTDIGIT7_WC,
  _NL_CTYPE_OUTDIGIT8_WC,
  _NL_CTYPE_OUTDIGIT9_WC,
  _NL_CTYPE_TRANSLIT_TAB_SIZE,
  _NL_CTYPE_TRANSLIT_FROM_IDX,
  _NL_CTYPE_TRANSLIT_FROM_TBL,
  _NL_CTYPE_TRANSLIT_TO_IDX,
  _NL_CTYPE_TRANSLIT_TO_TBL,
  _NL_CTYPE_TRANSLIT_DEFAULT_MISSING_LEN,
  _NL_CTYPE_TRANSLIT_DEFAULT_MISSING,
  _NL_CTYPE_TRANSLIT_IGNORE_LEN,
  _NL_CTYPE_TRANSLIT_IGNORE,
  _NL_CTYPE_MAP_TO_NONASCII,
  _NL_CTYPE_NONASCII_CASE,
  _NL_CTYPE_EXTRA_MAP_1,
  _NL_CTYPE_EXTRA_MAP_2,
  _NL_CTYPE_EXTRA_MAP_3,
  _NL_CTYPE_EXTRA_MAP_4,
  _NL_CTYPE_EXTRA_MAP_5,
  _NL_CTYPE_EXTRA_MAP_6,
  _NL_CTYPE_EXTRA_MAP_7,
  _NL_CTYPE_EXTRA_MAP_8,
  _NL_CTYPE_EXTRA_MAP_9,
  _NL_CTYPE_EXTRA_MAP_10,
  _NL_CTYPE_EXTRA_MAP_11,
  _NL_CTYPE_EXTRA_MAP_12,
  _NL_CTYPE_EXTRA_MAP_13,
  _NL_CTYPE_EXTRA_MAP_14,
  _NL_NUM_LC_CTYPE,




  __INT_CURR_SYMBOL = (((4) << 16) | (0)),



  __CURRENCY_SYMBOL,



  __MON_DECIMAL_POINT,



  __MON_THOUSANDS_SEP,



  __MON_GROUPING,



  __POSITIVE_SIGN,



  __NEGATIVE_SIGN,



  __INT_FRAC_DIGITS,



  __FRAC_DIGITS,



  __P_CS_PRECEDES,



  __P_SEP_BY_SPACE,



  __N_CS_PRECEDES,



  __N_SEP_BY_SPACE,



  __P_SIGN_POSN,



  __N_SIGN_POSN,



  _NL_MONETARY_CRNCYSTR,

  __INT_P_CS_PRECEDES,



  __INT_P_SEP_BY_SPACE,



  __INT_N_CS_PRECEDES,



  __INT_N_SEP_BY_SPACE,



  __INT_P_SIGN_POSN,



  __INT_N_SIGN_POSN,



  _NL_MONETARY_DUO_INT_CURR_SYMBOL,
  _NL_MONETARY_DUO_CURRENCY_SYMBOL,
  _NL_MONETARY_DUO_INT_FRAC_DIGITS,
  _NL_MONETARY_DUO_FRAC_DIGITS,
  _NL_MONETARY_DUO_P_CS_PRECEDES,
  _NL_MONETARY_DUO_P_SEP_BY_SPACE,
  _NL_MONETARY_DUO_N_CS_PRECEDES,
  _NL_MONETARY_DUO_N_SEP_BY_SPACE,
  _NL_MONETARY_DUO_INT_P_CS_PRECEDES,
  _NL_MONETARY_DUO_INT_P_SEP_BY_SPACE,
  _NL_MONETARY_DUO_INT_N_CS_PRECEDES,
  _NL_MONETARY_DUO_INT_N_SEP_BY_SPACE,
  _NL_MONETARY_DUO_P_SIGN_POSN,
  _NL_MONETARY_DUO_N_SIGN_POSN,
  _NL_MONETARY_DUO_INT_P_SIGN_POSN,
  _NL_MONETARY_DUO_INT_N_SIGN_POSN,
  _NL_MONETARY_UNO_VALID_FROM,
  _NL_MONETARY_UNO_VALID_TO,
  _NL_MONETARY_DUO_VALID_FROM,
  _NL_MONETARY_DUO_VALID_TO,
  _NL_MONETARY_CONVERSION_RATE,
  _NL_MONETARY_DECIMAL_POINT_WC,
  _NL_MONETARY_THOUSANDS_SEP_WC,
  _NL_MONETARY_CODESET,
  _NL_NUM_LC_MONETARY,



  __DECIMAL_POINT = (((1) << 16) | (0)),



  RADIXCHAR = __DECIMAL_POINT,

  __THOUSANDS_SEP,



  THOUSEP = __THOUSANDS_SEP,

  __GROUPING,



  _NL_NUMERIC_DECIMAL_POINT_WC,
  _NL_NUMERIC_THOUSANDS_SEP_WC,
  _NL_NUMERIC_CODESET,
  _NL_NUM_LC_NUMERIC,

  __YESEXPR = (((5) << 16) | (0)),

  __NOEXPR,

  __YESSTR,



  __NOSTR,



  _NL_MESSAGES_CODESET,
  _NL_NUM_LC_MESSAGES,

  _NL_PAPER_HEIGHT = (((7) << 16) | (0)),
  _NL_PAPER_WIDTH,
  _NL_PAPER_CODESET,
  _NL_NUM_LC_PAPER,

  _NL_NAME_NAME_FMT = (((8) << 16) | (0)),
  _NL_NAME_NAME_GEN,
  _NL_NAME_NAME_MR,
  _NL_NAME_NAME_MRS,
  _NL_NAME_NAME_MISS,
  _NL_NAME_NAME_MS,
  _NL_NAME_CODESET,
  _NL_NUM_LC_NAME,

  _NL_ADDRESS_POSTAL_FMT = (((9) << 16) | (0)),
  _NL_ADDRESS_COUNTRY_NAME,
  _NL_ADDRESS_COUNTRY_POST,
  _NL_ADDRESS_COUNTRY_AB2,
  _NL_ADDRESS_COUNTRY_AB3,
  _NL_ADDRESS_COUNTRY_CAR,
  _NL_ADDRESS_COUNTRY_NUM,
  _NL_ADDRESS_COUNTRY_ISBN,
  _NL_ADDRESS_LANG_NAME,
  _NL_ADDRESS_LANG_AB,
  _NL_ADDRESS_LANG_TERM,
  _NL_ADDRESS_LANG_LIB,
  _NL_ADDRESS_CODESET,
  _NL_NUM_LC_ADDRESS,

  _NL_TELEPHONE_TEL_INT_FMT = (((10) << 16) | (0)),
  _NL_TELEPHONE_TEL_DOM_FMT,
  _NL_TELEPHONE_INT_SELECT,
  _NL_TELEPHONE_INT_PREFIX,
  _NL_TELEPHONE_CODESET,
  _NL_NUM_LC_TELEPHONE,

  _NL_MEASUREMENT_MEASUREMENT = (((11) << 16) | (0)),
  _NL_MEASUREMENT_CODESET,
  _NL_NUM_LC_MEASUREMENT,

  _NL_IDENTIFICATION_TITLE = (((12) << 16) | (0)),
  _NL_IDENTIFICATION_SOURCE,
  _NL_IDENTIFICATION_ADDRESS,
  _NL_IDENTIFICATION_CONTACT,
  _NL_IDENTIFICATION_EMAIL,
  _NL_IDENTIFICATION_TEL,
  _NL_IDENTIFICATION_FAX,
  _NL_IDENTIFICATION_LANGUAGE,
  _NL_IDENTIFICATION_TERRITORY,
  _NL_IDENTIFICATION_AUDIENCE,
  _NL_IDENTIFICATION_APPLICATION,
  _NL_IDENTIFICATION_ABBREVIATION,
  _NL_IDENTIFICATION_REVISION,
  _NL_IDENTIFICATION_DATE,
  _NL_IDENTIFICATION_CATEGORY,
  _NL_IDENTIFICATION_CODESET,
  _NL_NUM_LC_IDENTIFICATION,


  _NL_NUM
};
# 661 "/usr/include/langinfo.h" 3 4
extern char *nl_langinfo (nl_item __item) __attribute__ ((__nothrow__ ));





# 1 "/usr/include/x86_64-linux-gnu/bits/types/locale_t.h" 1 3 4
# 22 "/usr/include/x86_64-linux-gnu/bits/types/locale_t.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/__locale_t.h" 1 3 4
# 28 "/usr/include/x86_64-linux-gnu/bits/types/__locale_t.h" 3 4
struct __locale_struct
{

  struct __locale_data *__locales[13];


  const unsigned short int *__ctype_b;
  const int *__ctype_tolower;
  const int *__ctype_toupper;


  const char *__names[13];
};

typedef struct __locale_struct *__locale_t;
# 23 "/usr/include/x86_64-linux-gnu/bits/types/locale_t.h" 2 3 4

typedef __locale_t locale_t;
# 667 "/usr/include/langinfo.h" 2 3 4


extern char *nl_langinfo_l (nl_item __item, locale_t __l);
# 33 "../lib/langinfo.h" 2 3
# 654 "../lib/langinfo.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 23 "numfmt.c" 2

# 1 "../lib/mbsalign.h" 1
# 17 "../lib/mbsalign.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 18 "../lib/mbsalign.h" 2

typedef enum { MBS_ALIGN_LEFT, MBS_ALIGN_RIGHT, MBS_ALIGN_CENTER } mbs_align_t;

enum {


  MBA_UNIBYTE_FALLBACK = 0x0001,



  MBA_UNIBYTE_ONLY = 0x0002,


  MBA_NO_LEFT_PAD = 0x0004,


  MBA_NO_RIGHT_PAD = 0x0008
# 52 "../lib/mbsalign.h"
};

size_t
mbsalign (const char *src, char *dest, size_t dest_size,
          size_t *width, mbs_align_t align, int flags);

char *
ambsalign (const char *src, size_t *width, mbs_align_t align, int flags);
# 25 "numfmt.c" 2
# 1 "../lib/argmatch.h" 1
# 25 "../lib/argmatch.h"
# 1 "../lib/limits.h" 1
# 23 "../lib/limits.h" 3




# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/limits.h" 1 3
# 21 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/limits.h" 3
# 1 "/usr/include/limits.h" 1 3 4
# 26 "/usr/include/limits.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/libc-header-start.h" 1 3 4
# 27 "/usr/include/limits.h" 2 3 4
# 183 "/usr/include/limits.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/posix1_lim.h" 1 3 4
# 160 "/usr/include/x86_64-linux-gnu/bits/posix1_lim.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/local_lim.h" 1 3 4
# 38 "/usr/include/x86_64-linux-gnu/bits/local_lim.h" 3 4
# 1 "/usr/include/linux/limits.h" 1 3 4
# 39 "/usr/include/x86_64-linux-gnu/bits/local_lim.h" 2 3 4
# 161 "/usr/include/x86_64-linux-gnu/bits/posix1_lim.h" 2 3 4
# 184 "/usr/include/limits.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/posix2_lim.h" 1 3 4
# 188 "/usr/include/limits.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/xopen_lim.h" 1 3 4
# 64 "/usr/include/x86_64-linux-gnu/bits/xopen_lim.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/uio_lim.h" 1 3 4
# 65 "/usr/include/x86_64-linux-gnu/bits/xopen_lim.h" 2 3 4
# 192 "/usr/include/limits.h" 2 3 4
# 22 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/limits.h" 2 3
# 28 "../lib/limits.h" 2 3
# 26 "../lib/argmatch.h" 2
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdbool.h" 1 3
# 27 "../lib/argmatch.h" 2
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 28 "../lib/argmatch.h" 2
# 1 "../lib/stdio.h" 1
# 21 "../lib/stdio.h" 3
# 29 "../lib/argmatch.h" 2
# 1 "../lib/string.h" 1
# 21 "../lib/string.h" 3
# 41 "../lib/string.h" 3
# 1 "/usr/include/string.h" 1 3 4
# 26 "/usr/include/string.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/libc-header-start.h" 1 3 4
# 27 "/usr/include/string.h" 2 3 4






# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 34 "/usr/include/string.h" 2 3 4








extern void *memcpy (void *__restrict __dest, const void *__restrict __src,
       size_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern void *memmove (void *__dest, const void *__src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));





extern void *memccpy (void *__restrict __dest, const void *__restrict __src,
        int __c, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern void *memset (void *__s, int __c, size_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int memcmp (const void *__s1, const void *__s2, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 90 "/usr/include/string.h" 3 4
extern void *memchr (const void *__s, int __c, size_t __n)
      __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));
# 103 "/usr/include/string.h" 3 4
extern void *rawmemchr (const void *__s, int __c)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));
# 114 "/usr/include/string.h" 3 4
extern void *memrchr (const void *__s, int __c, size_t __n)
      __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));





extern char *strcpy (char *__restrict __dest, const char *__restrict __src)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));

extern char *strncpy (char *__restrict __dest,
        const char *__restrict __src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern char *strcat (char *__restrict __dest, const char *__restrict __src)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));

extern char *strncat (char *__restrict __dest, const char *__restrict __src,
        size_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern int strcmp (const char *__s1, const char *__s2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));

extern int strncmp (const char *__s1, const char *__s2, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));


extern int strcoll (const char *__s1, const char *__s2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));

extern size_t strxfrm (char *__restrict __dest,
         const char *__restrict __src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));






extern int strcoll_l (const char *__s1, const char *__s2, locale_t __l)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2, 3)));


extern size_t strxfrm_l (char *__dest, const char *__src, size_t __n,
    locale_t __l) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 4)));





extern char *strdup (const char *__s)
     __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) __attribute__ ((__nonnull__ (1)));






extern char *strndup (const char *__string, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) __attribute__ ((__nonnull__ (1)));
# 225 "/usr/include/string.h" 3 4
extern char *strchr (const char *__s, int __c)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));
# 252 "/usr/include/string.h" 3 4
extern char *strrchr (const char *__s, int __c)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));
# 265 "/usr/include/string.h" 3 4
extern char *strchrnul (const char *__s, int __c)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));





extern size_t strcspn (const char *__s, const char *__reject)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));


extern size_t strspn (const char *__s, const char *__accept)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 302 "/usr/include/string.h" 3 4
extern char *strpbrk (const char *__s, const char *__accept)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 329 "/usr/include/string.h" 3 4
extern char *strstr (const char *__haystack, const char *__needle)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));




extern char *strtok (char *__restrict __s, const char *__restrict __delim)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));



extern char *__strtok_r (char *__restrict __s,
    const char *__restrict __delim,
    char **__restrict __save_ptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));

extern char *strtok_r (char *__restrict __s, const char *__restrict __delim,
         char **__restrict __save_ptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
# 359 "/usr/include/string.h" 3 4
extern char *strcasestr (const char *__haystack, const char *__needle)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));







extern void *memmem (const void *__haystack, size_t __haystacklen,
       const void *__needle, size_t __needlelen)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 3)));



extern void *__mempcpy (void *__restrict __dest,
   const void *__restrict __src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern void *mempcpy (void *__restrict __dest,
        const void *__restrict __src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern size_t strlen (const char *__s)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));




extern size_t strnlen (const char *__string, size_t __maxlen)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));




extern char *strerror (int __errnum) __attribute__ ((__nothrow__ ));
# 420 "/usr/include/string.h" 3 4
extern char *strerror_r (int __errnum, char *__buf, size_t __buflen)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2))) ;





extern char *strerror_l (int __errnum, locale_t __l) __attribute__ ((__nothrow__ ));




# 1 "/usr/include/strings.h" 1 3 4
# 23 "/usr/include/strings.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 24 "/usr/include/strings.h" 2 3 4
# 34 "/usr/include/strings.h" 3 4
extern int bcmp (const void *__s1, const void *__s2, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));


extern void bcopy (const void *__src, void *__dest, size_t __n)
  __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern void bzero (void *__s, size_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 68 "/usr/include/strings.h" 3 4
extern char *index (const char *__s, int __c)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));
# 96 "/usr/include/strings.h" 3 4
extern char *rindex (const char *__s, int __c)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));






extern int ffs (int __i) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));





extern int ffsl (long int __l) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
__extension__ extern int ffsll (long long int __ll)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__));



extern int strcasecmp (const char *__s1, const char *__s2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));


extern int strncasecmp (const char *__s1, const char *__s2, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));






extern int strcasecmp_l (const char *__s1, const char *__s2, locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2, 3)));



extern int strncasecmp_l (const char *__s1, const char *__s2,
     size_t __n, locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2, 4)));
# 432 "/usr/include/string.h" 2 3 4



extern void explicit_bzero (void *__s, size_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern char *strsep (char **__restrict __stringp,
       const char *__restrict __delim)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern char *strsignal (int __sig) __attribute__ ((__nothrow__ ));


extern char *__stpcpy (char *__restrict __dest, const char *__restrict __src)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern char *stpcpy (char *__restrict __dest, const char *__restrict __src)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));



extern char *__stpncpy (char *__restrict __dest,
   const char *__restrict __src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern char *stpncpy (char *__restrict __dest,
        const char *__restrict __src, size_t __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern int strverscmp (const char *__s1, const char *__s2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));


extern char *strfry (char *__string) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern void *memfrob (void *__s, size_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 486 "/usr/include/string.h" 3 4
extern char *basename (const char *__filename) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 42 "../lib/string.h" 2 3







# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 50 "../lib/string.h" 2 3
# 555 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 614 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;
# 624 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;
# 678 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 700 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;







extern int _gl_cxxalias_dummy;
# 755 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 788 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 867 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 891 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 920 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 950 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1084 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;
# 1094 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;
# 1241 "../lib/string.h" 3
extern size_t mbslen (const char *string) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));


extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1271 "../lib/string.h" 3
extern char * mbschr (const char *string, int c) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1)));


extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1306 "../lib/string.h" 3
extern char * mbsstr (const char *haystack, const char *needle)
     __attribute__ ((__pure__))
     __attribute__ ((__nonnull__ (1, 2)));
# 1318 "../lib/string.h" 3
extern int mbscasecmp (const char *s1, const char *s2)
     __attribute__ ((__pure__))
     __attribute__ ((__nonnull__ (1, 2)));
# 1458 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1512 "../lib/string.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 30 "../lib/argmatch.h" 2

# 1 "../lib/gettext.h" 1
# 26 "../lib/gettext.h"
# 1 "/usr/include/libintl.h" 1 3 4
# 39 "/usr/include/libintl.h" 3 4
extern char *gettext (const char *__msgid)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (1)));



extern char *dgettext (const char *__domainname, const char *__msgid)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (2)));
extern char *__dgettext (const char *__domainname, const char *__msgid)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (2)));



extern char *dcgettext (const char *__domainname,
   const char *__msgid, int __category)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (2)));
extern char *__dcgettext (const char *__domainname,
     const char *__msgid, int __category)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (2)));




extern char *ngettext (const char *__msgid1, const char *__msgid2,
         unsigned long int __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (1))) __attribute__ ((__format_arg__ (2)));



extern char *dngettext (const char *__domainname, const char *__msgid1,
   const char *__msgid2, unsigned long int __n)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (2))) __attribute__ ((__format_arg__ (3)));



extern char *dcngettext (const char *__domainname, const char *__msgid1,
    const char *__msgid2, unsigned long int __n,
    int __category)
     __attribute__ ((__nothrow__ )) __attribute__ ((__format_arg__ (2))) __attribute__ ((__format_arg__ (3)));





extern char *textdomain (const char *__domainname) __attribute__ ((__nothrow__ ));



extern char *bindtextdomain (const char *__domainname,
        const char *__dirname) __attribute__ ((__nothrow__ ));



extern char *bind_textdomain_codeset (const char *__domainname,
          const char *__codeset) __attribute__ ((__nothrow__ ));
# 27 "../lib/gettext.h" 2
# 142 "../lib/gettext.h"
__inline





static const char *
pgettext_aux (const char *domain,
              const char *msg_ctxt_id, const char *msgid,
              int category)
{
  const char *translation = dcgettext (domain, msg_ctxt_id, category);
  if (translation == msg_ctxt_id)
    return msgid;
  else
    return translation;
}


__inline





static const char *
npgettext_aux (const char *domain,
               const char *msg_ctxt_id, const char *msgid,
               const char *msgid_plural, unsigned long int n,
               int category)
{
  const char *translation =
    dcngettext (domain, msg_ctxt_id, msgid_plural, n, category);
  if (translation == msg_ctxt_id || translation == msgid_plural)
    return (n == 1 ? msgid : msgid_plural);
  else
    return translation;
}






# 1 "../lib/string.h" 1
# 21 "../lib/string.h" 3
# 186 "../lib/gettext.h" 2
# 203 "../lib/gettext.h"
# 1 "../lib/stdlib.h" 1
# 21 "../lib/stdlib.h" 3
# 36 "../lib/stdlib.h" 3
# 1 "/usr/include/stdlib.h" 1 3 4
# 25 "/usr/include/stdlib.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/libc-header-start.h" 1 3 4
# 26 "/usr/include/stdlib.h" 2 3 4





# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 32 "/usr/include/stdlib.h" 2 3 4







# 1 "/usr/include/x86_64-linux-gnu/bits/waitflags.h" 1 3 4
# 52 "/usr/include/x86_64-linux-gnu/bits/waitflags.h" 3 4
typedef enum
{
  P_ALL,
  P_PID,
  P_PGID
} idtype_t;
# 40 "/usr/include/stdlib.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/waitstatus.h" 1 3 4
# 41 "/usr/include/stdlib.h" 2 3 4
# 55 "/usr/include/stdlib.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/floatn.h" 1 3 4
# 120 "/usr/include/x86_64-linux-gnu/bits/floatn.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/long-double.h" 1 3 4
# 25 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 2 3 4
# 207 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 3 4
typedef float _Float32;
# 244 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 3 4
typedef double _Float64;
# 261 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 3 4
typedef double _Float32x;
# 278 "/usr/include/x86_64-linux-gnu/bits/floatn-common.h" 3 4
typedef long double _Float64x;
# 121 "/usr/include/x86_64-linux-gnu/bits/floatn.h" 2 3 4
# 56 "/usr/include/stdlib.h" 2 3 4


typedef struct
  {
    int quot;
    int rem;
  } div_t;



typedef struct
  {
    long int quot;
    long int rem;
  } ldiv_t;





__extension__ typedef struct
  {
    long long int quot;
    long long int rem;
  } lldiv_t;
# 97 "/usr/include/stdlib.h" 3 4
extern size_t __ctype_get_mb_cur_max (void) __attribute__ ((__nothrow__ )) ;



extern double atof (const char *__nptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1))) ;

extern int atoi (const char *__nptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1))) ;

extern long int atol (const char *__nptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1))) ;



__extension__ extern long long int atoll (const char *__nptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1))) ;



extern double strtod (const char *__restrict __nptr,
        char **__restrict __endptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern float strtof (const char *__restrict __nptr,
       char **__restrict __endptr) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));

extern long double strtold (const char *__restrict __nptr,
       char **__restrict __endptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 140 "/usr/include/stdlib.h" 3 4
extern _Float32 strtof32 (const char *__restrict __nptr,
     char **__restrict __endptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern _Float64 strtof64 (const char *__restrict __nptr,
     char **__restrict __endptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 158 "/usr/include/stdlib.h" 3 4
extern _Float32x strtof32x (const char *__restrict __nptr,
       char **__restrict __endptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern _Float64x strtof64x (const char *__restrict __nptr,
       char **__restrict __endptr)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 176 "/usr/include/stdlib.h" 3 4
extern long int strtol (const char *__restrict __nptr,
   char **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));

extern unsigned long int strtoul (const char *__restrict __nptr,
      char **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



__extension__
extern long long int strtoq (const char *__restrict __nptr,
        char **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));

__extension__
extern unsigned long long int strtouq (const char *__restrict __nptr,
           char **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));




__extension__
extern long long int strtoll (const char *__restrict __nptr,
         char **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));

__extension__
extern unsigned long long int strtoull (const char *__restrict __nptr,
     char **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));




extern int strfromd (char *__dest, size_t __size, const char *__format,
       double __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));

extern int strfromf (char *__dest, size_t __size, const char *__format,
       float __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));

extern int strfroml (char *__dest, size_t __size, const char *__format,
       long double __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));
# 232 "/usr/include/stdlib.h" 3 4
extern int strfromf32 (char *__dest, size_t __size, const char * __format,
         _Float32 __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));



extern int strfromf64 (char *__dest, size_t __size, const char * __format,
         _Float64 __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));
# 250 "/usr/include/stdlib.h" 3 4
extern int strfromf32x (char *__dest, size_t __size, const char * __format,
   _Float32x __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));



extern int strfromf64x (char *__dest, size_t __size, const char * __format,
   _Float64x __f)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));
# 274 "/usr/include/stdlib.h" 3 4
extern long int strtol_l (const char *__restrict __nptr,
     char **__restrict __endptr, int __base,
     locale_t __loc) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 4)));

extern unsigned long int strtoul_l (const char *__restrict __nptr,
        char **__restrict __endptr,
        int __base, locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 4)));

__extension__
extern long long int strtoll_l (const char *__restrict __nptr,
    char **__restrict __endptr, int __base,
    locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 4)));

__extension__
extern unsigned long long int strtoull_l (const char *__restrict __nptr,
       char **__restrict __endptr,
       int __base, locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 4)));

extern double strtod_l (const char *__restrict __nptr,
   char **__restrict __endptr, locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));

extern float strtof_l (const char *__restrict __nptr,
         char **__restrict __endptr, locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));

extern long double strtold_l (const char *__restrict __nptr,
         char **__restrict __endptr,
         locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));
# 316 "/usr/include/stdlib.h" 3 4
extern _Float32 strtof32_l (const char *__restrict __nptr,
       char **__restrict __endptr,
       locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));



extern _Float64 strtof64_l (const char *__restrict __nptr,
       char **__restrict __endptr,
       locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));
# 337 "/usr/include/stdlib.h" 3 4
extern _Float32x strtof32x_l (const char *__restrict __nptr,
         char **__restrict __endptr,
         locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));



extern _Float64x strtof64x_l (const char *__restrict __nptr,
         char **__restrict __endptr,
         locale_t __loc)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3)));
# 385 "/usr/include/stdlib.h" 3 4
extern char *l64a (long int __n) __attribute__ ((__nothrow__ )) ;


extern long int a64l (const char *__s)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1))) ;





# 1 "../lib/sys/types.h" 1 3 4
# 21 "../lib/sys/types.h" 3
# 395 "/usr/include/stdlib.h" 2 3 4






extern long int random (void) __attribute__ ((__nothrow__ ));


extern void srandom (unsigned int __seed) __attribute__ ((__nothrow__ ));





extern char *initstate (unsigned int __seed, char *__statebuf,
   size_t __statelen) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));



extern char *setstate (char *__statebuf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));







struct random_data
  {
    int32_t *fptr;
    int32_t *rptr;
    int32_t *state;
    int rand_type;
    int rand_deg;
    int rand_sep;
    int32_t *end_ptr;
  };

extern int random_r (struct random_data *__restrict __buf,
       int32_t *__restrict __result) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));

extern int srandom_r (unsigned int __seed, struct random_data *__buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));

extern int initstate_r (unsigned int __seed, char *__restrict __statebuf,
   size_t __statelen,
   struct random_data *__restrict __buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 4)));

extern int setstate_r (char *__restrict __statebuf,
         struct random_data *__restrict __buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));





extern int rand (void) __attribute__ ((__nothrow__ ));

extern void srand (unsigned int __seed) __attribute__ ((__nothrow__ ));



extern int rand_r (unsigned int *__seed) __attribute__ ((__nothrow__ ));







extern double drand48 (void) __attribute__ ((__nothrow__ ));
extern double erand48 (unsigned short int __xsubi[3]) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern long int lrand48 (void) __attribute__ ((__nothrow__ ));
extern long int nrand48 (unsigned short int __xsubi[3])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern long int mrand48 (void) __attribute__ ((__nothrow__ ));
extern long int jrand48 (unsigned short int __xsubi[3])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern void srand48 (long int __seedval) __attribute__ ((__nothrow__ ));
extern unsigned short int *seed48 (unsigned short int __seed16v[3])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
extern void lcong48 (unsigned short int __param[7]) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





struct drand48_data
  {
    unsigned short int __x[3];
    unsigned short int __old_x[3];
    unsigned short int __c;
    unsigned short int __init;
    __extension__ unsigned long long int __a;

  };


extern int drand48_r (struct drand48_data *__restrict __buffer,
        double *__restrict __result) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern int erand48_r (unsigned short int __xsubi[3],
        struct drand48_data *__restrict __buffer,
        double *__restrict __result) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern int lrand48_r (struct drand48_data *__restrict __buffer,
        long int *__restrict __result)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern int nrand48_r (unsigned short int __xsubi[3],
        struct drand48_data *__restrict __buffer,
        long int *__restrict __result)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern int mrand48_r (struct drand48_data *__restrict __buffer,
        long int *__restrict __result)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern int jrand48_r (unsigned short int __xsubi[3],
        struct drand48_data *__restrict __buffer,
        long int *__restrict __result)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));


extern int srand48_r (long int __seedval, struct drand48_data *__buffer)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));

extern int seed48_r (unsigned short int __seed16v[3],
       struct drand48_data *__buffer) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));

extern int lcong48_r (unsigned short int __param[7],
        struct drand48_data *__buffer)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern void *malloc (size_t __size) __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) ;

extern void *calloc (size_t __nmemb, size_t __size)
     __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) ;






extern void *realloc (void *__ptr, size_t __size)
     __attribute__ ((__nothrow__ )) __attribute__ ((__warn_unused_result__));







extern void *reallocarray (void *__ptr, size_t __nmemb, size_t __size)
     __attribute__ ((__nothrow__ )) __attribute__ ((__warn_unused_result__));



extern void free (void *__ptr) __attribute__ ((__nothrow__ ));



# 1 "../lib/alloca.h" 1 3 4
# 567 "/usr/include/stdlib.h" 2 3 4





extern void *valloc (size_t __size) __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) ;




extern int posix_memalign (void **__memptr, size_t __alignment, size_t __size)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;




extern void *aligned_alloc (size_t __alignment, size_t __size)
     __attribute__ ((__nothrow__ )) __attribute__ ((__malloc__)) ;



extern void abort (void) __attribute__ ((__nothrow__ )) __attribute__ ((__noreturn__));



extern int atexit (void (*__func) (void)) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));







extern int at_quick_exit (void (*__func) (void)) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));






extern int on_exit (void (*__func) (int __status, void *__arg), void *__arg)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern void exit (int __status) __attribute__ ((__nothrow__ )) __attribute__ ((__noreturn__));





extern void quick_exit (int __status) __attribute__ ((__nothrow__ )) __attribute__ ((__noreturn__));





extern void _Exit (int __status) __attribute__ ((__nothrow__ )) __attribute__ ((__noreturn__));




extern char *getenv (const char *__name) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;




extern char *secure_getenv (const char *__name)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;






extern int putenv (char *__string) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int setenv (const char *__name, const char *__value, int __replace)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));


extern int unsetenv (const char *__name) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));






extern int clearenv (void) __attribute__ ((__nothrow__ ));
# 672 "/usr/include/stdlib.h" 3 4
extern char *mktemp (char *__template) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 685 "/usr/include/stdlib.h" 3 4
extern int mkstemp (char *__template) __attribute__ ((__nonnull__ (1))) ;
# 695 "/usr/include/stdlib.h" 3 4
extern int mkstemp64 (char *__template) __attribute__ ((__nonnull__ (1))) ;
# 707 "/usr/include/stdlib.h" 3 4
extern int mkstemps (char *__template, int __suffixlen) __attribute__ ((__nonnull__ (1))) ;
# 717 "/usr/include/stdlib.h" 3 4
extern int mkstemps64 (char *__template, int __suffixlen)
     __attribute__ ((__nonnull__ (1))) ;
# 728 "/usr/include/stdlib.h" 3 4
extern char *mkdtemp (char *__template) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;
# 739 "/usr/include/stdlib.h" 3 4
extern int mkostemp (char *__template, int __flags) __attribute__ ((__nonnull__ (1))) ;
# 749 "/usr/include/stdlib.h" 3 4
extern int mkostemp64 (char *__template, int __flags) __attribute__ ((__nonnull__ (1))) ;
# 759 "/usr/include/stdlib.h" 3 4
extern int mkostemps (char *__template, int __suffixlen, int __flags)
     __attribute__ ((__nonnull__ (1))) ;
# 771 "/usr/include/stdlib.h" 3 4
extern int mkostemps64 (char *__template, int __suffixlen, int __flags)
     __attribute__ ((__nonnull__ (1))) ;
# 781 "/usr/include/stdlib.h" 3 4
extern int system (const char *__command) ;





extern char *canonicalize_file_name (const char *__name)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;
# 797 "/usr/include/stdlib.h" 3 4
extern char *realpath (const char *__restrict __name,
         char *__restrict __resolved) __attribute__ ((__nothrow__ )) ;






typedef int (*__compar_fn_t) (const void *, const void *);


typedef __compar_fn_t comparison_fn_t;



typedef int (*__compar_d_fn_t) (const void *, const void *, void *);




extern void *bsearch (const void *__key, const void *__base,
        size_t __nmemb, size_t __size, __compar_fn_t __compar)
     __attribute__ ((__nonnull__ (1, 2, 5))) ;







extern void qsort (void *__base, size_t __nmemb, size_t __size,
     __compar_fn_t __compar) __attribute__ ((__nonnull__ (1, 4)));

extern void qsort_r (void *__base, size_t __nmemb, size_t __size,
       __compar_d_fn_t __compar, void *__arg)
  __attribute__ ((__nonnull__ (1, 4)));




extern int abs (int __x) __attribute__ ((__nothrow__ )) __attribute__ ((__const__)) ;
extern long int labs (long int __x) __attribute__ ((__nothrow__ )) __attribute__ ((__const__)) ;


__extension__ extern long long int llabs (long long int __x)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__)) ;






extern div_t div (int __numer, int __denom)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__)) ;
extern ldiv_t ldiv (long int __numer, long int __denom)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__)) ;


__extension__ extern lldiv_t lldiv (long long int __numer,
        long long int __denom)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__)) ;
# 869 "/usr/include/stdlib.h" 3 4
extern char *ecvt (double __value, int __ndigit, int *__restrict __decpt,
     int *__restrict __sign) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4))) ;




extern char *fcvt (double __value, int __ndigit, int *__restrict __decpt,
     int *__restrict __sign) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4))) ;




extern char *gcvt (double __value, int __ndigit, char *__buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3))) ;




extern char *qecvt (long double __value, int __ndigit,
      int *__restrict __decpt, int *__restrict __sign)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4))) ;
extern char *qfcvt (long double __value, int __ndigit,
      int *__restrict __decpt, int *__restrict __sign)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4))) ;
extern char *qgcvt (long double __value, int __ndigit, char *__buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3))) ;




extern int ecvt_r (double __value, int __ndigit, int *__restrict __decpt,
     int *__restrict __sign, char *__restrict __buf,
     size_t __len) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4, 5)));
extern int fcvt_r (double __value, int __ndigit, int *__restrict __decpt,
     int *__restrict __sign, char *__restrict __buf,
     size_t __len) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4, 5)));

extern int qecvt_r (long double __value, int __ndigit,
      int *__restrict __decpt, int *__restrict __sign,
      char *__restrict __buf, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4, 5)));
extern int qfcvt_r (long double __value, int __ndigit,
      int *__restrict __decpt, int *__restrict __sign,
      char *__restrict __buf, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4, 5)));





extern int mblen (const char *__s, size_t __n) __attribute__ ((__nothrow__ ));


extern int mbtowc (wchar_t *__restrict __pwc,
     const char *__restrict __s, size_t __n) __attribute__ ((__nothrow__ ));


extern int wctomb (char *__s, wchar_t __wchar) __attribute__ ((__nothrow__ ));



extern size_t mbstowcs (wchar_t *__restrict __pwcs,
   const char *__restrict __s, size_t __n) __attribute__ ((__nothrow__ ));

extern size_t wcstombs (char *__restrict __s,
   const wchar_t *__restrict __pwcs, size_t __n)
     __attribute__ ((__nothrow__ ));







extern int rpmatch (const char *__response) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;
# 954 "/usr/include/stdlib.h" 3 4
extern int getsubopt (char **__restrict __optionp,
        char *const *__restrict __tokens,
        char **__restrict __valuep)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2, 3))) ;





extern void setkey (const char *__key) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));







extern int posix_openpt (int __oflag) ;







extern int grantpt (int __fd) __attribute__ ((__nothrow__ ));



extern int unlockpt (int __fd) __attribute__ ((__nothrow__ ));




extern char *ptsname (int __fd) __attribute__ ((__nothrow__ )) ;






extern int ptsname_r (int __fd, char *__buf, size_t __buflen)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));


extern int getpt (void);






extern int getloadavg (double __loadavg[], int __nelem)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 1016 "/usr/include/stdlib.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/stdlib-float.h" 1 3 4
# 1017 "/usr/include/stdlib.h" 2 3 4
# 37 "../lib/stdlib.h" 2 3





# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 43 "../lib/stdlib.h" 2 3
# 691 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 716 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;





extern int _gl_cxxalias_dummy;
# 741 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 809 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 837 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 887 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 947 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1062 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1353 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1416 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1461 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1493 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1525 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1552 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1579 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1620 "../lib/stdlib.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 204 "../lib/gettext.h" 2








__inline





static const char *
dcpgettext_expr (const char *domain,
                 const char *msgctxt, const char *msgid,
                 int category)
{
  size_t msgctxt_len = strlen (msgctxt) + 1;
  size_t msgid_len = strlen (msgid) + 1;
  const char *translation;



  char buf[1024];
  char *msg_ctxt_id =
    (msgctxt_len + msgid_len <= sizeof (buf)
     ? buf
     : (char *) malloc (msgctxt_len + msgid_len));
  if (msg_ctxt_id != ((void*)0))

    {
      int found_translation;
      memcpy (msg_ctxt_id, msgctxt, msgctxt_len - 1);
      msg_ctxt_id[msgctxt_len - 1] = '\004';
      memcpy (msg_ctxt_id + msgctxt_len, msgid, msgid_len);
      translation = dcgettext (domain, msg_ctxt_id, category);
      found_translation = (translation != msg_ctxt_id);

      if (msg_ctxt_id != buf)
        free (msg_ctxt_id);

      if (found_translation)
        return translation;
    }
  return msgid;
}







__inline





static const char *
dcnpgettext_expr (const char *domain,
                  const char *msgctxt, const char *msgid,
                  const char *msgid_plural, unsigned long int n,
                  int category)
{
  size_t msgctxt_len = strlen (msgctxt) + 1;
  size_t msgid_len = strlen (msgid) + 1;
  const char *translation;



  char buf[1024];
  char *msg_ctxt_id =
    (msgctxt_len + msgid_len <= sizeof (buf)
     ? buf
     : (char *) malloc (msgctxt_len + msgid_len));
  if (msg_ctxt_id != ((void*)0))

    {
      int found_translation;
      memcpy (msg_ctxt_id, msgctxt, msgctxt_len - 1);
      msg_ctxt_id[msgctxt_len - 1] = '\004';
      memcpy (msg_ctxt_id + msgctxt_len, msgid, msgid_len);
      translation = dcngettext (domain, msg_ctxt_id, msgid_plural, n, category);
      found_translation = !(translation == msg_ctxt_id || translation == msgid_plural);

      if (msg_ctxt_id != buf)
        free (msg_ctxt_id);

      if (found_translation)
        return translation;
    }
  return (n == 1 ? msgid : msgid_plural);
}
# 32 "../lib/argmatch.h" 2
# 1 "../lib/quote.h" 1
# 21 "../lib/quote.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 22 "../lib/quote.h" 2



extern struct quoting_options quote_quoting_options;





char const *quote_n_mem (int n, char const *arg, size_t argsize);




char const *quote_mem (char const *arg, size_t argsize);



char const *quote_n (int n, char const *arg);



char const *quote (char const *arg);
# 33 "../lib/argmatch.h" 2
# 1 "../lib/verify.h" 1
# 34 "../lib/argmatch.h" 2
# 52 "../lib/argmatch.h"
ptrdiff_t argmatch (char const *arg, char const *const *arglist,
                    void const *vallist, size_t valsize) __attribute__ ((__pure__));







typedef void (*argmatch_exit_fn) (void);
extern argmatch_exit_fn argmatch_die;



void argmatch_invalid (char const *context, char const *value,
                       ptrdiff_t problem);
# 78 "../lib/argmatch.h"
void argmatch_valid (char const *const *arglist,
                     void const *vallist, size_t valsize);
# 89 "../lib/argmatch.h"
ptrdiff_t __xargmatch_internal (char const *context,
                                char const *arg, char const *const *arglist,
                                void const *vallist, size_t valsize,
                                argmatch_exit_fn exit_fn);
# 104 "../lib/argmatch.h"
char const *argmatch_to_argument (void const *value,
                                  char const *const *arglist,
                                  void const *vallist, size_t valsize)
  __attribute__ ((__pure__));
# 26 "numfmt.c" 2
# 1 "../lib/c-ctype.h" 1
# 168 "../lib/c-ctype.h"
inline _Bool
c_isalnum (int c)
{
  switch (c)
    {
    case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isalpha (int c)
{
  switch (c)
    {
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}



inline _Bool
c_isascii (int c)
{
  switch (c)
    {
    case ' ':
    case '\a': case '\b': case '\f': case '\n': case '\r': case '\t': case '\v': case '\x00': case '\x01': case '\x02': case '\x03': case '\x04': case '\x05': case '\x06': case '\x0e': case '\x0f': case '\x10': case '\x11': case '\x12': case '\x13': case '\x14': case '\x15': case '\x16': case '\x17': case '\x18': case '\x19': case '\x1a': case '\x1b': case '\x1c': case '\x1d': case '\x1e': case '\x1f': case '\x7f':
    case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
    case '!': case '"': case '#': case '$': case '%': case '&': case '\'': case '(': case ')': case '*': case '+': case ',': case '-': case '.': case '/': case ':': case ';': case '<': case '=': case '>': case '?': case '@': case '[': case '\\': case ']': case '^': case '_': case '`': case '{': case '|': case '}': case '~':
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isblank (int c)
{
  return c == ' ' || c == '\t';
}

inline _Bool
c_iscntrl (int c)
{
  switch (c)
    {
    case '\a': case '\b': case '\f': case '\n': case '\r': case '\t': case '\v': case '\x00': case '\x01': case '\x02': case '\x03': case '\x04': case '\x05': case '\x06': case '\x0e': case '\x0f': case '\x10': case '\x11': case '\x12': case '\x13': case '\x14': case '\x15': case '\x16': case '\x17': case '\x18': case '\x19': case '\x1a': case '\x1b': case '\x1c': case '\x1d': case '\x1e': case '\x1f': case '\x7f':
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isdigit (int c)
{
  switch (c)
    {
    case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isgraph (int c)
{
  switch (c)
    {
    case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
    case '!': case '"': case '#': case '$': case '%': case '&': case '\'': case '(': case ')': case '*': case '+': case ',': case '-': case '.': case '/': case ':': case ';': case '<': case '=': case '>': case '?': case '@': case '[': case '\\': case ']': case '^': case '_': case '`': case '{': case '|': case '}': case '~':
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_islower (int c)
{
  switch (c)
    {
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isprint (int c)
{
  switch (c)
    {
    case ' ':
    case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
    case '!': case '"': case '#': case '$': case '%': case '&': case '\'': case '(': case ')': case '*': case '+': case ',': case '-': case '.': case '/': case ':': case ';': case '<': case '=': case '>': case '?': case '@': case '[': case '\\': case ']': case '^': case '_': case '`': case '{': case '|': case '}': case '~':
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_ispunct (int c)
{
  switch (c)
    {
    case '!': case '"': case '#': case '$': case '%': case '&': case '\'': case '(': case ')': case '*': case '+': case ',': case '-': case '.': case '/': case ':': case ';': case '<': case '=': case '>': case '?': case '@': case '[': case '\\': case ']': case '^': case '_': case '`': case '{': case '|': case '}': case '~':
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isspace (int c)
{
  switch (c)
    {
    case ' ': case '\t': case '\n': case '\v': case '\f': case '\r':
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isupper (int c)
{
  switch (c)
    {
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}

inline _Bool
c_isxdigit (int c)
{
  switch (c)
    {
    case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'):
      return 1;
    default:
      return 0;
    }
}

inline int
c_tolower (int c)
{
  switch (c)
    {
    case 'a' + ('A' - 'a'): case 'b' + ('A' - 'a'): case 'c' + ('A' - 'a'): case 'd' + ('A' - 'a'): case 'e' + ('A' - 'a'): case 'f' + ('A' - 'a'): case 'g' + ('A' - 'a'): case 'h' + ('A' - 'a'): case 'i' + ('A' - 'a'): case 'j' + ('A' - 'a'): case 'k' + ('A' - 'a'): case 'l' + ('A' - 'a'): case 'm' + ('A' - 'a'): case 'n' + ('A' - 'a'): case 'o' + ('A' - 'a'): case 'p' + ('A' - 'a'): case 'q' + ('A' - 'a'): case 'r' + ('A' - 'a'): case 's' + ('A' - 'a'): case 't' + ('A' - 'a'): case 'u' + ('A' - 'a'): case 'v' + ('A' - 'a'): case 'w' + ('A' - 'a'): case 'x' + ('A' - 'a'): case 'y' + ('A' - 'a'): case 'z' + ('A' - 'a'):
      return c - 'A' + 'a';
    default:
      return c;
    }
}

inline int
c_toupper (int c)
{
  switch (c)
    {
    case 'a' + (0): case 'b' + (0): case 'c' + (0): case 'd' + (0): case 'e' + (0): case 'f' + (0): case 'g' + (0): case 'h' + (0): case 'i' + (0): case 'j' + (0): case 'k' + (0): case 'l' + (0): case 'm' + (0): case 'n' + (0): case 'o' + (0): case 'p' + (0): case 'q' + (0): case 'r' + (0): case 's' + (0): case 't' + (0): case 'u' + (0): case 'v' + (0): case 'w' + (0): case 'x' + (0): case 'y' + (0): case 'z' + (0):
      return c - 'a' + 'A';
    default:
      return c;
    }
}
# 27 "numfmt.c" 2
# 1 "./die.h" 1
# 22 "./die.h"
# 1 "../lib/error.h" 1
# 52 "../lib/error.h"
extern void error (int __status, int __errnum, const char *__format, ...)
     __attribute__ ((__format__ (__printf__, 3, 4)));

extern void error_at_line (int __status, int __errnum, const char *__fname,
                           unsigned int __lineno, const char *__format, ...)
     __attribute__ ((__format__ (__printf__, 5, 6)));




extern void (*error_print_progname) (void);


extern unsigned int error_message_count;



extern int error_one_per_line;
# 23 "./die.h" 2
# 28 "numfmt.c" 2


# 1 "./system.h" 1
# 21 "./system.h"
# 1 "../lib/sys/stat.h" 1
# 26 "../lib/sys/stat.h" 3
# 41 "../lib/sys/stat.h" 3
# 1 "../lib/sys/types.h" 1 3
# 21 "../lib/sys/types.h" 3
# 42 "../lib/sys/stat.h" 2 3


# 1 "../lib/time.h" 1 3
# 21 "../lib/time.h" 3
# 47 "../lib/time.h" 3
# 1 "/usr/include/time.h" 1 3 4
# 29 "/usr/include/time.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 30 "/usr/include/time.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/time.h" 1 3 4
# 73 "/usr/include/x86_64-linux-gnu/bits/time.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/timex.h" 1 3 4
# 26 "/usr/include/x86_64-linux-gnu/bits/timex.h" 3 4
struct timex
{
  unsigned int modes;
  __syscall_slong_t offset;
  __syscall_slong_t freq;
  __syscall_slong_t maxerror;
  __syscall_slong_t esterror;
  int status;
  __syscall_slong_t constant;
  __syscall_slong_t precision;
  __syscall_slong_t tolerance;
  struct timeval time;
  __syscall_slong_t tick;
  __syscall_slong_t ppsfreq;
  __syscall_slong_t jitter;
  int shift;
  __syscall_slong_t stabil;
  __syscall_slong_t jitcnt;
  __syscall_slong_t calcnt;
  __syscall_slong_t errcnt;
  __syscall_slong_t stbcnt;

  int tai;


  int :32; int :32; int :32; int :32;
  int :32; int :32; int :32; int :32;
  int :32; int :32; int :32;
};
# 74 "/usr/include/x86_64-linux-gnu/bits/time.h" 2 3 4




extern int clock_adjtime (__clockid_t __clock_id, struct timex *__utx) __attribute__ ((__nothrow__ ));
# 34 "/usr/include/time.h" 2 3 4





# 1 "/usr/include/x86_64-linux-gnu/bits/types/struct_tm.h" 1 3 4






struct tm
{
  int tm_sec;
  int tm_min;
  int tm_hour;
  int tm_mday;
  int tm_mon;
  int tm_year;
  int tm_wday;
  int tm_yday;
  int tm_isdst;


  long int tm_gmtoff;
  const char *tm_zone;




};
# 40 "/usr/include/time.h" 2 3 4








# 1 "/usr/include/x86_64-linux-gnu/bits/types/struct_itimerspec.h" 1 3 4







struct itimerspec
  {
    struct timespec it_interval;
    struct timespec it_value;
  };
# 49 "/usr/include/time.h" 2 3 4
struct sigevent;
# 72 "/usr/include/time.h" 3 4
extern clock_t clock (void) __attribute__ ((__nothrow__ ));


extern time_t time (time_t *__timer) __attribute__ ((__nothrow__ ));


extern double difftime (time_t __time1, time_t __time0)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__));


extern time_t mktime (struct tm *__tp) __attribute__ ((__nothrow__ ));





extern size_t strftime (char *__restrict __s, size_t __maxsize,
   const char *__restrict __format,
   const struct tm *__restrict __tp) __attribute__ ((__nothrow__ ));




extern char *strptime (const char *__restrict __s,
         const char *__restrict __fmt, struct tm *__tp)
     __attribute__ ((__nothrow__ ));






extern size_t strftime_l (char *__restrict __s, size_t __maxsize,
     const char *__restrict __format,
     const struct tm *__restrict __tp,
     locale_t __loc) __attribute__ ((__nothrow__ ));



extern char *strptime_l (const char *__restrict __s,
    const char *__restrict __fmt, struct tm *__tp,
    locale_t __loc) __attribute__ ((__nothrow__ ));





extern struct tm *gmtime (const time_t *__timer) __attribute__ ((__nothrow__ ));



extern struct tm *localtime (const time_t *__timer) __attribute__ ((__nothrow__ ));




extern struct tm *gmtime_r (const time_t *__restrict __timer,
       struct tm *__restrict __tp) __attribute__ ((__nothrow__ ));



extern struct tm *localtime_r (const time_t *__restrict __timer,
          struct tm *__restrict __tp) __attribute__ ((__nothrow__ ));




extern char *asctime (const struct tm *__tp) __attribute__ ((__nothrow__ ));


extern char *ctime (const time_t *__timer) __attribute__ ((__nothrow__ ));






extern char *asctime_r (const struct tm *__restrict __tp,
   char *__restrict __buf) __attribute__ ((__nothrow__ ));


extern char *ctime_r (const time_t *__restrict __timer,
        char *__restrict __buf) __attribute__ ((__nothrow__ ));




extern char *__tzname[2];
extern int __daylight;
extern long int __timezone;




extern char *tzname[2];



extern void tzset (void) __attribute__ ((__nothrow__ ));



extern int daylight;
extern long int timezone;





extern int stime (const time_t *__when) __attribute__ ((__nothrow__ ));
# 196 "/usr/include/time.h" 3 4
extern time_t timegm (struct tm *__tp) __attribute__ ((__nothrow__ ));


extern time_t timelocal (struct tm *__tp) __attribute__ ((__nothrow__ ));


extern int dysize (int __year) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
# 211 "/usr/include/time.h" 3 4
extern int nanosleep (const struct timespec *__requested_time,
        struct timespec *__remaining);



extern int clock_getres (clockid_t __clock_id, struct timespec *__res) __attribute__ ((__nothrow__ ));


extern int clock_gettime (clockid_t __clock_id, struct timespec *__tp) __attribute__ ((__nothrow__ ));


extern int clock_settime (clockid_t __clock_id, const struct timespec *__tp)
     __attribute__ ((__nothrow__ ));






extern int clock_nanosleep (clockid_t __clock_id, int __flags,
       const struct timespec *__req,
       struct timespec *__rem);


extern int clock_getcpuclockid (pid_t __pid, clockid_t *__clock_id) __attribute__ ((__nothrow__ ));




extern int timer_create (clockid_t __clock_id,
    struct sigevent *__restrict __evp,
    timer_t *__restrict __timerid) __attribute__ ((__nothrow__ ));


extern int timer_delete (timer_t __timerid) __attribute__ ((__nothrow__ ));


extern int timer_settime (timer_t __timerid, int __flags,
     const struct itimerspec *__restrict __value,
     struct itimerspec *__restrict __ovalue) __attribute__ ((__nothrow__ ));


extern int timer_gettime (timer_t __timerid, struct itimerspec *__value)
     __attribute__ ((__nothrow__ ));


extern int timer_getoverrun (timer_t __timerid) __attribute__ ((__nothrow__ ));





extern int timespec_get (struct timespec *__ts, int __base)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 280 "/usr/include/time.h" 3 4
extern int getdate_err;
# 289 "/usr/include/time.h" 3 4
extern struct tm *getdate (const char *__string);
# 303 "/usr/include/time.h" 3 4
extern int getdate_r (const char *__restrict __string,
        struct tm *__restrict __resbufp);
# 48 "../lib/time.h" 2 3


# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 51 "../lib/time.h" 2 3
# 569 "../lib/time.h" 3
struct __time_t_must_be_integral {
  unsigned int __floating_time_t_unsupported : (time_t) 1;
};
# 583 "../lib/time.h" 3
extern int rpl_nanosleep (struct timespec const *__rqtp, struct timespec *__rmtp) __attribute__ ((__nonnull__ (1)));


extern int _gl_cxxalias_dummy;
# 597 "../lib/time.h" 3
extern int _gl_cxxalias_dummy;
# 613 "../lib/time.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 627 "../lib/time.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 654 "../lib/time.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 676 "../lib/time.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 778 "../lib/time.h" 3
typedef struct tm_zone *timezone_t;
extern timezone_t tzalloc (char const *__name);
extern int _gl_cxxalias_dummy;
extern void tzfree (timezone_t __tz);
extern int _gl_cxxalias_dummy;
extern struct tm * localtime_rz (timezone_t __tz, time_t const *__restrict __timer, struct tm *__restrict __result) __attribute__ ((__nonnull__ (2, 3)));


extern int _gl_cxxalias_dummy;


extern time_t mktime_z (timezone_t __tz, struct tm *__restrict __result) __attribute__ ((__nonnull__ (2)));


extern int _gl_cxxalias_dummy;
# 809 "../lib/time.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 45 "../lib/sys/stat.h" 2 3


# 1 "/usr/include/x86_64-linux-gnu/sys/stat.h" 1 3 4
# 101 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/stat.h" 1 3 4
# 46 "/usr/include/x86_64-linux-gnu/bits/stat.h" 3 4
struct stat
  {
    __dev_t st_dev;




    __ino_t st_ino;







    __nlink_t st_nlink;
    __mode_t st_mode;

    __uid_t st_uid;
    __gid_t st_gid;

    int __pad0;

    __dev_t st_rdev;




    __off_t st_size;



    __blksize_t st_blksize;

    __blkcnt_t st_blocks;
# 91 "/usr/include/x86_64-linux-gnu/bits/stat.h" 3 4
    struct timespec st_atim;
    struct timespec st_mtim;
    struct timespec st_ctim;
# 106 "/usr/include/x86_64-linux-gnu/bits/stat.h" 3 4
    __syscall_slong_t __glibc_reserved[3];
# 115 "/usr/include/x86_64-linux-gnu/bits/stat.h" 3 4
  };



struct stat64
  {
    __dev_t st_dev;

    __ino64_t st_ino;
    __nlink_t st_nlink;
    __mode_t st_mode;






    __uid_t st_uid;
    __gid_t st_gid;

    int __pad0;
    __dev_t st_rdev;
    __off_t st_size;





    __blksize_t st_blksize;
    __blkcnt64_t st_blocks;







    struct timespec st_atim;
    struct timespec st_mtim;
    struct timespec st_ctim;
# 164 "/usr/include/x86_64-linux-gnu/bits/stat.h" 3 4
    __syscall_slong_t __glibc_reserved[3];



  };
# 102 "/usr/include/x86_64-linux-gnu/sys/stat.h" 2 3 4
# 205 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
extern int stat (const char *__restrict __file,
   struct stat *__restrict __buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));



extern int fstat (int __fd, struct stat *__buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));
# 224 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
extern int stat64 (const char *__restrict __file,
     struct stat64 *__restrict __buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
extern int fstat64 (int __fd, struct stat64 *__buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));







extern int fstatat (int __fd, const char *__restrict __file,
      struct stat *__restrict __buf, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
# 249 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
extern int fstatat64 (int __fd, const char *__restrict __file,
        struct stat64 *__restrict __buf, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));







extern int lstat (const char *__restrict __file,
    struct stat *__restrict __buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
# 272 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
extern int lstat64 (const char *__restrict __file,
      struct stat64 *__restrict __buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));





extern int chmod (const char *__file, __mode_t __mode)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int lchmod (const char *__file, __mode_t __mode)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));




extern int fchmod (int __fd, __mode_t __mode) __attribute__ ((__nothrow__ ));





extern int fchmodat (int __fd, const char *__file, __mode_t __mode,
       int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2))) ;






extern __mode_t umask (__mode_t __mask) __attribute__ ((__nothrow__ ));




extern __mode_t getumask (void) __attribute__ ((__nothrow__ ));



extern int mkdir (const char *__path, __mode_t __mode)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int mkdirat (int __fd, const char *__path, __mode_t __mode)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));






extern int mknod (const char *__path, __mode_t __mode, __dev_t __dev)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int mknodat (int __fd, const char *__path, __mode_t __mode,
      __dev_t __dev) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));





extern int mkfifo (const char *__path, __mode_t __mode)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int mkfifoat (int __fd, const char *__path, __mode_t __mode)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));





extern int utimensat (int __fd, const char *__path,
        const struct timespec __times[2],
        int __flags)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));




extern int futimens (int __fd, const struct timespec __times[2]) __attribute__ ((__nothrow__ ));
# 395 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
extern int __fxstat (int __ver, int __fildes, struct stat *__stat_buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));
extern int __xstat (int __ver, const char *__filename,
      struct stat *__stat_buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
extern int __lxstat (int __ver, const char *__filename,
       struct stat *__stat_buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
extern int __fxstatat (int __ver, int __fildes, const char *__filename,
         struct stat *__stat_buf, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4)));
# 428 "/usr/include/x86_64-linux-gnu/sys/stat.h" 3 4
extern int __fxstat64 (int __ver, int __fildes, struct stat64 *__stat_buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3)));
extern int __xstat64 (int __ver, const char *__filename,
        struct stat64 *__stat_buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
extern int __lxstat64 (int __ver, const char *__filename,
         struct stat64 *__stat_buf) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3)));
extern int __fxstatat64 (int __ver, int __fildes, const char *__filename,
    struct stat64 *__stat_buf, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 4)));

extern int __xmknod (int __ver, const char *__path, __mode_t __mode,
       __dev_t *__dev) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 4)));

extern int __xmknodat (int __ver, int __fd, const char *__path,
         __mode_t __mode, __dev_t *__dev)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (3, 5)));
# 48 "../lib/sys/stat.h" 2 3
# 871 "../lib/sys/stat.h" 3
extern int rpl_fchmodat (int fd, char const *file, mode_t mode, int flag) __attribute__ ((__nonnull__ (2)));


extern int _gl_cxxalias_dummy;
# 885 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;
# 904 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 942 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 975 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 993 "../lib/sys/stat.h" 3
extern int lchmod (const char *filename, mode_t mode) __attribute__ ((__nonnull__ (1)));


extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1027 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1074 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1110 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1153 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1278 "../lib/sys/stat.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 22 "./system.h" 2
# 31 "./system.h"
# 1 "/usr/include/x86_64-linux-gnu/sys/param.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/sys/param.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/sys/param.h" 2 3 4

# 1 "../lib/sys/types.h" 1 3 4
# 21 "../lib/sys/types.h" 3
# 26 "/usr/include/x86_64-linux-gnu/sys/param.h" 2 3 4


# 1 "../lib/signal.h" 1 3 4
# 21 "../lib/signal.h" 3
# 49 "../lib/signal.h" 3
# 1 "../lib/sys/types.h" 1 3
# 21 "../lib/sys/types.h" 3
# 50 "../lib/signal.h" 2 3


# 1 "/usr/include/signal.h" 1 3 4
# 30 "/usr/include/signal.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/signum.h" 1 3 4
# 26 "/usr/include/x86_64-linux-gnu/bits/signum.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/signum-generic.h" 1 3 4
# 27 "/usr/include/x86_64-linux-gnu/bits/signum.h" 2 3 4
# 31 "/usr/include/signal.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types/sig_atomic_t.h" 1 3 4







typedef __sig_atomic_t sig_atomic_t;
# 33 "/usr/include/signal.h" 2 3 4
# 57 "/usr/include/signal.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/siginfo_t.h" 1 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 5 "/usr/include/x86_64-linux-gnu/bits/types/siginfo_t.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types/__sigval_t.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/types/__sigval_t.h" 3 4
union sigval
{
  int sival_int;
  void *sival_ptr;
};

typedef union sigval __sigval_t;
# 7 "/usr/include/x86_64-linux-gnu/bits/types/siginfo_t.h" 2 3 4
# 16 "/usr/include/x86_64-linux-gnu/bits/types/siginfo_t.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/siginfo-arch.h" 1 3 4
# 17 "/usr/include/x86_64-linux-gnu/bits/types/siginfo_t.h" 2 3 4
# 36 "/usr/include/x86_64-linux-gnu/bits/types/siginfo_t.h" 3 4
typedef struct
  {
    int si_signo;

    int si_errno;

    int si_code;





    int __pad0;


    union
      {
 int _pad[((128 / sizeof (int)) - 4)];


 struct
   {
     __pid_t si_pid;
     __uid_t si_uid;
   } _kill;


 struct
   {
     int si_tid;
     int si_overrun;
     __sigval_t si_sigval;
   } _timer;


 struct
   {
     __pid_t si_pid;
     __uid_t si_uid;
     __sigval_t si_sigval;
   } _rt;


 struct
   {
     __pid_t si_pid;
     __uid_t si_uid;
     int si_status;
     __clock_t si_utime;
     __clock_t si_stime;
   } _sigchld;


 struct
   {
     void *si_addr;

     short int si_addr_lsb;
     union
       {

  struct
    {
      void *_lower;
      void *_upper;
    } _addr_bnd;

  __uint32_t _pkey;
       } _bounds;
   } _sigfault;


 struct
   {
     long int si_band;
     int si_fd;
   } _sigpoll;



 struct
   {
     void *_call_addr;
     int _syscall;
     unsigned int _arch;
   } _sigsys;

      } _sifields;
  } siginfo_t ;
# 58 "/usr/include/signal.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/siginfo-consts.h" 1 3 4
# 35 "/usr/include/x86_64-linux-gnu/bits/siginfo-consts.h" 3 4
enum
{
  SI_ASYNCNL = -60,
  SI_TKILL = -6,
  SI_SIGIO,

  SI_ASYNCIO,
  SI_MESGQ,
  SI_TIMER,





  SI_QUEUE,
  SI_USER,
  SI_KERNEL = 0x80
# 63 "/usr/include/x86_64-linux-gnu/bits/siginfo-consts.h" 3 4
};




enum
{
  ILL_ILLOPC = 1,

  ILL_ILLOPN,

  ILL_ILLADR,

  ILL_ILLTRP,

  ILL_PRVOPC,

  ILL_PRVREG,

  ILL_COPROC,

  ILL_BADSTK

};


enum
{
  FPE_INTDIV = 1,

  FPE_INTOVF,

  FPE_FLTDIV,

  FPE_FLTOVF,

  FPE_FLTUND,

  FPE_FLTRES,

  FPE_FLTINV,

  FPE_FLTSUB

};


enum
{
  SEGV_MAPERR = 1,

  SEGV_ACCERR,

  SEGV_BNDERR,

  SEGV_PKUERR

};


enum
{
  BUS_ADRALN = 1,

  BUS_ADRERR,

  BUS_OBJERR,

  BUS_MCEERR_AR,

  BUS_MCEERR_AO

};




enum
{
  TRAP_BRKPT = 1,

  TRAP_TRACE

};




enum
{
  CLD_EXITED = 1,

  CLD_KILLED,

  CLD_DUMPED,

  CLD_TRAPPED,

  CLD_STOPPED,

  CLD_CONTINUED

};


enum
{
  POLL_IN = 1,

  POLL_OUT,

  POLL_MSG,

  POLL_ERR,

  POLL_PRI,

  POLL_HUP

};






# 1 "/usr/include/x86_64-linux-gnu/bits/siginfo-consts-arch.h" 1 3 4
# 189 "/usr/include/x86_64-linux-gnu/bits/siginfo-consts.h" 2 3 4
# 59 "/usr/include/signal.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/types/sigval_t.h" 1 3 4
# 16 "/usr/include/x86_64-linux-gnu/bits/types/sigval_t.h" 3 4
typedef __sigval_t sigval_t;
# 63 "/usr/include/signal.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/types/sigevent_t.h" 1 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 5 "/usr/include/x86_64-linux-gnu/bits/types/sigevent_t.h" 2 3 4
# 22 "/usr/include/x86_64-linux-gnu/bits/types/sigevent_t.h" 3 4
typedef struct sigevent
  {
    __sigval_t sigev_value;
    int sigev_signo;
    int sigev_notify;

    union
      {
 int _pad[((64 / sizeof (int)) - 4)];



 __pid_t _tid;

 struct
   {
     void (*_function) (__sigval_t);
     pthread_attr_t *_attribute;
   } _sigev_thread;
      } _sigev_un;
  } sigevent_t;
# 67 "/usr/include/signal.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/sigevent-consts.h" 1 3 4
# 27 "/usr/include/x86_64-linux-gnu/bits/sigevent-consts.h" 3 4
enum
{
  SIGEV_SIGNAL = 0,

  SIGEV_NONE,

  SIGEV_THREAD,


  SIGEV_THREAD_ID = 4


};
# 68 "/usr/include/signal.h" 2 3 4




typedef void (*__sighandler_t) (int);




extern __sighandler_t __sysv_signal (int __sig, __sighandler_t __handler)
     __attribute__ ((__nothrow__ ));

extern __sighandler_t sysv_signal (int __sig, __sighandler_t __handler)
     __attribute__ ((__nothrow__ ));






extern __sighandler_t signal (int __sig, __sighandler_t __handler)
     __attribute__ ((__nothrow__ ));
# 112 "/usr/include/signal.h" 3 4
extern int kill (__pid_t __pid, int __sig) __attribute__ ((__nothrow__ ));






extern int killpg (__pid_t __pgrp, int __sig) __attribute__ ((__nothrow__ ));



extern int raise (int __sig) __attribute__ ((__nothrow__ ));



extern __sighandler_t ssignal (int __sig, __sighandler_t __handler)
     __attribute__ ((__nothrow__ ));
extern int gsignal (int __sig) __attribute__ ((__nothrow__ ));




extern void psignal (int __sig, const char *__s);


extern void psiginfo (const siginfo_t *__pinfo, const char *__s);
# 151 "/usr/include/signal.h" 3 4
extern int sigpause (int __sig) __asm__ ("__xpg_sigpause");
# 170 "/usr/include/signal.h" 3 4
extern int sigblock (int __mask) __attribute__ ((__nothrow__ )) __attribute__ ((__deprecated__));


extern int sigsetmask (int __mask) __attribute__ ((__nothrow__ )) __attribute__ ((__deprecated__));


extern int siggetmask (void) __attribute__ ((__nothrow__ )) __attribute__ ((__deprecated__));
# 185 "/usr/include/signal.h" 3 4
typedef __sighandler_t sighandler_t;




typedef __sighandler_t sig_t;





extern int sigemptyset (sigset_t *__set) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int sigfillset (sigset_t *__set) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int sigaddset (sigset_t *__set, int __signo) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int sigdelset (sigset_t *__set, int __signo) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int sigismember (const sigset_t *__set, int __signo)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern int sigisemptyset (const sigset_t *__set) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int sigandset (sigset_t *__set, const sigset_t *__left,
        const sigset_t *__right) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2, 3)));


extern int sigorset (sigset_t *__set, const sigset_t *__left,
       const sigset_t *__right) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2, 3)));





# 1 "/usr/include/x86_64-linux-gnu/bits/sigaction.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/sigaction.h" 3 4
struct sigaction
  {


    union
      {

 __sighandler_t sa_handler;

 void (*sa_sigaction) (int, siginfo_t *, void *);
      }
    __sigaction_handler;







    __sigset_t sa_mask;


    int sa_flags;


    void (*sa_restorer) (void);
  };
# 227 "/usr/include/signal.h" 2 3 4


extern int sigprocmask (int __how, const sigset_t *__restrict __set,
   sigset_t *__restrict __oset) __attribute__ ((__nothrow__ ));






extern int sigsuspend (const sigset_t *__set) __attribute__ ((__nonnull__ (1)));


extern int sigaction (int __sig, const struct sigaction *__restrict __act,
        struct sigaction *__restrict __oact) __attribute__ ((__nothrow__ ));


extern int sigpending (sigset_t *__set) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));







extern int sigwait (const sigset_t *__restrict __set, int *__restrict __sig)
     __attribute__ ((__nonnull__ (1, 2)));







extern int sigwaitinfo (const sigset_t *__restrict __set,
   siginfo_t *__restrict __info) __attribute__ ((__nonnull__ (1)));






extern int sigtimedwait (const sigset_t *__restrict __set,
    siginfo_t *__restrict __info,
    const struct timespec *__restrict __timeout)
     __attribute__ ((__nonnull__ (1)));



extern int sigqueue (__pid_t __pid, int __sig, const union sigval __val)
     __attribute__ ((__nothrow__ ));
# 286 "/usr/include/signal.h" 3 4
extern const char *const _sys_siglist[(64 + 1)];
extern const char *const sys_siglist[(64 + 1)];




# 1 "/usr/include/x86_64-linux-gnu/bits/sigcontext.h" 1 3 4
# 31 "/usr/include/x86_64-linux-gnu/bits/sigcontext.h" 3 4
struct _fpx_sw_bytes
{
  __uint32_t magic1;
  __uint32_t extended_size;
  __uint64_t xstate_bv;
  __uint32_t xstate_size;
  __uint32_t __glibc_reserved1[7];
};

struct _fpreg
{
  unsigned short significand[4];
  unsigned short exponent;
};

struct _fpxreg
{
  unsigned short significand[4];
  unsigned short exponent;
  unsigned short __glibc_reserved1[3];
};

struct _xmmreg
{
  __uint32_t element[4];
};
# 123 "/usr/include/x86_64-linux-gnu/bits/sigcontext.h" 3 4
struct _fpstate
{

  __uint16_t cwd;
  __uint16_t swd;
  __uint16_t ftw;
  __uint16_t fop;
  __uint64_t rip;
  __uint64_t rdp;
  __uint32_t mxcsr;
  __uint32_t mxcr_mask;
  struct _fpxreg _st[8];
  struct _xmmreg _xmm[16];
  __uint32_t __glibc_reserved1[24];
};

struct sigcontext
{
  __uint64_t r8;
  __uint64_t r9;
  __uint64_t r10;
  __uint64_t r11;
  __uint64_t r12;
  __uint64_t r13;
  __uint64_t r14;
  __uint64_t r15;
  __uint64_t rdi;
  __uint64_t rsi;
  __uint64_t rbp;
  __uint64_t rbx;
  __uint64_t rdx;
  __uint64_t rax;
  __uint64_t rcx;
  __uint64_t rsp;
  __uint64_t rip;
  __uint64_t eflags;
  unsigned short cs;
  unsigned short gs;
  unsigned short fs;
  unsigned short __pad0;
  __uint64_t err;
  __uint64_t trapno;
  __uint64_t oldmask;
  __uint64_t cr2;
  __extension__ union
    {
      struct _fpstate * fpstate;
      __uint64_t __fpstate_word;
    };
  __uint64_t __reserved1 [8];
};



struct _xsave_hdr
{
  __uint64_t xstate_bv;
  __uint64_t __glibc_reserved1[2];
  __uint64_t __glibc_reserved2[5];
};

struct _ymmh_state
{
  __uint32_t ymmh_space[64];
};

struct _xstate
{
  struct _fpstate fpstate;
  struct _xsave_hdr xstate_hdr;
  struct _ymmh_state ymmh;
};
# 292 "/usr/include/signal.h" 2 3 4


extern int sigreturn (struct sigcontext *__scp) __attribute__ ((__nothrow__ ));







# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 302 "/usr/include/signal.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/types/stack_t.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/bits/types/stack_t.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/types/stack_t.h" 2 3 4


typedef struct
  {
    void *ss_sp;
    int ss_flags;
    size_t ss_size;
  } stack_t;
# 304 "/usr/include/signal.h" 2 3 4


# 1 "/usr/include/x86_64-linux-gnu/sys/ucontext.h" 1 3 4
# 37 "/usr/include/x86_64-linux-gnu/sys/ucontext.h" 3 4
__extension__ typedef long long int greg_t;
# 46 "/usr/include/x86_64-linux-gnu/sys/ucontext.h" 3 4
typedef greg_t gregset_t[23];



enum
{
  REG_R8 = 0,

  REG_R9,

  REG_R10,

  REG_R11,

  REG_R12,

  REG_R13,

  REG_R14,

  REG_R15,

  REG_RDI,

  REG_RSI,

  REG_RBP,

  REG_RBX,

  REG_RDX,

  REG_RAX,

  REG_RCX,

  REG_RSP,

  REG_RIP,

  REG_EFL,

  REG_CSGSFS,

  REG_ERR,

  REG_TRAPNO,

  REG_OLDMASK,

  REG_CR2

};


struct _libc_fpxreg
{
  unsigned short int significand[4];
  unsigned short int exponent;
  unsigned short int __glibc_reserved1[3];
};

struct _libc_xmmreg
{
  __uint32_t element[4];
};

struct _libc_fpstate
{

  __uint16_t cwd;
  __uint16_t swd;
  __uint16_t ftw;
  __uint16_t fop;
  __uint64_t rip;
  __uint64_t rdp;
  __uint32_t mxcsr;
  __uint32_t mxcr_mask;
  struct _libc_fpxreg _st[8];
  struct _libc_xmmreg _xmm[16];
  __uint32_t __glibc_reserved1[24];
};


typedef struct _libc_fpstate *fpregset_t;


typedef struct
  {
    gregset_t gregs;

    fpregset_t fpregs;
    __extension__ unsigned long long __reserved1 [8];
} mcontext_t;


typedef struct ucontext_t
  {
    unsigned long int uc_flags;
    struct ucontext_t *uc_link;
    stack_t uc_stack;
    mcontext_t uc_mcontext;
    sigset_t uc_sigmask;
    struct _libc_fpstate __fpregs_mem;
  } ucontext_t;
# 307 "/usr/include/signal.h" 2 3 4







extern int siginterrupt (int __sig, int __interrupt) __attribute__ ((__nothrow__ ));


# 1 "/usr/include/x86_64-linux-gnu/bits/sigstack.h" 1 3 4
# 317 "/usr/include/signal.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/ss_flags.h" 1 3 4
# 27 "/usr/include/x86_64-linux-gnu/bits/ss_flags.h" 3 4
enum
{
  SS_ONSTACK = 1,

  SS_DISABLE

};
# 318 "/usr/include/signal.h" 2 3 4



extern int sigaltstack (const stack_t *__restrict __ss,
   stack_t *__restrict __oss) __attribute__ ((__nothrow__ ));





# 1 "/usr/include/x86_64-linux-gnu/bits/types/struct_sigstack.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/bits/types/struct_sigstack.h" 3 4
struct sigstack
  {
    void *ss_sp;
    int ss_onstack;
  };
# 328 "/usr/include/signal.h" 2 3 4







extern int sigstack (struct sigstack *__ss, struct sigstack *__oss)
     __attribute__ ((__nothrow__ )) __attribute__ ((__deprecated__));






extern int sighold (int __sig) __attribute__ ((__nothrow__ ));


extern int sigrelse (int __sig) __attribute__ ((__nothrow__ ));


extern int sigignore (int __sig) __attribute__ ((__nothrow__ ));


extern __sighandler_t sigset (int __sig, __sighandler_t __disp) __attribute__ ((__nothrow__ ));







# 1 "/usr/include/x86_64-linux-gnu/bits/sigthread.h" 1 3 4
# 31 "/usr/include/x86_64-linux-gnu/bits/sigthread.h" 3 4
extern int pthread_sigmask (int __how,
       const __sigset_t *__restrict __newmask,
       __sigset_t *__restrict __oldmask)__attribute__ ((__nothrow__ ));


extern int pthread_kill (pthread_t __threadid, int __signo) __attribute__ ((__nothrow__ ));



extern int pthread_sigqueue (pthread_t __threadid, int __signo,
        const union sigval __value) __attribute__ ((__nothrow__ ));
# 360 "/usr/include/signal.h" 2 3 4






extern int __libc_current_sigrtmin (void) __attribute__ ((__nothrow__ ));

extern int __libc_current_sigrtmax (void) __attribute__ ((__nothrow__ ));
# 53 "../lib/signal.h" 2 3
# 621 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;





extern int _gl_cxxalias_dummy;
# 650 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 707 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 719 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 732 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 745 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 757 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;





extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 781 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;







typedef void (*_gl_function_taking_int_returning_void_t) (int);
# 814 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 938 "../lib/signal.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 29 "/usr/include/x86_64-linux-gnu/sys/param.h" 2 3 4


# 1 "/usr/include/x86_64-linux-gnu/bits/param.h" 1 3 4
# 28 "/usr/include/x86_64-linux-gnu/bits/param.h" 3 4
# 1 "/usr/include/linux/param.h" 1 3 4




# 1 "/usr/include/x86_64-linux-gnu/asm/param.h" 1 3 4
# 1 "/usr/include/asm-generic/param.h" 1 3 4
# 2 "/usr/include/x86_64-linux-gnu/asm/param.h" 2 3 4
# 6 "/usr/include/linux/param.h" 2 3 4
# 29 "/usr/include/x86_64-linux-gnu/bits/param.h" 2 3 4
# 32 "/usr/include/x86_64-linux-gnu/sys/param.h" 2 3 4
# 32 "./system.h" 2


# 1 "../lib/unistd.h" 1
# 22 "../lib/unistd.h" 3
# 40 "../lib/unistd.h" 3
# 1 "/usr/include/unistd.h" 1 3 4
# 205 "/usr/include/unistd.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/posix_opt.h" 1 3 4
# 206 "/usr/include/unistd.h" 2 3 4



# 1 "/usr/include/x86_64-linux-gnu/bits/environments.h" 1 3 4
# 22 "/usr/include/x86_64-linux-gnu/bits/environments.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/bits/environments.h" 2 3 4
# 210 "/usr/include/unistd.h" 2 3 4
# 229 "/usr/include/unistd.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 230 "/usr/include/unistd.h" 2 3 4
# 270 "/usr/include/unistd.h" 3 4
typedef __intptr_t intptr_t;






typedef __socklen_t socklen_t;
# 290 "/usr/include/unistd.h" 3 4
extern int access (const char *__name, int __type) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));




extern int euidaccess (const char *__name, int __type)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int eaccess (const char *__name, int __type)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));






extern int faccessat (int __fd, const char *__file, int __type, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2))) ;
# 337 "/usr/include/unistd.h" 3 4
extern __off_t lseek (int __fd, __off_t __offset, int __whence) __attribute__ ((__nothrow__ ));
# 348 "/usr/include/unistd.h" 3 4
extern __off64_t lseek64 (int __fd, __off64_t __offset, int __whence)
     __attribute__ ((__nothrow__ ));






extern int close (int __fd);






extern ssize_t read (int __fd, void *__buf, size_t __nbytes) ;





extern ssize_t write (int __fd, const void *__buf, size_t __n) ;
# 379 "/usr/include/unistd.h" 3 4
extern ssize_t pread (int __fd, void *__buf, size_t __nbytes,
        __off_t __offset) ;






extern ssize_t pwrite (int __fd, const void *__buf, size_t __n,
         __off_t __offset) ;
# 407 "/usr/include/unistd.h" 3 4
extern ssize_t pread64 (int __fd, void *__buf, size_t __nbytes,
   __off64_t __offset) ;


extern ssize_t pwrite64 (int __fd, const void *__buf, size_t __n,
    __off64_t __offset) ;







extern int pipe (int __pipedes[2]) __attribute__ ((__nothrow__ )) ;




extern int pipe2 (int __pipedes[2], int __flags) __attribute__ ((__nothrow__ )) ;
# 435 "/usr/include/unistd.h" 3 4
extern unsigned int alarm (unsigned int __seconds) __attribute__ ((__nothrow__ ));
# 447 "/usr/include/unistd.h" 3 4
extern unsigned int sleep (unsigned int __seconds);







extern __useconds_t ualarm (__useconds_t __value, __useconds_t __interval)
     __attribute__ ((__nothrow__ ));






extern int usleep (__useconds_t __useconds);
# 472 "/usr/include/unistd.h" 3 4
extern int pause (void);



extern int chown (const char *__file, __uid_t __owner, __gid_t __group)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;



extern int fchown (int __fd, __uid_t __owner, __gid_t __group) __attribute__ ((__nothrow__ )) ;




extern int lchown (const char *__file, __uid_t __owner, __gid_t __group)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;






extern int fchownat (int __fd, const char *__file, __uid_t __owner,
       __gid_t __group, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2))) ;



extern int chdir (const char *__path) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;



extern int fchdir (int __fd) __attribute__ ((__nothrow__ )) ;
# 514 "/usr/include/unistd.h" 3 4
extern char *getcwd (char *__buf, size_t __size) __attribute__ ((__nothrow__ )) ;





extern char *get_current_dir_name (void) __attribute__ ((__nothrow__ ));







extern char *getwd (char *__buf)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) __attribute__ ((__deprecated__)) ;




extern int dup (int __fd) __attribute__ ((__nothrow__ )) ;


extern int dup2 (int __fd, int __fd2) __attribute__ ((__nothrow__ ));




extern int dup3 (int __fd, int __fd2, int __flags) __attribute__ ((__nothrow__ ));



extern char **__environ;

extern char **environ;





extern int execve (const char *__path, char *const __argv[],
     char *const __envp[]) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern int fexecve (int __fd, char *const __argv[], char *const __envp[])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));




extern int execv (const char *__path, char *const __argv[])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));



extern int execle (const char *__path, const char *__arg, ...)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));



extern int execl (const char *__path, const char *__arg, ...)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));



extern int execvp (const char *__file, char *const __argv[])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern int execlp (const char *__file, const char *__arg, ...)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));




extern int execvpe (const char *__file, char *const __argv[],
      char *const __envp[])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));





extern int nice (int __inc) __attribute__ ((__nothrow__ )) ;




extern void _exit (int __status) __attribute__ ((__noreturn__));






# 1 "/usr/include/x86_64-linux-gnu/bits/confname.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/confname.h" 3 4
enum
  {
    _PC_LINK_MAX,

    _PC_MAX_CANON,

    _PC_MAX_INPUT,

    _PC_NAME_MAX,

    _PC_PATH_MAX,

    _PC_PIPE_BUF,

    _PC_CHOWN_RESTRICTED,

    _PC_NO_TRUNC,

    _PC_VDISABLE,

    _PC_SYNC_IO,

    _PC_ASYNC_IO,

    _PC_PRIO_IO,

    _PC_SOCK_MAXBUF,

    _PC_FILESIZEBITS,

    _PC_REC_INCR_XFER_SIZE,

    _PC_REC_MAX_XFER_SIZE,

    _PC_REC_MIN_XFER_SIZE,

    _PC_REC_XFER_ALIGN,

    _PC_ALLOC_SIZE_MIN,

    _PC_SYMLINK_MAX,

    _PC_2_SYMLINKS

  };


enum
  {
    _SC_ARG_MAX,

    _SC_CHILD_MAX,

    _SC_CLK_TCK,

    _SC_NGROUPS_MAX,

    _SC_OPEN_MAX,

    _SC_STREAM_MAX,

    _SC_TZNAME_MAX,

    _SC_JOB_CONTROL,

    _SC_SAVED_IDS,

    _SC_REALTIME_SIGNALS,

    _SC_PRIORITY_SCHEDULING,

    _SC_TIMERS,

    _SC_ASYNCHRONOUS_IO,

    _SC_PRIORITIZED_IO,

    _SC_SYNCHRONIZED_IO,

    _SC_FSYNC,

    _SC_MAPPED_FILES,

    _SC_MEMLOCK,

    _SC_MEMLOCK_RANGE,

    _SC_MEMORY_PROTECTION,

    _SC_MESSAGE_PASSING,

    _SC_SEMAPHORES,

    _SC_SHARED_MEMORY_OBJECTS,

    _SC_AIO_LISTIO_MAX,

    _SC_AIO_MAX,

    _SC_AIO_PRIO_DELTA_MAX,

    _SC_DELAYTIMER_MAX,

    _SC_MQ_OPEN_MAX,

    _SC_MQ_PRIO_MAX,

    _SC_VERSION,

    _SC_PAGESIZE,


    _SC_RTSIG_MAX,

    _SC_SEM_NSEMS_MAX,

    _SC_SEM_VALUE_MAX,

    _SC_SIGQUEUE_MAX,

    _SC_TIMER_MAX,




    _SC_BC_BASE_MAX,

    _SC_BC_DIM_MAX,

    _SC_BC_SCALE_MAX,

    _SC_BC_STRING_MAX,

    _SC_COLL_WEIGHTS_MAX,

    _SC_EQUIV_CLASS_MAX,

    _SC_EXPR_NEST_MAX,

    _SC_LINE_MAX,

    _SC_RE_DUP_MAX,

    _SC_CHARCLASS_NAME_MAX,


    _SC_2_VERSION,

    _SC_2_C_BIND,

    _SC_2_C_DEV,

    _SC_2_FORT_DEV,

    _SC_2_FORT_RUN,

    _SC_2_SW_DEV,

    _SC_2_LOCALEDEF,


    _SC_PII,

    _SC_PII_XTI,

    _SC_PII_SOCKET,

    _SC_PII_INTERNET,

    _SC_PII_OSI,

    _SC_POLL,

    _SC_SELECT,

    _SC_UIO_MAXIOV,

    _SC_IOV_MAX = _SC_UIO_MAXIOV,

    _SC_PII_INTERNET_STREAM,

    _SC_PII_INTERNET_DGRAM,

    _SC_PII_OSI_COTS,

    _SC_PII_OSI_CLTS,

    _SC_PII_OSI_M,

    _SC_T_IOV_MAX,



    _SC_THREADS,

    _SC_THREAD_SAFE_FUNCTIONS,

    _SC_GETGR_R_SIZE_MAX,

    _SC_GETPW_R_SIZE_MAX,

    _SC_LOGIN_NAME_MAX,

    _SC_TTY_NAME_MAX,

    _SC_THREAD_DESTRUCTOR_ITERATIONS,

    _SC_THREAD_KEYS_MAX,

    _SC_THREAD_STACK_MIN,

    _SC_THREAD_THREADS_MAX,

    _SC_THREAD_ATTR_STACKADDR,

    _SC_THREAD_ATTR_STACKSIZE,

    _SC_THREAD_PRIORITY_SCHEDULING,

    _SC_THREAD_PRIO_INHERIT,

    _SC_THREAD_PRIO_PROTECT,

    _SC_THREAD_PROCESS_SHARED,


    _SC_NPROCESSORS_CONF,

    _SC_NPROCESSORS_ONLN,

    _SC_PHYS_PAGES,

    _SC_AVPHYS_PAGES,

    _SC_ATEXIT_MAX,

    _SC_PASS_MAX,


    _SC_XOPEN_VERSION,

    _SC_XOPEN_XCU_VERSION,

    _SC_XOPEN_UNIX,

    _SC_XOPEN_CRYPT,

    _SC_XOPEN_ENH_I18N,

    _SC_XOPEN_SHM,


    _SC_2_CHAR_TERM,

    _SC_2_C_VERSION,

    _SC_2_UPE,


    _SC_XOPEN_XPG2,

    _SC_XOPEN_XPG3,

    _SC_XOPEN_XPG4,


    _SC_CHAR_BIT,

    _SC_CHAR_MAX,

    _SC_CHAR_MIN,

    _SC_INT_MAX,

    _SC_INT_MIN,

    _SC_LONG_BIT,

    _SC_WORD_BIT,

    _SC_MB_LEN_MAX,

    _SC_NZERO,

    _SC_SSIZE_MAX,

    _SC_SCHAR_MAX,

    _SC_SCHAR_MIN,

    _SC_SHRT_MAX,

    _SC_SHRT_MIN,

    _SC_UCHAR_MAX,

    _SC_UINT_MAX,

    _SC_ULONG_MAX,

    _SC_USHRT_MAX,


    _SC_NL_ARGMAX,

    _SC_NL_LANGMAX,

    _SC_NL_MSGMAX,

    _SC_NL_NMAX,

    _SC_NL_SETMAX,

    _SC_NL_TEXTMAX,


    _SC_XBS5_ILP32_OFF32,

    _SC_XBS5_ILP32_OFFBIG,

    _SC_XBS5_LP64_OFF64,

    _SC_XBS5_LPBIG_OFFBIG,


    _SC_XOPEN_LEGACY,

    _SC_XOPEN_REALTIME,

    _SC_XOPEN_REALTIME_THREADS,


    _SC_ADVISORY_INFO,

    _SC_BARRIERS,

    _SC_BASE,

    _SC_C_LANG_SUPPORT,

    _SC_C_LANG_SUPPORT_R,

    _SC_CLOCK_SELECTION,

    _SC_CPUTIME,

    _SC_THREAD_CPUTIME,

    _SC_DEVICE_IO,

    _SC_DEVICE_SPECIFIC,

    _SC_DEVICE_SPECIFIC_R,

    _SC_FD_MGMT,

    _SC_FIFO,

    _SC_PIPE,

    _SC_FILE_ATTRIBUTES,

    _SC_FILE_LOCKING,

    _SC_FILE_SYSTEM,

    _SC_MONOTONIC_CLOCK,

    _SC_MULTI_PROCESS,

    _SC_SINGLE_PROCESS,

    _SC_NETWORKING,

    _SC_READER_WRITER_LOCKS,

    _SC_SPIN_LOCKS,

    _SC_REGEXP,

    _SC_REGEX_VERSION,

    _SC_SHELL,

    _SC_SIGNALS,

    _SC_SPAWN,

    _SC_SPORADIC_SERVER,

    _SC_THREAD_SPORADIC_SERVER,

    _SC_SYSTEM_DATABASE,

    _SC_SYSTEM_DATABASE_R,

    _SC_TIMEOUTS,

    _SC_TYPED_MEMORY_OBJECTS,

    _SC_USER_GROUPS,

    _SC_USER_GROUPS_R,

    _SC_2_PBS,

    _SC_2_PBS_ACCOUNTING,

    _SC_2_PBS_LOCATE,

    _SC_2_PBS_MESSAGE,

    _SC_2_PBS_TRACK,

    _SC_SYMLOOP_MAX,

    _SC_STREAMS,

    _SC_2_PBS_CHECKPOINT,


    _SC_V6_ILP32_OFF32,

    _SC_V6_ILP32_OFFBIG,

    _SC_V6_LP64_OFF64,

    _SC_V6_LPBIG_OFFBIG,


    _SC_HOST_NAME_MAX,

    _SC_TRACE,

    _SC_TRACE_EVENT_FILTER,

    _SC_TRACE_INHERIT,

    _SC_TRACE_LOG,


    _SC_LEVEL1_ICACHE_SIZE,

    _SC_LEVEL1_ICACHE_ASSOC,

    _SC_LEVEL1_ICACHE_LINESIZE,

    _SC_LEVEL1_DCACHE_SIZE,

    _SC_LEVEL1_DCACHE_ASSOC,

    _SC_LEVEL1_DCACHE_LINESIZE,

    _SC_LEVEL2_CACHE_SIZE,

    _SC_LEVEL2_CACHE_ASSOC,

    _SC_LEVEL2_CACHE_LINESIZE,

    _SC_LEVEL3_CACHE_SIZE,

    _SC_LEVEL3_CACHE_ASSOC,

    _SC_LEVEL3_CACHE_LINESIZE,

    _SC_LEVEL4_CACHE_SIZE,

    _SC_LEVEL4_CACHE_ASSOC,

    _SC_LEVEL4_CACHE_LINESIZE,



    _SC_IPV6 = _SC_LEVEL1_ICACHE_SIZE + 50,

    _SC_RAW_SOCKETS,


    _SC_V7_ILP32_OFF32,

    _SC_V7_ILP32_OFFBIG,

    _SC_V7_LP64_OFF64,

    _SC_V7_LPBIG_OFFBIG,


    _SC_SS_REPL_MAX,


    _SC_TRACE_EVENT_NAME_MAX,

    _SC_TRACE_NAME_MAX,

    _SC_TRACE_SYS_MAX,

    _SC_TRACE_USER_EVENT_MAX,


    _SC_XOPEN_STREAMS,


    _SC_THREAD_ROBUST_PRIO_INHERIT,

    _SC_THREAD_ROBUST_PRIO_PROTECT

  };


enum
  {
    _CS_PATH,


    _CS_V6_WIDTH_RESTRICTED_ENVS,



    _CS_GNU_LIBC_VERSION,

    _CS_GNU_LIBPTHREAD_VERSION,


    _CS_V5_WIDTH_RESTRICTED_ENVS,



    _CS_V7_WIDTH_RESTRICTED_ENVS,



    _CS_LFS_CFLAGS = 1000,

    _CS_LFS_LDFLAGS,

    _CS_LFS_LIBS,

    _CS_LFS_LINTFLAGS,

    _CS_LFS64_CFLAGS,

    _CS_LFS64_LDFLAGS,

    _CS_LFS64_LIBS,

    _CS_LFS64_LINTFLAGS,


    _CS_XBS5_ILP32_OFF32_CFLAGS = 1100,

    _CS_XBS5_ILP32_OFF32_LDFLAGS,

    _CS_XBS5_ILP32_OFF32_LIBS,

    _CS_XBS5_ILP32_OFF32_LINTFLAGS,

    _CS_XBS5_ILP32_OFFBIG_CFLAGS,

    _CS_XBS5_ILP32_OFFBIG_LDFLAGS,

    _CS_XBS5_ILP32_OFFBIG_LIBS,

    _CS_XBS5_ILP32_OFFBIG_LINTFLAGS,

    _CS_XBS5_LP64_OFF64_CFLAGS,

    _CS_XBS5_LP64_OFF64_LDFLAGS,

    _CS_XBS5_LP64_OFF64_LIBS,

    _CS_XBS5_LP64_OFF64_LINTFLAGS,

    _CS_XBS5_LPBIG_OFFBIG_CFLAGS,

    _CS_XBS5_LPBIG_OFFBIG_LDFLAGS,

    _CS_XBS5_LPBIG_OFFBIG_LIBS,

    _CS_XBS5_LPBIG_OFFBIG_LINTFLAGS,


    _CS_POSIX_V6_ILP32_OFF32_CFLAGS,

    _CS_POSIX_V6_ILP32_OFF32_LDFLAGS,

    _CS_POSIX_V6_ILP32_OFF32_LIBS,

    _CS_POSIX_V6_ILP32_OFF32_LINTFLAGS,

    _CS_POSIX_V6_ILP32_OFFBIG_CFLAGS,

    _CS_POSIX_V6_ILP32_OFFBIG_LDFLAGS,

    _CS_POSIX_V6_ILP32_OFFBIG_LIBS,

    _CS_POSIX_V6_ILP32_OFFBIG_LINTFLAGS,

    _CS_POSIX_V6_LP64_OFF64_CFLAGS,

    _CS_POSIX_V6_LP64_OFF64_LDFLAGS,

    _CS_POSIX_V6_LP64_OFF64_LIBS,

    _CS_POSIX_V6_LP64_OFF64_LINTFLAGS,

    _CS_POSIX_V6_LPBIG_OFFBIG_CFLAGS,

    _CS_POSIX_V6_LPBIG_OFFBIG_LDFLAGS,

    _CS_POSIX_V6_LPBIG_OFFBIG_LIBS,

    _CS_POSIX_V6_LPBIG_OFFBIG_LINTFLAGS,


    _CS_POSIX_V7_ILP32_OFF32_CFLAGS,

    _CS_POSIX_V7_ILP32_OFF32_LDFLAGS,

    _CS_POSIX_V7_ILP32_OFF32_LIBS,

    _CS_POSIX_V7_ILP32_OFF32_LINTFLAGS,

    _CS_POSIX_V7_ILP32_OFFBIG_CFLAGS,

    _CS_POSIX_V7_ILP32_OFFBIG_LDFLAGS,

    _CS_POSIX_V7_ILP32_OFFBIG_LIBS,

    _CS_POSIX_V7_ILP32_OFFBIG_LINTFLAGS,

    _CS_POSIX_V7_LP64_OFF64_CFLAGS,

    _CS_POSIX_V7_LP64_OFF64_LDFLAGS,

    _CS_POSIX_V7_LP64_OFF64_LIBS,

    _CS_POSIX_V7_LP64_OFF64_LINTFLAGS,

    _CS_POSIX_V7_LPBIG_OFFBIG_CFLAGS,

    _CS_POSIX_V7_LPBIG_OFFBIG_LDFLAGS,

    _CS_POSIX_V7_LPBIG_OFFBIG_LIBS,

    _CS_POSIX_V7_LPBIG_OFFBIG_LINTFLAGS,


    _CS_V6_ENV,

    _CS_V7_ENV

  };
# 613 "/usr/include/unistd.h" 2 3 4


extern long int pathconf (const char *__path, int __name)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern long int fpathconf (int __fd, int __name) __attribute__ ((__nothrow__ ));


extern long int sysconf (int __name) __attribute__ ((__nothrow__ ));



extern size_t confstr (int __name, char *__buf, size_t __len) __attribute__ ((__nothrow__ ));




extern __pid_t getpid (void) __attribute__ ((__nothrow__ ));


extern __pid_t getppid (void) __attribute__ ((__nothrow__ ));


extern __pid_t getpgrp (void) __attribute__ ((__nothrow__ ));


extern __pid_t __getpgid (__pid_t __pid) __attribute__ ((__nothrow__ ));

extern __pid_t getpgid (__pid_t __pid) __attribute__ ((__nothrow__ ));






extern int setpgid (__pid_t __pid, __pid_t __pgid) __attribute__ ((__nothrow__ ));
# 663 "/usr/include/unistd.h" 3 4
extern int setpgrp (void) __attribute__ ((__nothrow__ ));






extern __pid_t setsid (void) __attribute__ ((__nothrow__ ));



extern __pid_t getsid (__pid_t __pid) __attribute__ ((__nothrow__ ));



extern __uid_t getuid (void) __attribute__ ((__nothrow__ ));


extern __uid_t geteuid (void) __attribute__ ((__nothrow__ ));


extern __gid_t getgid (void) __attribute__ ((__nothrow__ ));


extern __gid_t getegid (void) __attribute__ ((__nothrow__ ));




extern int getgroups (int __size, __gid_t __list[]) __attribute__ ((__nothrow__ )) ;



extern int group_member (__gid_t __gid) __attribute__ ((__nothrow__ ));






extern int setuid (__uid_t __uid) __attribute__ ((__nothrow__ )) ;




extern int setreuid (__uid_t __ruid, __uid_t __euid) __attribute__ ((__nothrow__ )) ;




extern int seteuid (__uid_t __uid) __attribute__ ((__nothrow__ )) ;






extern int setgid (__gid_t __gid) __attribute__ ((__nothrow__ )) ;




extern int setregid (__gid_t __rgid, __gid_t __egid) __attribute__ ((__nothrow__ )) ;




extern int setegid (__gid_t __gid) __attribute__ ((__nothrow__ )) ;





extern int getresuid (__uid_t *__ruid, __uid_t *__euid, __uid_t *__suid)
     __attribute__ ((__nothrow__ ));



extern int getresgid (__gid_t *__rgid, __gid_t *__egid, __gid_t *__sgid)
     __attribute__ ((__nothrow__ ));



extern int setresuid (__uid_t __ruid, __uid_t __euid, __uid_t __suid)
     __attribute__ ((__nothrow__ )) ;



extern int setresgid (__gid_t __rgid, __gid_t __egid, __gid_t __sgid)
     __attribute__ ((__nothrow__ )) ;






extern __pid_t fork (void) __attribute__ ((__nothrow__));







extern __pid_t vfork (void) __attribute__ ((__nothrow__ ));





extern char *ttyname (int __fd) __attribute__ ((__nothrow__ ));



extern int ttyname_r (int __fd, char *__buf, size_t __buflen)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2))) ;



extern int isatty (int __fd) __attribute__ ((__nothrow__ ));




extern int ttyslot (void) __attribute__ ((__nothrow__ ));




extern int link (const char *__from, const char *__to)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2))) ;




extern int linkat (int __fromfd, const char *__from, int __tofd,
     const char *__to, int __flags)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 4))) ;




extern int symlink (const char *__from, const char *__to)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2))) ;




extern ssize_t readlink (const char *__restrict __path,
    char *__restrict __buf, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2))) ;




extern int symlinkat (const char *__from, int __tofd,
        const char *__to) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 3))) ;


extern ssize_t readlinkat (int __fd, const char *__restrict __path,
      char *__restrict __buf, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 3))) ;



extern int unlink (const char *__name) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern int unlinkat (int __fd, const char *__name, int __flag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2)));



extern int rmdir (const char *__path) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern __pid_t tcgetpgrp (int __fd) __attribute__ ((__nothrow__ ));


extern int tcsetpgrp (int __fd, __pid_t __pgrp_id) __attribute__ ((__nothrow__ ));






extern char *getlogin (void);







extern int getlogin_r (char *__name, size_t __name_len) __attribute__ ((__nonnull__ (1)));




extern int setlogin (const char *__name) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));








# 1 "/usr/include/x86_64-linux-gnu/bits/getopt_posix.h" 1 3 4
# 873 "/usr/include/unistd.h" 2 3 4







extern int gethostname (char *__name, size_t __len) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));






extern int sethostname (const char *__name, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;



extern int sethostid (long int __id) __attribute__ ((__nothrow__ )) ;





extern int getdomainname (char *__name, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;
extern int setdomainname (const char *__name, size_t __len)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;





extern int vhangup (void) __attribute__ ((__nothrow__ ));


extern int revoke (const char *__file) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;







extern int profil (unsigned short int *__sample_buffer, size_t __size,
     size_t __offset, unsigned int __scale)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int acct (const char *__name) __attribute__ ((__nothrow__ ));



extern char *getusershell (void) __attribute__ ((__nothrow__ ));
extern void endusershell (void) __attribute__ ((__nothrow__ ));
extern void setusershell (void) __attribute__ ((__nothrow__ ));





extern int daemon (int __nochdir, int __noclose) __attribute__ ((__nothrow__ )) ;






extern int chroot (const char *__path) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;



extern char *getpass (const char *__prompt) __attribute__ ((__nonnull__ (1)));







extern int fsync (int __fd);





extern int syncfs (int __fd) __attribute__ ((__nothrow__ ));






extern long int gethostid (void);


extern void sync (void) __attribute__ ((__nothrow__ ));





extern int getpagesize (void) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));




extern int getdtablesize (void) __attribute__ ((__nothrow__ ));
# 994 "/usr/include/unistd.h" 3 4
extern int truncate (const char *__file, __off_t __length)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;
# 1006 "/usr/include/unistd.h" 3 4
extern int truncate64 (const char *__file, __off64_t __length)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1))) ;
# 1017 "/usr/include/unistd.h" 3 4
extern int ftruncate (int __fd, __off_t __length) __attribute__ ((__nothrow__ )) ;
# 1027 "/usr/include/unistd.h" 3 4
extern int ftruncate64 (int __fd, __off64_t __length) __attribute__ ((__nothrow__ )) ;
# 1038 "/usr/include/unistd.h" 3 4
extern int brk (void *__addr) __attribute__ ((__nothrow__ )) ;





extern void *sbrk (intptr_t __delta) __attribute__ ((__nothrow__ ));
# 1059 "/usr/include/unistd.h" 3 4
extern long int syscall (long int __sysno, ...) __attribute__ ((__nothrow__ ));
# 1082 "/usr/include/unistd.h" 3 4
extern int lockf (int __fd, int __cmd, __off_t __len) ;
# 1092 "/usr/include/unistd.h" 3 4
extern int lockf64 (int __fd, int __cmd, __off64_t __len) ;
# 1110 "/usr/include/unistd.h" 3 4
ssize_t copy_file_range (int __infd, __off64_t *__pinoff,
    int __outfd, __off64_t *__poutoff,
    size_t __length, unsigned int __flags);





extern int fdatasync (int __fildes);







extern char *crypt (const char *__key, const char *__salt)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));



extern void encrypt (char *__glibc_block, int __edflag)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));






extern void swab (const void *__restrict __from, void *__restrict __to,
    ssize_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1, 2)));
# 1167 "/usr/include/unistd.h" 3 4
int getentropy (void *__buffer, size_t __length) ;
# 41 "../lib/unistd.h" 2 3
# 753 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 783 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 806 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 846 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 874 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 967 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1000 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1034 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1062 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1083 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1102 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1129 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1161 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1225 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1254 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1290 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1319 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1444 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1476 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1494 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1509 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1525 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1541 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1561 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1592 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1621 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1656 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1682 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1701 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 1725 "../lib/unistd.h" 3
extern int rpl_pipe2 (int fd[2], int flags) __attribute__ ((__nonnull__ (1)));
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 1827 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1857 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1890 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;



extern int _gl_cxxalias_dummy;
# 1913 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 1994 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 2023 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 2105 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 2131 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 2189 "../lib/unistd.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 35 "./system.h" 2



# 1 "../lib/pathmax.h" 1
# 39 "./system.h" 2




# 1 "../lib/configmake.h" 1
# 44 "./system.h" 2

# 1 "../lib/sys/time.h" 1
# 25 "../lib/sys/time.h" 3
# 39 "../lib/sys/time.h" 3
# 1 "/usr/include/x86_64-linux-gnu/sys/time.h" 1 3 4
# 32 "/usr/include/x86_64-linux-gnu/sys/time.h" 3 4
# 1 "../lib/sys/select.h" 1 3 4
# 20 "../lib/sys/select.h" 3
# 33 "/usr/include/x86_64-linux-gnu/sys/time.h" 2 3 4
# 52 "/usr/include/x86_64-linux-gnu/sys/time.h" 3 4
struct timezone
  {
    int tz_minuteswest;
    int tz_dsttime;
  };

typedef struct timezone *__restrict __timezone_ptr_t;
# 68 "/usr/include/x86_64-linux-gnu/sys/time.h" 3 4
extern int gettimeofday (struct timeval *__restrict __tv,
    __timezone_ptr_t __tz) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));




extern int settimeofday (const struct timeval *__tv,
    const struct timezone *__tz)
     __attribute__ ((__nothrow__ ));





extern int adjtime (const struct timeval *__delta,
      struct timeval *__olddelta) __attribute__ ((__nothrow__ ));




enum __itimer_which
  {

    ITIMER_REAL = 0,


    ITIMER_VIRTUAL = 1,



    ITIMER_PROF = 2

  };



struct itimerval
  {

    struct timeval it_interval;

    struct timeval it_value;
  };




typedef enum __itimer_which __itimer_which_t;






extern int getitimer (__itimer_which_t __which,
        struct itimerval *__value) __attribute__ ((__nothrow__ ));




extern int setitimer (__itimer_which_t __which,
        const struct itimerval *__restrict __new,
        struct itimerval *__restrict __old) __attribute__ ((__nothrow__ ));




extern int utimes (const char *__file, const struct timeval __tvp[2])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));



extern int lutimes (const char *__file, const struct timeval __tvp[2])
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern int futimes (int __fd, const struct timeval __tvp[2]) __attribute__ ((__nothrow__ ));






extern int futimesat (int __fd, const char *__file,
        const struct timeval __tvp[2]) __attribute__ ((__nothrow__ ));
# 40 "../lib/sys/time.h" 2 3
# 579 "../lib/sys/time.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 46 "./system.h" 2
# 1 "../lib/time.h" 1
# 21 "../lib/time.h" 3
# 47 "./system.h" 2







# 1 "/usr/include/x86_64-linux-gnu/sys/sysmacros.h" 1 3 4
# 55 "./system.h" 2
# 72 "./system.h"
# 1 "../lib/string.h" 1
# 21 "../lib/string.h" 3
# 73 "./system.h" 2
# 1 "/usr/include/errno.h" 1 3 4
# 28 "/usr/include/errno.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/errno.h" 1 3 4
# 26 "/usr/include/x86_64-linux-gnu/bits/errno.h" 3 4
# 1 "/usr/include/linux/errno.h" 1 3 4
# 1 "/usr/include/x86_64-linux-gnu/asm/errno.h" 1 3 4
# 1 "/usr/include/asm-generic/errno.h" 1 3 4




# 1 "/usr/include/asm-generic/errno-base.h" 1 3 4
# 6 "/usr/include/asm-generic/errno.h" 2 3 4
# 2 "/usr/include/x86_64-linux-gnu/asm/errno.h" 2 3 4
# 2 "/usr/include/linux/errno.h" 2 3 4
# 27 "/usr/include/x86_64-linux-gnu/bits/errno.h" 2 3 4
# 29 "/usr/include/errno.h" 2 3 4








extern int *__errno_location (void) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));







extern char *program_invocation_name;
extern char *program_invocation_short_name;





typedef int error_t;
# 74 "./system.h" 2
# 83 "./system.h"
# 1 "../lib/stdlib.h" 1
# 21 "../lib/stdlib.h" 3
# 84 "./system.h" 2
# 1 "./version.h" 1
extern char const *Version;
# 85 "./system.h" 2


enum
{
  EXIT_TIMEDOUT = 124,
  EXIT_CANCELED = 125,
  EXIT_CANNOT_INVOKE = 126,
  EXIT_ENOENT = 127
};


# 1 "../lib/exitfail.h" 1
# 18 "../lib/exitfail.h"
extern int volatile exit_failure;
# 96 "./system.h" 2


static inline void
initialize_exit_failure (int status)
{
  if (status != 1)
    exit_failure = status;
}


# 1 "../lib/fcntl.h" 1
# 23 "../lib/fcntl.h" 3
# 56 "../lib/fcntl.h" 3
# 1 "../lib/sys/types.h" 1 3
# 21 "../lib/sys/types.h" 3
# 57 "../lib/fcntl.h" 2 3
# 67 "../lib/fcntl.h" 3
# 1 "/usr/include/fcntl.h" 1 3 4
# 35 "/usr/include/fcntl.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/fcntl.h" 1 3 4
# 35 "/usr/include/x86_64-linux-gnu/bits/fcntl.h" 3 4
struct flock
  {
    short int l_type;
    short int l_whence;

    __off_t l_start;
    __off_t l_len;




    __pid_t l_pid;
  };


struct flock64
  {
    short int l_type;
    short int l_whence;
    __off64_t l_start;
    __off64_t l_len;
    __pid_t l_pid;
  };




# 1 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 1 3 4
# 38 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/types/struct_iovec.h" 1 3 4
# 23 "/usr/include/x86_64-linux-gnu/bits/types/struct_iovec.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/types/struct_iovec.h" 2 3 4


struct iovec
  {
    void *iov_base;
    size_t iov_len;
  };
# 39 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 2 3 4
# 265 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 3 4
enum __pid_type
  {
    F_OWNER_TID = 0,
    F_OWNER_PID,
    F_OWNER_PGRP,
    F_OWNER_GID = F_OWNER_PGRP
  };


struct f_owner_ex
  {
    enum __pid_type type;
    __pid_t pid;
  };
# 346 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 3 4
# 1 "/usr/include/linux/falloc.h" 1 3 4
# 347 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 2 3 4



struct file_handle
{
  unsigned int handle_bytes;
  int handle_type;

  unsigned char f_handle[0];
};
# 385 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 3 4
extern __ssize_t readahead (int __fd, __off64_t __offset, size_t __count)
    __attribute__ ((__nothrow__ ));






extern int sync_file_range (int __fd, __off64_t __offset, __off64_t __count,
       unsigned int __flags);






extern __ssize_t vmsplice (int __fdout, const struct iovec *__iov,
      size_t __count, unsigned int __flags);





extern __ssize_t splice (int __fdin, __off64_t *__offin, int __fdout,
    __off64_t *__offout, size_t __len,
    unsigned int __flags);





extern __ssize_t tee (int __fdin, int __fdout, size_t __len,
        unsigned int __flags);






extern int fallocate (int __fd, int __mode, __off_t __offset, __off_t __len);
# 435 "/usr/include/x86_64-linux-gnu/bits/fcntl-linux.h" 3 4
extern int fallocate64 (int __fd, int __mode, __off64_t __offset,
   __off64_t __len);




extern int name_to_handle_at (int __dfd, const char *__name,
         struct file_handle *__handle, int *__mnt_id,
         int __flags) __attribute__ ((__nothrow__ ));





extern int open_by_handle_at (int __mountdirfd, struct file_handle *__handle,
         int __flags);
# 62 "/usr/include/x86_64-linux-gnu/bits/fcntl.h" 2 3 4
# 36 "/usr/include/fcntl.h" 2 3 4
# 78 "/usr/include/fcntl.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/stat.h" 1 3 4
# 79 "/usr/include/fcntl.h" 2 3 4
# 147 "/usr/include/fcntl.h" 3 4
extern int fcntl (int __fd, int __cmd, ...);
# 157 "/usr/include/fcntl.h" 3 4
extern int open (const char *__file, int __oflag, ...) __attribute__ ((__nonnull__ (1)));
# 167 "/usr/include/fcntl.h" 3 4
extern int open64 (const char *__file, int __oflag, ...) __attribute__ ((__nonnull__ (1)));
# 181 "/usr/include/fcntl.h" 3 4
extern int openat (int __fd, const char *__file, int __oflag, ...)
     __attribute__ ((__nonnull__ (2)));
# 192 "/usr/include/fcntl.h" 3 4
extern int openat64 (int __fd, const char *__file, int __oflag, ...)
     __attribute__ ((__nonnull__ (2)));
# 203 "/usr/include/fcntl.h" 3 4
extern int creat (const char *__file, mode_t __mode) __attribute__ ((__nonnull__ (1)));
# 213 "/usr/include/fcntl.h" 3 4
extern int creat64 (const char *__file, mode_t __mode) __attribute__ ((__nonnull__ (1)));
# 249 "/usr/include/fcntl.h" 3 4
extern int posix_fadvise (int __fd, off_t __offset, off_t __len,
     int __advise) __attribute__ ((__nothrow__ ));
# 261 "/usr/include/fcntl.h" 3 4
extern int posix_fadvise64 (int __fd, off64_t __offset, off64_t __len,
       int __advise) __attribute__ ((__nothrow__ ));
# 271 "/usr/include/fcntl.h" 3 4
extern int posix_fallocate (int __fd, off_t __offset, off_t __len);
# 282 "/usr/include/fcntl.h" 3 4
extern int posix_fallocate64 (int __fd, off64_t __offset, off64_t __len);
# 68 "../lib/fcntl.h" 2 3
# 588 "../lib/fcntl.h" 3
extern int rpl_fcntl (int fd, int action, ...);
extern int _gl_cxxalias_dummy;
# 602 "../lib/fcntl.h" 3
extern int _gl_cxxalias_dummy;
# 621 "../lib/fcntl.h" 3
extern int _gl_cxxalias_dummy;




extern int _gl_cxxalias_dummy;
# 652 "../lib/fcntl.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 106 "./system.h" 2

# 1 "../lib/dirent.h" 1
# 22 "../lib/dirent.h" 3





# 1 "/usr/include/dirent.h" 1 3 4
# 61 "/usr/include/dirent.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/dirent.h" 1 3 4
# 22 "/usr/include/x86_64-linux-gnu/bits/dirent.h" 3 4
struct dirent
  {

    __ino_t d_ino;
    __off_t d_off;




    unsigned short int d_reclen;
    unsigned char d_type;
    char d_name[256];
  };


struct dirent64
  {
    __ino64_t d_ino;
    __off64_t d_off;
    unsigned short int d_reclen;
    unsigned char d_type;
    char d_name[256];
  };
# 62 "/usr/include/dirent.h" 2 3 4
# 97 "/usr/include/dirent.h" 3 4
enum
  {
    DT_UNKNOWN = 0,

    DT_FIFO = 1,

    DT_CHR = 2,

    DT_DIR = 4,

    DT_BLK = 6,

    DT_REG = 8,

    DT_LNK = 10,

    DT_SOCK = 12,

    DT_WHT = 14

  };
# 127 "/usr/include/dirent.h" 3 4
typedef struct __dirstream DIR;






extern DIR *opendir (const char *__name) __attribute__ ((__nonnull__ (1)));






extern DIR *fdopendir (int __fd);







extern int closedir (DIR *__dirp) __attribute__ ((__nonnull__ (1)));
# 162 "/usr/include/dirent.h" 3 4
extern struct dirent *readdir (DIR *__dirp) __attribute__ ((__nonnull__ (1)));
# 173 "/usr/include/dirent.h" 3 4
extern struct dirent64 *readdir64 (DIR *__dirp) __attribute__ ((__nonnull__ (1)));
# 183 "/usr/include/dirent.h" 3 4
extern int readdir_r (DIR *__restrict __dirp,
        struct dirent *__restrict __entry,
        struct dirent **__restrict __result)
     __attribute__ ((__nonnull__ (1, 2, 3))) __attribute__ ((__deprecated__));
# 201 "/usr/include/dirent.h" 3 4
extern int readdir64_r (DIR *__restrict __dirp,
   struct dirent64 *__restrict __entry,
   struct dirent64 **__restrict __result)
  __attribute__ ((__nonnull__ (1, 2, 3))) __attribute__ ((__deprecated__));




extern void rewinddir (DIR *__dirp) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern void seekdir (DIR *__dirp, long int __pos) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));


extern long int telldir (DIR *__dirp) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));





extern int dirfd (DIR *__dirp) __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (1)));
# 245 "/usr/include/dirent.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 246 "/usr/include/dirent.h" 2 3 4
# 255 "/usr/include/dirent.h" 3 4
extern int scandir (const char *__restrict __dir,
      struct dirent ***__restrict __namelist,
      int (*__selector) (const struct dirent *),
      int (*__cmp) (const struct dirent **,
      const struct dirent **))
     __attribute__ ((__nonnull__ (1, 2)));
# 278 "/usr/include/dirent.h" 3 4
extern int scandir64 (const char *__restrict __dir,
        struct dirent64 ***__restrict __namelist,
        int (*__selector) (const struct dirent64 *),
        int (*__cmp) (const struct dirent64 **,
        const struct dirent64 **))
     __attribute__ ((__nonnull__ (1, 2)));
# 293 "/usr/include/dirent.h" 3 4
extern int scandirat (int __dfd, const char *__restrict __dir,
        struct dirent ***__restrict __namelist,
        int (*__selector) (const struct dirent *),
        int (*__cmp) (const struct dirent **,
        const struct dirent **))
     __attribute__ ((__nonnull__ (2, 3)));
# 315 "/usr/include/dirent.h" 3 4
extern int scandirat64 (int __dfd, const char *__restrict __dir,
   struct dirent64 ***__restrict __namelist,
   int (*__selector) (const struct dirent64 *),
   int (*__cmp) (const struct dirent64 **,
          const struct dirent64 **))
     __attribute__ ((__nonnull__ (2, 3)));




extern int alphasort (const struct dirent **__e1,
        const struct dirent **__e2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 340 "/usr/include/dirent.h" 3 4
extern int alphasort64 (const struct dirent64 **__e1,
   const struct dirent64 **__e2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 353 "/usr/include/dirent.h" 3 4
extern __ssize_t getdirentries (int __fd, char *__restrict __buf,
    size_t __nbytes,
    __off_t *__restrict __basep)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 4)));
# 370 "/usr/include/dirent.h" 3 4
extern __ssize_t getdirentries64 (int __fd, char *__restrict __buf,
      size_t __nbytes,
      __off64_t *__restrict __basep)
     __attribute__ ((__nothrow__ )) __attribute__ ((__nonnull__ (2, 4)));






extern int versionsort (const struct dirent **__e1,
   const struct dirent **__e2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 396 "/usr/include/dirent.h" 3 4
extern int versionsort64 (const struct dirent64 **__e1,
     const struct dirent64 **__e2)
     __attribute__ ((__nothrow__ )) __attribute__ ((__pure__)) __attribute__ ((__nonnull__ (1, 2)));
# 28 "../lib/dirent.h" 2 3






# 1 "../lib/sys/types.h" 1 3
# 21 "../lib/sys/types.h" 3
# 35 "../lib/dirent.h" 2 3
# 559 "../lib/dirent.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 574 "../lib/dirent.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 588 "../lib/dirent.h" 3
extern int _gl_cxxalias_dummy;
extern int _gl_cxxalias_dummy;
# 611 "../lib/dirent.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 649 "../lib/dirent.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 677 "../lib/dirent.h" 3
extern int _gl_cxxalias_dummy;

extern int _gl_cxxalias_dummy;
# 108 "./system.h" 2




enum
{
  NOT_AN_INODE_NUMBER = 0
};
# 125 "./system.h"
# 1 "../lib/inttypes.h" 1
# 26 "../lib/inttypes.h" 3
# 41 "../lib/inttypes.h" 3
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/inttypes.h" 1 3
# 21 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/inttypes.h" 3
# 1 "/usr/include/inttypes.h" 1 3 4
# 27 "/usr/include/inttypes.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdint.h" 1 3 4
# 52 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdint.h" 3 4
# 1 "/usr/include/stdint.h" 1 3 4
# 26 "/usr/include/stdint.h" 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/libc-header-start.h" 1 3 4
# 27 "/usr/include/stdint.h" 2 3 4

# 1 "/usr/include/x86_64-linux-gnu/bits/wchar.h" 1 3 4
# 29 "/usr/include/stdint.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/wordsize.h" 1 3 4
# 30 "/usr/include/stdint.h" 2 3 4







# 1 "/usr/include/x86_64-linux-gnu/bits/stdint-uintn.h" 1 3 4
# 24 "/usr/include/x86_64-linux-gnu/bits/stdint-uintn.h" 3 4
typedef __uint8_t uint8_t;
typedef __uint16_t uint16_t;
typedef __uint32_t uint32_t;
typedef __uint64_t uint64_t;
# 38 "/usr/include/stdint.h" 2 3 4





typedef signed char int_least8_t;
typedef short int int_least16_t;
typedef int int_least32_t;

typedef long int int_least64_t;






typedef unsigned char uint_least8_t;
typedef unsigned short int uint_least16_t;
typedef unsigned int uint_least32_t;

typedef unsigned long int uint_least64_t;
# 68 "/usr/include/stdint.h" 3 4
typedef signed char int_fast8_t;

typedef long int int_fast16_t;
typedef long int int_fast32_t;
typedef long int int_fast64_t;
# 81 "/usr/include/stdint.h" 3 4
typedef unsigned char uint_fast8_t;

typedef unsigned long int uint_fast16_t;
typedef unsigned long int uint_fast32_t;
typedef unsigned long int uint_fast64_t;
# 100 "/usr/include/stdint.h" 3 4
typedef unsigned long int uintptr_t;
# 111 "/usr/include/stdint.h" 3 4
typedef __intmax_t intmax_t;
typedef __uintmax_t uintmax_t;
# 53 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stdint.h" 2 3 4
# 28 "/usr/include/inttypes.h" 2 3 4






typedef int __gwchar_t;
# 271 "/usr/include/inttypes.h" 3 4
typedef struct
  {
    long int quot;
    long int rem;
  } imaxdiv_t;
# 290 "/usr/include/inttypes.h" 3 4
extern intmax_t imaxabs (intmax_t __n) __attribute__ ((__nothrow__ )) __attribute__ ((__const__));


extern imaxdiv_t imaxdiv (intmax_t __numer, intmax_t __denom)
      __attribute__ ((__nothrow__ )) __attribute__ ((__const__));


extern intmax_t strtoimax (const char *__restrict __nptr,
      char **__restrict __endptr, int __base) __attribute__ ((__nothrow__ ));


extern uintmax_t strtoumax (const char *__restrict __nptr,
       char ** __restrict __endptr, int __base) __attribute__ ((__nothrow__ ));


extern intmax_t wcstoimax (const __gwchar_t *__restrict __nptr,
      __gwchar_t **__restrict __endptr, int __base)
     __attribute__ ((__nothrow__ ));


extern uintmax_t wcstoumax (const __gwchar_t *__restrict __nptr,
       __gwchar_t ** __restrict __endptr, int __base)
     __attribute__ ((__nothrow__ ));
# 22 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/inttypes.h" 2 3
# 42 "../lib/inttypes.h" 2 3
# 1578 "../lib/inttypes.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 1608 "../lib/inttypes.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 126 "./system.h" 2
# 138 "./system.h"
# 1 "../lib/stat-macros.h" 1
# 139 "./system.h" 2

# 1 "../lib/timespec.h" 1
# 22 "../lib/timespec.h"
# 1 "../lib/time.h" 1
# 21 "../lib/time.h" 3
# 23 "../lib/timespec.h" 2
# 36 "../lib/timespec.h"
# 1 "../lib/arg-nonnull.h" 1
# 37 "../lib/timespec.h" 2





enum { TIMESPEC_HZ = 1000000000 };
enum { LOG10_TIMESPEC_HZ = 9 };




enum { TIMESPEC_RESOLUTION = TIMESPEC_HZ };
enum { LOG10_TIMESPEC_RESOLUTION = LOG10_TIMESPEC_HZ };



inline struct timespec
make_timespec (time_t s, long int ns)
{
  struct timespec r;
  r.tv_sec = s;
  r.tv_nsec = ns;
  return r;
}
# 88 "../lib/timespec.h"
inline int __attribute__ ((__pure__))
timespec_cmp (struct timespec a, struct timespec b)
{
  if (a.tv_sec < b.tv_sec)
    return -1;
  if (a.tv_sec > b.tv_sec)
    return 1;



  ((-1 <= a.tv_nsec && a.tv_nsec <= 2 * TIMESPEC_HZ) ? (void) 0 : __builtin_unreachable ());
  ((-1 <= b.tv_nsec && b.tv_nsec <= 2 * TIMESPEC_HZ) ? (void) 0 : __builtin_unreachable ());

  return a.tv_nsec - b.tv_nsec;
}



inline int __attribute__ ((__pure__))
timespec_sign (struct timespec a)
{
  return a.tv_sec < 0 ? -1 : a.tv_sec || a.tv_nsec;
}

struct timespec timespec_add (struct timespec, struct timespec)
  __attribute__ ((__const__));
struct timespec timespec_sub (struct timespec, struct timespec)
  __attribute__ ((__const__));
struct timespec dtotimespec (double)
  __attribute__ ((__const__));


inline double
timespectod (struct timespec a)
{
  return a.tv_sec + a.tv_nsec / 1e9;
}

struct timespec current_timespec (void);
void gettime (struct timespec *) __attribute__ ((__nonnull__ (1)));
int settime (struct timespec const *) __attribute__ ((__nonnull__ (1)));
# 141 "./system.h" 2

# 1 "../lib/ctype.h" 1
# 30 "../lib/ctype.h" 3





# 1 "/usr/include/ctype.h" 1 3 4
# 46 "/usr/include/ctype.h" 3 4
enum
{
  _ISupper = ((0) < 8 ? ((1 << (0)) << 8) : ((1 << (0)) >> 8)),
  _ISlower = ((1) < 8 ? ((1 << (1)) << 8) : ((1 << (1)) >> 8)),
  _ISalpha = ((2) < 8 ? ((1 << (2)) << 8) : ((1 << (2)) >> 8)),
  _ISdigit = ((3) < 8 ? ((1 << (3)) << 8) : ((1 << (3)) >> 8)),
  _ISxdigit = ((4) < 8 ? ((1 << (4)) << 8) : ((1 << (4)) >> 8)),
  _ISspace = ((5) < 8 ? ((1 << (5)) << 8) : ((1 << (5)) >> 8)),
  _ISprint = ((6) < 8 ? ((1 << (6)) << 8) : ((1 << (6)) >> 8)),
  _ISgraph = ((7) < 8 ? ((1 << (7)) << 8) : ((1 << (7)) >> 8)),
  _ISblank = ((8) < 8 ? ((1 << (8)) << 8) : ((1 << (8)) >> 8)),
  _IScntrl = ((9) < 8 ? ((1 << (9)) << 8) : ((1 << (9)) >> 8)),
  _ISpunct = ((10) < 8 ? ((1 << (10)) << 8) : ((1 << (10)) >> 8)),
  _ISalnum = ((11) < 8 ? ((1 << (11)) << 8) : ((1 << (11)) >> 8))
};
# 79 "/usr/include/ctype.h" 3 4
extern const unsigned short int **__ctype_b_loc (void)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
extern const __int32_t **__ctype_tolower_loc (void)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
extern const __int32_t **__ctype_toupper_loc (void)
     __attribute__ ((__nothrow__ )) __attribute__ ((__const__));
# 108 "/usr/include/ctype.h" 3 4
extern int isalnum (int) __attribute__ ((__nothrow__ ));
extern int isalpha (int) __attribute__ ((__nothrow__ ));
extern int iscntrl (int) __attribute__ ((__nothrow__ ));
extern int isdigit (int) __attribute__ ((__nothrow__ ));
extern int islower (int) __attribute__ ((__nothrow__ ));
extern int isgraph (int) __attribute__ ((__nothrow__ ));
extern int isprint (int) __attribute__ ((__nothrow__ ));
extern int ispunct (int) __attribute__ ((__nothrow__ ));
extern int isspace (int) __attribute__ ((__nothrow__ ));
extern int isupper (int) __attribute__ ((__nothrow__ ));
extern int isxdigit (int) __attribute__ ((__nothrow__ ));



extern int tolower (int __c) __attribute__ ((__nothrow__ ));


extern int toupper (int __c) __attribute__ ((__nothrow__ ));




extern int isblank (int) __attribute__ ((__nothrow__ ));




extern int isctype (int __c, int __mask) __attribute__ ((__nothrow__ ));






extern int isascii (int __c) __attribute__ ((__nothrow__ ));



extern int toascii (int __c) __attribute__ ((__nothrow__ ));



extern int _toupper (int) __attribute__ ((__nothrow__ ));
extern int _tolower (int) __attribute__ ((__nothrow__ ));
# 251 "/usr/include/ctype.h" 3 4
extern int isalnum_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isalpha_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int iscntrl_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isdigit_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int islower_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isgraph_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isprint_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int ispunct_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isspace_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isupper_l (int, locale_t) __attribute__ ((__nothrow__ ));
extern int isxdigit_l (int, locale_t) __attribute__ ((__nothrow__ ));

extern int isblank_l (int, locale_t) __attribute__ ((__nothrow__ ));



extern int __tolower_l (int __c, locale_t __l) __attribute__ ((__nothrow__ ));
extern int tolower_l (int __c, locale_t __l) __attribute__ ((__nothrow__ ));


extern int __toupper_l (int __c, locale_t __l) __attribute__ ((__nothrow__ ));
extern int toupper_l (int __c, locale_t __l) __attribute__ ((__nothrow__ ));
# 36 "../lib/ctype.h" 2 3
# 143 "./system.h" 2
# 156 "./system.h"
static inline unsigned char to_uchar (char ch) { return ch; }


static inline _Bool
field_sep (unsigned char ch)
{
  return ((*__ctype_b_loc ())[(int) ((ch))] & (unsigned short int) _ISblank) || ch == '\n';
}


# 1 "../lib/locale.h" 1
# 20 "../lib/locale.h" 3
# 41 "../lib/locale.h" 3
# 1 "/usr/include/locale.h" 1 3 4
# 28 "/usr/include/locale.h" 3 4
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3 4
# 29 "/usr/include/locale.h" 2 3 4
# 1 "/usr/include/x86_64-linux-gnu/bits/locale.h" 1 3 4
# 30 "/usr/include/locale.h" 2 3 4
# 51 "/usr/include/locale.h" 3 4
struct lconv
{


  char *decimal_point;
  char *thousands_sep;





  char *grouping;





  char *int_curr_symbol;
  char *currency_symbol;
  char *mon_decimal_point;
  char *mon_thousands_sep;
  char *mon_grouping;
  char *positive_sign;
  char *negative_sign;
  char int_frac_digits;
  char frac_digits;

  char p_cs_precedes;

  char p_sep_by_space;

  char n_cs_precedes;

  char n_sep_by_space;






  char p_sign_posn;
  char n_sign_posn;


  char int_p_cs_precedes;

  char int_p_sep_by_space;

  char int_n_cs_precedes;

  char int_n_sep_by_space;






  char int_p_sign_posn;
  char int_n_sign_posn;
# 118 "/usr/include/locale.h" 3 4
};



extern char *setlocale (int __category, const char *__locale) __attribute__ ((__nothrow__ ));


extern struct lconv *localeconv (void) __attribute__ ((__nothrow__ ));
# 141 "/usr/include/locale.h" 3 4
extern locale_t newlocale (int __category_mask, const char *__locale,
      locale_t __base) __attribute__ ((__nothrow__ ));
# 176 "/usr/include/locale.h" 3 4
extern locale_t duplocale (locale_t __dataset) __attribute__ ((__nothrow__ ));



extern void freelocale (locale_t __dataset) __attribute__ ((__nothrow__ ));






extern locale_t uselocale (locale_t __dataset) __attribute__ ((__nothrow__ ));
# 42 "../lib/locale.h" 2 3







# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 50 "../lib/locale.h" 2 3
# 640 "../lib/locale.h" 3
extern int _gl_cxxalias_dummy;


extern int _gl_cxxalias_dummy;
# 682 "../lib/locale.h" 3
# 1 "../lib/setlocale_null.h" 1 3
# 22 "../lib/setlocale_null.h" 3
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 23 "../lib/setlocale_null.h" 2 3

# 1 "../lib/arg-nonnull.h" 1 3
# 25 "../lib/setlocale_null.h" 2 3
# 64 "../lib/setlocale_null.h" 3
extern int setlocale_null_r (int category, char *buf, size_t bufsize)
  __attribute__ ((__nonnull__ (2)));
# 75 "../lib/setlocale_null.h" 3
extern const char *setlocale_null (int category);
# 683 "../lib/locale.h" 2 3
# 166 "./system.h" 2
# 182 "./system.h"
static inline unsigned long int
select_plural (uintmax_t n)
{


  enum { PLURAL_REDUCER = 1000000 };
  return (n <= (9223372036854775807L *2UL+1UL) ? n : n % PLURAL_REDUCER + PLURAL_REDUCER);
}
# 241 "./system.h"
# 1 "../lib/xalloc.h" 1
# 21 "../lib/xalloc.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 22 "../lib/xalloc.h" 2


# 1 "../lib/xalloc-oversized.h" 1
# 21 "../lib/xalloc-oversized.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 22 "../lib/xalloc-oversized.h" 2
# 34 "../lib/xalloc-oversized.h"
typedef ptrdiff_t __xalloc_count_type;
# 25 "../lib/xalloc.h" 2
# 51 "../lib/xalloc.h"
           _Noreturn void xalloc_die (void);

void *xmalloc (size_t s)
      __attribute__ ((__malloc__)) ;
void *xzalloc (size_t s)
      __attribute__ ((__malloc__)) ;
void *xcalloc (size_t n, size_t s)
      __attribute__ ((__malloc__)) ;
void *xrealloc (void *p, size_t s)
                                    ;
void *x2realloc (void *p, size_t *pn);
void *xmemdup (void const *p, size_t s)
                                    ;
char *xstrdup (char const *str)
      __attribute__ ((__malloc__));
# 96 "../lib/xalloc.h"
inline void *xnmalloc (size_t n, size_t s)
                    __attribute__ ((__malloc__)) ;
inline void *
xnmalloc (size_t n, size_t s)
{
  if (((size_t) ((9223372036854775807L) < (18446744073709551615UL) ? (9223372036854775807L) : (18446744073709551615UL) - 1) / (s) < (n)))
    xalloc_die ();
  return xmalloc (n * s);
}




inline void *xnrealloc (void *p, size_t n, size_t s)
                                                     ;
inline void *
xnrealloc (void *p, size_t n, size_t s)
{
  if (((size_t) ((9223372036854775807L) < (18446744073709551615UL) ? (9223372036854775807L) : (18446744073709551615UL) - 1) / (s) < (n)))
    xalloc_die ();
  return xrealloc (p, n * s);
}
# 173 "../lib/xalloc.h"
inline void *
x2nrealloc (void *p, size_t *pn, size_t s)
{
  size_t n = *pn;

  if (! p)
    {
      if (! n)
        {




          enum { DEFAULT_MXFAST = 64 * sizeof (size_t) / 4 };

          n = DEFAULT_MXFAST / s;
          n += !n;
        }
      if (((size_t) ((9223372036854775807L) < (18446744073709551615UL) ? (9223372036854775807L) : (18446744073709551615UL) - 1) / (s) < (n)))
        xalloc_die ();
    }
  else
    {




      if (((9223372036854775807L) < (18446744073709551615UL) ? (9223372036854775807L) : (18446744073709551615UL)) / 3 * 2 / s
          <= n)
        xalloc_die ();
      n += n / 2 + 1;
    }

  *pn = n;
  return xrealloc (p, n * s);
}




inline char *xcharalloc (size_t n)
                    __attribute__ ((__malloc__)) ;
inline char *
xcharalloc (size_t n)
{
  return ((char *) (sizeof (char) == 1 ? xmalloc (n) : xnmalloc (n, sizeof (char))));
}
# 242 "./system.h" 2
# 258 "./system.h"
# 1 "../lib/unlocked-io.h" 1
# 34 "../lib/unlocked-io.h"
# 1 "../lib/stdio.h" 1
# 21 "../lib/stdio.h" 3
# 35 "../lib/unlocked-io.h" 2
# 259 "./system.h" 2
# 1 "../lib/same-inode.h" 1
# 21 "../lib/same-inode.h"
# 1 "../lib/sys/types.h" 1
# 21 "../lib/sys/types.h" 3
# 22 "../lib/same-inode.h" 2
# 260 "./system.h" 2

# 1 "../lib/dirname.h" 1
# 23 "../lib/dirname.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 24 "../lib/dirname.h" 2
# 1 "../lib/dosname.h" 1
# 25 "../lib/dirname.h" 2
# 39 "../lib/dirname.h"
char *base_name (char const *file) __attribute__ ((__malloc__));
char *dir_name (char const *file);


char *mdir_name (char const *file);
size_t base_len (char const *file) __attribute__ ((__pure__));
size_t dir_len (char const *file) __attribute__ ((__pure__));
char *last_component (char const *file) __attribute__ ((__pure__));

_Bool strip_trailing_slashes (char *file);
# 262 "./system.h" 2
# 1 "../lib/openat.h" 1
# 22 "../lib/openat.h"
# 1 "../lib/fcntl.h" 1
# 23 "../lib/fcntl.h" 3
# 23 "../lib/openat.h" 2

# 1 "../lib/sys/types.h" 1
# 21 "../lib/sys/types.h" 3
# 25 "../lib/openat.h" 2
# 1 "../lib/sys/stat.h" 1
# 26 "../lib/sys/stat.h" 3
# 26 "../lib/openat.h" 2
# 48 "../lib/openat.h"
_Noreturn void openat_restore_fail (int);
_Noreturn void openat_save_fail (int);
# 61 "../lib/openat.h"
inline int
chownat (int fd, char const *file, uid_t owner, gid_t group)
{
  return fchownat (fd, file, owner, group, 0);
}

inline int
lchownat (int fd, char const *file, uid_t owner, gid_t group)
{
  return fchownat (fd, file, owner, group, 0x100);
}
# 81 "../lib/openat.h"
inline int
chmodat (int fd, char const *file, mode_t mode)
{
  return rpl_fchmodat (fd, file, mode, 0);
}

inline int
lchmodat (int fd, char const *file, mode_t mode)
{
  return rpl_fchmodat (fd, file, mode, 0x100);
}
# 101 "../lib/openat.h"
inline int
statat (int fd, char const *name, struct stat *st)
{
  return fstatat (fd, name, st, 0);
}

inline int
lstatat (int fd, char const *name, struct stat *st)
{
  return fstatat (fd, name, st, 0x100);
}
# 263 "./system.h" 2

static inline _Bool
dot_or_dotdot (char const *file_name)
{
  if (file_name[0] == '.')
    {
      char sep = file_name[(file_name[1] == '.') + 1];
      return (! sep || ((sep) == '/'));
    }
  else
    return 0;
}


static inline struct dirent const *
readdir_ignoring_dot_and_dotdot (DIR *dirp)
{
  while (1)
    {
      struct dirent const *dp = readdir (dirp);
      if (dp == ((void*)0) || ! dot_or_dotdot (dp->d_name))
        return dp;
    }
}




static inline _Bool
is_empty_dir (int fd_cwd, char const *dir)
{
  DIR *dirp;
  struct dirent const *dp;
  int saved_errno;
  int fd = openat (fd_cwd, dir,
                   (00 | 0200000
                    | 0400 | 0400000 | 04000));

  if (fd < 0)
    return 0;

  dirp = fdopendir (fd);
  if (dirp == ((void*)0))
    {
      close (fd);
      return 0;
    }

  (*__errno_location ()) = 0;
  dp = readdir_ignoring_dot_and_dotdot (dirp);
  saved_errno = (*__errno_location ());
  closedir (dirp);
  (*__errno_location ()) = saved_errno;
  if (dp != ((void*)0))
    return 0;
  return saved_errno == 0 ? 1 : 0;
}






enum
{
  GETOPT_HELP_CHAR = ((-127 -1) - 2),
  GETOPT_VERSION_CHAR = ((-127 -1) - 3)
};
# 357 "./system.h"
# 1 "../lib/closein.h" 1
# 25 "../lib/closein.h"
void close_stdin_set_file_name (const char *file);
void close_stdin (void);
# 358 "./system.h" 2
# 1 "../lib/closeout.h" 1
# 28 "../lib/closeout.h"
void close_stdout_set_file_name (const char *file);
void close_stdout_set_ignore_EPIPE (_Bool ignore);
void close_stdout (void);
# 359 "./system.h" 2


# 1 "../lib/version-etc.h" 1
# 23 "../lib/version-etc.h"
# 1 "../lib/stdio.h" 1
# 21 "../lib/stdio.h" 3
# 24 "../lib/version-etc.h" 2
# 34 "../lib/version-etc.h"
extern const char version_etc_copyright[];
# 52 "../lib/version-etc.h"
extern void version_etc_arn (FILE *stream,
                             const char *command_name, const char *package,
                             const char *version,
                             const char * const * authors, size_t n_authors);


extern void version_etc_ar (FILE *stream,
                            const char *command_name, const char *package,
                            const char *version, const char * const * authors);


extern void version_etc_va (FILE *stream,
                            const char *command_name, const char *package,
                            const char *version, va_list authors);



extern void version_etc (FILE *stream,
                         const char *command_name, const char *package,
                         const char *version,
                                                              ...)
  __attribute__ ((__sentinel__));


extern void unused__emit_bug_reporting_address (void);
# 362 "./system.h" 2


# 1 "../lib/propername.h" 1
# 92 "../lib/propername.h"
extern const char * proper_name (const char *name) ;





extern const char * proper_name_utf8 (const char *name_ascii,
                                      const char *name_utf8);
# 365 "./system.h" 2







# 1 "../lib/progname.h" 1
# 32 "../lib/progname.h"
extern const char *program_name;




extern void set_program_name (const char *argv0);
# 373 "./system.h" 2
# 389 "./system.h"
# 1 "../lib/intprops.h" 1
# 390 "./system.h" 2
# 471 "./system.h"
static inline size_t __attribute__ ((__const__))
gcd (size_t u, size_t v)
{
  do
    {
      size_t t = u % v;
      u = v;
      v = t;
    }
  while (v);

  return u;
}





static inline size_t __attribute__ ((__const__))
lcm (size_t u, size_t v)
{
  return u * (v / gcd (u, v));
}






static inline void *
ptr_align (void const *ptr, size_t alignment)
{
  char const *p0 = ptr;
  char const *p1 = p0 + alignment - 1;
  return (void *) (p1 - (size_t) p1 % alignment);
}




static inline _Bool __attribute__ ((__pure__))
is_nul (void const *buf, size_t length)
{
  const unsigned char *p = buf;
# 524 "./system.h"
  unsigned char word;


  if (! length)
      return 1;


  while (__builtin_expect ((length & (sizeof word - 1)), 0))
    {
      if (*p)
        return 0;
      p++;
      length--;
      if (! length)
        return 1;
   }


  for (;;)
    {
      memcpy (&word, p, sizeof word);
      if (word)
        return 0;
      p += sizeof word;
      length -= sizeof word;
      if (! length)
        return 1;
      if (__builtin_expect ((length & 15), 0) == 0)
        break;
   }


   return memcmp (buf, p, length) == 0;
}
# 580 "./system.h"
static inline void
emit_stdin_note (void)
{
  fputs_unlocked (gettext ("\nWith no FILE, or when FILE is -, read standard input.\n"),stdout);


}
static inline void
emit_mandatory_arg_note (void)
{
  fputs_unlocked (gettext ("\nMandatory arguments to long options are mandatory for short options too.\n"),stdout);


}

static inline void
emit_size_note (void)
{
  fputs_unlocked (gettext ("\nThe SIZE argument is an integer and optional unit (example: 10K is 10*1024).\nUnits are K,M,G,T,P,E,Z,Y (powers of 1024) or KB,MB,... (powers of 1000).\nBinary prefixes can be used, too: KiB=K, MiB=M, and so on.\n"),stdout);




}

static inline void
emit_blocksize_note (char const *program)
{
  printf (gettext ("\nDisplay values are in units of the first available SIZE from --block-size,\nand the %s_BLOCK_SIZE, BLOCK_SIZE and BLOCKSIZE environment variables.\nOtherwise, units default to 1024 bytes (or 512 if POSIXLY_CORRECT is set).\n"), program);




}

static inline void
emit_backup_suffix_note (void)
{
  fputs_unlocked (gettext ("\nThe backup suffix is '~', unless set with --suffix or SIMPLE_BACKUP_SUFFIX.\nThe version control method may be selected via the --backup option or through\nthe VERSION_CONTROL environment variable.  Here are the values:\n\n"),stdout);






  fputs_unlocked (gettext ("  none, off       never make backups (even if --backup is given)\n  numbered, t     make numbered backups\n  existing, nil   numbered if numbered backups exist, simple otherwise\n  simple, never   always make simple backups\n"),stdout);





}

static inline void
emit_ancillary_info (char const *program)
{
  struct infomap { char const *program; char const *node; } const infomap[] = {
    { "[", "test invocation" },
    { "coreutils", "Multi-call invocation" },
    { "sha224sum", "sha2 utilities" },
    { "sha256sum", "sha2 utilities" },
    { "sha384sum", "sha2 utilities" },
    { "sha512sum", "sha2 utilities" },
    { ((void*)0), ((void*)0) }
  };

  char const *node = program;
  struct infomap const *map_prog = infomap;

  while (map_prog->program && ! (strcmp (program, map_prog->program) == 0))
    map_prog++;

  if (map_prog->node)
    node = map_prog->node;

  printf (gettext ("\n%s online help: <%s>\n"), "GNU coreutils", "https://www.gnu.org/software/coreutils/");



  const char *lc_messages = setlocale (5, ((void*)0));
  if (lc_messages && strncmp (lc_messages, "" "en_" "", sizeof ("en_") - 1))
    {




      fputs_unlocked (gettext ("Report any translation bugs to " "<https://translationproject.org/team/>\n"),stdout);

    }
  printf (gettext ("Full documentation <%s%s>\n"),
          "https://www.gnu.org/software/coreutils/", program);
  printf (gettext ("or available locally via: info '(coreutils) %s%s'\n"),
          node, node == program ? " invocation" : "");
}
# 687 "./system.h"
# 1 "../lib/inttostr.h" 1
# 21 "../lib/inttostr.h"
# 1 "../lib/sys/types.h" 1
# 21 "../lib/sys/types.h" 3
# 22 "../lib/inttostr.h" 2
# 42 "../lib/inttostr.h"
char *imaxtostr (intmax_t, char *) __attribute__ ((__warn_unused_result__));
char *inttostr (int, char *) __attribute__ ((__warn_unused_result__));
char *offtostr (off_t, char *) __attribute__ ((__warn_unused_result__));
char *uinttostr (unsigned int, char *) __attribute__ ((__warn_unused_result__));
char *umaxtostr (uintmax_t, char *) __attribute__ ((__warn_unused_result__));
# 688 "./system.h" 2

static inline char *
timetostr (time_t t, char *buf)
{
  return ((! ((time_t) 0 < (time_t) -1))
          ? imaxtostr (t, buf)
          : umaxtostr (t, buf));
}

static inline char *
bad_cast (char const *s)
{
  return (char *) s;
}


static inline _Bool
usable_st_size (struct stat const *sb)
{
  return (((((sb->st_mode)) & 0170000) == (0100000)) || ((((sb->st_mode)) & 0170000) == (0120000))
          || ((sb)->st_mode - (sb)->st_mode) || 0);
}

void usage (int status) __attribute__ ((__noreturn__));
# 740 "./system.h"
static inline char *
stzncpy (char *__restrict dest, char const *__restrict src, size_t len)
{
  char const *src_end = src + len;
  while (src < src_end && *src)
    *dest++ = *src++;
  *dest = 0;
  return dest;
}
# 758 "./system.h"
static inline char * se_const (char const * sctx) { return (char *) sctx; }





static inline _Bool
is_ENOTSUP (int err)
{
  return err == 95 || (95 != 95 && err == 95);
}





# 1 "../lib/quotearg.h" 1
# 24 "../lib/quotearg.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 25 "../lib/quotearg.h" 2







enum quoting_style
  {
# 45 "../lib/quotearg.h"
    literal_quoting_style,
# 59 "../lib/quotearg.h"
    shell_quoting_style,
# 74 "../lib/quotearg.h"
    shell_always_quoting_style,
# 89 "../lib/quotearg.h"
    shell_escape_quoting_style,
# 105 "../lib/quotearg.h"
    shell_escape_always_quoting_style,
# 119 "../lib/quotearg.h"
    c_quoting_style,
# 131 "../lib/quotearg.h"
    c_maybe_quoting_style,
# 144 "../lib/quotearg.h"
    escape_quoting_style,
# 170 "../lib/quotearg.h"
    locale_quoting_style,
# 195 "../lib/quotearg.h"
    clocale_quoting_style,
# 238 "../lib/quotearg.h"
    custom_quoting_style
  };


enum quoting_flags
  {



    QA_ELIDE_NULL_BYTES = 0x01,




    QA_ELIDE_OUTER_QUOTES = 0x02,





    QA_SPLIT_TRIGRAPHS = 0x04
  };







extern char const *const quoting_style_args[];
extern enum quoting_style const quoting_style_vals[];

struct quoting_options;







struct quoting_options *clone_quoting_options (struct quoting_options *o);


enum quoting_style get_quoting_style (struct quoting_options const *o);



void set_quoting_style (struct quoting_options *o, enum quoting_style s);
# 294 "../lib/quotearg.h"
int set_char_quoting (struct quoting_options *o, char c, int i);





int set_quoting_flags (struct quoting_options *o, int i);
# 311 "../lib/quotearg.h"
void set_custom_quoting (struct quoting_options *o,
                         char const *left_quote,
                         char const *right_quote);
# 326 "../lib/quotearg.h"
size_t quotearg_buffer (char *__restrict buffer, size_t buffersize,
                        char const *arg, size_t argsize,
                        struct quoting_options const *o);




char *quotearg_alloc (char const *arg, size_t argsize,
                      struct quoting_options const *o);







char *quotearg_alloc_mem (char const *arg, size_t argsize,
                          size_t *size, struct quoting_options const *o);
# 352 "../lib/quotearg.h"
char *quotearg_n (int n, char const *arg);


char *quotearg (char const *arg);




char *quotearg_n_mem (int n, char const *arg, size_t argsize);


char *quotearg_mem (char const *arg, size_t argsize);




char *quotearg_n_style (int n, enum quoting_style s, char const *arg);




char *quotearg_n_style_mem (int n, enum quoting_style s,
                            char const *arg, size_t argsize);


char *quotearg_style (enum quoting_style s, char const *arg);


char *quotearg_style_mem (enum quoting_style s,
                          char const *arg, size_t argsize);



char *quotearg_char (char const *arg, char ch);


char *quotearg_char_mem (char const *arg, size_t argsize, char ch);


char *quotearg_colon (char const *arg);


char *quotearg_colon_mem (char const *arg, size_t argsize);


char *quotearg_n_style_colon (int n, enum quoting_style s, char const *arg);





char *quotearg_n_custom (int n, char const *left_quote,
                         char const *right_quote, char const *arg);



char *quotearg_n_custom_mem (int n, char const *left_quote,
                             char const *right_quote,
                             char const *arg, size_t argsize);


char *quotearg_custom (char const *left_quote, char const *right_quote,
                       char const *arg);



char *quotearg_custom_mem (char const *left_quote,
                           char const *right_quote,
                           char const *arg, size_t argsize);


void quotearg_free (void);
# 774 "./system.h" 2
# 31 "numfmt.c" 2
# 1 "../lib/xstrtol.h" 1
# 22 "../lib/xstrtol.h"
# 1 "../lib/inttypes.h" 1
# 26 "../lib/inttypes.h" 3
# 23 "../lib/xstrtol.h" 2


enum strtol_error
  {
    LONGINT_OK = 0,



    LONGINT_OVERFLOW = 1,
    LONGINT_INVALID_SUFFIX_CHAR = 2,

    LONGINT_INVALID_SUFFIX_CHAR_WITH_OVERFLOW = (LONGINT_INVALID_SUFFIX_CHAR
                                                 | LONGINT_OVERFLOW),
    LONGINT_INVALID = 4
  };
typedef enum strtol_error strtol_error;




strtol_error xstrtol (const char *, char **, int, long int *, const char *);
strtol_error xstrtoul (const char *, char **, int, unsigned long int *, const char *);
strtol_error xstrtoll (const char *, char **, int, long long int *, const char *);
strtol_error xstrtoull (const char *, char **, int, unsigned long long int *, const char *);
strtol_error xstrtoimax (const char *, char **, int, intmax_t *, const char *);
strtol_error xstrtoumax (const char *, char **, int, uintmax_t *, const char *);
# 32 "numfmt.c" 2
# 1 "../lib/xstrndup.h" 1
# 18 "../lib/xstrndup.h"
# 1 "/home/codeman/.itsoflife/mydata/local/packages-live/llvm-clang9.0.0/build/lib/clang/9.0.0/include/stddef.h" 1 3
# 19 "../lib/xstrndup.h" 2




extern char *xstrndup (const char *string, size_t n) __attribute__ ((__malloc__));
# 33 "numfmt.c" 2

# 1 "./set-fields.h" 1
# 20 "./set-fields.h"
struct field_range_pair
  {
    uintmax_t lo;
    uintmax_t hi;
  };


extern struct field_range_pair *frp;


extern size_t n_frp;


enum
{
  SETFLD_ALLOW_DASH = 0x01,
  SETFLD_COMPLEMENT = 0x02,
  SETFLD_ERRMSG_USE_POS = 0x04

};


extern void set_fields (const char *fieldstr, unsigned int options);


extern void reset_fields (void);
# 35 "numfmt.c" 2
# 46 "numfmt.c"
enum { EXIT_CONVERSION_WARNINGS = 2 };

enum
{
  FROM_OPTION = 127 + 1,
  FROM_UNIT_OPTION,
  TO_OPTION,
  TO_UNIT_OPTION,
  ROUND_OPTION,
  SUFFIX_OPTION,
  GROUPING_OPTION,
  PADDING_OPTION,
  FIELD_OPTION,
  DEBUG_OPTION,
  DEV_DEBUG_OPTION,
  HEADER_OPTION,
  FORMAT_OPTION,
  INVALID_OPTION
};

enum scale_type
{
  scale_none,
  scale_auto,
  scale_SI,
  scale_IEC,
  scale_IEC_I
};

static char const *const scale_from_args[] =
{
  "none", "auto", "si", "iec", "iec-i", ((void*)0)
};

static enum scale_type const scale_from_types[] =
{
  scale_none, scale_auto, scale_SI, scale_IEC, scale_IEC_I
};

static char const *const scale_to_args[] =
{
  "none", "si", "iec", "iec-i", ((void*)0)
};

static enum scale_type const scale_to_types[] =
{
  scale_none, scale_SI, scale_IEC, scale_IEC_I
};


enum round_type
{
  round_ceiling,
  round_floor,
  round_from_zero,
  round_to_zero,
  round_nearest,
};

static char const *const round_args[] =
{
  "up", "down", "from-zero", "towards-zero", "nearest", ((void*)0)
};

static enum round_type const round_types[] =
{
  round_ceiling, round_floor, round_from_zero, round_to_zero, round_nearest
};


enum inval_type
{
  inval_abort,
  inval_fail,
  inval_warn,
  inval_ignore
};

static char const *const inval_args[] =
{
  "abort", "fail", "warn", "ignore", ((void*)0)
};

static enum inval_type const inval_types[] =
{
  inval_abort, inval_fail, inval_warn, inval_ignore
};

static struct option const longopts[] =
{
  {"from", 1, ((void*)0), FROM_OPTION},
  {"from-unit", 1, ((void*)0), FROM_UNIT_OPTION},
  {"to", 1, ((void*)0), TO_OPTION},
  {"to-unit", 1, ((void*)0), TO_UNIT_OPTION},
  {"round", 1, ((void*)0), ROUND_OPTION},
  {"padding", 1, ((void*)0), PADDING_OPTION},
  {"suffix", 1, ((void*)0), SUFFIX_OPTION},
  {"grouping", 0, ((void*)0), GROUPING_OPTION},
  {"delimiter", 1, ((void*)0), 'd'},
  {"field", 1, ((void*)0), FIELD_OPTION},
  {"debug", 0, ((void*)0), DEBUG_OPTION},
  {"-debug", 0, ((void*)0), DEV_DEBUG_OPTION},
  {"header", 2, ((void*)0), HEADER_OPTION},
  {"format", 1, ((void*)0), FORMAT_OPTION},
  {"invalid", 1, ((void*)0), INVALID_OPTION},
  {"zero-terminated", 0, ((void*)0), 'z'},
  {"help", 0, ((void*)0), GETOPT_HELP_CHAR},
  {"version", 0, ((void*)0), GETOPT_VERSION_CHAR},
  {((void*)0), 0, ((void*)0), 0}
};


enum { DELIMITER_DEFAULT = 127 + 1 };



enum { MAX_UNSCALED_DIGITS = 18 };





enum { MAX_ACCEPTABLE_DIGITS = 27 };

static enum scale_type scale_from = scale_none;
static enum scale_type scale_to = scale_none;
static enum round_type round_style = round_from_zero;
static enum inval_type inval_style = inval_abort;
static const char *suffix = ((void*)0);
static uintmax_t from_unit_size = 1;
static uintmax_t to_unit_size = 1;
static int grouping = 0;
static char *padding_buffer = ((void*)0);
static size_t padding_buffer_size = 0;
static long int padding_width = 0;
static long int zero_padding_width = 0;
static long int user_precision = -1;
static const char *format_str = ((void*)0);
static char *format_str_prefix = ((void*)0);
static char *format_str_suffix = ((void*)0);


static int conv_exit_code = EXIT_CONVERSION_WARNINGS;



static int auto_padding = 0;
static mbs_align_t padding_alignment = MBS_ALIGN_RIGHT;


static int delimiter = DELIMITER_DEFAULT;


static unsigned char line_delim = '\n';


static uintmax_t header = 0;



static _Bool debug;


static const char *decimal_point;
static int decimal_point_length;


static _Bool dev_debug = 0;


static inline int
default_scale_base (enum scale_type scale)
{
  switch (scale)
    {
    case scale_IEC:
    case scale_IEC_I:
      return 1024;

    case scale_none:
    case scale_auto:
    case scale_SI:
    default:
      return 1000;
    }
}

static inline int
valid_suffix (const char suf)
{
  static const char *valid_suffixes = "KMGTPEZY";
  return (strchr (valid_suffixes, suf) != ((void*)0));
}

static inline int
suffix_power (const char suf)
{
  switch (suf)
    {
    case 'K':
      return 1;

    case 'M':
      return 2;

    case 'G':
      return 3;

    case 'T':
      return 4;

    case 'P':
      return 5;

    case 'E':
      return 6;

    case 'Z':
      return 7;

    case 'Y':
      return 8;

    default:
      return 0;
    }
}

static inline const char *
suffix_power_char (unsigned int power)
{
  switch (power)
    {
    case 0:
      return "";

    case 1:
      return "K";

    case 2:
      return "M";

    case 3:
      return "G";

    case 4:
      return "T";

    case 5:
      return "P";

    case 6:
      return "E";

    case 7:
      return "Z";

    case 8:
      return "Y";

    default:
      return "(error)";
    }
}


static long double
powerld (long double base, unsigned int x)
{
  long double result = base;
  if (x == 0)
    return 1;




  while (--x)
    result *= base;
  return result;
}


static inline long double
absld (long double val)
{
  return val < 0 ? -val : val;
}





static long double
expld (long double val, unsigned int base, unsigned int *x)
{
  unsigned int power = 0;

  if (val >= -1.18973149535723176502e+4932L && val <= 1.18973149535723176502e+4932L)
    {
      while (absld (val) >= base)
        {
          ++power;
          val /= base;
        }
    }
  if (x)
    *x = power;
  return val;
}



static inline intmax_t
simple_round_ceiling (long double val)
{
  intmax_t intval = val;
  if (intval < val)
    intval++;
  return intval;
}



static inline intmax_t
simple_round_floor (long double val)
{
  return -simple_round_ceiling (-val);
}



static inline intmax_t
simple_round_from_zero (long double val)
{
  return val < 0 ? simple_round_floor (val) : simple_round_ceiling (val);
}



static inline intmax_t
simple_round_to_zero (long double val)
{
  return val;
}



static inline intmax_t
simple_round_nearest (long double val)
{
  return val < 0 ? val - 0.5 : val + 0.5;
}

static inline long double __attribute__ ((__const__))
simple_round (long double val, enum round_type t)
{
  intmax_t rval;
  intmax_t intmax_mul = val / (9223372036854775807L);
  val -= (long double) (9223372036854775807L) * intmax_mul;

  switch (t)
    {
    case round_ceiling:
      rval = simple_round_ceiling (val);
      break;

    case round_floor:
      rval = simple_round_floor (val);
      break;

    case round_from_zero:
      rval = simple_round_from_zero (val);
      break;

    case round_to_zero:
      rval = simple_round_to_zero (val);
      break;

    case round_nearest:
      rval = simple_round_nearest (val);
      break;

    default:

      return 0;
    }

  return (long double) (9223372036854775807L) * intmax_mul + rval;
}

enum simple_strtod_error
{
  SSE_OK = 0,
  SSE_OK_PRECISION_LOSS,
  SSE_OVERFLOW,
  SSE_INVALID_NUMBER,


  SSE_VALID_BUT_FORBIDDEN_SUFFIX,
  SSE_INVALID_SUFFIX,
  SSE_MISSING_I_SUFFIX
};
# 465 "numfmt.c"
static enum simple_strtod_error
simple_strtod_int (const char *input_str,
                   char **endptr, long double *value, _Bool *negative)
{
  enum simple_strtod_error e = SSE_OK;

  long double val = 0;
  unsigned int digits = 0;
  _Bool found_digit = 0;

  if (*input_str == '-')
    {
      input_str++;
      *negative = 1;
    }
  else
    *negative = 0;

  *endptr = (char *) input_str;
  while (*endptr && c_isdigit (**endptr))
    {
      int digit = (**endptr) - '0';

      found_digit = 1;

      if (val || digit)
        digits++;

      if (digits > MAX_UNSCALED_DIGITS)
        e = SSE_OK_PRECISION_LOSS;

      if (digits > MAX_ACCEPTABLE_DIGITS)
        return SSE_OVERFLOW;

      val *= 10;
      val += digit;

      ++(*endptr);
    }
  if (! found_digit
      && ! (strncmp (*endptr, decimal_point, decimal_point_length) == 0))
    return SSE_INVALID_NUMBER;
  if (*negative)
    val = -val;

  if (value)
    *value = val;

  return e;
}
# 530 "numfmt.c"
static enum simple_strtod_error
simple_strtod_float (const char *input_str,
                     char **endptr,
                     long double *value,
                     size_t *precision)
{
  _Bool negative;
  enum simple_strtod_error e = SSE_OK;

  if (precision)
    *precision = 0;


  e = simple_strtod_int (input_str, endptr, value, &negative);
  if (e != SSE_OK && e != SSE_OK_PRECISION_LOSS)
    return e;


  if ((strncmp (*endptr, decimal_point, decimal_point_length) == 0))
    {
      char *ptr2;
      long double val_frac = 0;
      _Bool neg_frac;

      (*endptr) += decimal_point_length;
      enum simple_strtod_error e2 =
        simple_strtod_int (*endptr, &ptr2, &val_frac, &neg_frac);
      if (e2 != SSE_OK && e2 != SSE_OK_PRECISION_LOSS)
        return e2;
      if (e2 == SSE_OK_PRECISION_LOSS)
        e = e2;
      if (neg_frac)
        return SSE_INVALID_NUMBER;


      size_t exponent = ptr2 - *endptr;

      val_frac = ((long double) val_frac) / powerld (10, exponent);



      if (value)
        {
          if (negative)
            *value -= val_frac;
          else
            *value += val_frac;
        }

      if (precision)
        *precision = exponent;

      *endptr = ptr2;
    }
  return e;
}
# 606 "numfmt.c"
static enum simple_strtod_error
simple_strtod_human (const char *input_str,
                     char **endptr, long double *value, size_t *precision,
                     enum scale_type allowed_scaling)
{
  int power = 0;

  int scale_base = default_scale_base (allowed_scaling);

  do { if (dev_debug) fprintf (stderr, "simple_strtod_human:\n  input string: %s\n" "  locale decimal-point: %s\n" "  MAX_UNSCALED_DIGITS: %d\n", quote_n (0, input_str), quote_n (1, decimal_point), MAX_UNSCALED_DIGITS); } while (0);






  enum simple_strtod_error e =
    simple_strtod_float (input_str, endptr, value, precision);
  if (e != SSE_OK && e != SSE_OK_PRECISION_LOSS)
    return e;

  do { if (dev_debug) fprintf (stderr, "  parsed numeric value: %Lf\n" "  input precision = %d\n", *value, (int)*precision); } while (0);


  if (**endptr != '\0')
    {



      while (((*__ctype_b_loc ())[(int) ((to_uchar (**endptr)))] & (unsigned short int) _ISblank))
        (*endptr)++;

      if (!valid_suffix (**endptr))
        return SSE_INVALID_SUFFIX;

      if (allowed_scaling == scale_none)
        return SSE_VALID_BUT_FORBIDDEN_SUFFIX;

      power = suffix_power (**endptr);
      (*endptr)++;

      if (allowed_scaling == scale_auto && **endptr == 'i')
        {


          scale_base = 1024;
          (*endptr)++;
          do { if (dev_debug) fprintf (stderr, "  Auto-scaling, found 'i', switching to base %d\n", scale_base); } while (0);

        }

      *precision = 0;
    }

  if (allowed_scaling == scale_IEC_I)
    {
      if (**endptr == 'i')
        (*endptr)++;
      else
        return SSE_MISSING_I_SUFFIX;
    }

  long double multiplier = powerld (scale_base, power);

  do { if (dev_debug) fprintf (stderr, "  suffix power=%d^%d = %Lf\n", scale_base, power, multiplier); } while (0);


  (*value) = (*value) * multiplier;

  do { if (dev_debug) fprintf (stderr, "  returning value: %Lf (%LG)\n", *value, *value); } while (0);

  return e;
}


static void
simple_strtod_fatal (enum simple_strtod_error err, char const *input_str)
{
  char const *msgid = ((void*)0);

  switch (err)
    {
    case SSE_OK_PRECISION_LOSS:
    case SSE_OK:

      abort ();

    case SSE_OVERFLOW:
      msgid = "value too large to be converted: %s";
      break;

    case SSE_INVALID_NUMBER:
      msgid = "invalid number: %s";
      break;

    case SSE_VALID_BUT_FORBIDDEN_SUFFIX:
      msgid = "rejecting suffix in input: %s (consider using --from)";
      break;

    case SSE_INVALID_SUFFIX:
      msgid = "invalid suffix in input: %s";
      break;

    case SSE_MISSING_I_SUFFIX:
      msgid = "missing 'i' suffix in input: %s (e.g Ki/Mi/Gi)";
      break;

    }

  if (inval_style != inval_ignore)
    error (conv_exit_code, 0, gettext (msgid), quote (input_str));
}


static void
double_to_human (long double val, int precision,
                 char *buf, size_t buf_size,
                 enum scale_type scale, int group, enum round_type round)
{
  int num_size;
  char fmt[64];
  _Static_assert (sizeof (fmt) > (((((((sizeof (zero_padding_width) * 8) - (! ((__typeof__ (zero_padding_width)) 0 < (__typeof__ (zero_padding_width)) -1))) * 146 + 484) / 485) + (! ((__typeof__ (zero_padding_width)) 0 < (__typeof__ (zero_padding_width)) -1))) + 1) + ((((((sizeof (precision) * 8) - (! ((__typeof__ (precision)) 0 < (__typeof__ (precision)) -1))) * 146 + 484) / 485) + (! ((__typeof__ (precision)) 0 < (__typeof__ (precision)) -1))) + 1) + 10 ), "verify (" "sizeof (fmt) > (INT_BUFSIZE_BOUND (zero_padding_width) + INT_BUFSIZE_BOUND (precision) + 10 )" ")");



  char *pfmt = fmt;
  *pfmt++ = '%';

  if (group)
    *pfmt++ = '\'';

  if (zero_padding_width)
    pfmt += snprintf (pfmt, sizeof (fmt) - 2, "0%ld", zero_padding_width);

  do { if (dev_debug) fprintf (stderr, "double_to_human:\n"); } while (0);

  if (scale == scale_none)
    {
      val *= powerld (10, precision);
      val = simple_round (val, round);
      val /= powerld (10, precision);

      do { if (dev_debug) fprintf (stderr, (group) ? "  no scaling, returning (grouped) value: %'.*Lf\n" : "  no scaling, returning value: %.*Lf\n", precision, val); } while (0);



      stpcpy (pfmt, ".*Lf");

      num_size = snprintf (buf, buf_size, fmt, precision, val);
      if (num_size < 0 || num_size >= (int) buf_size)
        ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"failed to prepare value '%Lf' for printing\"), val), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("failed to prepare value '%Lf' for printing"), val), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("failed to prepare value '%Lf' for printing"), val), ((0) ? (void) 0 : __builtin_unreachable ()))));

      return;
    }


  double scale_base = default_scale_base (scale);


  unsigned int power = 0;
  val = expld (val, scale_base, &power);
  do { if (dev_debug) fprintf (stderr, "  scaled value to %Lf * %0.f ^ %u\n", val, scale_base, power); } while (0);


  unsigned int power_adjust = 0;
  if (user_precision != -1)
    power_adjust = (((power * 3)<(user_precision))?(power * 3):(user_precision));
  else if (absld (val) < 10)
    {


      power_adjust = 1;
    }

  val *= powerld (10, power_adjust);
  val = simple_round (val, round);
  val /= powerld (10, power_adjust);




  if (absld (val) >= scale_base)
    {
      val /= scale_base;
      power++;
    }



  int show_decimal_point = (val != 0) && (absld (val) < 10) && (power > 0);


  do { if (dev_debug) fprintf (stderr, "  after rounding, value=%Lf * %0.f ^ %u\n", val, scale_base, power); } while (0);

  stpcpy (pfmt, ".*Lf%s");

  int prec = user_precision == -1 ? show_decimal_point : user_precision;


  num_size = snprintf (buf, buf_size - 1, fmt, prec, val,
                       suffix_power_char (power));
  if (num_size < 0 || num_size >= (int) buf_size - 1)
    ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"failed to prepare value '%Lf' for printing\"), val), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("failed to prepare value '%Lf' for printing"), val), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("failed to prepare value '%Lf' for printing"), val), ((0) ? (void) 0 : __builtin_unreachable ()))));


  if (scale == scale_IEC_I && power > 0)
    strncat (buf, "i", buf_size - num_size - 1);

  do { if (dev_debug) fprintf (stderr, "  returning value: %s\n", quote (buf)); } while (0);

  return;
}





static uintmax_t
unit_to_umax (const char *n_string)
{
  strtol_error s_err;
  const char *c_string = n_string;
  char *t_string = ((void*)0);
  size_t n_len = strlen (n_string);
  char *end = ((void*)0);
  uintmax_t n;
  const char *suffixes = "KMGTPEZY";


  if (n_len && ! c_isdigit (n_string[n_len - 1]))
    {
      t_string = xmalloc (n_len + 2);
      end = t_string + n_len - 1;
      memcpy (t_string, n_string, n_len);

      if (*end == 'i' && 2 <= n_len && ! c_isdigit (*(end - 1)))
        *end = '\0';
      else
        {
          *++end = 'B';
          *++end = '\0';
          suffixes = "KMGTPEZY0";
        }

      c_string = t_string;
    }

  s_err = xstrtoumax (c_string, &end, 10, &n, suffixes);

  if (s_err != LONGINT_OK || *end || n == 0)
    {
      free (t_string);
      ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"invalid unit size: %s\"), quote (n_string)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("invalid unit size: %s"), quote (n_string)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("invalid unit size: %s"), quote (n_string)), ((0) ? (void) 0 : __builtin_unreachable ()))));
    }

  free (t_string);

  return n;
}


static void
setup_padding_buffer (size_t min_size)
{
  if (padding_buffer_size > min_size)
    return;

  padding_buffer_size = min_size + 1;
  padding_buffer = xrealloc (padding_buffer, padding_buffer_size);
}

void
usage (int status)
{
  if (status != 0)
    do { fprintf (stderr, gettext ("Try '%s --help' for more information.\n"), program_name); } while (0);
  else
    {
      printf (gettext ("Usage: %s [OPTION]... [NUMBER]...\n"), program_name);


      fputs_unlocked (gettext ("Reformat NUMBER(s), or the numbers from standard input if none are specified.\n"),stdout);


      emit_mandatory_arg_note ();
      fputs_unlocked (gettext ("      --debug          print warnings about invalid input\n"),stdout);


      fputs_unlocked (gettext ("  -d, --delimiter=X    use X instead of whitespace for field delimiter\n"),stdout);


      fputs_unlocked (gettext ("      --field=FIELDS   replace the numbers in these input fields (default=1)\n                         see FIELDS below\n"),stdout);



      fputs_unlocked (gettext ("      --format=FORMAT  use printf style floating-point FORMAT;\n                         see FORMAT below for details\n"),stdout);



      fputs_unlocked (gettext ("      --from=UNIT      auto-scale input numbers to UNITs; default is 'none';\n                         see UNIT below\n"),stdout);



      fputs_unlocked (gettext ("      --from-unit=N    specify the input unit size (instead of the default 1)\n"),stdout);


      fputs_unlocked (gettext ("      --grouping       use locale-defined grouping of digits, e.g. 1,000,000\n                         (which means it has no effect in the C/POSIX locale)\n"),stdout);



      fputs_unlocked (gettext ("      --header[=N]     print (without converting) the first N header lines;\n                         N defaults to 1 if not specified\n"),stdout);



      fputs_unlocked (gettext ("      --invalid=MODE   failure mode for invalid numbers: MODE can be:\n                         abort (default), fail, warn, ignore\n"),stdout);



      fputs_unlocked (gettext ("      --padding=N      pad the output to N characters; positive N will\n                         right-align; negative N will left-align;\n                         padding is ignored if the output is wider than N;\n                         the default is to automatically pad if a whitespace\n                         is found\n"),stdout);






      fputs_unlocked (gettext ("      --round=METHOD   use METHOD for rounding when scaling; METHOD can be:\n                         up, down, from-zero (default), towards-zero, nearest\n"),stdout);



      fputs_unlocked (gettext ("      --suffix=SUFFIX  add SUFFIX to output numbers, and accept optional\n                         SUFFIX in input numbers\n"),stdout);



      fputs_unlocked (gettext ("      --to=UNIT        auto-scale output numbers to UNITs; see UNIT below\n"),stdout);


      fputs_unlocked (gettext ("      --to-unit=N      the output unit size (instead of the default 1)\n"),stdout);


      fputs_unlocked (gettext ("  -z, --zero-terminated    line delimiter is NUL, not newline\n"),stdout);


      fputs_unlocked (gettext ("      --help     display this help and exit\n"),stdout);
      fputs_unlocked (gettext ("      --version  output version information and exit\n"),stdout);

      fputs_unlocked (gettext ("\nUNIT options:\n"),stdout);


      fputs_unlocked (gettext ("  none       no auto-scaling is done; suffixes will trigger an error\n"),stdout);


      fputs_unlocked (gettext ("  auto       accept optional single/two letter suffix:\n               1K = 1000,\n               1Ki = 1024,\n               1M = 1000000,\n               1Mi = 1048576,\n"),stdout);





      fputs_unlocked (gettext ("  si         accept optional single letter suffix:\n               1K = 1000,\n               1M = 1000000,\n               ...\n"),stdout);




      fputs_unlocked (gettext ("  iec        accept optional single letter suffix:\n               1K = 1024,\n               1M = 1048576,\n               ...\n"),stdout);




      fputs_unlocked (gettext ("  iec-i      accept optional two-letter suffix:\n               1Ki = 1024,\n               1Mi = 1048576,\n               ...\n"),stdout);





      fputs_unlocked (gettext ("\nFIELDS supports cut(1) style field ranges:\n  N    N'th field, counted from 1\n  N-   from N'th field, to end of line\n  N-M  from N'th to M'th field (inclusive)\n  -M   from first to M'th field (inclusive)\n  -    all fields\nMultiple fields/ranges can be separated with commas\n"),stdout);
# 989 "numfmt.c"
      fputs_unlocked (gettext ("\nFORMAT must be suitable for printing one floating-point argument '%f'.\nOptional quote (%'f) will enable --grouping (if supported by current locale).\nOptional width value (%10f) will pad output. Optional zero (%010f) width\nwill zero pad the number. Optional negative values (%-10f) will left align.\nOptional precision (%.1f) will override the input determined precision.\n"),stdout);







      printf (gettext ("\nExit status is 0 if all input numbers were successfully converted.\nBy default, %s will stop at the first conversion error with exit status 2.\nWith --invalid='fail' a warning is printed for each conversion error\nand the exit status is 2.  With --invalid='warn' each conversion error is\ndiagnosed, but the exit status is 0.  With --invalid='ignore' conversion\nerrors are not diagnosed and the exit status is 0.\n"), program_name);
# 1006 "numfmt.c"
      printf (gettext ("\nExamples:\n  $ %s --to=si 1000\n            -> \"1.0K\"\n  $ %s --to=iec 2048\n           -> \"2.0K\"\n  $ %s --to=iec-i 4096\n           -> \"4.0Ki\"\n  $ echo 1K | %s --from=si\n           -> \"1000\"\n  $ echo 1K | %s --from=iec\n           -> \"1024\"\n  $ df -B1 | %s --header --field 2-4 --to=si\n  $ ls -l  | %s --header --field 5 --to=iec\n  $ ls -lh | %s --header --field 5 --from=iec --padding=10\n  $ ls -lh | %s --header --field 5 --from=iec --format %%10f\n"),
# 1022 "numfmt.c"
              program_name, program_name, program_name,
              program_name, program_name, program_name,
              program_name, program_name, program_name);
      emit_ancillary_info ("numfmt");
    }
  exit (status);
}
# 1045 "numfmt.c"
static void
parse_format_string (char const *fmt)
{
  size_t i;
  size_t prefix_len = 0;
  size_t suffix_pos;
  long int pad = 0;
  char *endptr = ((void*)0);
  _Bool zero_padding = 0;

  for (i = 0; !(fmt[i] == '%' && fmt[i + 1] != '%'); i += (fmt[i] == '%') + 1)
    {
      if (!fmt[i])
        ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"format %s has no %% directive\"), quote (fmt)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("format %s has no %% directive"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("format %s has no %% directive"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))));

      prefix_len++;
    }

  i++;
  while (1)
    {
      size_t skip = strspn (fmt + i, " ");
      i += skip;
      if (fmt[i] == '\'')
        {
          grouping = 1;
          i++;
        }
      else if (fmt[i] == '0')
        {
          zero_padding = 1;
          i++;
        }
      else if (! skip)
        break;
    }

  (*__errno_location ()) = 0;
  pad = strtol (fmt + i, &endptr, 10);
  if ((*__errno_location ()) == 34 || pad < -9223372036854775807L)
    ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"invalid format %s (width overflow)\"), quote (fmt)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("invalid format %s (width overflow)"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("invalid format %s (width overflow)"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))));


  if (endptr != (fmt + i) && pad != 0)
    {
      if (debug && padding_width && !(zero_padding && pad > 0))
        error (0, 0, gettext ("--format padding overriding --padding"));

      if (pad < 0)
        {
          padding_alignment = MBS_ALIGN_LEFT;
          padding_width = -pad;
        }
      else
        {
          if (zero_padding)
            zero_padding_width = pad;
          else
            padding_width = pad;
        }

    }
  i = endptr - fmt;

  if (fmt[i] == '\0')
    ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"format %s ends in %%\"), quote (fmt)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("format %s ends in %%"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("format %s ends in %%"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))));

  if (fmt[i] == '.')
    {
      i++;
      (*__errno_location ()) = 0;
      user_precision = strtol (fmt + i, &endptr, 10);
      if ((*__errno_location ()) == 34 || user_precision < 0 || (18446744073709551615UL) < user_precision
          || ((*__ctype_b_loc ())[(int) ((fmt[i]))] & (unsigned short int) _ISblank) || fmt[i] == '+')
        {





          ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"invalid precision in format %s\"), quote (fmt)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("invalid precision in format %s"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("invalid precision in format %s"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))));

        }
      i = endptr - fmt;
    }

  if (fmt[i] != 'f')
    ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"invalid format %s,\" \" directive must be %%[0]['][-][N][.][N]f\"), quote (fmt)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("invalid format %s," " directive must be %%[0]['][-][N][.][N]f"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("invalid format %s," " directive must be %%[0]['][-][N][.][N]f"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))));


  i++;
  suffix_pos = i;

  for (; fmt[i] != '\0'; i += (fmt[i] == '%') + 1)
    if (fmt[i] == '%' && fmt[i + 1] != '%')
      ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"format %s has too many %% directives\"), quote (fmt)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("format %s has too many %% directives"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("format %s has too many %% directives"), quote (fmt)), ((0) ? (void) 0 : __builtin_unreachable ()))));


  if (prefix_len)
    format_str_prefix = xstrndup (fmt, prefix_len);
  if (fmt[suffix_pos] != '\0')
    format_str_suffix = xstrdup (fmt + suffix_pos);

  do { if (dev_debug) fprintf (stderr, "format String:\n  input: %s\n  grouping: %s\n" "  padding width: %ld\n  alignment: %s\n" "  prefix: %s\n  suffix: %s\n", quote_n (0, fmt), (grouping) ? "yes" : "no", padding_width, (padding_alignment == MBS_ALIGN_LEFT) ? "Left" : "Right", quote_n (1, format_str_prefix ? format_str_prefix : ""), quote_n (2, format_str_suffix ? format_str_suffix : "")); } while (0);







}
# 1166 "numfmt.c"
static enum simple_strtod_error
parse_human_number (const char *str, long double *value,
                    size_t *precision)
{
  char *ptr = ((void*)0);

  enum simple_strtod_error e =
    simple_strtod_human (str, &ptr, value, precision, scale_from);
  if (e != SSE_OK && e != SSE_OK_PRECISION_LOSS)
    {
      simple_strtod_fatal (e, str);
      return e;
    }

  if (ptr && *ptr != '\0')
    {
      if (inval_style != inval_ignore)
        error (conv_exit_code, 0, gettext ("invalid suffix in input %s: %s"),
               quote_n (0, str), quote_n (1, ptr));
      e = SSE_INVALID_SUFFIX;
    }
  return e;
}




static int
prepare_padded_number (const long double val, size_t precision)
{

  char buf[128];

  size_t precision_used = user_precision == -1 ? precision : user_precision;


  unsigned int x;
  expld (val, 10, &x);

  if (scale_to == scale_none
      && x + precision_used > MAX_UNSCALED_DIGITS)
    {
      if (inval_style != inval_ignore)
        {
          if (precision_used)
            error (conv_exit_code, 0,
                   gettext ("value/precision too large to be printed: '%Lg/%""l" "u""'" " (consider using --to)"), val, (uintmax_t)precision_used);

          else
            error (conv_exit_code, 0,
                   gettext ("value too large to be printed: '%Lg'" " (consider using --to)"), val);

        }
      return 0;
    }

  if (x > MAX_ACCEPTABLE_DIGITS - 1)
    {
      if (inval_style != inval_ignore)
        error (conv_exit_code, 0, gettext ("value too large to be printed: '%Lg'" " (cannot handle values > 999Y)"), val);

      return 0;
    }

  double_to_human (val, precision_used, buf, sizeof (buf),
                   scale_to, grouping, round_style);
  if (suffix)
    strncat (buf, suffix, sizeof (buf) - strlen (buf) -1);

  do { if (dev_debug) fprintf (stderr, "formatting output:\n  value: %Lf\n  humanized: %s\n", val, quote (buf)); } while (0);


  if (padding_width && strlen (buf) < padding_width)
    {
      size_t w = padding_width;
      mbsalign (buf, padding_buffer, padding_buffer_size, &w,
                padding_alignment, MBA_UNIBYTE_ONLY);

      do { if (dev_debug) fprintf (stderr, "  After padding: %s\n", quote (padding_buffer)); } while (0);
    }
  else
    {
      setup_padding_buffer (strlen (buf) + 1);
      strcpy (padding_buffer, buf);
    }

  return 1;
}

static void
print_padded_number (void)
{
  if (format_str_prefix)
    fputs_unlocked (format_str_prefix,stdout);

  fputs_unlocked (padding_buffer,stdout);

  if (format_str_suffix)
    fputs_unlocked (format_str_suffix,stdout);
}



static int
process_suffixed_number (char *text, long double *result,
                         size_t *precision, long int field)
{
  if (suffix && strlen (text) > strlen (suffix))
    {
      char *possible_suffix = text + strlen (text) - strlen (suffix);

      if ((strcmp (suffix, possible_suffix) == 0))
        {

          *possible_suffix = '\0';
          do { if (dev_debug) fprintf (stderr, "trimming suffix %s\n", quote (suffix)); } while (0);
        }
      else
        do { if (dev_debug) fprintf (stderr, "no valid suffix found\n"); } while (0);
    }


  char *p = text;
  while (*p && ((*__ctype_b_loc ())[(int) ((to_uchar (*p)))] & (unsigned short int) _ISblank))
    ++p;
  const unsigned int skip_count = text - p;


  if (auto_padding)
    {
      if (skip_count > 0 || field > 1)
        {
          padding_width = strlen (text);
          setup_padding_buffer (padding_width);
        }
      else
        {
          padding_width = 0;
        }
     do { if (dev_debug) fprintf (stderr, "setting Auto-Padding to %ld characters\n", padding_width); } while (0);
    }

  long double val = 0;
  enum simple_strtod_error e = parse_human_number (p, &val, precision);
  if (e == SSE_OK_PRECISION_LOSS && debug)
    error (0, 0, gettext ("large input value %s: possible precision loss"),
           quote (p));

  if (from_unit_size != 1 || to_unit_size != 1)
    val = (val * from_unit_size) / to_unit_size;

  *result = val;

  return (e == SSE_OK || e == SSE_OK_PRECISION_LOSS);
}



static char*
next_field (char **line)
{
  char *field_start = *line;
  char *field_end = field_start;

  if (delimiter != DELIMITER_DEFAULT)
    {
      if (*field_start != delimiter)
        {
          while (*field_end && *field_end != delimiter)
            ++field_end;
        }

    }
  else
    {

      while (*field_end && field_sep (*field_end))
        ++field_end;

      while (*field_end && ! field_sep (*field_end))
        ++field_end;
    }

  *line = field_end;
  return field_start;
}

static _Bool __attribute__ ((__pure__))
include_field (uintmax_t field)
{
  struct field_range_pair *p = frp;
  if (!p)
    return field == 1;

  while (p->lo != (18446744073709551615UL))
    {
      if (p->lo <= field && p->hi >= field)
        return 1;
      ++p;
    }
  return 0;
}



static _Bool
process_field (char *text, uintmax_t field)
{
  long double val = 0;
  size_t precision = 0;
  _Bool valid_number = 1;

  if (include_field (field))
    {
      valid_number =
        process_suffixed_number (text, &val, &precision, field);

      if (valid_number)
        valid_number = prepare_padded_number (val, precision);

      if (valid_number)
        print_padded_number ();
      else
        fputs_unlocked (text,stdout);
    }
  else
    fputs_unlocked (text,stdout);

  return valid_number;
}



static int
process_line (char *line, _Bool newline)
{
  char *next;
  uintmax_t field = 0;
  _Bool valid_number = 1;

  while (1) {
    ++field;
    next = next_field (&line);

    if (*line != '\0')
      {

        *line = '\0';

        if (! process_field (next, field))
          valid_number = 0;

        fputc_unlocked ((delimiter == DELIMITER_DEFAULT) ? ' ' : delimiter,stdout);

        ++line;
      }
    else
      {

        if (! process_field (next, field))
          valid_number = 0;

        break;
      }
  }

  if (newline)
    putchar_unlocked (line_delim);

  return valid_number;
}

int
main (int argc, char **argv)
{
  int valid_numbers = 1;
  _Bool locale_ok;

                                ;
  set_program_name (argv[0]);
  locale_ok = !!setlocale (6, "");
  bindtextdomain ("coreutils", "/usr/local/share/locale");
  textdomain ("coreutils");






  decimal_point = nl_langinfo (RADIXCHAR);
  if (decimal_point == ((void*)0) || strlen (decimal_point) == 0)
    decimal_point = ".";
  decimal_point_length = strlen (decimal_point);

  atexit (close_stdout);

  while (1)
    {
      int c = getopt_long (argc, argv, "d:z", longopts, ((void*)0));

      if (c == -1)
        break;

      switch (c)
        {
        case FROM_OPTION:
          scale_from = ((scale_from_types) [__xargmatch_internal ("--from", optarg, scale_from_args, (void const *) (scale_from_types), sizeof *(scale_from_types), argmatch_die)]);

          break;

        case FROM_UNIT_OPTION:
          from_unit_size = unit_to_umax (optarg);
          break;

        case TO_OPTION:
          scale_to =
            ((scale_to_types) [__xargmatch_internal ("--to", optarg, scale_to_args, (void const *) (scale_to_types), sizeof *(scale_to_types), argmatch_die)]);
          break;

        case TO_UNIT_OPTION:
          to_unit_size = unit_to_umax (optarg);
          break;

        case ROUND_OPTION:
          round_style = ((round_types) [__xargmatch_internal ("--round", optarg, round_args, (void const *) (round_types), sizeof *(round_types), argmatch_die)]);
          break;

        case GROUPING_OPTION:
          grouping = 1;
          break;

        case PADDING_OPTION:
          if (xstrtol (optarg, ((void*)0), 10, &padding_width, "") != LONGINT_OK
              || padding_width == 0)
            ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"invalid padding value %s\"), quote (optarg)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("invalid padding value %s"), quote (optarg)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("invalid padding value %s"), quote (optarg)), ((0) ? (void) 0 : __builtin_unreachable ()))));

          if (padding_width < 0)
            {
              padding_alignment = MBS_ALIGN_LEFT;
              padding_width = -padding_width;
            }


          break;

        case FIELD_OPTION:
          if (n_frp)
            ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"multiple field specifications\")), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("multiple field specifications")), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("multiple field specifications")), ((0) ? (void) 0 : __builtin_unreachable ()))));
          set_fields (optarg, SETFLD_ALLOW_DASH);
          break;

        case 'd':

          if (optarg[0] != '\0' && optarg[1] != '\0')
            ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"the delimiter must be a single character\")), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("the delimiter must be a single character")), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("the delimiter must be a single character")), ((0) ? (void) 0 : __builtin_unreachable ()))));

          delimiter = optarg[0];
          break;

        case 'z':
          line_delim = '\0';
          break;

        case SUFFIX_OPTION:
          suffix = optarg;
          break;

        case DEBUG_OPTION:
          debug = 1;
          break;

        case DEV_DEBUG_OPTION:
          dev_debug = 1;
          debug = 1;
          break;

        case HEADER_OPTION:
          if (optarg)
            {
              if (xstrtoumax (optarg, ((void*)0), 10, &header, "") != LONGINT_OK
                  || header == 0)
                ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"invalid header value %s\"), quote (optarg)), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("invalid header value %s"), quote (optarg)), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("invalid header value %s"), quote (optarg)), ((0) ? (void) 0 : __builtin_unreachable ()))));

            }
          else
            {
              header = 1;
            }
          break;

        case FORMAT_OPTION:
          format_str = optarg;
          break;

        case INVALID_OPTION:
          inval_style = ((inval_types) [__xargmatch_internal ("--invalid", optarg, inval_args, (void const *) (inval_types), sizeof *(inval_types), argmatch_die)]);

          break;

          case GETOPT_HELP_CHAR: usage (0); break;;
          case GETOPT_VERSION_CHAR: version_etc (stdout, "numfmt", "GNU coreutils", Version, ("Assaf Gordon"), (char *) ((void*)0)); exit (0); break;;

        default:
          usage (1);
        }
    }

  if (format_str != ((void*)0) && grouping)
    ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"--grouping cannot be combined with --format\")), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("--grouping cannot be combined with --format")), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("--grouping cannot be combined with --format")), ((0) ? (void) 0 : __builtin_unreachable ()))));

  if (debug && ! locale_ok)
    error (0, 0, gettext ("failed to set locale"));


  if (debug && scale_from == scale_none && scale_to == scale_none
      && !grouping && (padding_width == 0) && (format_str == ((void*)0)))
    error (0, 0, gettext ("no conversion option specified"));

  if (format_str)
    parse_format_string (format_str);

  if (grouping)
    {
      if (scale_to != scale_none)
        ((!!sizeof (struct { _Static_assert (1, "verify_expr (" "1" ", " "(error (1, 0, gettext (\"grouping cannot be combined with --to\")), assume (false))" ")"); int _gl_dummy; })) ? ((error (1, 0, gettext ("grouping cannot be combined with --to")), ((0) ? (void) 0 : __builtin_unreachable ()))) : ((error (1, 0, gettext ("grouping cannot be combined with --to")), ((0) ? (void) 0 : __builtin_unreachable ()))));
      if (debug && (strlen (nl_langinfo (THOUSEP)) == 0))
        error (0, 0, gettext ("grouping has no effect in this locale"));
    }


  setup_padding_buffer (padding_width);
  auto_padding = (padding_width == 0 && delimiter == DELIMITER_DEFAULT);

  if (inval_style != inval_abort)
    conv_exit_code = 0;

  if (argc > optind)
    {
      if (debug && header)
        error (0, 0, gettext ("--header ignored with command-line input"));

      for (; optind < argc; optind++)
        valid_numbers &= process_line (argv[optind], 1);
    }
  else
    {
      char *line = ((void*)0);
      size_t line_allocated = 0;
      ssize_t len;

      while (header-- && getdelim (&line, &line_allocated,
                                   line_delim, stdin) > 0)
        fputs_unlocked (line,stdout);

      while ((len = getdelim (&line, &line_allocated,
                              line_delim, stdin)) > 0)
        {
          _Bool newline = line[len - 1] == line_delim;
          if (newline)
            line[len - 1] = '\0';
          valid_numbers &= process_line (line, newline);
        }

                           ;

      if (ferror_unlocked (stdin))
        error (0, (*__errno_location ()), gettext ("error reading input"));
    }
# 1642 "numfmt.c"
  if (debug && !valid_numbers)
    error (0, 0, gettext ("failed to convert some of the input numbers"));

  int exit_status = 0;
  if (!valid_numbers
      && inval_style != inval_warn && inval_style != inval_ignore)
    exit_status = EXIT_CONVERSION_WARNINGS;

  return exit_status;
}
