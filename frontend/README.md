# Frontend Plan

This folder will contain the real web app for the ForGF project.

The frontend is not a generic dashboard. It is a private, mobile-first face verification flow that should feel intimate, cinematic, and intentional.

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

## Frontend TODO

### Foundation

- Choose the frontend stack.
- Set up the project inside this folder.
- Define color tokens, spacing tokens, and typography tokens.
- Add the chosen font pair.
- Create a global page background and visual theme variables.

### App Structure

- Create routes or screen-state flow for:
  - intro
  - camera
  - blocked
  - wishes
- Define a shared app shell for mobile-first layouts.
- Decide whether the wishes page is one screen or a sequence.

### Camera Flow

- Add camera permission request after a user tap.
- Show the local video preview.
- Add a hidden canvas or equivalent frame-capture path.
- Capture snapshots on an interval.
- Send frames to `POST /verify`.
- Prevent overlapping verify requests.
- Handle camera denial cleanly.
- Handle backend failure cleanly.

### Verification UX

- Map backend `status` values to UI states.
- Show clear messages for:
  - no face
  - multiple faces
  - unknown face
  - matching in progress
- Add frontend stable-match logic before redirect.
- Tune the polling cadence so the UI feels responsive without spamming the backend.

### Visual Details

- Design the cinematic corner markers.
- Add subtle entrance transitions.
- Add success transition from camera screen to wishes screen.
- Keep the blocked screen visually restrained.
- Ensure the interface feels intentional on both phone and iPad.

### Real Content

- Write the actual intro copy.
- Write the actual blocked/failure copy.
- Define the real wishes-page content.
- Decide whether the wishes experience is static, sequential, or interactive.

### Device Testing

- Test on phone browser.
- Test on tablet browser.
- Test camera permission behavior.
- Test portrait and landscape layouts.
- Test lower-light conditions.

## Out Of Scope For V1

- multi-user support
- account system
- public sign-up
- heavy analytics
- continuous video streaming
- overly complex animations

## Short Summary

This frontend should feel like a private cinematic verification gate, not a normal app. The core job is to open the camera gracefully, verify the face through backend snapshot polling, require stable success, and then reveal the wishes page with stronger visual emotion.
