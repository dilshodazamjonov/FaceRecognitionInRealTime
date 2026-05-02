const VERIFY_INTERVAL_MS = 900;
const CAPTURE_MAX_WIDTH = 720;
const GUIDE_TARGET_X = 0.5;
const GUIDE_TARGET_Y = 0.43;
const OUTCOME_STORAGE_KEY = "forgfLastOutcome";
const STATUS_STORAGE_KEY = "forgfLastStatus";
const FACE_FOUND_STORAGE_KEY = "forgfFaceFound";
const FACE_FOUND_MAX_AGE_MS = 10 * 60 * 1000;

const elements = {
  stopButton: document.querySelector("#stop-button"),
  continueButton: document.querySelector("#continue-button"),
  video: document.querySelector("#camera-video"),
  canvas: document.querySelector("#capture-canvas"),
  cameraStage: document.querySelector(".camera-stage"),
  faceHintBox: document.querySelector("#face-hint-box"),
  statusChip: document.querySelector("#status-chip"),
  cameraKicker: document.querySelector("#camera-kicker"),
  statusMessage: document.querySelector("#status-message"),
  backendState: document.querySelector("#backend-state"),
  lastResult: document.querySelector("#last-result"),
  stabilityDots: Array.from(document.querySelectorAll(".stability-dot")),
};

const state = {
  stream: null,
  pollTimer: null,
  activeRequest: null,
  isVerifying: false,
  passed: false,
  unlockedLabel: "",
  lastCaptureWidth: 0,
  lastCaptureHeight: 0,
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

function prettifyLabel(label) {
  if (!label) {
    return "Love";
  }

  return label
    .replace(/[_-]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function setStatusDock(stateLabel, message) {
  elements.backendState.textContent = stateLabel;
  elements.lastResult.textContent = message;

  try {
    window.sessionStorage.setItem(
      STATUS_STORAGE_KEY,
      JSON.stringify({ stateLabel, message, savedAt: Date.now() }),
    );
  } catch (_) {
    // Ignore storage failures.
  }
}

function setVerificationState(status, kicker, message, chipLabel) {
  elements.cameraStage.dataset.verificationState = status;
  elements.cameraKicker.textContent = kicker;
  elements.statusMessage.textContent = message;
  elements.statusChip.textContent = chipLabel;
}

function setFaceGuideState(guide) {
  elements.cameraStage.dataset.faceGuide = guide;
}

function setContinueEnabled(enabled, label = "") {
  state.passed = enabled;
  state.unlockedLabel = enabled ? label : "";
  elements.continueButton.disabled = !enabled;
}

function saveFaceFound(label) {
  try {
    window.sessionStorage.setItem(
      FACE_FOUND_STORAGE_KEY,
      JSON.stringify({
        label,
        savedAt: Date.now(),
      }),
    );
  } catch (_) {
    // Ignore storage failures.
  }
}

function loadFaceFound() {
  try {
    const raw = window.sessionStorage.getItem(FACE_FOUND_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw);
    if (!parsed || !parsed.savedAt || Date.now() - parsed.savedAt > FACE_FOUND_MAX_AGE_MS) {
      window.sessionStorage.removeItem(FACE_FOUND_STORAGE_KEY);
      return null;
    }

    return parsed;
  } catch (_) {
    return null;
  }
}

function clearFaceFound() {
  try {
    window.sessionStorage.removeItem(FACE_FOUND_STORAGE_KEY);
  } catch (_) {
    // Ignore storage failures.
  }
}

function saveOutcome(label) {
  try {
    window.sessionStorage.setItem(
      OUTCOME_STORAGE_KEY,
      JSON.stringify({
        type: "success",
        label,
        savedAt: Date.now(),
      }),
    );
  } catch (_) {
    // Ignore storage failures.
  }
}

function unlockContinue(label, message, statusLabel = "Face Found") {
  const normalizedLabel = label || "face found";
  state.passed = true;
  state.unlockedLabel = normalizedLabel;
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  paintStability(3);
  elements.continueButton.disabled = false;
  setVerificationState("revealed", "found a face", message, "ready");
  setStatusDock(statusLabel, message);
  saveFaceFound(normalizedLabel);
  saveOutcome(normalizedLabel);
}

function hideFaceHintBox() {
  elements.faceHintBox.classList.add("is-hidden");
  setFaceGuideState("hidden");
}

function resetStability() {
  elements.stabilityDots.forEach((dot) => dot.classList.remove("is-filled"));
}

function paintStability(filled) {
  elements.stabilityDots.forEach((dot, index) => {
    dot.classList.toggle("is-filled", index < filled);
  });
}

function stopPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  if (state.activeRequest) {
    state.activeRequest.abort();
    state.activeRequest = null;
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
}

function formatFetchError(error) {
  if (error && error.message === "Failed to fetch") {
    return `Failed to fetch from backend at ${BACKEND_BASE_URL}.`;
  }

  return error && error.message ? error.message : "Something did not work. Try again.";
}

function drawFrameToCanvas() {
  const videoWidth = elements.video.videoWidth;
  const videoHeight = elements.video.videoHeight;

  if (!videoWidth || !videoHeight) {
    return false;
  }

  const scale = Math.min(1, CAPTURE_MAX_WIDTH / videoWidth);
  const width = Math.max(1, Math.round(videoWidth * scale));
  const height = Math.max(1, Math.round(videoHeight * scale));
  const context = elements.canvas.getContext("2d", { alpha: false });

  elements.canvas.width = width;
  elements.canvas.height = height;
  state.lastCaptureWidth = width;
  state.lastCaptureHeight = height;
  context.drawImage(elements.video, 0, 0, width, height);
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

function getPrimaryBox(result) {
  return result && Array.isArray(result.boxes) && result.boxes.length ? result.boxes[0] : null;
}

function getBoxMetrics(box) {
  if (!box || state.lastCaptureWidth <= 0 || state.lastCaptureHeight <= 0) {
    return null;
  }

  const [x1, y1, x2, y2] = box;
  const width = Math.max(0, x2 - x1);
  const height = Math.max(0, y2 - y1);
  if (!width || !height) {
    return null;
  }

  const leftRatio = Math.max(0, Math.min(1, (state.lastCaptureWidth - x2) / state.lastCaptureWidth));
  const topRatio = Math.max(0, Math.min(1, y1 / state.lastCaptureHeight));
  const widthRatio = Math.max(0, Math.min(1, width / state.lastCaptureWidth));
  const heightRatio = Math.max(0, Math.min(1, height / state.lastCaptureHeight));

  return {
    leftPercent: leftRatio * 100,
    topPercent: topRatio * 100,
    widthPercent: widthRatio * 100,
    heightPercent: heightRatio * 100,
    centerX: leftRatio + widthRatio / 2,
    centerY: topRatio + heightRatio / 2,
    sizeRatio: Math.max(widthRatio, heightRatio),
  };
}

function paintFaceHintBox(box) {
  const metrics = getBoxMetrics(box);
  if (!metrics) {
    hideFaceHintBox();
    return null;
  }

  elements.faceHintBox.style.left = `${metrics.leftPercent}%`;
  elements.faceHintBox.style.top = `${metrics.topPercent}%`;
  elements.faceHintBox.style.width = `${metrics.widthPercent}%`;
  elements.faceHintBox.style.height = `${metrics.heightPercent}%`;
  elements.faceHintBox.classList.remove("is-hidden");
  return metrics;
}

function deriveGuide(metrics) {
  if (!metrics) {
    return "hidden";
  }

  if (metrics.sizeRatio < 0.24) {
    return "too_far";
  }

  if (metrics.sizeRatio > 0.68) {
    return "too_close";
  }

  if (
    Math.abs(metrics.centerX - GUIDE_TARGET_X) > 0.16 ||
    Math.abs(metrics.centerY - GUIDE_TARGET_Y) > 0.18
  ) {
    return "off_center";
  }

  return "aligned";
}

function guidanceCopy(status, guide) {
  if (status === "multiple_faces") {
    return "I found more than one person. Keep it just one face for me.";
  }

  if (status === "no_face") {
    return "I can't see anyone yet. Come into the little frame for me.";
  }

  if (guide === "too_far") {
    return "Come a little closer.";
  }

  if (guide === "too_close") {
    return "Ease back just a touch.";
  }

  if (guide === "off_center") {
    return "Center your face in the little frame.";
  }

  if (status === "unknown") {
    return "I found a person, but it is not the saved match yet.";
  }

  return "Stay there for a second.";
}

function applyFaceGuide(result) {
  const status = result && result.status ? result.status : "unknown";
  const primaryBox = getPrimaryBox(result);

  if (status === "no_face") {
    hideFaceHintBox();
    setFaceGuideState("hidden");
    return guidanceCopy(status, "hidden");
  }

  const metrics = paintFaceHintBox(primaryBox);
  const guide = status === "multiple_faces" ? "multiple" : deriveGuide(metrics);
  setFaceGuideState(status === "unknown" && guide === "aligned" ? "mismatch" : guide);
  return guidanceCopy(status, guide);
}

function summarizeResult(result) {
  const label = prettifyLabel(result && result.label ? result.label : "");

  if (result && result.status === "match" && result.access_granted) {
    return `Backend connected. Face found for ${label}.`;
  }

  if (result && result.status === "unknown") {
    return "Backend connected. Face found.";
  }

  if (result && result.status === "multiple_faces") {
    return "Backend connected. More than one face was seen.";
  }

  if (result && result.status === "no_face") {
    return "Backend connected. No face was detected.";
  }

  return "Backend connected. A verify result was received.";
}

function handleVerificationResult(result) {
  if (state.passed) {
    return;
  }

  const status = result && result.status ? result.status : "unknown";
  const guidance = applyFaceGuide(result);
  const matchedLabel = result && result.label ? result.label : "";

  if (status === "match" && result.access_granted) {
    const displayName = prettifyLabel(matchedLabel);
    hideFaceHintBox();
    unlockContinue(matchedLabel, `${displayName}, you can continue whenever you want.`);
    return;
  }

  if (status === "unknown") {
    hideFaceHintBox();
    unlockContinue("face found", "Face found. You can continue whenever you want.");
    return;
  }

  setContinueEnabled(false);
  resetStability();

  if (status === "multiple_faces") {
    setVerificationState("multiple_faces", "too many people", guidance, "one face");
    return;
  }

  if (status === "no_face") {
    setVerificationState("no_face", "no one yet", guidance, "searching");
    return;
  }

  setVerificationState("idle", "still looking", guidance, "waiting");
}

async function verifyCurrentFrame() {
  if (state.isVerifying || state.passed) {
    return;
  }

  if (!drawFrameToCanvas()) {
    return;
  }

  state.isVerifying = true;
  const controller = new AbortController();
  state.activeRequest = controller;

  try {
    const blob = await canvasToBlob(elements.canvas);
    const formData = new FormData();
    formData.append("image", blob, "camera-frame.jpg");

    const response = await fetch(`${BACKEND_BASE_URL}/verify`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    if (state.passed) {
      return;
    }

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const message = payload && payload.error ? payload.error.message : "Verification is not available.";
      throw new Error(message);
    }

    setStatusDock("Backend Connected", summarizeResult(payload));
    handleVerificationResult(payload);
  } catch (error) {
    if (error && error.name === "AbortError") {
      return;
    }

    if (state.passed) {
      return;
    }

    const errorMessage = formatFetchError(error);
    resetStability();
    hideFaceHintBox();
    setContinueEnabled(false);
    setStatusDock("Backend Error", errorMessage);
    setVerificationState("idle", "still here", errorMessage, "waiting");
  } finally {
    if (state.activeRequest === controller) {
      state.activeRequest = null;
    }
    state.isVerifying = false;
  }
}

function startPolling() {
  stopPolling();
  verifyCurrentFrame();
  state.pollTimer = window.setInterval(verifyCurrentFrame, VERIFY_INTERVAL_MS);
}

async function startCamera() {
  const savedFace = loadFaceFound();
  if (!savedFace) {
    setContinueEnabled(false);
  }
  resetStability();
  hideFaceHintBox();
  setVerificationState("idle", "just checking", "Opening the camera.", "opening");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setVerificationState("idle", "camera unavailable", "This browser cannot open the camera here.", "blocked");
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

    if (savedFace) {
      unlockContinue(
        savedFace.label,
        "Face found. You can continue whenever you want.",
      );
      return;
    }

    setVerificationState("idle", "just checking", "Stay there for a second.", "looking");
    startPolling();
  } catch (error) {
    const denied = error && (error.name === "NotAllowedError" || error.name === "PermissionDeniedError");
    setVerificationState(
      "idle",
      denied ? "camera blocked" : "camera unavailable",
      denied ? "The camera permission was blocked." : "The camera could not be opened.",
      "blocked",
    );
  }
}

elements.stopButton.addEventListener("click", () => {
  clearFaceFound();
  stopCamera();
  window.location.href = "./index.html";
});

elements.continueButton.addEventListener("click", () => {
  if (!state.passed || !state.unlockedLabel) {
    return;
  }

  saveOutcome(state.unlockedLabel);
  window.location.href = "./wishes.html";
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopPolling();
    return;
  }

  if (state.stream && !state.passed) {
    startPolling();
  }
});

window.addEventListener("pagehide", stopCamera);

startCamera();
