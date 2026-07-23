FROM python:3.10-slim

WORKDIR /app

# Copy requirements and dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Environment variable default settings
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Ho_Chi_Minh

# Default command runs the main automation pipeline
CMD ["python", "main_automation.py", "--now"]
