# Frontend TODO

This file tracks what is still left before the frontend feels complete and shippable.

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

## Remaining Work

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
