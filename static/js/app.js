const stateElements = {
  clockLabel: document.querySelector("#clockLabel"),
  cpuState: document.querySelector("#cpuState"),
  totalJobs: document.querySelector("#totalJobs"),
  queueSize: document.querySelector("#queueSize"),
  completedCount: document.querySelector("#completedCount"),
  runningJobCard: document.querySelector("#runningJobCard"),
  queueBody: document.querySelector("#queueBody"),
  completedList: document.querySelector("#completedList"),
  logList: document.querySelector("#logList"),
  feedback: document.querySelector("#feedback"),
  form: document.querySelector("#jobForm"),
  resetButton: document.querySelector("#resetButton"),
  nameInput: document.querySelector("#nameInput"),
  burstInput: document.querySelector("#burstInput"),
};

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[character];
  });

const setFeedback = (message, kind = "") => {
  stateElements.feedback.textContent = message;
  stateElements.feedback.className = `feedback ${kind}`.trim();
};

const renderRunningJob = (job) => {
  if (!job) {
    stateElements.runningJobCard.className = "running-card empty";
    stateElements.runningJobCard.innerHTML = "<p>No job is using the CPU yet.</p>";
    return;
  }

  stateElements.runningJobCard.className = "running-card";
  stateElements.runningJobCard.innerHTML = `
    <div class="running-title">
      <div>
        <p class="panel-kicker">Now Encoding</p>
        <strong>${escapeHtml(job.name)}</strong>
      </div>
      <span class="cpu-pill busy">${escapeHtml(job.pid)}</span>
    </div>
    <div class="running-grid">
      <article class="metric">
        <span>Remaining</span>
        <strong>${job.remaining_time}s</strong>
      </article>
      <article class="metric">
        <span>Burst</span>
        <strong>${job.burst_time}s</strong>
      </article>
      <article class="metric">
        <span>Arrival</span>
        <strong>${job.arrival_time}s</strong>
      </article>
      <article class="metric">
        <span>Priority</span>
        <strong>${job.effective_priority}</strong>
      </article>
    </div>
  `;
};

const renderQueue = (jobs) => {
  if (!jobs.length) {
    stateElements.queueBody.innerHTML = `
      <tr class="empty-row">
        <td colspan="6">The ready queue is empty.</td>
      </tr>
    `;
    return;
  }

  stateElements.queueBody.innerHTML = jobs
    .map(
      (job) => `
        <tr>
          <td>${escapeHtml(job.pid)}</td>
          <td>${escapeHtml(job.name)}</td>
          <td>${job.burst_time}s</td>
          <td>${job.remaining_time}s</td>
          <td>${job.waiting_time}s</td>
          <td>${job.effective_priority}</td>
        </tr>
      `,
    )
    .join("");
};

const renderCompleted = (jobs) => {
  if (!jobs.length) {
    stateElements.completedList.innerHTML =
      '<p class="empty-copy">Completed jobs will appear here.</p>';
    return;
  }

  stateElements.completedList.innerHTML = jobs
    .slice()
    .reverse()
    .map(
      (job) => `
        <article class="completed-item">
          <strong>${escapeHtml(job.pid)} · ${escapeHtml(job.name)}</strong>
          <small>
            Turnaround ${job.turnaround_time}s · Completed at ${job.completed_at}s
          </small>
        </article>
      `,
    )
    .join("");
};

const renderLogs = (lines) => {
  if (!lines.length) {
    stateElements.logList.innerHTML =
      '<p class="log-line muted">Waiting for scheduler events...</p>';
    return;
  }

  stateElements.logList.innerHTML = lines
    .slice()
    .reverse()
    .map((line) => `<p class="log-line">${escapeHtml(line)}</p>`)
    .join("");
};

const renderState = (state) => {
  stateElements.clockLabel.textContent = state.clock_label;
  stateElements.totalJobs.textContent = state.stats.total_jobs;
  stateElements.queueSize.textContent = state.stats.queue_size;
  stateElements.completedCount.textContent = state.stats.completed_count;
  stateElements.cpuState.textContent =
    state.stats.cpu_state === "busy" ? "CPU Busy" : "CPU Idle";
  stateElements.cpuState.className = `cpu-pill ${state.stats.cpu_state}`;
  renderRunningJob(state.running_job);
  renderQueue(state.ready_queue);
  renderCompleted(state.completed_jobs);
  renderLogs(state.event_log);
};

const fetchState = async () => {
  const response = await fetch("/api/state");
  if (!response.ok) {
    throw new Error("Failed to fetch the scheduler state.");
  }
  const state = await response.json();
  renderState(state);
};

const submitJob = async (event) => {
  event.preventDefault();
  const name = stateElements.nameInput.value.trim();
  const burstTime = Number(stateElements.burstInput.value);

  if (!name || !Number.isInteger(burstTime) || burstTime <= 0) {
    setFeedback("Provide a job name and a positive burst time.", "error");
    return;
  }

  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name,
      burst_time: burstTime,
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Job submission failed.");
  }

  renderState(payload.state);
  stateElements.form.reset();
  stateElements.nameInput.focus();
  setFeedback(`Added ${payload.job.pid} for ${payload.job.name}.`, "success");
};

const resetSimulation = async () => {
  const response = await fetch("/api/reset", { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to reset the simulation.");
  }

  const state = await response.json();
  renderState(state);
  setFeedback("Simulation reset.", "success");
};

const safelyRun = async (task) => {
  try {
    await task();
  } catch (error) {
    setFeedback(error.message || "Unexpected error.", "error");
  }
};

stateElements.form.addEventListener("submit", (event) => {
  safelyRun(() => submitJob(event));
});

stateElements.resetButton.addEventListener("click", () => {
  safelyRun(resetSimulation);
});

safelyRun(fetchState);
window.setInterval(() => {
  safelyRun(fetchState);
}, 1000);
