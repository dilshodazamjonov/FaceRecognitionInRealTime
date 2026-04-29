# Frontend Plan

This folder will contain the real web app for the ForGF project.

The frontend is not a generic dashboard. It is a private, mobile-first face verification flow that should feel intimate, cinematic, and intentional.

## Current Implementation

The current frontend is a dependency-free static browser app:

- `index.html`: screen structure
- `styles.css`: visual system and responsive camera layout
- `app.js`: camera access, snapshot polling, backend verification, and stable-match logic

Run it from this folder:

```powershell
python -m http.server 3000
```

Then open:

```text
http://127.0.0.1:3000
```

The backend should be running at:

```text
http://127.0.0.1:8000
```

To point the frontend at a different backend for testing:

```text
http://127.0.0.1:3000?backend=http://127.0.0.1:8001
```

## Locked Product Idea

- The browser camera is the real product path.
- The frontend is primarily for phone and iPad use.
- The user flow is short:
  1. intro
  2. camera permission
  3. live verification
  4. success reveal or blocked result
- A successful match unlocks the wishes page.
- A non-match must stay blocked.
- False accepts are worse than false rejects, so the UX should respect a strict verification flow.

## Locked Visual Direction

- Warm cinematic mood, not a cold tech product.
- Editorial feeling, not an admin panel.
- Minimal UI around the camera.
- Soft motion and reveal-based transitions.
- Corner markers around the camera target area, inspired by cinema focus framing.
- No noisy HUD, no sci-fi overload, no generic startup landing page look.

## Visual System

### Palette

- Background ivory
- Warm sand
- Rose beige
- Deep espresso
- Muted red accent
- Reserved green-gold success tone

The palette should stay warm, soft, and slightly romantic. Avoid harsh neon colors, purple-heavy gradients, and default blue app styling.

### Typography

- Expressive serif for headings
- Clean sans-serif for interface text

The type should feel elegant and deliberate. The wishes page should lean more editorial than the verification screen.

### Camera Framing

- Large live camera preview
- Four corner brackets instead of a full border box
- Subtle vignette or soft overlay
- Calm instruction text
- Small status chip or line
- Optional lightweight match-stability indicator

## UX Direction

The camera should not try to auto-open on first page load.

Preferred flow:

1. Show a clean intro screen with one strong headline and one action button.
2. Request camera permission only after user interaction.
3. Open the live preview screen.
4. Capture frames on an interval and send them to the backend.
5. Use a short client-side consecutive-match rule before redirecting.
6. Transition into the wishes page only after stable success.

## Backend Contract The Frontend Must Use

The backend already provides a usable verification response.

Important verify response fields:

- `status`
- `matched`
- `access_granted`
- `message`
- `next_screen`
- `should_redirect`
- `boxes`
- `distance`
- `threshold`

Expected state handling:

- `match`
- `unknown`
- `no_face`
- `multiple_faces`

Important product note:

- the backend currently returns a successful match per frame
- the frontend should still require a short streak of successful frames before navigation

## Screen Plan

### 1. Intro

Purpose:

- set tone
- avoid immediate permission shock
- give the user one deliberate entry point

Should include:

- title
- short line of guidance
- start button

### 2. Camera Verification

Purpose:

- request permission
- show live preview
- guide the face into frame
- communicate status clearly

Should include:

- full camera preview
- corner-frame overlay
- instruction text
- lightweight verification status
- stable-success progress indicator

### 3. Failure / Blocked

Purpose:

- show that access is not granted
- keep the message simple and restrained

Should include:

- short blocked message
- retry path

### 4. Wishes

Purpose:

- reward successful verification with a more emotional reveal

Should include:

- richer typography
- stronger composition
- softer motion
- actual content reveal

## Current Status

### Done

- Static frontend app exists in `frontend/`.
- Intro, camera, blocked, and wishes screens exist.
- Browser camera opens only after a user tap.
- Local video preview works through `getUserMedia`.
- Frame capture uses a hidden canvas.
- Snapshot polling sends frames to backend `POST /verify`.
- Verify requests are guarded so overlapping requests do not stack.
- Backend result states are mapped into the UI.
- Frontend requires a stable match streak before opening the wishes screen.
- Camera denial and backend failures have basic user-facing handling.
- Camera frame is resized and centered instead of full-bleed.
- Cinematic corner markers exist inside the camera frame.
- Generated SVG botanical decoration exists around the camera page.
- Responsive CSS exists for phone, iPad, and desktop.

## Remaining TODO

### Product Content

- Replace placeholder wishes-page text with the real message.
- Decide whether the wishes page is one letter, multiple wishes, a timeline, or a small gallery.
- Write final blocked/failure copy in the exact tone you want.
- Decide whether the intro should stay as one screen or include a small pre-reveal animation.

### Visual Polish

- Fine-tune the SVG flowers after checking on a real iPhone 13.
- Fine-tune the SVG flowers after checking on a real iPad.
- Check whether the camera frame should be taller or wider on iPad landscape.
- Add a more graceful success transition from camera to wishes.
- Add a softer failed-match transition before the blocked screen.
- Decide whether the wishes page should also use flowers or a different visual mood.
- Replace fallback system fonts with real bundled or hosted fonts if desired.

### Camera And Verification

- Test camera permission behavior on iPhone Safari.
- Test camera permission behavior on iPad Safari.
- Test camera behavior on desktop Chrome or Edge.
- Test whether the current `900ms` polling interval feels too slow or too heavy.
- Tune `REQUIRED_MATCH_STREAK` from real device behavior.
- Tune `REQUIRED_UNKNOWN_STREAK` so it does not block too aggressively.
- Decide whether `unknown` should immediately block or allow more retries.
- Add a visible backend-offline state if the API is not running.

### Responsive Testing

- Verify iPhone 13 portrait layout.
- Verify iPhone 13 landscape layout, or intentionally block landscape if it looks bad.
- Verify iPad portrait layout.
- Verify iPad landscape layout.
- Verify desktop layout at common widths:
  - 1366px
  - 1440px
  - 1920px
- Check safe-area spacing around iPhone notch and bottom browser controls.

### Backend Integration

- Confirm `FORGF_ALLOWED_ORIGINS` includes the real frontend origin used for phone/iPad testing.
- Test frontend against backend on localhost.
- Test frontend against backend over LAN from a phone.
- Decide the real backend URL strategy for non-local use.
- Decide whether the frontend should show reference-missing errors differently.

### Security And Shipping

- Do not expose the backend publicly until HTTPS is available.
- Replace the default admin token before real use.
- Keep `python/.env` untracked before adding real secrets.
- Add rate limiting or another abuse guard before network exposure.
- Keep enrollment protected or CLI-only for V1.

### Optional Later

- Add liveness or anti-photo-spoofing checks.
- Add a small wishes sequence after unlock.
- Add optional music or sound only after user interaction.
- Add an admin-friendly test mode that does not require a real face match.
- Convert the static app into a Vite/React app only if the interaction grows beyond simple screens.

## Out Of Scope For V1

- multi-user support
- account system
- public sign-up
- heavy analytics
- continuous video streaming
- overly complex animations

## Short Summary

This frontend should feel like a private cinematic verification gate, not a normal app. The core job is to open the camera gracefully, verify the face through backend snapshot polling, require stable success, and then reveal the wishes page with stronger visual emotion.
