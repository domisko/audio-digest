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
  tagFilter: document.getElementById("tag-filter"),
};

let currentSegments = [];
let activeTag = null;

function showState(name) {
  for (const key of ["loading", "empty", "error", "digest"]) {
    el[key].hidden = key !== name;
  }
}

function renderSegment(segment, index) {
  const wrapper = document.createElement("div");
  wrapper.className = "segment";
  wrapper.dataset.index = String(index);

  if (segment.tags && segment.tags.length) {
    const tagRow = document.createElement("div");
    tagRow.className = "segment-tags";
    for (const tag of segment.tags) {
      const pill = document.createElement("span");
      pill.className = "segment-tag";
      pill.textContent = tag;
      tagRow.appendChild(pill);
    }
    wrapper.appendChild(tagRow);
  }

  const heading = document.createElement("h3");
  heading.textContent = segment.headline;
  wrapper.appendChild(heading);

  const summary = document.createElement("p");
  summary.textContent = segment.summary_short;
  wrapper.appendChild(summary);

  if (segment.tone_axis && segment.tone_score !== null && segment.tone_score !== undefined) {
    wrapper.appendChild(renderToneScale(segment.tone_axis, segment.tone_score));
  }

  wrapper.appendChild(renderActions(segment));

  return wrapper;
}

function renderActions(segment) {
  const actions = document.createElement("div");
  actions.className = "segment-actions";

  if (segment.audio_start_seconds !== null && segment.audio_start_seconds !== undefined) {
    const jumpBtn = document.createElement("button");
    jumpBtn.type = "button";
    jumpBtn.className = "timestamp-btn";
    jumpBtn.textContent = `▶ ${formatTime(segment.audio_start_seconds)}`;
    jumpBtn.addEventListener("click", () => player.playFrom(segment.audio_start_seconds));
    actions.appendChild(jumpBtn);
  }

  const link = document.createElement("a");
  link.className = "article-link";
  link.href = segment.source_article_url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Mehr erfahren ↗";
  actions.appendChild(link);

  return actions;
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

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return "0:00";
  const total = Math.floor(seconds);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// --- Tag filter bar ---

function renderTagFilter(segments) {
  const tags = [...new Set(segments.flatMap((s) => s.tags || []))];
  el.tagFilter.innerHTML = "";

  if (tags.length === 0) {
    el.tagFilter.hidden = true;
    return;
  }
  el.tagFilter.hidden = false;

  const allChip = document.createElement("button");
  allChip.type = "button";
  allChip.className = "tag-chip" + (activeTag === null ? " active" : "");
  allChip.textContent = "Alle";
  allChip.addEventListener("click", () => setActiveTag(null));
  el.tagFilter.appendChild(allChip);

  for (const tag of tags) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "tag-chip" + (activeTag === tag ? " active" : "");
    chip.textContent = tag;
    chip.addEventListener("click", () => setActiveTag(tag));
    el.tagFilter.appendChild(chip);
  }
}

function setActiveTag(tag) {
  activeTag = tag;
  renderTagFilter(currentSegments);
  renderSegmentList();
}

function renderSegmentList() {
  el.segments.innerHTML = "";
  currentSegments.forEach((segment, index) => {
    if (activeTag !== null && !(segment.tags || []).includes(activeTag)) return;
    el.segments.appendChild(renderSegment(segment, index));
  });
}

// --- Custom audio player: play/pause, seek, volume, and a bar visualizer ---
// driven by the Web Audio API's AnalyserNode.

function initPlayer() {
  const audio = document.getElementById("audio");
  const playerEl = document.getElementById("player");
  const toggle = document.getElementById("play-toggle");
  const iconPlay = document.getElementById("icon-play");
  const iconPause = document.getElementById("icon-pause");
  const track = document.getElementById("progress-track");
  const fill = document.getElementById("progress-fill");
  const handle = document.getElementById("progress-handle");
  const timeCurrent = document.getElementById("time-current");
  const timeDuration = document.getElementById("time-duration");
  const muteToggle = document.getElementById("mute-toggle");
  const iconVolume = document.getElementById("icon-volume");
  const iconMuted = document.getElementById("icon-muted");
  const volumeSlider = document.getElementById("volume-slider");
  const canvas = document.getElementById("visualizer");
  const ctx2d = canvas.getContext("2d");

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
    playerEl.classList.add("playing");
    iconPlay.hidden = true;
    iconPause.hidden = false;
    toggle.setAttribute("aria-label", "Pausieren");
    startVisualizer();
  });

  audio.addEventListener("pause", () => {
    playerEl.classList.remove("playing");
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
    highlightActiveSegment(audio.currentTime);
  });

  audio.addEventListener("ended", () => setProgress(0));

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

  // --- Volume / mute ---
  let lastVolume = 1;

  function updateVolumeIcon() {
    const isMuted = audio.muted || audio.volume === 0;
    iconVolume.hidden = isMuted;
    iconMuted.hidden = !isMuted;
  }

  volumeSlider.addEventListener("input", () => {
    audio.volume = Number(volumeSlider.value);
    audio.muted = audio.volume === 0;
    updateVolumeIcon();
  });

  muteToggle.addEventListener("click", () => {
    if (audio.muted || audio.volume === 0) {
      audio.muted = false;
      audio.volume = lastVolume || 1;
      volumeSlider.value = String(audio.volume);
    } else {
      lastVolume = audio.volume;
      audio.muted = true;
    }
    updateVolumeIcon();
  });

  // --- Bar visualizer (Web Audio API) ---
  let analyser = null;
  let freqData = null;
  let rafId = null;

  function ensureAudioGraph() {
    if (analyser) return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      const source = audioCtx.createMediaElementSource(audio);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      freqData = new Uint8Array(analyser.frequencyBinCount);
      source.connect(analyser);
      analyser.connect(audioCtx.destination);
      if (audioCtx.state === "suspended") audioCtx.resume();
    } catch (err) {
      console.warn("Visualizer unavailable (Web Audio API blocked):", err);
    }
  }

  function drawVisualizer() {
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
      canvas.width = width * dpr;
      canvas.height = height * dpr;
    }
    ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx2d.clearRect(0, 0, width, height);

    if (!analyser || audio.paused) {
      rafId = null;
      return;
    }

    analyser.getByteFrequencyData(freqData);
    const barCount = 28;
    const step = Math.floor(freqData.length / barCount) || 1;
    const barWidth = width / barCount;
    const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();

    for (let i = 0; i < barCount; i++) {
      const value = freqData[i * step] / 255;
      const barHeight = Math.max(2, value * height);
      ctx2d.fillStyle = accent;
      ctx2d.globalAlpha = 0.35 + value * 0.65;
      ctx2d.fillRect(i * barWidth + 1, height - barHeight, barWidth - 2, barHeight);
    }
    ctx2d.globalAlpha = 1;

    rafId = requestAnimationFrame(drawVisualizer);
  }

  function startVisualizer() {
    ensureAudioGraph();
    if (!analyser) return;
    if (!rafId) rafId = requestAnimationFrame(drawVisualizer);
  }

  function highlightActiveSegment(currentTime) {
    document.querySelectorAll(".segment").forEach((segEl) => {
      const index = Number(segEl.dataset.index);
      const segment = currentSegments[index];
      if (!segment || segment.audio_start_seconds === null) return;
      const next = currentSegments[index + 1];
      const nextStart = next && next.audio_start_seconds !== null ? next.audio_start_seconds : Infinity;
      const isActive = currentTime >= segment.audio_start_seconds && currentTime < nextStart;
      segEl.classList.toggle("active", isActive);
    });
  }

  return {
    setSrc: (src) => (audio.src = src),
    playFrom: (seconds) => {
      audio.currentTime = seconds;
      audio.play();
    },
  };
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

  currentSegments = result.script.segments;
  activeTag = null;
  renderTagFilter(currentSegments);
  renderSegmentList();

  if (currentSegments.some((s) => s.tone_axis)) {
    const caveat = document.createElement("p");
    caveat.className = "tone-caveat";
    caveat.textContent =
      "Die Tonalitäts-Skalen sind eine subjektive, KI-generierte stilistische Einschätzung — kein Faktencheck.";
    el.digest.appendChild(caveat);
  }
}

loadDigest();
