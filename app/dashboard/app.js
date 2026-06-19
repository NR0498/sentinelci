const apiInput = document.querySelector("#api-base");
const statusBadge = document.querySelector("#aws-badge");
const statusState = document.querySelector("#aws-state");
const statusDetail = document.querySelector("#aws-detail");
const artifactList = document.querySelector("#artifact-list");
const eventList = document.querySelector("#event-list");
const uploadForm = document.querySelector("#upload-form");
const uploadResult = document.querySelector("#upload-result");
const deliveryCount = document.querySelector("#delivery-count");
const updatedAt = document.querySelector("#updated-at");

const localDefault =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? window.location.origin
    : "";
apiInput.value = localStorage.getItem("sentinelci-api") || localDefault;

function api(path) {
  const base = apiInput.value.trim().replace(/\/$/, "");
  if (!base) {
    throw new Error("Set a reachable local API endpoint to load live data.");
  }
  localStorage.setItem("sentinelci-api", base);
  return `${base}${path}`;
}

function formatBytes(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function escapeHtml(value = "") {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

async function loadStatus() {
  try {
    const response = await fetch(api("/api/aws/status"));
    const data = await response.json();
    if (!response.ok || !data.connected) {
      throw new Error(data.error || data.detail || "LocalStack unavailable");
    }
    statusBadge.textContent = "Connected";
    statusBadge.className = "status good";
    statusState.textContent = "Online";
    statusDetail.textContent = data.bucket;
  } catch (error) {
    statusBadge.textContent = "Offline";
    statusBadge.className = "status idle";
    statusState.textContent = "Demo";
    statusDetail.textContent = error.message;
  }
}

async function loadArtifacts() {
  try {
    const response = await fetch(api("/api/artifacts"));
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Artifact query failed");
    artifactList.innerHTML = data.artifacts.length
      ? data.artifacts
          .map(
            (item) => `
              <div class="list-row">
                <div>
                  <strong title="${escapeHtml(item.key)}">${escapeHtml(item.key)}</strong>
                  <small>${new Date(item.last_modified).toLocaleString()}</small>
                </div>
                <code>${formatBytes(item.size)}</code>
              </div>`,
          )
          .join("")
      : '<div class="empty">The S3 bucket is ready for its first artifact.</div>';
  } catch (error) {
    artifactList.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

async function loadEvents() {
  try {
    const response = await fetch(api("/api/notifications"));
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Notification query failed");
    deliveryCount.textContent = data.notifications.length;
    eventList.innerHTML = data.notifications.length
      ? data.notifications
          .map(
            (item) => `
              <div class="list-row">
                <div>
                  <strong>${escapeHtml(item.subject || item.payload.event)}</strong>
                  <small>${escapeHtml(item.payload.key || "SNS event")}</small>
                </div>
                <code>DELIVERED</code>
              </div>`,
          )
          .join("")
      : '<div class="empty">Upload an artifact to publish an SNS event.</div>';
  } catch (error) {
    eventList.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

async function refreshAll() {
  await Promise.all([loadStatus(), loadArtifacts(), loadEvents()]);
  updatedAt.textContent = `Updated ${new Date().toLocaleTimeString()}`;
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.querySelector("#artifact-file");
  if (!input.files.length) return;
  const formData = new FormData();
  formData.append("file", input.files[0]);
  uploadResult.className = "result";
  uploadResult.textContent = "Uploading to S3 and publishing SNS notification…";
  try {
    const response = await fetch(api("/api/artifacts/upload"), {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Upload failed");
    uploadResult.className = "result success";
    uploadResult.textContent = `${data.s3_uri} · SNS ${data.message_id}`;
    await refreshAll();
  } catch (error) {
    uploadResult.className = "result error";
    uploadResult.textContent = error.message;
  }
});

document.querySelector("#refresh-button").addEventListener("click", refreshAll);
document.querySelector("#artifact-refresh").addEventListener("click", loadArtifacts);
document.querySelector("#event-refresh").addEventListener("click", loadEvents);
document.querySelector("#artifact-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) {
    document.querySelector("#drop-zone strong").textContent = file.name;
    document.querySelector("#drop-zone small").textContent = formatBytes(file.size);
  }
});

refreshAll();
