const VERIFY_INTERVAL_MS = 900;
const REQUIRED_MATCH_STREAK = 3;
const REQUIRED_UNKNOWN_STREAK = 2;
const CAPTURE_MAX_WIDTH = 720;

const screens = {
  intro: document.querySelector("#intro-screen"),
  camera: document.querySelector("#camera-screen"),
  blocked: document.querySelector("#blocked-screen"),
  wishes: document.querySelector("#wishes-screen"),
};

const elements = {
  startButton: document.querySelector("#start-button"),
  stopButton: document.querySelector("#stop-button"),
  retryButton: document.querySelector("#retry-button"),
  againButton: document.querySelector("#again-button"),
  video: document.querySelector("#camera-video"),
  canvas: document.querySelector("#capture-canvas"),
  cameraStage: document.querySelector(".camera-stage"),
  statusChip: document.querySelector("#status-chip"),
  statusMessage: document.querySelector("#status-message"),
  blockedMessage: document.querySelector("#blocked-message"),
  stabilityDots: Array.from(document.querySelectorAll(".stability-dot")),
};

const state = {
  stream: null,
  pollTimer: null,
  isVerifying: false,
  matchStreak: 0,
  unknownStreak: 0,
  currentScreen: "intro",
};

function getBackendBaseUrl() {
  const params = new URLSearchParams(window.location.search);
  const queryBackend = params.get("backend");

  if (queryBackend) {
    window.localStorage.setItem("forgfBackendUrl", queryBackend.replace(/\/$/, ""));
    return queryBackend.replace(/\/$/, "");
  }

  const storedBackend = window.localStorage.getItem("forgfBackendUrl");
  if (storedBackend) {
    return storedBackend.replace(/\/$/, "");
  }

  const hostname = window.location.hostname || "127.0.0.1";
  return `http://${hostname}:8000`;
}

const BACKEND_BASE_URL = getBackendBaseUrl();

function showScreen(name) {
  Object.entries(screens).forEach(([screenName, screen]) => {
    screen.classList.toggle("is-active", screenName === name);
  });
  state.currentScreen = name;
}

function setVerificationState(status, message, chipLabel) {
  elements.cameraStage.dataset.verificationState = status;
  elements.statusMessage.textContent = message;
  elements.statusChip.textContent = chipLabel;
}

function resetStability() {
  state.matchStreak = 0;
  state.unknownStreak = 0;
  elements.stabilityDots.forEach((dot) => dot.classList.remove("is-filled"));
}

function paintStability() {
  elements.stabilityDots.forEach((dot, index) => {
    dot.classList.toggle("is-filled", index < state.matchStreak);
  });
}

function stopPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  state.isVerifying = false;
}

function stopCamera() {
  stopPolling();

  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }

  elements.video.srcObject = null;
  resetStability();
}

function blockAccess(message) {
  stopCamera();
  elements.blockedMessage.textContent = message;
  showScreen("blocked");
}

async function startCamera() {
  resetStability();
  showScreen("camera");
  setVerificationState("idle", "Opening the camera.", "opening");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    blockAccess("This browser cannot open the camera here.");
    return;
  }

  try {
    state.stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: "user",
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
    });

    elements.video.srcObject = state.stream;
    await elements.video.play();
    setVerificationState("idle", "Stay there for a second.", "looking");
    startPolling();
  } catch (error) {
    const denied = error && (error.name === "NotAllowedError" || error.name === "PermissionDeniedError");
    blockAccess(denied ? "The camera permission was blocked." : "The camera could not be opened.");
  }
}

function startPolling() {
  stopPolling();
  verifyCurrentFrame();
  state.pollTimer = window.setInterval(verifyCurrentFrame, VERIFY_INTERVAL_MS);
}

function drawFrameToCanvas() {
  const video = elements.video;
  const videoWidth = video.videoWidth;
  const videoHeight = video.videoHeight;

  if (!videoWidth || !videoHeight) {
    return false;
  }

  const scale = Math.min(1, CAPTURE_MAX_WIDTH / videoWidth);
  const width = Math.max(1, Math.round(videoWidth * scale));
  const height = Math.max(1, Math.round(videoHeight * scale));
  const canvas = elements.canvas;
  const context = canvas.getContext("2d", { alpha: false });

  canvas.width = width;
  canvas.height = height;
  context.drawImage(video, 0, 0, width, height);
  return true;
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob);
      } else {
        reject(new Error("Frame capture failed."));
      }
    }, "image/jpeg", 0.82);
  });
}

async function verifyCurrentFrame() {
  if (state.isVerifying || state.currentScreen !== "camera") {
    return;
  }

  if (!drawFrameToCanvas()) {
    return;
  }

  state.isVerifying = true;

  try {
    const blob = await canvasToBlob(elements.canvas);
    const formData = new FormData();
    formData.append("image", blob, "camera-frame.jpg");

    const response = await fetch(`${BACKEND_BASE_URL}/verify`, {
      method: "POST",
      body: formData,
    });

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const message = payload && payload.error ? payload.error.message : "Verification is not available.";
      throw new Error(message);
    }

    handleVerificationResult(payload);
  } catch (error) {
    resetStability();
    setVerificationState(
      "idle",
      error && error.message ? error.message : "Something did not work. Try again.",
      "waiting",
    );
  } finally {
    state.isVerifying = false;
  }
}

function handleVerificationResult(result) {
  const status = result && result.status ? result.status : "unknown";

  if (status === "match" && result.access_granted) {
    state.matchStreak = Math.min(REQUIRED_MATCH_STREAK, state.matchStreak + 1);
    state.unknownStreak = 0;
    paintStability();
    setVerificationState(
      "match",
      state.matchStreak >= REQUIRED_MATCH_STREAK ? "There you are." : "Yes, stay there.",
      `${state.matchStreak}/${REQUIRED_MATCH_STREAK}`,
    );

    if (state.matchStreak >= REQUIRED_MATCH_STREAK) {
      window.setTimeout(() => {
        stopCamera();
        showScreen("wishes");
      }, 420);
    }
    return;
  }

  if (status === "unknown") {
    state.matchStreak = 0;
    state.unknownStreak += 1;
    paintStability();
    setVerificationState("unknown", result.message || "I could not tell it was you.", "not yet");

    if (state.unknownStreak >= REQUIRED_UNKNOWN_STREAK) {
      blockAccess(result.message || "I could not tell it was you from this frame.");
    }
    return;
  }

  state.matchStreak = 0;
  state.unknownStreak = 0;
  paintStability();

  if (status === "multiple_faces") {
    setVerificationState("multiple_faces", result.message || "Only your face should be in the frame.", "one face");
    return;
  }

  if (status === "no_face") {
    setVerificationState("no_face", result.message || "I cannot see you yet.", "searching");
    return;
  }

  setVerificationState("idle", result.message || "Stay still for one more second.", "waiting");
}

elements.startButton.addEventListener("click", startCamera);

elements.stopButton.addEventListener("click", () => {
  stopCamera();
  showScreen("intro");
});

elements.retryButton.addEventListener("click", startCamera);

elements.againButton.addEventListener("click", () => {
  stopCamera();
  resetStability();
  showScreen("intro");
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopPolling();
    return;
  }

  if (state.currentScreen === "camera" && state.stream) {
    startPolling();
  }
});
