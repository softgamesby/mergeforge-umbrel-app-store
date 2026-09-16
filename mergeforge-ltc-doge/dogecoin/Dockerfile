FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254 AS fetch

ARG DOGECOIN_VERSION=1.14.9
ARG DOGECOIN_SHA256=4f227117b411a7c98622c970986e27bcfc3f547a72bef65e7d9e82989175d4f8

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

RUN curl -fsSLO "https://github.com/dogecoin/dogecoin/releases/download/v${DOGECOIN_VERSION}/dogecoin-${DOGECOIN_VERSION}-x86_64-linux-gnu.tar.gz" && \
    echo "${DOGECOIN_SHA256}  dogecoin-${DOGECOIN_VERSION}-x86_64-linux-gnu.tar.gz" | sha256sum -c - && \
    tar -xzf "dogecoin-${DOGECOIN_VERSION}-x86_64-linux-gnu.tar.gz"

FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    groupmod -n dogecoin ubuntu && \
    usermod -l dogecoin -d /home/dogecoin -m ubuntu && \
    usermod -G dogecoin dogecoin

COPY --from=fetch /tmp/dogecoin-1.14.9/bin/dogecoind /usr/local/bin/dogecoind
COPY --from=fetch /tmp/dogecoin-1.14.9/bin/dogecoin-cli /usr/local/bin/dogecoin-cli

RUN mkdir -p /data && chown -R dogecoin:dogecoin /data

USER dogecoin

EXPOSE 22556

ENTRYPOINT ["/usr/local/bin/dogecoind"]
