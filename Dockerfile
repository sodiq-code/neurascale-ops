FROM python:3.11-slim

# Metadata
LABEL org.opencontainers.image.title="NeuroScale Ops"
LABEL org.opencontainers.image.description="AI-powered Kubernetes Incident Response — UiPath Maestro"
LABEL org.opencontainers.image.source="https://github.com/sodiq-code/neurascale-ops"
LABEL org.opencontainers.image.authors="Sodiq Jimoh"

# Install system deps (kubectl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create non-root user
RUN useradd -m -u 1000 neurascale && chown -R neurascale:neurascale /app
USER neurascale

# Expose ports: 8501 = Streamlit dashboard, 8080 = API
EXPOSE 8501 8080

# Default: run dashboard
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
