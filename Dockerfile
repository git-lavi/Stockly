# Use the official Python image
FROM python:3.12-alpine

# Set environment variables to prevent Python from bufferring outputs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN apk add --no-cache postgresql-dev gcc musl-dev
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project files into the container
COPY . /code/

# Ensure correct permissions for working directory
RUN chmod -R 755 /code