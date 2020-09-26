// REF: https://stackoverflow.com/questions/3455157/example-code-to-trigger-clangs-static-analyser
struct elem {
  struct elem *prev;
  struct elem *next;
};

#define ELEM_INITIALIZER(NAME) { .prev = &(NAME), .next = &(NAME), }

struct head {
  struct elem header;
};

#define HEAD_INITIALIZER(NAME) { .header = ELEM_INITIALIZER(NAME.header) }

int main(int argc, char ** argv) {
  // myhead is used in the macro but in effect it is unused. Clang checker reports this.
  struct head myhead = HEAD_INITIALIZER(myhead);
}
