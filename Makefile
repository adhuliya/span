.PHONY: all clean build devbuild test vtest vet fmt proto docker tidy gen generate slang slang-dbg

GO=go
PROTOC=protoc
DOCKER=docker

all: tidy vet fmt build

build:
	cd span && $(GO) build -o bin/span ./cmd/span

# only dev builds generate the required files
devbuild: proto gen
	cd span && $(GO) build -o bin/span ./cmd/span

gen:
	cd span && $(GO) generate ./...

test:
	cd span && $(GO) test ./...
	cd slang && python3 run-tests.py --verbose

# Verbose tests
vtest:
	cd span && $(GO) test ./... -test.v

vet:
	cd span && $(GO) vet ./...

fmt:
	cd span && $(GO) fmt ./...

tidy:
	cd span && $(GO) mod tidy

proto:
	$(PROTOC) --go_out=. --go_opt=paths=source_relative \
		span/pkg/spir/spir.proto
	$(PROTOC) --cpp_out=slang/src --proto_path=span/pkg/spir \
		span/pkg/spir/spir.proto

slang:
	cd slang && mkdir -p built/rel && cd built/rel && cmake ../.. && make -j 4

slang-dbg:
	cd slang && mkdir -p built/dbg && cd built/dbg && cmake ../.. -DCMAKE_BUILD_TYPE=Debug && make -j 4

genall: gen proto
	echo "Generating auto-generated code..."

clean:
	rm -rf span/bin
	rm -f span/pkg/spir/*.pb.go
	rm -f slang/src/spir.pb.h
	rm -f slang/src/spir.pb.cc
	rm -rf slang/built/

docker-build:
	cd docker && $(DOCKER) build -t span-dev .

docker-run:
	cd docker && $(DOCKER) run -it --rm -v $(pwd):/span span-dev
