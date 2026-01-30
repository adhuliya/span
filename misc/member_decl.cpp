// A simple test to check if the order of member declarations in a class
// affects the compilation.

// compile with: clang -c member_decl.cpp
class MyClass {
  public:
    void functionA() {
      // functionA can call functionB, even though 
      // functionB is declared later in the class definition.
      functionB(); 
    }
    
  void functionB() {
    // functionB can call functionA.
    functionA();
  }
};

int main() {
  return 0;
}