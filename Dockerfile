# 1. Use a slim, official Python image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 && rm -rf /var/lib/apt/lists/*

# 4. Copy and install Python dependencies first to leverage Docker layer caching
COPY src/* .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Expose the port the application runs on
EXPOSE 8000

# 6. Define the command to run the application
# This runs uvicorn from within the fastapi_server.py script
CMD ["python", "run_server.py"]