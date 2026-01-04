# Multi-stage build for smaller final image
# Stage 1: Build stage with all dependencies
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies (needed for compiling packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies in a virtual environment
# This allows us to copy only the venv to the final stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install PyTorch CPU-only first (largest package)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove unnecessary files from the virtual environment to save space
RUN find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete

# Stage 2: Runtime stage (minimal final image)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code (only what's needed)
COPY src/ ./src/
COPY knowledge_base/ ./knowledge_base/

# Create directories and non-root user in one layer
RUN mkdir -p /app/chroma_db /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create volume mount points for persistence
VOLUME ["/app/chroma_db", "/app/logs"]

# Expose port
EXPOSE 8000

# Health check with shorter intervals
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
