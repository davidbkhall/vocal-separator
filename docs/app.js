/**
 * Vocal Separator – browser client for Audioshake Tasks API
 * Flow: upload asset → create task → poll until done → show download links
 */

const API_BASE = "https://api.audioshake.ai";
const POLL_INTERVAL_MS = 4000;

const apiKeyInput = document.getElementById("apiKey");
const modelSelect = document.getElementById("model");
const formatSelect = document.getElementById("format");
const variantSelect = document.getElementById("variant");
const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const dropLabel = document.getElementById("dropLabel");
const fileNameEl = document.getElementById("fileName");
const startBtn = document.getElementById("startBtn");
const cancelBtn = document.getElementById("cancelBtn");
const progressSection = document.getElementById("progressSection");
const progressText = document.getElementById("progressText");
const progressFill = document.getElementById("progressFill");
const resultSection = document.getElementById("resultSection");
const resultIntro = document.getElementById("resultIntro");
const resultList = document.getElementById("resultList");
const corsNote = document.getElementById("corsNote");
const errorSection = document.getElementById("errorSection");
const errorText = document.getElementById("errorText");

let selectedFile = null;
let abortController = null;

function getHeaders() {
  const key = (apiKeyInput && apiKeyInput.value) ? apiKeyInput.value.trim() : "";
  return {
    "x-api-key": key,
  };
}

function showError(message) {
  errorSection.hidden = false;
  resultSection.hidden = true;
  errorText.textContent = message;
}

function hideError() {
  errorSection.hidden = true;
}

function setProgress(text, show = true) {
  progressSection.hidden = !show;
  if (show) progressText.textContent = text || "Processing…";
}

function setResult(stemLinks, baseName) {
  errorSection.hidden = true;
  progressSection.hidden = true;
  resultSection.hidden = false;
  resultIntro.textContent = stemLinks.length
    ? `Done. ${stemLinks.length} file(s) ready (from ${baseName}):`
    : "Task finished but no output files were returned.";
  resultList.innerHTML = "";
  stemLinks.forEach(({ name, link }) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = link;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = name;
    a.download = `${baseName}_${name}.${link.match(/\.([a-z0-9]+)(?:\?|$)/i)?.[1] || "wav"}`;
    li.appendChild(a);
    resultList.appendChild(li);
  });
  corsNote.hidden = stemLinks.length === 0;
}

function setBusy(busy) {
  startBtn.disabled = busy;
  cancelBtn.hidden = !busy;
  if (!busy) abortController = null;
}

async function uploadAsset(file) {
  const form = new FormData();
  form.append("file", file, file.name);
  const res = await fetch(`${API_BASE}/assets`, {
    method: "POST",
    headers: getHeaders(),
    body: form,
    signal: abortController?.signal,
  });
  if (res.status === 401) {
    throw new Error("Invalid or expired API key. Check your key at audioshake.ai.");
  }
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`Upload failed (${res.status}): ${t || res.statusText}`);
  }
  const data = await res.json();
  return data.id;
}

async function createTask(assetId) {
  const variant = (variantSelect && variantSelect.value) ? variantSelect.value.trim() : null;
  const target = {
    model: modelSelect.value,
    formats: [formatSelect.value],
  };
  if (variant) target.variant = variant;

  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: {
      ...getHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ assetId, targets: [target] }),
    signal: abortController?.signal,
  });
  if (res.status === 401) {
    throw new Error("Invalid or expired API key. Check your key at audioshake.ai.");
  }
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`Task creation failed (${res.status}): ${t || res.statusText}`);
  }
  const data = await res.json();
  return data.id;
}

function taskDone(data) {
  const targets = data.targets || [];
  if (!targets.length) return { done: false, failed: false };
  const statuses = targets.map((t) => t.status);
  const allDone = statuses.every((s) => s === "completed");
  const anyFailed = statuses.some((s) => s === "failed");
  return { done: allDone, failed: anyFailed };
}

async function pollTask(taskId) {
  for (;;) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      headers: getHeaders(),
      signal: abortController?.signal,
    });
    if (res.status === 401) {
      throw new Error("Invalid or expired API key. Check your key at audioshake.ai.");
    }
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`Status check failed (${res.status}): ${t || res.statusText}`);
    }
    const data = await res.json();
    const { done, failed } = taskDone(data);
    if (failed) {
      const firstFailed = (data.targets || []).find((t) => t.status === "failed");
      throw new Error(firstFailed?.error || "Task failed.");
    }
    if (done) return data;
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }
}

function extractStemLinks(taskData) {
  const stems = [];
  for (const target of taskData.targets || []) {
    for (const out of target.output || []) {
      const name = out.name || "output";
      const link = out.link;
      if (link) stems.push({ name, link });
    }
  }
  return stems;
}

async function run() {
  const key = (apiKeyInput && apiKeyInput.value) ? apiKeyInput.value.trim() : "";
  if (!key) {
    showError("Enter your Audioshake API key.");
    return;
  }
  if (!selectedFile) {
    showError("Choose an audio file.");
    return;
  }

  hideError();
  setBusy(true);
  setProgress("Uploading…");

  try {
    setProgress("Uploading…");
    const assetId = await uploadAsset(selectedFile);
    if (!assetId) throw new Error("No asset ID returned.");

    setProgress("Starting separation…");
    const taskId = await createTask(assetId);
    if (!taskId) throw new Error("No task ID returned.");

    setProgress("Processing (this may take a minute)…");
    const taskData = await pollTask(taskId);
    const stems = extractStemLinks(taskData);
    const baseName = selectedFile.name.replace(/\.[^.]+$/, "") || "audio";
    setResult(stems, baseName);
  } catch (err) {
    if (err.name === "AbortError") {
      setProgress("Cancelled.", false);
      progressSection.hidden = true;
    } else {
      const message = err.message || String(err);
      if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
        showError(
          "Network error. If you see CORS errors in the console, the Audioshake API may not allow browser requests from this origin. Use the desktop or CLI app from the repo instead."
        );
      } else {
        showError(message);
      }
    }
  } finally {
    setBusy(false);
  }
}

function cancel() {
  if (abortController) abortController.abort();
}

// File selection
dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) {
    selectedFile = file;
    fileNameEl.textContent = file.name;
    startBtn.disabled = !apiKeyInput?.value?.trim();
  }
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer?.files?.[0];
  if (file) {
    selectedFile = file;
    fileNameEl.textContent = file.name;
    startBtn.disabled = !apiKeyInput?.value?.trim();
  }
});

apiKeyInput.addEventListener("input", () => {
  startBtn.disabled = !selectedFile || !apiKeyInput?.value?.trim();
});

startBtn.addEventListener("click", () => {
  abortController = new AbortController();
  run();
});
cancelBtn.addEventListener("click", cancel);
