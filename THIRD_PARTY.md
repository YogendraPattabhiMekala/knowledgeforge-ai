# Third-party software
The project source is MIT licensed. Dependencies retain their own licenses.

Local Docker development builds MinIO from the upstream, version-pinned
`RELEASE.2025-10-15T17-29-55Z` source because the older published images are
unavailable. **MinIO is AGPL-3.0**, not MIT; source, license and obligations:
https://github.com/minio/minio/tree/RELEASE.2025-10-15T17-29-55Z

The Dockerfile retrieves upstream source during the build; no MinIO source or
binaries are redistributed inside this source ZIP. Review AGPL obligations
before redistributing container images or offering modified MinIO over a network.
This is a dependency notice, not legal advice. The local demo without Docker
does not use MinIO and does not require any paid AI service.
