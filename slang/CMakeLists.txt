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

# Enable testing
enable_testing()

# Find lit
find_program(LIT_EXECUTABLE
    NAMES lit.py lit
    PATHS
        ${LLVM_TOOLS_BINARY_DIR}
        ${LLVM_TOOLS_BINARY_DIR}/../share/llvm
        /usr/lib/llvm-*/share/llvm
        /usr/lib/llvm-*/build/utils/lit
        /usr/local/lib/llvm*/share/llvm
        /opt/llvm*/share/llvm
)

if(LIT_EXECUTABLE)
    # Add test targets
    add_custom_target(check-slang
        COMMAND ${LIT_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test
        DEPENDS slang
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running slang tests"
    )
    
    # Add individual test categories
    add_custom_target(test-basic
        COMMAND ${LIT_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test/basic
        DEPENDS slang
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running basic tests"
    )
    
    add_custom_target(test-expressions
        COMMAND ${LIT_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test/expressions
        DEPENDS slang
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running expression tests"
    )
    
    add_custom_target(test-functions
        COMMAND ${LIT_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test/functions
        DEPENDS slang
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running function tests"
    )
    
    add_custom_target(test-proto
        COMMAND ${LIT_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test/proto
        DEPENDS slang
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Running proto tests"
    )
else()
    message(WARNING "lit not found, skipping test setup")
endif() 