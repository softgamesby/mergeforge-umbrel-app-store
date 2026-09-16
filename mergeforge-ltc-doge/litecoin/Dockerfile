FROM ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254 AS fetch

ARG LITECOIN_VERSION=0.21.5.8
ARG TARGETARCH
ARG LITECOIN_SHA256_AMD64=43200c9f9d65ebc126ea5833ca9429e144c4b3273da6bb9f4e89fd7450ab1be9
ARG LITECOIN_SHA256_ARM64=129f55defb9045d5635566382c7b9f6fd227d4106a6fc07847a38b25ff9b29a1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

RUN case "${TARGETARCH}" in \
        amd64) ARCH="x86_64"; SHA256="${LITECOIN_SHA256_AMD64}" ;; \
        arm64) ARCH="aarch64"; SHA256="${LITECOIN_SHA256_ARM64}" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac && \
    FILE="litecoin-${LITECOIN_VERSION}-${ARCH}-linux-gnu.tar.gz" && \
    curl -fsSLO "https://download.litecoin.org/litecoin-${LITECOIN_VERSION}/linux/${FILE}" && \
    echo "${SHA256}  ${FILE}" | sha256sum -c - && \
    tar -xzf "${FILE}"

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
