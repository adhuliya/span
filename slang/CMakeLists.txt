cmake_minimum_required(VERSION 3.20)
project(slang)

find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)
find_package(Protobuf REQUIRED)

add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${CLANG_INCLUDE_DIRS})
include_directories(${Protobuf_INCLUDE_DIRS})

add_executable(slang
    src/main.cpp
    src/spir.pb.cc
    src/util.cpp
)

target_link_libraries(slang
    clang-cpp
    LLVM
    ${Protobuf_LIBRARIES}
) 