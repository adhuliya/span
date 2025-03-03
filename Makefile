.PHONY: all clean build test vet fmt proto docker tidy

GO=go
PROTOC=protoc
DOCKER=docker

all: tidy vet fmt build

build: proto
	cd span && $(GO) build -o bin/span ./cmd/span

test:
	cd span && $(GO) test ./...

vet:
	cd span && $(GO) vet ./...

fmt:
	cd span && $(GO) fmt ./...

tidy:
	cd span && $(GO) mod tidy

proto:
	$(PROTOC) --go_out=. --go_opt=paths=source_relative \
		span/pkg/spir/spir.proto

clean:
	rm -rf bin/
	rm -f span/pkg/spir/*.pb.go

docker-build:
	cd docker && $(DOCKER) build -t span-dev .

docker-run:
	cd docker && $(DOCKER) run -it --rm -v $(pwd):/span span-dev
