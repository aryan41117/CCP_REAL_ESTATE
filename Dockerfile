# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=application.py
ENV FLASK_ENV=production
 
# Set the working directory inside the container
WORKDIR /app
 
# Copy application files into the container
COPY . /app
 
# Install required system and library dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    pkg-config \
    && apt-get clean
 
# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for the Flask app
EXPOSE 8080

# Define environment variables to run Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the command to start the app with Gunicorn, specifying the module and app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
