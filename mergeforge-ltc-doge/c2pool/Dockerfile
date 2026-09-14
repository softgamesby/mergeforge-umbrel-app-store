FROM ubuntu:24.04 AS build
ARG C2POOL_REF=v0.2.0
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git g++ cmake make python3 python3-pip pkg-config \
    libleveldb-dev libsecp256k1-dev libssl-dev libzmq3-dev && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages "conan>=2.0,<3.0"
WORKDIR /src
RUN git clone --depth 1 --branch "${C2POOL_REF}" https://github.com/frstrtr/c2pool.git .
RUN conan profile detect --force && mkdir -p build && cd build && \
    conan install .. --build=missing --output-folder=. --settings=build_type=Release && \
    cmake .. --preset conan-release && \
    cmake --build . --target c2pool-ltc -j2

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget libleveldb1d libsecp256k1-1 libssl3 libzmq5 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -r -u 1000 -m -d /home/mergeforge mergeforge
COPY --from=build /src/build/src/c2pool/c2pool-ltc /usr/local/bin/c2pool-ltc
RUN mkdir -p /data && chown -R mergeforge:mergeforge /data
USER mergeforge
EXPOSE 3333 8080
ENTRYPOINT []
