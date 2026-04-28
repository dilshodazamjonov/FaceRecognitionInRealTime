# Face Recognition

This repository is a scaffold for a small face access app. The code is not implemented yet. Use this file as the build guide and write the code yourself in the order below.

## Full Paths

- Project root: `D:\python projects\ForGF`
- App code: `D:\python projects\ForGF\face_access_app`
- Sample image: `D:\python projects\ForGF\data\photo_2026-04-25_13-00-12.jpg`
- Main files to implement:
  - `D:\python projects\ForGF\face_access_app\storage.py`
  - `D:\python projects\ForGF\face_access_app\enroll.py`
  - `D:\python projects\ForGF\face_access_app\verifier.py`

## Current State

What already exists:
- basic repo structure
- Python package metadata in `face_access_app\pyproject.toml`
- one sample image in `data\`
- empty module stubs for storage, enrollment, and verification

What does not exist yet:
- face detection
- face embedding extraction
- enrollment logic
- verification logic
- saved reference data format
- command-line interface
- tests

## Recommended Build Order

Write the project in this order. Do not start with `verifier.py`. Start with storage and one image-to-embedding path first.

### Step 1: Choose the recognition backend

Decide how you will generate face embeddings.

Recommended options:
- `face_recognition`: easiest first version
- `insightface`: better quality, more setup

Current dependencies in `face_access_app\pyproject.toml` only give you image loading and array math. `opencv-python` and `numpy` alone are not enough for reliable face recognition.

Before writing logic, update:
- `D:\python projects\ForGF\face_access_app\pyproject.toml`

Add the library you choose there.

### Step 2: Implement storage first

File:
- `D:\python projects\ForGF\face_access_app\storage.py`

Purpose:
- save one enrolled reference embedding
- load it later for verification
- optionally store metadata such as label, source image path, and threshold

Implement these responsibilities:
- choose a file location for saved data
- save a `numpy` embedding array
- save metadata
- load both back
- raise clear errors if the saved file does not exist or is invalid

A simple first version can use:
- one `.npz` file for embedding plus metadata
- or one `.npy` file and one `.json` file

Suggested first functions:

```python
def save_reference(embedding, label, output_path, source_image_path, threshold=None):
    ...

def load_reference(input_path):
    ...
```

Keep this module free of face-model logic. It should only save and load data.

### Step 3: Build image loading and embedding extraction

You can place helper functions in either:
- `D:\python projects\ForGF\face_access_app\enroll.py`
- or a new helper module if you decide to add one later

Responsibilities:
- load an image from disk
- detect faces
- reject images with zero faces
- reject images with more than one face for the first version
- generate one embedding vector

Suggested helper flow:

```python
def load_image(image_path):
    ...

def extract_single_face_embedding(image_path):
    ...
```

Your first goal here is not a polished CLI. Your first goal is:
- input image path
- output one embedding vector

Test this directly with:
- `D:\python projects\ForGF\data\photo_2026-04-25_13-00-12.jpg`

### Step 4: Implement enrollment

File:
- `D:\python projects\ForGF\face_access_app\enroll.py`

Purpose:
- take a reference image
- extract one face embedding
- save it through `storage.py`

Suggested enrollment flow:
1. accept image path and label
2. load image
3. detect exactly one face
4. generate embedding
5. save reference embedding
6. print or return where it was saved

Suggested first function:

```python
def enroll_reference(image_path, label, output_path):
    ...
```

Add clear failures for:
- file not found
- unreadable image
- no face found
- multiple faces found

### Step 5: Implement verification

File:
- `D:\python projects\ForGF\face_access_app\verifier.py`

Purpose:
- compare a candidate image against the enrolled reference

Suggested verification flow:
1. load saved reference embedding from `storage.py`
2. load candidate image
3. detect exactly one face
4. generate candidate embedding
5. compute distance between embeddings
6. compare distance to a threshold
7. return match result, distance, and threshold

Suggested first functions:

```python
def compare_embeddings(reference_embedding, candidate_embedding):
    ...

def verify_image(image_path, reference_path, threshold):
    ...
```

Common distance choices:
- cosine distance
- Euclidean distance

Pick one and keep it consistent.

### Step 6: Add a minimal CLI

You can keep this inside the same files for the first version.

Suggested commands:
- enrollment command
- verification command

Example shape:

```text
python enroll.py --image <path> --label <name> --out <reference file>
python verifier.py --image <path> --reference <reference file> --threshold <value>
```

If you want a cleaner structure later, move CLI parsing into a separate `main.py`, but that is optional for the first pass.

### Step 7: Test manually before adding automated tests

Manual checks:
1. enroll from the sample image
2. verify the same image and confirm it matches
3. verify a different image and confirm it fails or produces a larger distance
4. run failure cases:
   - bad path
   - image with no face
   - image with multiple faces

## Suggested File Responsibilities

### `D:\python projects\ForGF\face_access_app\storage.py`

Write only persistence code here:
- save embedding
- load embedding
- save small metadata
- validate saved data

### `D:\python projects\ForGF\face_access_app\enroll.py`

Write enrollment code here:
- parse input
- load image
- extract reference embedding
- call `storage.py`

### `D:\python projects\ForGF\face_access_app\verifier.py`

Write verification code here:
- load saved reference
- extract candidate embedding
- compare vectors
- return decision

## First Milestone

Your first working milestone should be very small:
- enroll one person from one image
- save one reference embedding locally
- verify one candidate image against that reference

Do not add webcam support, multiple users, or UI yet. Those are second-phase features.

## Optional Next Improvements

After the first milestone works, then add:
- a shared helper module for image and embedding code
- automated tests
- configurable thresholds
- support for multiple enrolled identities
- webcam or live camera input
- logging

## Practical Advice

- Keep version one strict: exactly one face per image.
- Return explicit error messages instead of silent failures.
- Save raw distances during verification so you can tune the threshold later.
- Do not over-design storage yet. One saved reference file is enough for the first version.

## Repo Note

The duplicate file `D:\python projects\ForGF\face_access_app\README.md` was removed so this root README stays the single source of truth.
