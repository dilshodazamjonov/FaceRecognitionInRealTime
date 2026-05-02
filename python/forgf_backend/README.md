# ForGF Backend

FastAPI backend for the ForGF web app.

## Run

From the repo root:

```powershell
uv run --project .\python forgf-backend
```

If you are already inside `python/`:

```powershell
uv run --project . forgf-backend
```

Example with a custom admin token and a non-default port:

```powershell
$env:FORGF_ADMIN_TOKEN='my-secret-token'
$env:FORGF_ADMIN_PASSWORD='my-secret-password'
$env:FORGF_PORT='8001'
uv run --project . forgf-backend
```

## Environment File

The backend auto-loads `python/.env` when it builds config.

Recommended setup:

- put real local values in `python/.env`
- keep `python/.env.example` as the tracked placeholder template
- keep the keys aligned between both files

Bootstrap command:

```powershell
Copy-Item .\python\.env.example .\python\.env
```

## Endpoints

- `GET /health`
- `GET /reference`
- `POST /enroll`
- `POST /verify`
- `GET /admin/logs`
- `POST /admin/logs/{log_id}/delete`
- `POST /admin/logs/clear`

## Admin Logs

Open:

```text
http://127.0.0.1:8000/admin
```

Use `python/.env` for real local settings and `python/.env.example` as the template.

With the custom token and port example above, open:

```text
http://127.0.0.1:8001/admin
```

Login behavior:

- the admin page now uses a simple password form
- if `FORGF_ADMIN_PASSWORD` is set, that is the password
- otherwise the backend falls back to `FORGF_ADMIN_TOKEN` as the password
- after login, the browser keeps an admin cookie so you do not need to paste a token into the URL

The admin page currently shows:

- recent verification attempts
- IP addresses
- browser and device hints
- verification status and messages
- distance and threshold values

The admin page also supports:

- deleting a single log entry
- clearing all log entries

Important note:

- the admin page only shows backend verification requests
- local CLI runs like `face-verify` and `face-live` do not create admin rows

If port `8000` is already in use, run on another port:

```powershell
$env:FORGF_PORT='8001'
uv run --project . forgf-backend
```

Then open:

- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/docs`
- `http://127.0.0.1:8001/admin`
