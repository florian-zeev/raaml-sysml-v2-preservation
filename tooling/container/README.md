# Reproducible validation container

The container is a clean, Linux/x86-64 execution environment for the
validation gates. Its official Python base image is pinned by immutable OCI
index digest in `Dockerfile`.

The image contains only this project's original source and documentation plus
the upstream Python base. It deliberately excludes:

- `sources/cache`;
- `tooling/cache`;
- generated diagnostics and reports;
- Git history.

Official standards files, the SysML validator distribution, and the pinned
Linux JDK remain outside the image. Supply them through a read-only mount after
`./raaml sources fetch` and `./raaml sources verify` have succeeded.

Example:

```text
docker build \
  --pull \
  --no-cache \
  --platform linux/amd64 \
  --build-arg VCS_REF="$(git rev-parse HEAD)" \
  --tag raaml-preservation:milestone-0 \
  .

chmod -R a+rX sources/cache

docker run \
  --rm \
  --network none \
  --platform linux/amd64 \
  --volume "$PWD/sources/cache:/workspace/sources/cache:ro" \
  raaml-preservation:milestone-0 \
  sh -ec '
    ./raaml sources verify
    ./raaml tooling bootstrap
    ./raaml schemas validate
    ./raaml tests unit
    ./raaml tests milestone-0
  '
```

The container run is offline. The GitHub workflow records the content-addressed
built image ID in its log and job summary. The image is not pushed to a
registry while third-party and publication policy remains under review.
