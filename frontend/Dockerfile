FROM python:3.9-slim

WORKDIR /app

# Copy frontend files
COPY . .

# Install Python dependencies for the simple HTTP server
RUN pip install --no-cache-dir flask

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

# Start the Python server
CMD ["python", "server.py"]
