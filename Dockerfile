FROM python:3.11-slim-buster

COPY . /app

WORKDIR /app

# Install nginx and gunicorn (web server and WSGI server)
RUN apt-get update && apt-get install -y nginx gunicorn git

RUN pip install -r requirements.txt

# Expose the port for Flask app
EXPOSE 5000

# Define the Gunicorn command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]