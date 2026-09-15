// Fetches and renders today's digest. No build step, no framework — kept
// deliberately simple since this page's only job is a read-only showcase view.
// Waveform/playback is powered by wavesurfer.js (loaded via CDN in index.html).

const API_BASE = document.querySelector('meta[name="api-base"]').content;
const PLAYBACK_RATES = [1, 1.25, 1.5, 1.75, 2];

// --- Background: blobs drift on their own (CSS keyframes) and additionally
// ease toward the pointer position for a subtle interactive parallax, without
// fighting the CSS animation since the pointer offset is applied to a wrapper
// element around each blob rather than the blob itself.
function initBackgroundParallax() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const wraps = [...document.querySelectorAll(".blob-wrap")].map((wrap) => ({
    el: wrap,
    depth: Number(wrap.dataset.depth) || 0.5,
    x: 0,
    y: 0,
  }));
  if (wraps.length === 0) return;

  let targetX = 0;
  let targetY = 0;

  window.addEventListener("pointermove", (e) => {
    targetX = e.clientX / window.innerWidth - 0.5;
    targetY = e.clientY / window.innerHeight - 0.5;
  });

  const MAX_SHIFT_PX = 110;

  function tick() {
    for (const wrap of wraps) {
      const goalX = targetX * MAX_SHIFT_PX * wrap.depth;
      const goalY = targetY * MAX_SHIFT_PX * wrap.depth;
      wrap.x += (goalX - wrap.x) * 0.09;
      wrap.y += (goalY - wrap.y) * 0.09;
      const scale = 1 + (Math.abs(targetX) + Math.abs(targetY)) * 0.12 * wrap.depth;
      wrap.el.style.transform = `translate(${wrap.x.toFixed(1)}px, ${wrap.y.toFixed(1)}px) scale(${scale.toFixed(3)})`;
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

initBackgroundParallax();

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

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return "0:00";
  const total = Math.floor(seconds);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// --- Segment rendering ---

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

  const text = document.createElement("p");
  text.textContent = segment.summary_short;
  wrapper.appendChild(text);

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

  if (segment.source_name) {
    const badge = document.createElement("span");
    badge.className = "source-badge";

    const favicon = document.createElement("img");
    favicon.alt = "";
    favicon.width = 14;
    favicon.height = 14;
    favicon.addEventListener("error", () => favicon.remove());
    try {
      const hostname = new URL(segment.source_article_url).hostname;
      favicon.src = `https://www.google.com/s2/favicons?domain=${hostname}&sz=32`;
    } catch {
      favicon.remove();
    }
    badge.appendChild(favicon);

    const name = document.createElement("span");
    name.textContent = segment.source_name;
    badge.appendChild(name);

    actions.appendChild(badge);
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

// --- Player: wavesurfer.js waveform + our own controls around it ---

function initPlayer() {
  const playerEl = document.getElementById("player");
  const toggle = document.getElementById("play-toggle");
  const iconPlay = document.getElementById("icon-play");
  const iconPause = document.getElementById("icon-pause");
  const timeCurrent = document.getElementById("time-current");
  const timeDuration = document.getElementById("time-duration");
  const muteToggle = document.getElementById("mute-toggle");
  const iconVolume = document.getElementById("icon-volume");
  const iconMuted = document.getElementById("icon-muted");
  const volumeSlider = document.getElementById("volume-slider");
  const speedToggle = document.getElementById("speed-toggle");
  const ccToggle = document.getElementById("cc-toggle");
  const captionBox = document.getElementById("caption-box");
  const captionText = document.getElementById("caption-text");

  const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
  const border = getComputedStyle(document.documentElement).getPropertyValue("--border").trim();

  const ws = WaveSurfer.create({
    container: "#waveform",
    height: 40,
    waveColor: border,
    progressColor: accent,
    cursorColor: "#ffffff",
    cursorWidth: 2,
    barWidth: 2,
    barGap: 1,
    barRadius: 2,
    normalize: true,
  });

  let rateIndex = 0;
  let lastVolume = 1;
  let captionsOn = false;
  let lastActiveIndex = -1;
  let captionWords = [];

  // Setting inline `style.display` directly rather than the `hidden`
  // attribute — a previous version relied on `[hidden]{display:none}` from
  // the stylesheet, which is fragile against stale caches of an old CSS
  // file. Inline styles always win regardless of what CSS happens to be
  // loaded, so this can't silently regress again.
  function updatePlayIcon(playing) {
    playerEl.classList.toggle("playing", playing);
    iconPlay.style.display = playing ? "none" : "";
    iconPause.style.display = playing ? "" : "none";
    toggle.setAttribute("aria-label", playing ? "Pausieren" : "Abspielen");
  }

  function updateVolumeIcon() {
    const isMuted = ws.getVolume() === 0;
    iconVolume.style.display = isMuted ? "none" : "";
    iconMuted.style.display = isMuted ? "" : "none";
    muteToggle.setAttribute("aria-label", isMuted ? "Ton einschalten" : "Stummschalten");
  }

  updatePlayIcon(false);
  updateVolumeIcon();

  toggle.addEventListener("click", () => ws.playPause());
  ws.on("play", () => updatePlayIcon(true));
  ws.on("pause", () => updatePlayIcon(false));
  ws.on("finish", () => updatePlayIcon(false));

  ws.on("ready", (duration) => {
    timeDuration.textContent = formatTime(duration);
  });

  ws.on("timeupdate", (currentTime) => {
    timeCurrent.textContent = formatTime(currentTime);
    updateActiveSegment(currentTime);
    updateActiveWord(currentTime);
  });

  ccToggle.addEventListener("click", () => {
    captionsOn = !captionsOn;
    ccToggle.setAttribute("aria-pressed", String(captionsOn));
    captionBox.hidden = !captionsOn;
    if (captionsOn) renderCaptionSegment(lastActiveIndex);
  });

  volumeSlider.addEventListener("input", () => {
    const value = Number(volumeSlider.value);
    ws.setVolume(value);
    updateVolumeIcon();
  });

  muteToggle.addEventListener("click", () => {
    if (ws.getVolume() === 0) {
      ws.setVolume(lastVolume || 1);
      volumeSlider.value = String(ws.getVolume());
    } else {
      lastVolume = ws.getVolume();
      ws.setVolume(0);
      volumeSlider.value = "0";
    }
    updateVolumeIcon();
  });

  speedToggle.addEventListener("click", () => {
    rateIndex = (rateIndex + 1) % PLAYBACK_RATES.length;
    const rate = PLAYBACK_RATES[rateIndex];
    ws.setPlaybackRate(rate, true);
    speedToggle.textContent = `${rate}×`;
  });

  function activeSegmentIndexAt(currentTime) {
    for (let index = 0; index < currentSegments.length; index++) {
      const segment = currentSegments[index];
      if (segment.audio_start_seconds === null || segment.audio_start_seconds === undefined) {
        continue;
      }
      const next = currentSegments[index + 1];
      const nextStart =
        next && next.audio_start_seconds !== null && next.audio_start_seconds !== undefined
          ? next.audio_start_seconds
          : Infinity;
      if (currentTime >= segment.audio_start_seconds && currentTime < nextStart) return index;
    }
    return -1;
  }

  // Renders the segment's narration as one <span> per word (from the TTS
  // backend's word-boundary timing) so updateActiveWord() can highlight
  // exactly the word being spoken right now. Falls back to plain text if a
  // TTS backend didn't provide word timing (only EdgeTTS currently does).
  function renderCaptionSegment(index) {
    const segment = currentSegments[index];
    captionText.innerHTML = "";
    captionWords = [];
    if (!segment) return;

    if (segment.words && segment.words.length) {
      for (const word of segment.words) {
        const span = document.createElement("span");
        span.className = "cap-word";
        span.textContent = word.text + " ";
        captionText.appendChild(span);
        captionWords.push({
          el: span,
          start: word.start_seconds,
          end: word.start_seconds + word.duration_seconds,
        });
      }
    } else {
      captionText.textContent = segment.narration;
    }
  }

  function updateActiveWord(currentTime) {
    if (!captionsOn || captionWords.length === 0) return;
    let activeEl = null;
    for (const word of captionWords) {
      const isActive = currentTime >= word.start && currentTime < word.end;
      word.el.classList.toggle("active", isActive);
      if (isActive) activeEl = word.el;
    }
    if (activeEl) activeEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function updateActiveSegment(currentTime) {
    const index = activeSegmentIndexAt(currentTime);
    if (index === lastActiveIndex) return;
    lastActiveIndex = index;

    document.querySelectorAll(".segment").forEach((segEl) => {
      segEl.classList.toggle("active", Number(segEl.dataset.index) === index);
    });

    if (captionsOn) renderCaptionSegment(index);
  }

  return {
    setSrc: (src) => ws.load(src),
    playFrom: (seconds) => {
      const duration = ws.getDuration();
      if (duration) ws.seekTo(Math.max(0, Math.min(1, seconds / duration)));
      ws.play();
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
