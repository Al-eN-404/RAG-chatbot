# Use a stable Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies required by Playwright and chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and download chromium browser + all OS dependencies cleanly
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Expose port (default Streamlit port)
EXPOSE 8501

# Run the streamlit application, reading the PORT variable dynamically for cloud providers (like Render)
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
