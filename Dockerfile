FROM python:3.9-slim-buster

RUN pip install -r requirements.txt

# Copy your application code
COPY . /app

# Set the working directory
WORKDIR /app

# Install nginx and gunicorn (web server and WSGI server)
RUN apt-get update && apt-get install -y nginx gunicorn

# Expose the port for Flask app
EXPOSE 5000

# Define the Gunicorn command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]