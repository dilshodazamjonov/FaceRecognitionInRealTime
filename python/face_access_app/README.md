# Face Access App

Single-person face verification pipeline.

Version 1 is built for one enrolled identity only:

- one reference image in `../data/`
- one saved reference embedding
- one live camera check against that saved reference

The live result is effectively:

- `TRUE` when the camera face matches the enrolled person
- `FALSE` when the face does not match
- `NO FACE` when nothing is detected
- `MULTIPLE FACES` when more than one face is detected

## Files

- `storage.py`: save and load the enrolled reference embedding
- `face_pipeline.py`: shared face detection, embedding, and comparison logic
- `enroll.py`: create the saved reference from one image
- `verifier.py`: verify one image against the saved reference
- `live_verifier.py`: run webcam verification
- `references/`: saved `.npz` reference files

## Commands

Run all commands from inside `python/face_access_app/`.

```powershell
cd .\python\face_access_app
```

### 1. Enroll The Reference Image

This reads the first supported image from `..\..\data\` and saves the enrolled reference.

```powershell
uv run --project .. face-enroll
```

By default, the saved file is:

```text
.\references\girlfriend_reference.npz
```

### 2. Verify An Image

Verify a candidate image against the saved reference:

```powershell
uv run --project .. face-verify --image ..\..\data\photo_2026-04-25_13-00-12.jpg
```

### 3. Run Live Camera Verification

Start webcam verification:

```powershell
uv run --project .. face-live
```

Press `q` to close the camera window.

Smoother local example:

```powershell
uv run --project .. face-live --process-interval-ms 500 --max-inference-dimension 512
```

## Commands From Repo Root

If you want to stay in the repo root, use `--project`.

### Enroll

```powershell
uv run --project .\python face-enroll
```

### Verify

```powershell
uv run --project .\python face-verify --image .\data\photo_2026-04-25_13-00-12.jpg
```

### Live Camera

```powershell
uv run --project .\python face-live
```

## Commands From Inside `python/`

If your terminal is already in `D:\python projects\ForGF\python`, use `--project .` and remember the image path is one level up in `..\data\`.

### Enroll

```powershell
uv run --project . face-enroll
```

### Verify

```powershell
uv run --project . face-verify --image ..\data\photo_2026-04-25_13-00-12.jpg
```

### Live Camera

```powershell
uv run --project . face-live
```

### Backend From Inside `python/`

```powershell
uv run --project . forgf-backend
```

Custom token and port example:

```powershell
$env:FORGF_ADMIN_TOKEN='my-secret-token'
$env:FORGF_PORT='8001'
uv run --project . forgf-backend
```

## Useful Options

Enroll with an explicit image and label:

```powershell
uv run --project .\python face-enroll --image .\data\photo_2026-04-25_13-00-12.jpg --label girlfriend
```

Enroll to a custom output file:

```powershell
uv run --project .\python face-enroll --out .\python\face_access_app\references\my_reference.npz
```

Verify using a custom reference file:

```powershell
uv run --project .\python face-verify --image .\data\photo_2026-04-25_13-00-12.jpg --reference .\python\face_access_app\references\my_reference.npz
```

Override the threshold during verification:

```powershell
uv run --project .\python face-verify --image .\data\photo_2026-04-25_13-00-12.jpg --threshold 0.50
```

Run live mode and exit once a stable match is found:

```powershell
uv run --project .\python face-live --exit-on-match
```

Use a different camera index:

```powershell
uv run --project .\python face-live --camera-index 1
```

Require more consecutive matching frames before `TRUE`:

```powershell
uv run --project .\python face-live --required-consecutive-matches 5
```

Override the live threshold:

```powershell
uv run --project .\python face-live --threshold 0.50
```

Slow-machine tuning example:

```powershell
uv run --project .\python face-live --process-interval-ms 500 --max-inference-dimension 512
```

## Typical Flow

1. Enroll the reference image once.
2. Verify that same image to confirm the pipeline works.
3. Run live camera verification.

Example:

```powershell
uv run --project .\python face-enroll
uv run --project .\python face-verify --image .\data\photo_2026-04-25_13-00-12.jpg
uv run --project .\python face-live
```

## Output Meaning

During live verification:

- `TRUE`: stable match confirmed and ready to move to the wishes page
- `MATCHING`: current frames are matching, but the required streak is not reached yet
- `FALSE: unknown`: a face was found, but it is not the enrolled person
- `NO FACE`: no face detected in the frame
- `MULTIPLE FACES`: more than one face detected

## Notes

- Version 1 is intentionally single-person only.
- Enrollment expects exactly one face in the reference image.
- Verification expects exactly one face for a proper match decision.
- The saved reference file stores the embedding plus metadata such as label, threshold, model, and detector backend.
- Live verification is for local debugging; the real product path is browser camera -> backend `POST /verify`.
