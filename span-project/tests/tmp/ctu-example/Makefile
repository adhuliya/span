.DEFAULT: all
.PHONY: all

CC=cilly \
  --merge \
  --keepmerged \
  --noPrintLn \
  --gcc=clang

all: main.o foo.o
	$(CC) main.o foo.o;

main.o: main.c
	$(CC) -c main.c -o main.o;

foo.o: foo.c
	$(CC) -c foo.c -o foo.o;

clean:
	rm -rf *.o a.out;

