# Project Overview

This project is a Korean land analysis service. It takes land data as input, performs a comprehensive analysis using AI, and generates a report in various formats (Markdown, HTML, PDF). The service is built as a microservice-based architecture, containerized with Docker, and deployed on AWS using Kubernetes.

## Main Technologies

*   **Backend:** Python, FastAPI
*   **AI:** Strands Agents
*   **Frontend:** HTML, CSS, JavaScript (with Jinja2 for templating)
*   **Database:** None (in-memory task storage)
*   **Deployment:** Docker, Kubernetes, AWS (ECR, EKS)
*   **CI/CD:** Jenkins

## Architecture

The application consists of the following main components:

*   **FastAPI Server (`fastapi_server.py`):** This is the main entry point of the application. It provides a RESTful API for starting and monitoring analysis tasks, and for retrieving the results.
*   **Main Orchestrator (`main_orchestrator.py`):** This module contains the core logic for the land analysis. It orchestrates the work of the knowledge and policy agents, and generates the final report.
*   **Knowledge Agent (`knowledge_agent_tool.py`):** This agent is responsible for analyzing the land data and providing a professional analysis based on its knowledge base.
*   **Policy Agent (`policy_agent.py`):** This agent is responsible for searching for and analyzing government support policies related to the land.
*   **Dockerfile:** This file defines the Docker image for the application.
*   **Jenkinsfile:** This file defines the CI/CD pipeline for building and deploying the application.
*   **Kubernetes Deployment (`k8s_deployment/ai-report.yaml`):** This file defines the Kubernetes resources for deploying the application.

# Building and Running

## Building the Docker Image

To build the Docker image, run the following command:

```bash
docker build -t izza/aireport .
```

## Running the Application Locally

To run the application locally, you can use the following command:

```bash
python src/run_server.py
```

This will start the FastAPI server on `http://localhost:8000`.

## Running with Docker

To run the application with Docker, use the following command:

```bash
docker run -p 8000:8000 izza/aireport
```

# Development Conventions

*   **Coding Style:** The code follows the PEP 8 style guide.
*   **Testing:** The project includes a `main` function in `main_orchestrator.py` that can be used for testing the analysis pipeline. There is also a browser-based test page at `/browser_test.html`.
*   **API Documentation:** The API is documented using OpenAPI (Swagger). The documentation is available at `http://localhost:8000/docs`.

# Key Configurations

*   **Logging:** The application is configured to output logs exclusively in JSON format. The Uvicorn access logs are disabled to ensure log consistency.
*   **CORS:** The API has Cross-Origin Resource Sharing (CORS) enabled to allow requests from any domain. This is configured in `fastapi_server.py`.