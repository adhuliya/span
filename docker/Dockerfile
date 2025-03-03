FROM arm64v8/ubuntu:24.04

# Install Go
RUN apt-get update && apt-get install -y \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.24
RUN wget -O go.tgz https://go.dev/dl/go1.24.0.linux-arm64.tar.gz && \
    tar -C /usr/local -xzf go.tgz && \
    rm go.tgz

# Set Go environment variables
ENV GOROOT=/usr/local/go
ENV GOPATH=/go
ENV PATH=$GOPATH/bin:$GOROOT/bin:$PATH

# Create Go workspace directory
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"

# Install required packages
RUN apt-get update && apt-get install -y \
    binutils=2.42* \
    cmake=3.28.3* \
    clang-19 \
    llvm-19 \
    libclang-19-dev \
    llvm-19-dev \
    llvm-19-doc \
    libclang-cpp19 \
    libllvm19 \
    llvm-19-linker-tools \
    llvm-19-runtime \
    llvm-19-tools \
    protobuf-compiler=3.21.12* \
    libprotobuf-dev=3.21.12* \
    protoc-gen-go=1.32.0* \
    && rm -rf /var/lib/apt/lists/*

# Install protoc-gen-go
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@1.36.5

# Set working directory
WORKDIR /span