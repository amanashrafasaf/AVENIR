/* AVENIR frontend — no build step, vanilla JS. */

const $ = (sel) => document.querySelector(sel);
const PROGRESS_KEY = "careeros_progress_v1";

let currentProfile = null;
let currentRoadmap = null;

/* ---------------------------------------------------------------- helpers */
function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

/* ---------------------------------------------------------------- health */
async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const badge = $("#modeBadge");
    if (data.demo_mode) {
      badge.textContent = "⚙ DEMO MODE (offline engine)";
      badge.classList.add("demo");
      $("#footerMode").textContent = "DEMO_MODE offline engine active";
    } else {
      badge.textContent = "✦ AI connected";
      badge.classList.add("ai");
      $("#footerMode").textContent = "Live AI engine";
    }
  } catch {
    $("#modeBadge").textContent = "⚠ offline";
    $("#modeBadge").classList.add("demo");
  }
}

/* ---------------------------------------------------------------- profile */
const DEMO_PROFILE = {
  name: "Aarav",
  educationLevel: "Class 11/12",
  subjects: "Maths, Physics, Computer Science",
  marks: "82",
  interests: "coding, chess, gaming",
  skills: "Python basics, Excel",
  careerInterests: "something in tech",
  location: "Patna, Bihar",
  financialPreference: "Need scholarships/grants",
  preferredEducationPath: "University degree",
};

function fillForm(profile) {
  for (const [key, value] of Object.entries(profile)) {
    const input = document.querySelector(`[name="${key}"]`);
    if (input) input.value = value;
  }
}

function readForm() {
  const form = $("#profileForm");
  const data = {};
  for (const input of form.querySelectorAll("input, select")) {
    data[input.name] = input.value.trim();
  }
  return data;
}

function setGenerating(on) {
  $("#spinner").hidden = !on;
  $("#generateLabel").textContent = on ? "Analyzing your profile…" : "Generate my career roadmap →";
  $("#generateBtn").disabled = on;
}

/* ---------------------------------------------------------------- generate */
async function generateRoadmap(profile) {
  setGenerating(true);
  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile }),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    currentProfile = profile;
    currentRoadmap = data;
    renderResults(data, profile);
    $("#resultsSection").hidden = false;
    $("#chatSection").hidden = false;
    $("#profileSection").scrollIntoView({ behavior: "smooth", block: "start" });
    $("#resultsSection").scrollIntoView({ behavior: "smooth", block: "start" });
    addChatBot("Your roadmap is ready! 🎉 Ask me anything about it — or tap a suggested question below.");
  } catch (err) {
    console.error(err);
    addChatBot("⚠ Couldn't reach the analysis engine. Is the server running?");
  } finally {
    setGenerating(false);
  }
}

/* ---------------------------------------------------------------- render */
function renderResults(data, profile) {
  $("#resultMeta").textContent =
    `Based on ${profile.name || "your"} profile — ${profile.educationLevel}, ${profile.subjects || "your subjects"} · ` +
    `engine: ${data.mode === "mock" ? "offline engine" : "AI"}`;

  // Recommendations
  const recBox = $("#recommendations");
  recBox.innerHTML = "";
  data.recommendations.forEach((rec, i) => {
    const card = el("div", "career-card" + (i === 0 ? " top" : ""));
    card.innerHTML = `
      <div class="career-card-top">
        <span class="rank">#${i + 1}</span>
        <h3>${esc(rec.career)}</h3>
        <span class="score" style="--pct:${rec.match_score}%">${rec.match_score}%</span>
      </div>
      <p class="career-summary">${esc(rec.summary)}</p>
      <ul class="match-reasons">${rec.match_reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
      <div class="career-meta">
        <span>💰 ${esc(rec.salary_range)}</span>
        <span>📈 Demand: ${esc(rec.demand_outlook)}</span>
      </div>`;
    card.addEventListener("click", () => renderDetail(rec, data));
    recBox.appendChild(card);
  });

  // Auto-open the top recommendation
  renderDetail(data.recommendations[0], data);
}

function renderDetail(rec, data) {
  $("#detailSection").hidden = false;
  // Highlight selected card
  document.querySelectorAll(".career-card").forEach((c) => c.classList.remove("selected"));
  const cards = [...document.querySelectorAll(".career-card")];
  const idx = data.recommendations.findIndex((r) => r.career === rec.career);
  if (cards[idx]) cards[idx].classList.add("selected");

  // Skill gaps
  const gaps = $("#skillGaps");
  gaps.innerHTML = "";
  (data.skill_gaps.length ? data.skill_gaps : [{ skill: "None — you're well prepared!", importance: "low", how_to_learn: "Keep building and applying." }])
    .forEach((g) => {
      const li = el("li", "gap-item");
      li.innerHTML = `
        <div class="gap-head">
          <span class="gap-name">${esc(g.skill)}</span>
          <span class="badge badge-${esc(g.importance)}">${esc(g.importance)}</span>
        </div>
        <p class="muted small">${esc(g.how_to_learn)}</p>`;
      gaps.appendChild(li);
    });

  // Progress
  renderProgress(data);

  // Roadmap timeline
  const tl = $("#roadmapYears");
  tl.innerHTML = "";
  data.roadmap.years.forEach((yr, yi) => {
    const item = el("div", "tl-item");
    const head = el("div", "tl-head");
    const dot = el("span", "tl-dot");
    head.appendChild(dot);
    head.appendChild(el("div", "", ""));
    head.lastChild.appendChild(el("h4", "tl-year", yr.year));
    head.lastChild.appendChild(el("p", "muted small", yr.phase));
    item.appendChild(head);
    const body = el("div", "tl-body");
    yr.milestones.forEach((m) => {
      const key = `${rec.career}|${yi}|${m.title}`;
      const done = getProgress()[key] === true;
      const label = el("label", "milestone" + (done ? " done" : ""));
      const cb = el("input");
      cb.type = "checkbox";
      cb.checked = done;
      cb.addEventListener("change", () => toggleMilestone(key, cb.checked, rec.career));
      label.appendChild(cb);
      const inner = el("span", "");
      inner.innerHTML = `<strong>${esc(m.title)}</strong> <span class="type-tag">${esc(capitalize(m.type))}</span>
        <span class="muted small">${esc(m.detail)}</span>`;
      label.appendChild(inner);
      body.appendChild(label);
    });
    item.appendChild(body);
    tl.appendChild(item);
  });

  // Courses / certs / degrees / scholarships
  $("#courses").innerHTML = data.roadmap.courses.map((c) => `<li>${esc(c)}</li>`).join("");
  $("#certs").innerHTML = data.roadmap.certifications.map((c) => `<li>${esc(c)}</li>`).join("");
  $("#degrees").innerHTML = data.roadmap.degree_options.map((c) => `<li>${esc(c)}</li>`).join("");
  $("#scholarships").innerHTML = data.roadmap.scholarships
    .map((s) => `<li><strong>${esc(s.name)}</strong> — ${esc(s.for)} <span class="scholar-amt">${esc(s.amount)}</span></li>`)
    .join("");

  $("#matchNote").textContent = data.roadmap.match_summary || "";
}

/* ---------------------------------------------------------------- progress */
function getProgress() {
  try { return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {}; }
  catch { return {}; }
}

function toggleMilestone(key, checked, career) {
  const prog = getProgress();
  if (checked) prog[key] = true; else delete prog[key];
  localStorage.setItem(PROGRESS_KEY, JSON.stringify(prog));
  renderProgress(currentRoadmap);
}

function renderProgress(data) {
  const total = data.roadmap.years.reduce((n, y) => n + y.milestones.length, 0);
  let done = 0;
  const prog = getProgress();
  data.roadmap.years.forEach((yr, yi) => {
    yr.milestones.forEach((m) => {
      if (prog[`${data.recommendations[0].career}|${yi}|${m.title}`]) done++;
    });
  });
  const pct = total ? Math.round((done / total) * 100) : 0;
  $("#progressFill").style.width = pct + "%";
  $("#progressLabel").textContent = `${done} / ${total} milestones done (${pct}%)`;
}

/* ---------------------------------------------------------------- chat */
function addChat(msg, who) {
  const log = $("#chatLog");
  const row = el("div", `msg msg-${who}`);
  row.textContent = msg;
  log.appendChild(row);
  log.scrollTop = log.scrollHeight;
}

function addChatBot(msg) { addChat(msg, "bot"); }
function addChatUser(msg) { addChat(msg, "user"); }

async function sendChat(message) {
  addChatUser(message);
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, profile: currentProfile || {} }),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    addChatBot(data.reply);
  } catch (err) {
    console.error(err);
    addChatBot("⚠ Chat engine unavailable right now.");
  }
}

/* ---------------------------------------------------------------- wire up */
$("#loadDemo").addEventListener("click", () => fillForm(DEMO_PROFILE));
$("#editProfile").addEventListener("click", () => {
  $("#resultsSection").scrollIntoView({ behavior: "smooth" });
  $("#profileSection").scrollIntoView({ behavior: "smooth" });
});

$("#profileForm").addEventListener("submit", (e) => {
  e.preventDefault();
  generateRoadmap(readForm());
});

$("#chatForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#chatMessage");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  sendChat(msg);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendChat(chip.dataset.q));
});

loadHealth();
