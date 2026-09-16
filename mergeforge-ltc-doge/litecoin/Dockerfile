FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254 AS fetch

ARG LITECOIN_VERSION=0.21.5.8
ARG LITECOIN_SHA256=43200c9f9d65ebc126ea5833ca9429e144c4b3273da6bb9f4e89fd7450ab1be9

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

RUN curl -fsSLO "https://download.litecoin.org/litecoin-${LITECOIN_VERSION}/linux/litecoin-${LITECOIN_VERSION}-x86_64-linux-gnu.tar.gz" && \
    echo "${LITECOIN_SHA256}  litecoin-${LITECOIN_VERSION}-x86_64-linux-gnu.tar.gz" | sha256sum -c - && \
    tar -xzf "litecoin-${LITECOIN_VERSION}-x86_64-linux-gnu.tar.gz"

FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    groupmod -n litecoin ubuntu && \
    usermod -l litecoin -d /home/litecoin -m ubuntu && \
    usermod -G litecoin litecoin

COPY --from=fetch /tmp/litecoin-0.21.5.8/bin/litecoind /usr/local/bin/litecoind
COPY --from=fetch /tmp/litecoin-0.21.5.8/bin/litecoin-cli /usr/local/bin/litecoin-cli

RUN mkdir -p /data && chown -R litecoin:litecoin /data

USER litecoin

EXPOSE 9333

ENTRYPOINT ["/usr/local/bin/litecoind"]
