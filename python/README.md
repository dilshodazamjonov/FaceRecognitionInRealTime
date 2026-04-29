# Python Workspace

This folder contains all Python code for the project.

## Layout

- `face_access_app/`: face recognition engine and local CLI tools
- `forgf_backend/`: FastAPI backend and admin logs page
- `.venv/`: shared Python virtual environment

## Main Commands

Run these from the repo root:

```powershell
uv run --project .\python face-enroll
uv run --project .\python face-verify --image .\data\photo_2026-04-25_13-00-12.jpg
uv run --project .\python face-live
uv run --project .\python forgf-backend
```

If you are already inside `python\`, use:

```powershell
uv run --project . face-enroll
uv run --project . face-verify --image ..\data\photo_2026-04-25_13-00-12.jpg
uv run --project . face-live
uv run --project . forgf-backend
```

Example with a custom admin token and a non-default port:

```powershell
$env:FORGF_ADMIN_TOKEN='my-secret-token'
$env:FORGF_PORT='8001'
uv run --project . forgf-backend
```

## Environment File

The backend reads `python/.env` automatically on startup.

Recommended setup:

- keep real local values in `python/.env`
- keep safe placeholder values in `python/.env.example`
- keep the same keys in both files

To create your local file for the first time:

```powershell
Copy-Item .\python\.env.example .\python\.env
```

## Admin Logs

Backend logs only come from requests that hit `POST /verify`.

Open the admin page with your token:

```text
http://127.0.0.1:8001/admin/logs?token=my-secret-token
```

The admin view currently supports:

- recent verification attempts
- summary counts
- IP and device/browser hints
- deleting one log row
- clearing all logs

## Notes

- Only one Python environment is used now: `python/.venv`
- The backend imports `face_access_app` directly from this shared workspace
- `python/.env.example` is the tracked template
- `python/.env` is the real local config file loaded by the backend
