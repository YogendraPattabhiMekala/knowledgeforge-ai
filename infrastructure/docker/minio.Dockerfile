# MinIO's old public binary images are unavailable. Build the pinned AGPL source.
FROM golang:1.24.8-alpine AS build
RUN apk add --no-cache ca-certificates git
WORKDIR /src
ADD https://codeload.github.com/minio/minio/tar.gz/refs/tags/RELEASE.2025-10-15T17-29-55Z /tmp/minio.tar.gz
RUN tar xzf /tmp/minio.tar.gz --strip-components=1 && CGO_ENABLED=0 GOMEMLIMIT=512MiB GOGC=20 GOMAXPROCS=1 go build -p 1 -mod=readonly -trimpath -o /minio .
FROM alpine:3.22.2
RUN apk add --no-cache ca-certificates && adduser -D -u 10001 minio && mkdir /data && chown minio /data
COPY --from=build /minio /usr/local/bin/minio
USER minio
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
