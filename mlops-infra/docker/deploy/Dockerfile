FROM ubuntu:22.04 AS builder
RUN apt-get update && \
    apt-get install -y gettext-base && \
    rm -rf /var/lib/apt/lists/*

FROM bitnami/kubectl:latest

COPY --from=builder /usr/bin/envsubst /usr/bin/envsubst

COPY --chmod=0755 deploy.sh /deploy.sh


ENTRYPOINT ["/deploy.sh"]
