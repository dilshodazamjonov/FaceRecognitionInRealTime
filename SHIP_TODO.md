# Ship TODO

This file tracks what is already done in the repo and what is still left before this becomes a real product.

## Locked Product

- Private web app for one person only: your girlfriend.
- Mobile and iPad-friendly layout.
- Browser camera is the real product path.
- Python CLI stays for enrollment, debugging, and threshold tuning.
- Match should unlock a wishes page.
- Non-match should stay blocked with a simple failure message.
- False accepts are more dangerous than false rejects, so the system should stay strict.

## Current Repo State

Current structure:

- `python/face_access_app/`: face engine
- `python/forgf_backend/`: FastAPI backend
- `frontend/`: future web UI
- `data/`: local image inputs

Current run commands:

```powershell
uv run --project .\python face-enroll
uv run --project .\python face-verify --image ..\data\photo_2026-04-25_13-00-12.jpg
uv run --project .\python face-live
uv run --project .\python forgf-backend
```

Custom backend launch example:

```powershell
$env:FORGF_ADMIN_TOKEN='my-secret-token'
$env:FORGF_PORT='8001'
uv run --project .\python forgf-backend
```

## Done

### Shared Python Workspace

- Moved Python code into one shared `python/` workspace.
- Reduced the project to one supported virtual environment: `python/.venv`.
- Added one shared `python/pyproject.toml` with CLI entry points.
- Updated the repo readmes to the unified structure.

### Face Engine

- `face-enroll` works and saves a single reference embedding.
- `face-verify` works against a stored reference.
- `face-live` works as the local OpenCV debugging path.
- Default matching threshold is strict at `0.50`.
- Live verification uses a stable consecutive-match requirement.
- Result payload is app-friendly:
  - `status`
  - `matched`
  - `access_granted`
  - `message`
  - `next_screen`
  - `should_redirect`
- Live mode no longer crashes when detection is unstable and now falls back more safely.
- Input frames are resized before inference to reduce CPU cost.
- Model warm-up and verification throttling were added for smoother local behavior.
- TensorFlow startup noise is suppressed in normal CLI use.

### Backend

- FastAPI backend exists in `python/forgf_backend/`.
- These routes exist:
  - `GET /`
  - `GET /health`
  - `GET /reference`
  - `POST /enroll`
  - `POST /verify`
  - `GET /admin/logs?token=your-token`
- Backend validates uploaded images and returns structured API errors.
- Backend calls the shared face engine instead of duplicating recognition logic.
- Reference loading is cached in memory.
- Model warm-up can run on backend startup.
- CORS and environment-based config are in place.

### Admin Logs

- Verification attempts are stored in SQLite.
- Each log captures:
  - timestamp
  - status
  - access result
  - IP address
  - browser and device hint
  - OS hint
  - message
  - distance
  - threshold
- Admin logs page exists with a styled HTML view.
- Admin page is protected by an admin token.
- Admin page now supports:
  - deleting a single log row
  - clearing all logs

### Verified Locally

- Enrollment command runs.
- Image verification command runs.
- Backend health route runs.
- Backend reference route runs.
- Backend verify route runs.
- Admin logs page renders.

## Partly Done

### Real-Time Web Flow

The backend side is ready for browser polling, but the frontend does not exist yet.

What is already true:

- backend accepts one uploaded frame at a time
- verify response already contains redirect-friendly fields
- browser camera design is defined as snapshot polling, not video streaming

What is still missing:

- actual browser camera UI
- frame capture loop in the frontend
- redirect logic to the wishes page
- real UX for denied camera permissions and backend failures

### Admin Experience

There is now a mini admin view, but it is still intentionally basic.

What it already does:

- shows recent attempts
- shows summary counts
- shows IPs and device/browser hints
- allows row deletion
- allows clear-all deletion

What it still does not do:

- login flow beyond token protection
- pagination
- filtering
- export
- audit protection against accidental destructive actions beyond confirm dialogs

## Still Left Before Shipping

### Frontend

- Build the real web app in `frontend/`.
- Make it mobile-first and iPad-friendly.
- Add browser camera permission handling.
- Show local camera preview in the browser.
- Capture frames on an interval and send them to `POST /verify`.
- Use backend result states to drive the screen:
  - `match`
  - `unknown`
  - `no_face`
  - `multiple_faces`
- Redirect to the wishes page only after stable success logic.
- Build at least these screens:
  - startup/loading
  - camera verification
  - not-found/failure
  - wishes

### Product Content

- Define what the wishes page actually is.
- Decide whether it is one page or a sequence.
- Decide whether it includes only text or also media.
- Write the real user-facing failure text.

### Recognition Hardening

- Test on real phone and tablet browsers.
- Test lighting changes and side angles.
- Test low-light behavior.
- Test another person in front of the camera.
- Test with photos shown to the camera.
- Re-tune the threshold if real testing shows false accepts or too many false rejects.
- Consider adding minimum face size rules.
- Consider adding detector-confidence rules.
- Consider adding anti-spoofing or liveness later if simple photo attacks become a concern.

### Security Before Network Exposure

- Replace the default admin token everywhere you actually use the backend.
- Add proper protection for admin and enroll routes.
- Use HTTPS when exposed beyond localhost.
- Add rate limiting to verification.
- Keep uploads size-limited and strictly validated.
- Avoid logging raw images.
- Decide whether the verify route should be public or gated.

### Data And Operations

- Decide backup rules for the `.npz` reference file.
- Decide whether enrollment should remain CLI-first or become a protected backend-only action.
- Decide whether reference replacement should keep history or overwrite cleanly.
- Decide log retention rules.
- Decide whether to keep SQLite for production or move to a more formal store later.

### Testing

- Add automated tests for:
  - storage and reference loading
  - verify route success and failure cases
  - admin route protection
  - log deletion routes
- Run cross-device manual tests:
  - phone
  - tablet
  - desktop browser
- Test startup behavior when no reference exists.
- Test backend behavior when the camera frame contains no face or multiple faces.

## Recommended Shipping Order

1. Build the frontend camera flow in `frontend/`.
2. Connect browser snapshot polling to `POST /verify`.
3. Add the wishes and failure pages.
4. Test on your real target devices.
5. Tighten threshold and live-match behavior from real results.
6. Harden admin and enroll security.
7. Expose over the network only after local and device testing is stable.

## Keep Out Of Scope For V1

- Multi-user enrollment
- Full identity management
- Public signup or public admin UI
- Heavy analytics
- Continuous video streaming
- Premature cloud scaling work

## Short Summary

The core face engine and backend are already in place. The main remaining work is the real browser frontend, real-device testing, content for the wishes flow, and security hardening before network exposure.
