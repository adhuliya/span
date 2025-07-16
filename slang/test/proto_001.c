// g++ -std=c++17 -I. -o proto_001 proto_001.c spir.pb.cc `pkg-config --cflags --libs protobuf`
// RUN: true

#include <iostream>
#include "spir.pb.h"

int main() {
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    bitcode::Entity e;
    e.set_kind(bitcode::K_Ent::VAR_GLOBAL);
    e.set_id(12345);

    std::cout << "Kind: " << e.kind() << ", ID: " << e.id() << std::endl;

    google::protobuf::ShutdownProtobufLibrary();
    return 0;
}