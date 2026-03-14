int main(int argc, char **argv) {
  if (argc > 1) goto caseone;
  switch(argc) {
    case 6:
      argc = 6;
    default:
      argc = 30;
caseone:
    case 1:
      argc = 1;
    case 2:
      return 2;
    case 3:
      argc = 3;
      break;
    case 4:
      argc = 4;
  }
  return 10;
}
