# LabourLens web app. The corpus (data/) is never copied into this image: it lives on the server disk and is bind-mounted
# at /app/data (see deploy/docker-compose.yml, deploy/runtime-data.txt and docs/deploy.md).
# Base images are pinned by tag, not digest: no digest was verified when this file was written.

FROM python:3.12-slim AS build
# uv version matches the one used to produce uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.9.25 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
ARG LABOURLENS_BUILD=""
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp \
    MPLCONFIGDIR=/tmp/mpl \
    LABOURLENS_BUILD=${LABOURLENS_BUILD}
RUN groupadd --system --gid 10001 labourlens \
 && useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin labourlens
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src
COPY pyproject.toml ./
COPY specs ./specs
COPY prompts ./prompts
COPY web ./web
# Empty mount point; the host bind mount replaces it. Owned by the service user so a plain `docker run` also works.
RUN mkdir /app/data && chown 10001:10001 /app/data
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4).status == 200 else 1)"]
# `labourlens serve` runs uvicorn with one worker, proxy_headers=True and forwarded_allow_ips taken from
# LABOURLENS_FORWARDED_ALLOW_IPS (default 127.0.0.1; compose sets the fixed Caddy address). It binds 0.0.0.0 inside the
# container network only; nothing publishes port 8000 to the host.
ENTRYPOINT ["labourlens", "serve"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
