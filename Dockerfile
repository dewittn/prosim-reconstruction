# PROSIM Web Interface — Production
# Multi-stage build for smaller final image

# =============================================================================
# Build stage — install dependencies and package
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy project files needed for install
COPY pyproject.toml ./
COPY prosim/ ./prosim/
COPY web/ ./web/

# Install the package with web extras into a prefix we can copy later
RUN pip install --no-cache-dir --prefix=/install ".[web]"

# =============================================================================
# Runtime stage — minimal image with only what's needed
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash prosim

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source (templates, static files, and modules)
COPY --chown=prosim:prosim prosim/ ./prosim/
COPY --chown=prosim:prosim web/ ./web/

# Create data directory for SQLite database
RUN mkdir -p /app/data && chown prosim:prosim /app/data

# Switch to non-root user
USER prosim

# Environment variables (override at runtime for production)
# Note: PROSIM_SECRET_KEY is intentionally not set here — provide at runtime
ENV PROSIM_DATABASE_URL=sqlite:///./data/prosim.db \
    PROSIM_HOST=0.0.0.0 \
    PROSIM_PORT=8000 \
    PROSIM_DEBUG=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
