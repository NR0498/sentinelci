const REPOSITORY = "NR0498/sentinelci";
const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const dataBase = isLocal ? "/dashboard-assets/data" : "/data";
const localApi = isLocal ? window.location.origin : "";

const $ = (selector) => document.querySelector(selector);

function escapeHtml(value = "") {
  const node = document.createElement("span");
  node.textContent = String(value);
  return node.innerHTML;
}

function badgeClass(status) {
  if (["passed", "success", "completed"].includes(status)) return "badge good";
  if (["failed", "failure", "cancelled"].includes(status)) return "badge bad";
  return "badge neutral";
}

function setEvidence(result) {
  const security = result.security;
  const counts = security.counts;
  $("#security-score").textContent = security.score;
  $("#security-badge").textContent = security.status;
  $("#security-badge").className = badgeClass(security.status);
  $("#score-bar").style.width = `${security.score}%`;
  $("#score-bar").style.background =
    security.status === "failed" ? "var(--red)" : "var(--green)";
  $("#score-context").textContent =
    `${security.total_findings} normalized finding${security.total_findings === 1 ? "" : "s"} from raw scanner output.`;
  $("#coverage-value").textContent = `${result.quality.coverage_percent}%`;
  $("#gate-status").textContent = security.gate.passed ? "Approved" : "Blocked";
  $("#finding-total").textContent =
    `${security.total_findings} finding${security.total_findings === 1 ? "" : "s"}`;
  ["critical", "high", "medium", "low"].forEach((severity) => {
    $(`#${severity}-count`).textContent = counts[severity];
  });
  $("#gate-indicator").className =
    `gate-indicator ${security.gate.passed ? "pass" : "fail"}`;
  $("#gate-title").textContent =
    security.gate.passed ? "Release gate passed" : "Release gate blocked";
  $("#gate-policy").textContent = security.gate.policy;
  $("#discord-status").textContent =
    result.delivery.discord_configured ? "Configured" : "Secret controlled";
  renderFindings(security.findings);
}

function renderFindings(findings) {
  const container = $("#finding-list");
  if (!findings.length) {
    container.innerHTML =
      '<div class="loading-block">No known vulnerabilities were reported for this run.</div>';
    return;
  }
  container.innerHTML = findings
    .map(
      (item) => `
      <article class="finding-card">
        <div>
          <span class="severity ${escapeHtml(item.severity)}">${escapeHtml(item.severity)}</span>
          <small>${escapeHtml(item.source)}</small>
        </div>
        <div>
          <strong>${escapeHtml(item.id)} in ${escapeHtml(item.package)}</strong>
          <span>${escapeHtml(item.title)}</span>
          <small>Installed ${escapeHtml(item.installed_version)} · Fixed ${escapeHtml(item.fixed_version)}</small>
        </div>
        <div class="finding-action">
          <strong>Recommended action</strong>
          <span>${escapeHtml(item.action)}</span>
        </div>
      </article>`,
    )
    .join("");
}

async function loadEvidence() {
  const response = await fetch(`${dataBase}/latest.json`, { cache: "no-store" });
  if (!response.ok) throw new Error("Pipeline evidence could not be loaded.");
  const result = await response.json();
  setEvidence(result);
  return result;
}

function runStatus(run) {
  return run.status === "completed" ? run.conclusion || "completed" : run.status;
}

async function loadGitHubRuns() {
  const response = await fetch(
    `https://api.github.com/repos/${REPOSITORY}/actions/runs?per_page=5`,
    { headers: { Accept: "application/vnd.github+json" } },
  );
  if (!response.ok) throw new Error(`GitHub API returned ${response.status}.`);
  const payload = await response.json();
  const runs = payload.workflow_runs || [];
  const latest = runs[0];
  if (latest) {
    const status = runStatus(latest);
    $("#workflow-status").textContent = status.replace("_", " ");
    $("#workflow-context").textContent =
      `${latest.head_branch} · ${latest.head_sha.slice(0, 7)} · ${latest.actor.login}`;
  }
  $("#workflow-list").classList.remove("loading-block");
  $("#workflow-list").innerHTML = runs.length
    ? runs
        .map((run) => {
          const status = runStatus(run);
          return `
            <a class="workflow-row" href="${escapeHtml(run.html_url)}" target="_blank" rel="noreferrer">
              <span class="run-state ${escapeHtml(status)}"></span>
              <div>
                <strong>${escapeHtml(run.name)} #${run.run_number}</strong>
                <small>${escapeHtml(run.head_branch)} · ${escapeHtml(run.event)} · ${escapeHtml(run.actor.login)}</small>
              </div>
              <code>${escapeHtml(run.head_sha.slice(0, 7))}</code>
              <span class="${badgeClass(status)}">${escapeHtml(status)}</span>
            </a>`;
        })
        .join("")
    : '<div class="loading-block">No workflow runs were returned.</div>';
}

function renderTrend(history) {
  const width = 720;
  const height = 210;
  const pad = 34;
  const x = (index) =>
    pad + (index * (width - pad * 2)) / Math.max(history.length - 1, 1);
  const y = (score) => height - pad - (score * (height - pad * 2)) / 100;
  const points = history.map((item, index) => `${x(index)},${y(item.score)}`);
  const area = `${pad},${height - pad} ${points.join(" ")} ${width - pad},${height - pad}`;
  $("#trend-chart").innerHTML = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Security score by pipeline run">
      <defs>
        <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#55e6a5" stop-opacity=".23"/>
          <stop offset="100%" stop-color="#55e6a5" stop-opacity="0"/>
        </linearGradient>
      </defs>
      ${[0,25,50,75,100].map((value) => `
        <line class="chart-grid" x1="${pad}" y1="${y(value)}" x2="${width-pad}" y2="${y(value)}"/>
        <text class="chart-label" x="0" y="${y(value)+3}">${value}</text>`).join("")}
      <polygon class="chart-area" points="${area}"/>
      <polyline class="chart-line" points="${points.join(" ")}"/>
      ${history.map((item,index) => `
        <circle class="chart-point" cx="${x(index)}" cy="${y(item.score)}" r="5"/>
        <text class="chart-label" text-anchor="middle" x="${x(index)}" y="${height-8}">#${item.run}</text>
        <text class="chart-label" text-anchor="middle" x="${x(index)}" y="${y(item.score)-12}">${item.score}</text>`).join("")}
    </svg>`;
}

async function loadHistory() {
  const response = await fetch(`${dataBase}/history.json`, { cache: "no-store" });
  if (!response.ok) throw new Error("History data could not be loaded.");
  renderTrend(await response.json());
}

async function loadLocalStatus() {
  if (!localApi) {
    $("#connection-label").textContent = "Hosted portfolio mode";
    $("#connection-detail").textContent = "Live GitHub status and committed evidence";
    return;
  }
  try {
    const response = await fetch(`${localApi}/api/aws/status`);
    const status = await response.json();
    $("#connection-label").textContent = status.connected
      ? "LocalStack connected"
      : "LocalStack unavailable";
    $("#connection-detail").textContent = status.connected
      ? status.bucket
      : "Start the Docker Compose stack";
  } catch {
    $("#connection-label").textContent = "Local API unavailable";
    $("#connection-detail").textContent = "Start Docker Compose to upload evidence";
  }
}

async function uploadEvidence(event) {
  event.preventDefault();
  if (!localApi) {
    $("#upload-result").className = "result error";
    $("#upload-result").textContent =
      "Hosted mode is read-only. Run the local Docker stack for S3 and SNS evidence uploads.";
    return;
  }
  const input = $("#artifact-file");
  if (!input.files.length) return;
  const form = new FormData();
  form.append("file", input.files[0]);
  $("#upload-result").className = "result";
  $("#upload-result").textContent = "Analyzing report, storing in S3, and publishing SNS.";
  try {
    const response = await fetch(`${localApi}/api/artifacts/upload`, {
      method: "POST",
      body: form,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Upload failed.");
    $("#upload-result").className = "result success";
    $("#upload-result").textContent =
      `${data.analysis.status} · ${data.analysis.score ?? "N/A"}/100 · ${data.s3_uri}`;
  } catch (error) {
    $("#upload-result").className = "result error";
    $("#upload-result").textContent = error.message;
  }
}

async function refresh() {
  const results = await Promise.allSettled([
    loadEvidence(),
    loadGitHubRuns(),
    loadHistory(),
    loadLocalStatus(),
  ]);
  const failures = results.filter((result) => result.status === "rejected");
  if (failures.length) {
    console.warn("Some dashboard sources failed:", failures);
  }
  $("#updated-at").textContent = `Updated ${new Date().toLocaleString()}`;
}

$("#refresh-button").addEventListener("click", refresh);
$("#upload-form").addEventListener("submit", uploadEvidence);
$("#artifact-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) {
    $("#drop-zone strong").textContent = file.name;
    $("#drop-zone small").textContent = `${Math.ceil(file.size / 1024)} KB selected`;
  }
});

refresh();
