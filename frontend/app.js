const startButton = document.querySelector("#start-button");
const terminalPanel = document.querySelector("#terminal-panel");
const STEP_INTERVAL_MS = 640;

const bootSteps = [
  "opening a quiet little sky...",
  "threading soft starlight around the door...",
  "warming the camera glow...",
  "listening for one gentle hello...",
  "ready. the secret path is open...",
];

function renderTerminalLine(text, index) {
  const line = document.createElement("p");
  line.className = "terminal-line";
  line.textContent = `> ${text}`;
  line.style.animationDelay = `${index * 40}ms`;
  terminalPanel.appendChild(line);
}

if (startButton) {
  startButton.addEventListener("click", () => {
    startButton.disabled = true;
    startButton.textContent = "Initializing";
    terminalPanel.replaceChildren();

    bootSteps.forEach((step, index) => {
      window.setTimeout(() => {
        renderTerminalLine(step, index);
      }, index * STEP_INTERVAL_MS);
    });

    window.setTimeout(() => {
      window.location.href = "./camera.html";
    }, bootSteps.length * STEP_INTERVAL_MS + 520);
  });
}
