.PHONY: all clean span span-rel span-dbg span-dev test test-span test-slang vtest vet fmt \
        proto docker tidy gen gen-go gen-proto slang slang-rel slang-dbg clean-slang \
        clean-span clean-proto clean-all

GO=go
PROTOC=protoc
DOCKER=docker
GOTAGS=debug
GOARGS=
VERBOSE=
CMAKE_CC=-DCMAKE_C_COMPILER=/usr/lib/llvm-19/bin/clang
CMAKE_CXX=-DCMAKE_CXX_COMPILER=/usr/lib/llvm-19/bin/clang++
CMAKE_CLANG=$(CMAKE_CC) $(CMAKE_CXX)

all: tidy vet fmt slang span

help:
	@echo "Usage: make <target> [GOTAGS=comma,separated,tags,without,spaces] [GOARGS='additional go build/test/run args']..."
	@echo ""
	@echo "Optional variables:"
	@echo "  GOTAGS    Set Go build tags. E.g., GOTAGS=debug"
	@echo "  GOARGS    Additional arguments to pass to 'go build', 'go test', etc. E.g., GOARGS='-v'"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

span: span-rel

span-rel: ## Build the span binary -- use this for release builds
	cd span && $(GO) build -tags release $(GOARGS) -o bin/span ./cmd/span

span-dev: gen ## Auto-generated code and build span (non-release)
	cd span && $(GO) build -tags "$(GOTAGS)" $(GOARGS) -o bin/span ./cmd/span

span-dbg: gen ## Auto-generated code and build span (debug)
	# -N disables optimization and -l disables inlining. This helps with debugging.
	cd span && $(GO) build -tags "$(GOTAGS)" $(GOARGS) -gcflags="all=-N -l" -o bin/span ./cmd/span

test: test-span test-slang

test-span: vet tidy fmt ## Run span tests
	echo "\nRunning span tests..."
	cd span && $(GO) test -run TestIDGenerator ./...
	cd span/test && python3 run-tests.py $(VERBOSE)

test-slang: ## Run slang tests
	echo "\nRunning slang tests..."
	cd slang/test && python3 run-tests.py $(VERBOSE)

# Verbose tests
vtest: ## Run span tests with verbose output
	cd span && $(GO) test ./... -test.v

vet: ## Run span vet checks
	cd span && $(GO) vet ./...

fmt: ## Run span fmt checks
	cd span && $(GO) fmt ./...

tidy: ## Run span tidy checks
	cd span && $(GO) mod tidy

gen-proto: ## Generate proto files
	$(PROTOC) --go_out=. --go_opt=paths=source_relative \
		span/pkg/spir/spir.proto
	$(PROTOC) --cpp_out=slang/src --proto_path=span/pkg/spir \
		span/pkg/spir/spir.proto
	$(PROTOC) --python_out=tools/spir_proto_to_text --proto_path=span/pkg/spir \
		span/pkg/spir/spir.proto

gen-go: ## Generate auto-generated code
	cd span && $(GO) generate ./...

gen: gen-go gen-proto ## Generate auto-generated code and proto files
	echo "Generating auto-generated code..."

slang: slang-rel

slang-rel: ## Release build of slang
	@# Detect if built/slang exists and is not a release binary, and if so, clean first
	@if [ -f slang/built/slang ]; then \
		if objdump -h slang/built/slang | grep -q ' \.debug_'; then \
			echo "Previous build appears to be a debug build (contains .debug_* sections). Cleaning..."; \
			rm -rf slang/built/; \
		fi; \
	fi
	mkdir -p slang/built
	cd slang/built && cmake $(CMAKE_CLANG) .. && make -j 4

slang-dbg: ## Debug build of slang
	@# Detect if built/slang exists and is not a debug binary, and if so, clean first
	@if [ -f slang/built/slang ]; then \
		if ! objdump -h slang/built/slang | grep -q ' \.debug_'; then \
			echo "Previous build is NOT a debug build (missing .debug_* sections). Cleaning..."; \
			rm -rf slang/built/; \
		fi; \
	fi
	mkdir -p slang/built
	cd slang/built && cmake $(CMAKE_CLANG) .. -DCMAKE_BUILD_TYPE=Debug && make -j 4

clean: clean-slang clean-span ## Clean up binaries
clean-all: clean clean-proto ## Clean up all binaries and proto files

clean-slang: ## Clean up slang binaries
	rm -rf slang/built/

clean-proto: ## Clean up proto files
	rm -f span/pkg/spir/*.pb.go
	rm -f slang/src/spir.pb.h
	rm -f slang/src/spir.pb.cc

clean-span: ## Clean up span binaries
	rm -rf span/bin

docker-build: ## Build the docker image
	cd docker && $(DOCKER) build -t span-dev .

docker-run: ## Run the docker container
	cd docker && $(DOCKER) run -it --rm -v $(pwd):/span span-dev

# Include API documentation targets
include span/Makefile.api

# Include test targets 
include span/Makefile.test
