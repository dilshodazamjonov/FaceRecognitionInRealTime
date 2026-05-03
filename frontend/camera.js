const VERIFY_INTERVAL_MS = 900;
const CAPTURE_MAX_WIDTH = 320;
const CAPTURE_JPEG_QUALITY = 0.58;
const GUIDE_TARGET_X = 0.5;
const GUIDE_TARGET_Y = 0.43;
const OUTCOME_STORAGE_KEY = "forgfLastOutcome";
const FRAME_VERIFY_MIN_GAP_MS = 900;
const VERIFY_REQUEST_TIMEOUT_MS = 60000;

const elements = {
  statusDock: document.querySelector("#status-dock"),
  statusProgress: document.querySelector(".status-dock-progress"),
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
  imageCapture: null,
  pollTimer: null,
  activeRequest: null,
  isVerifying: false,
  passed: false,
  unlockedLabel: "",
  lastCaptureWidth: 0,
  lastCaptureHeight: 0,
  toastTimer: null,
  lastToastKey: "",
  unlockTimer: null,
  startupTimers: [],
  videoFrameLoopRunning: false,
  lastVerifyStartedAt: 0,
  lastFrameWaitNoticeAt: 0,
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

function toastTone(stateLabel) {
  const normalized = stateLabel.toLowerCase();
  if (normalized.includes("found") || normalized.includes("passed")) {
    return "success";
  }
  if (
    normalized.includes("error") ||
    normalized.includes("blocked") ||
    normalized.includes("too many") ||
    normalized.includes("no face")
  ) {
    return "failure";
  }
  return "info";
}

function setStatusDock(stateLabel, message, options = {}) {
  const key = `${stateLabel}:${message}`;
  if (!options.force && key === state.lastToastKey && elements.statusDock.classList.contains("is-visible")) {
    return;
  }

  state.lastToastKey = key;
  elements.backendState.textContent = stateLabel;
  elements.lastResult.textContent = message;
  elements.statusDock.dataset.tone = toastTone(stateLabel);
  elements.statusDock.classList.remove("is-visible");
  elements.statusProgress.style.animation = "none";
  void elements.statusDock.offsetWidth;
  void elements.statusProgress.offsetWidth;
  elements.statusProgress.style.animation = "";

  window.requestAnimationFrame(() => {
    elements.statusDock.classList.add("is-visible");
  });

  if (state.toastTimer) {
    window.clearTimeout(state.toastTimer);
  }

  state.toastTimer = window.setTimeout(() => {
    elements.statusDock.classList.remove("is-visible");
    state.toastTimer = null;
  }, 3000);

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

function getVideoTrack() {
  return state.stream ? state.stream.getVideoTracks()[0] : null;
}

function setContinueEnabled(enabled, label = "") {
  state.passed = enabled;
  state.unlockedLabel = enabled ? label : "";
  elements.continueButton.disabled = !enabled;
  if (!enabled) {
    delete elements.cameraStage.dataset.skyOpen;
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

function unlockContinue(label, statusLabel = "Face Found") {
  const normalizedLabel = label || "face found";
  state.passed = true;
  state.unlockedLabel = normalizedLabel;
  if (state.unlockTimer) {
    window.clearTimeout(state.unlockTimer);
    state.unlockTimer = null;
  }
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  state.videoFrameLoopRunning = false;
  paintStability(3);
  elements.continueButton.disabled = true;
  elements.cameraStage.dataset.skyOpen = "true";
  setVerificationState("revealed", "confirmed", "Ready.", "ready");
  setStatusDock(statusLabel, "Face found. Continue is ready.", { force: true });
  saveOutcome(normalizedLabel);

  state.unlockTimer = window.setTimeout(() => {
    elements.continueButton.disabled = false;
    state.unlockTimer = null;
  }, 850);
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
  state.videoFrameLoopRunning = false;
}

function clearStartupTimers() {
  state.startupTimers.forEach((timer) => window.clearTimeout(timer));
  state.startupTimers = [];
}

function stopCamera() {
  stopPolling();
  clearStartupTimers();

  if (state.unlockTimer) {
    window.clearTimeout(state.unlockTimer);
    state.unlockTimer = null;
  }

  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }

  state.imageCapture = null;
  elements.video.srcObject = null;
}

function formatFetchError(error) {
  if (error && error.message === "Failed to fetch") {
    return `Failed to fetch from backend at ${BACKEND_BASE_URL}.`;
  }

  return error && error.message ? error.message : "Something did not work. Try again.";
}

function drawVideoFrameToCanvas() {
  const trackSettings = getVideoTrack() ? getVideoTrack().getSettings() : {};
  const videoWidth = elements.video.videoWidth || trackSettings.width || 0;
  const videoHeight = elements.video.videoHeight || trackSettings.height || 0;

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
  try {
    context.drawImage(elements.video, 0, 0, width, height);
    return true;
  } catch (_) {
    return false;
  }
}

function withTimeout(promise, timeoutMs) {
  let timeout = null;
  const timeoutPromise = new Promise((resolve) => {
    timeout = window.setTimeout(() => resolve(null), timeoutMs);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => {
    if (timeout) {
      window.clearTimeout(timeout);
    }
  });
}

async function drawCameraTrackToCanvas() {
  if (!state.imageCapture) {
    return false;
  }

  let frame = null;

  try {
    frame = await withTimeout(state.imageCapture.grabFrame(), 260);
    if (!frame) {
      return false;
    }
    const sourceWidth = frame.width;
    const sourceHeight = frame.height;

    if (!sourceWidth || !sourceHeight) {
      return false;
    }

    const scale = Math.min(1, CAPTURE_MAX_WIDTH / sourceWidth);
    const width = Math.max(1, Math.round(sourceWidth * scale));
    const height = Math.max(1, Math.round(sourceHeight * scale));
    const context = elements.canvas.getContext("2d", { alpha: false });

    elements.canvas.width = width;
    elements.canvas.height = height;
    state.lastCaptureWidth = width;
    state.lastCaptureHeight = height;
    context.drawImage(frame, 0, 0, width, height);
    return true;
  } catch (_) {
    return false;
  } finally {
    if (frame && typeof frame.close === "function") {
      frame.close();
    }
  }
}

async function drawFrameToCanvas() {
  if (drawVideoFrameToCanvas()) {
    return true;
  }

  return drawCameraTrackToCanvas();
}

function canvasToImageData(canvas) {
  try {
    return canvas.toDataURL("image/jpeg", CAPTURE_JPEG_QUALITY);
  } catch (_) {
    return null;
  }
}

function postVerifyFrame(imageData) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    state.activeRequest = xhr;

    xhr.open("POST", `${BACKEND_BASE_URL}/verify-frame-text`, true);
    xhr.setRequestHeader("Content-Type", "text/plain;charset=UTF-8");
    xhr.responseType = "json";
    xhr.timeout = VERIFY_REQUEST_TIMEOUT_MS;

    xhr.onload = () => {
      if (state.activeRequest === xhr) {
        state.activeRequest = null;
      }

      const payload = xhr.response || null;
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(payload);
        return;
      }

      const message = payload && payload.error ? payload.error.message : "Verification is not available.";
      reject(new Error(message));
    };

    xhr.onerror = () => {
      if (state.activeRequest === xhr) {
        state.activeRequest = null;
      }
      reject(new Error(`Failed to fetch from backend at ${BACKEND_BASE_URL}.`));
    };

    xhr.ontimeout = () => {
      if (state.activeRequest === xhr) {
        state.activeRequest = null;
      }
      reject(new Error("Backend request timed out."));
    };

    xhr.onabort = () => {
      if (state.activeRequest === xhr) {
        state.activeRequest = null;
      }
      reject(new DOMException("Request aborted.", "AbortError"));
    };

    xhr.send(imageData);
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
    return "One face only.";
  }

  if (status === "no_face") {
    return "No face.";
  }

  if (guide === "too_far") {
    return "Closer.";
  }

  if (guide === "too_close") {
    return "Back a little.";
  }

  if (guide === "off_center") {
    return "Center up.";
  }

  if (status === "unknown") {
    return "Face found.";
  }

  return "Hold still.";
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

function handleVerificationResult(result) {
  if (state.passed) {
    return;
  }

  const status = result && result.status ? result.status : "unknown";
  const guidance = applyFaceGuide(result);
  const matchedLabel = result && result.label ? result.label : "";

  if (status === "match" && result.access_granted) {
    hideFaceHintBox();
    unlockContinue(matchedLabel);
    return;
  }

  if (status === "unknown") {
    hideFaceHintBox();
    unlockContinue("face found");
    return;
  }

  setContinueEnabled(false);
  resetStability();

  if (status === "multiple_faces") {
    setVerificationState("multiple_faces", "too many", guidance, "one face");
    setStatusDock("Too Many Faces", "Keep one person in frame.");
    return;
  }

  if (status === "no_face") {
    setVerificationState("no_face", "searching", guidance, "searching");
    setStatusDock("No Face", "No face detected.");
    return;
  }

  setVerificationState("idle", "checking", guidance, "waiting");
}

async function verifyCurrentFrame() {
  if (state.isVerifying || state.passed) {
    return;
  }

  const now = Date.now();
  if (now - state.lastVerifyStartedAt < FRAME_VERIFY_MIN_GAP_MS) {
    return;
  }

  if (!(await drawFrameToCanvas())) {
    if (now - state.lastFrameWaitNoticeAt > 1400) {
      state.lastFrameWaitNoticeAt = now;
      setVerificationState("idle", "checking", "Waiting for camera frame.", "video");
    }
    return;
  }

  state.lastVerifyStartedAt = now;
  state.isVerifying = true;
  setVerificationState("idle", "checking", "Checking with backend.", "live");

  try {
    const imageData = canvasToImageData(elements.canvas);
    if (!imageData) {
      throw new Error("Frame capture failed.");
    }

    const payload = await postVerifyFrame(imageData);

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
    setVerificationState("idle", "waiting", "Retrying.", "waiting");
  } finally {
    state.isVerifying = false;
  }
}

function startPolling() {
  if (state.pollTimer || state.passed) {
    return;
  }

  setVerificationState("idle", "checking", "Scanning.", "live");
  verifyCurrentFrame();
  state.pollTimer = window.setInterval(verifyCurrentFrame, VERIFY_INTERVAL_MS);
}

function startVideoFrameVerificationLoop() {
  if (
    state.videoFrameLoopRunning ||
    !state.stream ||
    state.passed ||
    typeof elements.video.requestVideoFrameCallback !== "function"
  ) {
    return;
  }

  state.videoFrameLoopRunning = true;

  const onFrame = () => {
    if (!state.videoFrameLoopRunning || !state.stream || state.passed) {
      state.videoFrameLoopRunning = false;
      return;
    }

    verifyCurrentFrame();
    elements.video.requestVideoFrameCallback(onFrame);
  };

  elements.video.requestVideoFrameCallback(onFrame);
}

function startVerificationLoops() {
  if (!state.stream || state.passed) {
    return;
  }

  clearStartupTimers();
  startPolling();
}

function scheduleStartupPollChecks() {
  clearStartupTimers();
  [80, 240, 520, 900, 1500, 2400].forEach((delay) => {
    state.startupTimers.push(window.setTimeout(startVerificationLoops, delay));
  });
}

function handleCameraOpenError(error) {
  const denied = error && (error.name === "NotAllowedError" || error.name === "PermissionDeniedError");
  setVerificationState(
    "idle",
    denied ? "blocked" : "unavailable",
    denied ? "Camera blocked." : "No camera.",
    "blocked",
  );
  setStatusDock(
    "Camera Error",
    denied ? "Camera permission was blocked." : "The camera could not be opened.",
    { force: true },
  );
}

async function startCamera() {
  setContinueEnabled(false);
  resetStability();
  hideFaceHintBox();
  setVerificationState("idle", "checking", "Opening.", "opening");
  setStatusDock("Connecting", "Connecting to backend.", { force: true });

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setVerificationState("idle", "blocked", "No camera.", "blocked");
    setStatusDock("Camera Error", "This browser cannot open the camera here.", { force: true });
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

    elements.video.addEventListener("loadedmetadata", startVerificationLoops);
    elements.video.addEventListener("canplay", startVerificationLoops);
    elements.video.addEventListener("playing", startVerificationLoops);
    elements.video.srcObject = state.stream;
    const [videoTrack] = state.stream.getVideoTracks();
    if (videoTrack && typeof ImageCapture === "function") {
      state.imageCapture = new ImageCapture(videoTrack);
    }
    const playPromise = elements.video.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch((error) => {
        if (!state.pollTimer) {
          handleCameraOpenError(error);
        }
      });
    }

    scheduleStartupPollChecks();
    startVerificationLoops();
  } catch (error) {
    handleCameraOpenError(error);
  }
}

elements.stopButton.addEventListener("click", () => {
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
    return;
  }

  if (state.stream && !state.passed) {
    scheduleStartupPollChecks();
    startVerificationLoops();
  }
});

window.addEventListener("pagehide", stopCamera);

startCamera();
