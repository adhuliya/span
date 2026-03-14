FROM arm64v8/ubuntu:24.04

RUN apt-get update 
RUN apt-get install -y wget git

# Install Go 1.25
RUN wget -O go.tgz https://go.dev/dl/go1.25.5.linux-arm64.tar.gz && \
    tar -C /usr/local -xzf go.tgz && \
    rm go.tgz

# Set Go environment variables
ENV GOROOT=/usr/local/go
ENV GOPATH=/go
ENV PATH=$GOPATH/bin:$GOROOT/bin:/usr/lib/llvm-19/bin:$PATH

# Create Go workspace directory
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"

# Install required packages
RUN apt-get install -y \
    cmake \
    clangd-19 \
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
    gdb \
    python3 \
    python3-pip

# Install Jupyter Notebook
# Install Jupyter Notebook extensions and common data science/visualization tools
RUN apt-get install -y \
    python3-notebook \
    python3-widgetsnbextension \
    python3-graphviz \
    python3-matplotlib \
    python3-pandas
EXPOSE 8888

# Enable Jupyter Notebook extensions
RUN jupyter nbextension enable --py widgetsnbextension

# Install and enable extensions for dot graph visualization (Graphviz)
RUN jupyter nbextension install --py graphviz --sys-prefix || true
RUN jupyter nbextension enable --py graphviz --sys-prefix || true

# For matplotlib widgets (useful for rich plots in notebooks)
RUN jupyter nbextension enable --py --sys-prefix matplotlib || true

# Install protoc-gen-go
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
RUN go install golang.org/x/tools/cmd/stringer@latest

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set working directory
WORKDIR /span
