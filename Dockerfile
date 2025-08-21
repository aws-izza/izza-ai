# 1. Use a slim, official Python image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 && rm -rf /var/lib/apt/lists/*

# 4. Copy and install Python dependencies first to leverage Docker layer caching
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all necessary application code and assets
# Note the source path is 'final/' because the Dockerfile is in the project root
COPY src/fastapi_server.py .
COPY src/main_orchestrator.py .
COPY src/knowledge_agent_tool.py .
COPY src/policy_agent.py .
COPY src/config.py .
COPY src/prompts/ ./prompts/
COPY src/templates/ ./templates/
COPY src/static/ ./static/
COPY src/browser_test.html .
COPY src/template.html .
COPY src/.env .
COPY src/run_server.py .
COPY src/logging_config.py .

# 6. Expose the port the application runs on
EXPOSE 8000

# 7. Define the command to run the application
# This runs uvicorn from within the fastapi_server.py script
CMD ["python", "run_server.py"]