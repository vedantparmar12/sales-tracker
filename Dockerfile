# Use a slim and secure Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Run the application with gunicorn
# Replace 'main:app' with the name of your Python file and Flask/FastAPI app instance
# For example, if your main file is 'app.py' and your Flask app is named 'my_app',
# you would use 'app:my_app'
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
