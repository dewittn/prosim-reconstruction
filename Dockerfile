# PROSIM Web Interface
# Multi-stage build for smaller final image

# =============================================================================
# Build stage
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy only files needed for building
COPY pyproject.toml ./
COPY prosim/ ./prosim/
COPY web/ ./web/

# Build the wheel
RUN python -m build --wheel

# =============================================================================
# Runtime stage
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash prosim

# Copy wheel from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package with web dependencies
# Note: Need to use shell to expand glob, then install extras
RUN pip install --no-cache-dir /tmp/prosim-*.whl && \
    pip install --no-cache-dir "prosim[web]" && \
    rm /tmp/*.whl

# Copy templates and static files to installed package location
# The app looks for templates relative to the installed web package
COPY web/templates/ /usr/local/lib/python3.11/site-packages/web/templates/
COPY web/static/ /usr/local/lib/python3.11/site-packages/web/static/

# Ensure templates are readable by all users
RUN chmod -R a+r /usr/local/lib/python3.11/site-packages/web/templates/ && \
    chmod -R a+r /usr/local/lib/python3.11/site-packages/web/static/

# Create data directory for SQLite database
RUN mkdir -p /app/data && chown prosim:prosim /app/data

# Switch to non-root user
USER prosim

# Environment variables
ENV PROSIM_DATABASE_URL=sqlite:///./data/prosim.db
ENV PROSIM_HOST=0.0.0.0
ENV PROSIM_PORT=8000
ENV PROSIM_DEBUG=false

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
