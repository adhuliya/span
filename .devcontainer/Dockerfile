FROM arm64v8/ubuntu:24.04

# Install Go
RUN apt-get update && apt-get install -y \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.24
RUN wget -O go.tgz https://go.dev/dl/go1.24.2.linux-arm64.tar.gz && \
    tar -C /usr/local -xzf go.tgz && \
    rm go.tgz

# Set Go environment variables
ENV GOROOT=/usr/local/go
ENV GOPATH=/go
ENV PATH=$GOPATH/bin:$GOROOT/bin:/usr/lib/llvm-19/bin:$PATH

# Create Go workspace directory
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"

# Install required packages
RUN apt-get update && apt-get install -y \
    cmake \
    clang-19 \
    llvm-19 \
    clang-tools-19 \
    clang-format-19 \
    libclang-19-dev \
    llvm-19-dev \
    protobuf-compiler \
    libprotobuf-dev \
    libedit-dev \
    libzstd-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install protoc-gen-go
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
RUN go install golang.org/x/tools/cmd/stringer@latest

# Set working directory
WORKDIR /span