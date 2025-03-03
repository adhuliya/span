cmake_minimum_required(VERSION 3.10)
project(slang)

find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)

add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${CLANG_INCLUDE_DIRS})

add_executable(slang
    src/main.cpp
)

target_link_libraries(slang
    clang-cpp
    LLVM
) 