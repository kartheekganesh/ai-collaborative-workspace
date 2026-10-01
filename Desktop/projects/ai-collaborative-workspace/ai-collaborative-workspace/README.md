# AI Collaborative Workspace

## Run locally with Docker Compose

From the project root, start the backend and its dependencies:

```powershell
docker compose up --build
```

Open the published `app` URL shown by `docker compose ps` (port 8000 or 8001) in a browser. The backend serves the frontend at `/` and its assets at `/static`; use that URL rather than opening `frontend/index.html` directly or using a separate static-file server. Sign in or create an account when prompted. The REST API and WebSocket connect to the same host and port as the page.