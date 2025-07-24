# Local Development with Docker

This document outlines how to use Docker and Docker Compose to set up a consistent, isolated local development environment for this project.

## Overview

The current application requires manual setup of multiple services (database, backend, frontend) and has previously relied on the production database for local testing. This can lead to inconsistent environments and potential disruption to production data.

This Docker-based setup provides a solution by containerizing the application into three services:

-   `protein_db`: A PostgreSQL database.
-   `protein_backend`: The Flask backend API.
-   `protein_frontend`: The Svelte frontend application.

With this setup, the entire local development stack can be started with a single command, ensuring a consistent environment for all developers.

## Prerequisites

-   You must have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running on your system.

## Getting Started

1.  Make sure Docker Desktop is running.
2.  Navigate to the `Part2` directory in your terminal.
3.  Run the following command to build the container images and start the services:

    ```bash
    docker-compose up
    ```

    This command will display logs from all services in your terminal. To run the services in the background (detached mode), use:

    ```bash
    docker-compose up -d
    ```

## Verifying the Setup

Once the services are running, you can verify that everything is working correctly:

-   **Container Status**: You can see the `protein_db`, `protein_backend`, and `protein_frontend` containers running in Docker Desktop.
-   **Service Ports**:
    -   Database (`protein_db`): Port `5432`
    -   Backend (`protein_backend`): Port `3050`
    -   Frontend (`protein_frontend`): Port `5173`

### Manual Verification Steps

1.  **Frontend**: Open your web browser and go to `http://localhost:5173`. You should see the application's home page.
2.  **Backend**: The backend API is accessible at `http://localhost:3050`. You can test this with an API client or by checking network requests from the frontend.
3.  **Database**: The database schema is initialized automatically. You can check the logs of the `protein_db` container for "CREATE TABLE" statements to confirm.

## Development Features

### Hot Reloading

The development environment is configured for hot reloading to improve productivity:

-   Changes to the backend code in `Part2/Part2_Backend/` will automatically restart the Flask server.
-   Changes to the frontend code in `Part2/Part2_Frontend/src/` will automatically be reflected in the browser.

This is made possible by mounting the local source code directories as volumes in the containers.

### Database Persistence

Data in the PostgreSQL database is persisted in a Docker volume. This means your data will remain intact even after you stop and restart the containers.

## Stopping the Environment

-   If you ran `docker-compose up` in the foreground, press `Ctrl+C` in the terminal to stop the services.
-   If you ran the services in detached mode, use the following command:
    ```bash
    docker-compose down
    ```

To stop the services and **delete all data** (including the database volume), use the `-v` flag. This is useful when you want to start with a fresh database.

```bash
docker-compose down -v
```

## Additional Notes

-   **Backward Compatibility**: Developers can still run the frontend and backend manually without Docker if preferred.
-   **Database Isolation**: The Docker setup uses a local PostgreSQL instance, completely isolating it from any production database.
-   **Health Checks**: The backend service includes a health check that waits for the database to be fully ready before starting, preventing connection errors.
-   **Environment Variables**: The `docker-compose.yml` file is configured with the necessary environment variables for development and for services to communicate with each other.