FROM python:3.11-slim-buster

COPY . /app

WORKDIR /app
RUN python --version
# Install nginx and gunicorn (web server and WSGI server)
RUN apt-get update && apt-get install -y nginx git
RUN pip install gunicorn
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

# Expose the port for Flask app
EXPOSE 5000

# Define the Gunicorn command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "app:app"]