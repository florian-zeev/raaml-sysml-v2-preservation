FROM --platform=linux/amd64 python:3.14.4-slim-bookworm@sha256:fc74d22ffd0d5ac395a4b7bdda75a4539758862c49ebf3005647084631e63789

ARG VCS_REF=unknown
ARG SOURCE_STATE=unknown

LABEL org.opencontainers.image.title="RAAML SysML v2 preservation"
LABEL org.opencontainers.image.source="https://github.com/florian-zeev/raaml-sysml-v2-preservation"
LABEL org.opencontainers.image.revision="${VCS_REF}"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RAAML_VCS_REF="${VCS_REF}"
ENV RAAML_SOURCE_STATE="${SOURCE_STATE}"

WORKDIR /workspace
COPY --chown=65532:65532 . .
COPY --chown=65532:65532 --chmod=0755 raaml ./raaml

USER 65532:65532

CMD ["./raaml", "--help"]
