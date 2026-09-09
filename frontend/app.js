// Fetches and renders today's digest. No build step, no framework — kept
// deliberately simple since this page's only job is a read-only showcase view.

const API_BASE = document.querySelector('meta[name="api-base"]').content;

const el = {
  loading: document.getElementById("state-loading"),
  empty: document.getElementById("state-empty"),
  error: document.getElementById("state-error"),
  digest: document.getElementById("digest"),
  date: document.getElementById("date"),
  player: document.getElementById("player"),
  intro: document.getElementById("intro"),
  outro: document.getElementById("outro"),
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

  const narration = document.createElement("p");
  narration.textContent = segment.narration;
  wrapper.appendChild(narration);

  if (segment.tone_axis && segment.tone_score !== null && segment.tone_score !== undefined) {
    wrapper.appendChild(renderToneScale(segment.tone_axis, segment.tone_score));
  }

  return wrapper;
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
  el.date.textContent = new Date(result.digest_date).toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  el.player.src = `${API_BASE}/api/digest/today/audio`;
  el.intro.textContent = result.script.intro;
  el.outro.textContent = result.script.outro;

  el.segments.innerHTML = "";
  for (const segment of result.script.segments) {
    el.segments.appendChild(renderSegment(segment));
  }

  if (result.script.segments.some((s) => s.tone_axis)) {
    const caveat = document.createElement("p");
    caveat.className = "tone-caveat";
    caveat.textContent =
      "Tone scales are a subjective, AI-generated stylistic impression — not a fact check.";
    el.digest.appendChild(caveat);
  }
}

loadDigest();
