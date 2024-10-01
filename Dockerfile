FROM python:3.11-slim-buster

COPY . /app
WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install gunicorn
RUN pip install -r requirements.txt

# Expose port 8080 for SageMaker
EXPOSE 8080

# Define the Gunicorn command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "1800", "app:app"]