# thClaws Weather MCP — image for k3s hosting at weather-mcp.artech.cloud.
#
# Multi-stage build keeps the runtime image small (~80 MB) and excludes
# build tools from the surface area. Runs as non-root (uid 1000) to
# match the Pod's `securityContext: runAsNonRoot: true` from
# infra/k3s/thclaws-mcp/10-wikipedia-mcp.yaml (mirror that template
# with name=weather-mcp when deploying).

# ── builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# hatchling builds without external network when wheels are available;
# pre-fetch deps into /wheels so the runtime stage has them locally.
RUN pip install --no-cache-dir --upgrade pip build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip wheel --no-cache-dir --wheel-dir /wheels . \
    && pip wheel --no-cache-dir --wheel-dir /wheels mcp httpx

# ── runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user matches the Pod securityContext in the k3s manifests.
RUN groupadd -g 1000 thclaws \
    && useradd -u 1000 -g 1000 -m -s /bin/sh thclaws

WORKDIR /app

COPY --from=builder /wheels /tmp/wheels
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels thclaws-weather \
    && rm -rf /tmp/wheels

USER thclaws

# Default to SSE transport on port 8000 — the k3s manifest exposes this
# port; for local stdio use, override at run time:
#   docker run --rm -i -e MCP_TRANSPORT=stdio thclaws/weather-mcp
ENV MCP_TRANSPORT=sse \
    MCP_PORT=8000

EXPOSE 8000

ENTRYPOINT ["thclaws-weather"]
