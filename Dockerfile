FROM python:3.11-slim-buster

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs
    
RUN npm install -g serve

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh


# Install python dependencies
RUN pip install gunicorn
RUN pip install -r requirements.txt

# Expose port 8080 for SageMaker
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
# Define the Gunicorn command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "1800", "app:app","serve"]
