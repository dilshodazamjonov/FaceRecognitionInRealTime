# ForGF

Private face-access project for one enrolled person, with a shared Python workspace and a future web frontend.

## Folders

- `python/`: shared Python workspace for face recognition and the FastAPI backend
- `frontend/`: future browser app for phone and iPad layouts
- `data/`: local reference and test images

## Main Docs

- [python/README.md](python/README.md): shared workspace commands
- [python/face_access_app/README.md](python/face_access_app/README.md): face engine and CLI usage
- [python/forgf_backend/README.md](python/forgf_backend/README.md): backend routes, admin logs, and launch commands
- [SHIP_TODO.md](SHIP_TODO.md): what is done and what is left before shipping

## Quick Start

From the repo root:

```powershell
uv run --project .\python face-enroll
uv run --project .\python face-verify --image .\data\photo_2026-04-25_13-00-12.jpg
uv run --project .\python forgf-backend
```

Custom backend port and admin token example:

```powershell
$env:FORGF_ADMIN_TOKEN='my-secret-token'
$env:FORGF_PORT='8001'
uv run --project .\python forgf-backend
```

The backend admin logs page is available at:

```text
http://127.0.0.1:8001/admin/logs?token=my-secret-token
```
