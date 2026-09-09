// Fetches and renders today's digest. No build step, no framework — kept
// deliberately simple since this page's only job is a read-only showcase view.

const API_BASE = document.querySelector('meta[name="api-base"]').content;

const el = {
  loading: document.getElementById("state-loading"),
  empty: document.getElementById("state-empty"),
  error: document.getElementById("state-error"),
  digest: document.getElementById("digest"),
  date: document.getElementById("date"),
  segments: document.getElementById("segments"),
};

function showState(name) {
  for (const key of ["loading", "empty", "error", "digest"]) {
    el[key].hidden = key !== name;
  }
}

function renderSegment(segment) {
  const wrapper = document.createElement("div");
  wrapper.className = "segment";

  const heading = document.createElement("h3");
  heading.textContent = segment.headline;
  wrapper.appendChild(heading);

  const summary = document.createElement("p");
  summary.textContent = segment.summary_short;
  wrapper.appendChild(summary);

  if (segment.tone_axis && segment.tone_score !== null && segment.tone_score !== undefined) {
    wrapper.appendChild(renderToneScale(segment.tone_axis, segment.tone_score));
  }

  wrapper.appendChild(renderSource(segment.source_article_url));

  return wrapper;
}

function renderSource(url) {
  const details = document.createElement("details");
  details.className = "source";

  const summary = document.createElement("summary");
  summary.textContent = "Quelle";
  details.appendChild(summary);

  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  try {
    link.textContent = `${new URL(url).hostname.replace(/^www\./, "")} ↗`;
  } catch {
    link.textContent = `${url} ↗`;
  }
  details.appendChild(link);

  return details;
}

function renderToneScale(axis, score) {
  const [left, right] = axis.split(/vs\.?|↔/i).map((s) => s.trim());

  const tone = document.createElement("div");
  tone.className = "tone";

  const label = document.createElement("div");
  label.className = "tone-label";
  label.innerHTML = `<span>${left || axis}</span><span>${right || ""}</span>`;
  tone.appendChild(label);

  const track = document.createElement("div");
  track.className = "tone-track";
  const fill = document.createElement("div");
  fill.className = "tone-fill";
  fill.style.left = `calc(${Math.max(0, Math.min(100, score))}% - 3px)`;
  track.appendChild(fill);
  tone.appendChild(track);

  return tone;
}

// --- Custom audio player ---
// Wraps a hidden native <audio> element with our own play button and a
// draggable/clickable progress bar, since native player chrome can't be
// restyled consistently across browsers.

function initPlayer() {
  const audio = document.getElementById("audio");
  const player = document.getElementById("player");
  const toggle = document.getElementById("play-toggle");
  const iconPlay = document.getElementById("icon-play");
  const iconPause = document.getElementById("icon-pause");
  const track = document.getElementById("progress-track");
  const fill = document.getElementById("progress-fill");
  const handle = document.getElementById("progress-handle");
  const timeCurrent = document.getElementById("time-current");
  const timeDuration = document.getElementById("time-duration");

  function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return "0:00";
    const total = Math.floor(seconds);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function setProgress(ratio) {
    const pct = Math.max(0, Math.min(1, ratio)) * 100;
    fill.style.width = `${pct}%`;
    handle.style.left = `${pct}%`;
  }

  toggle.addEventListener("click", () => {
    if (audio.paused) {
      audio.play();
    } else {
      audio.pause();
    }
  });

  audio.addEventListener("play", () => {
    player.classList.add("playing");
    iconPlay.hidden = true;
    iconPause.hidden = false;
    toggle.setAttribute("aria-label", "Pausieren");
  });

  audio.addEventListener("pause", () => {
    player.classList.remove("playing");
    iconPlay.hidden = false;
    iconPause.hidden = true;
    toggle.setAttribute("aria-label", "Abspielen");
  });

  audio.addEventListener("loadedmetadata", () => {
    timeDuration.textContent = formatTime(audio.duration);
  });

  audio.addEventListener("timeupdate", () => {
    timeCurrent.textContent = formatTime(audio.currentTime);
    if (audio.duration) {
      setProgress(audio.currentTime / audio.duration);
    }
  });

  audio.addEventListener("ended", () => {
    setProgress(0);
  });

  function seekToClientX(clientX) {
    if (!audio.duration) return;
    const rect = track.getBoundingClientRect();
    const ratio = (clientX - rect.left) / rect.width;
    audio.currentTime = Math.max(0, Math.min(1, ratio)) * audio.duration;
  }

  track.addEventListener("click", (e) => seekToClientX(e.clientX));

  let dragging = false;
  track.addEventListener("pointerdown", (e) => {
    dragging = true;
    seekToClientX(e.clientX);
  });
  window.addEventListener("pointermove", (e) => {
    if (dragging) seekToClientX(e.clientX);
  });
  window.addEventListener("pointerup", () => {
    dragging = false;
  });

  return { setSrc: (src) => (audio.src = src) };
}

const player = initPlayer();

async function loadDigest() {
  showState("loading");
  try {
    const response = await fetch(`${API_BASE}/api/digest/today`);
    if (response.status === 404) {
      showState("empty");
      return;
    }
    if (!response.ok) {
      showState("error");
      return;
    }
    const result = await response.json();
    render(result);
    showState("digest");
  } catch (err) {
    console.error("Failed to load digest", err);
    showState("error");
  }
}

function render(result) {
  el.date.textContent = new Date(result.digest_date).toLocaleDateString("de-DE", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  player.setSrc(`${API_BASE}/api/digest/today/audio`);

  el.segments.innerHTML = "";
  for (const segment of result.script.segments) {
    el.segments.appendChild(renderSegment(segment));
  }

  if (result.script.segments.some((s) => s.tone_axis)) {
    const caveat = document.createElement("p");
    caveat.className = "tone-caveat";
    caveat.textContent =
      "Die Tonalitäts-Skalen sind eine subjektive, KI-generierte stilistische Einschätzung — kein Faktencheck.";
    el.digest.appendChild(caveat);
  }
}

loadDigest();
