/* SnapID UI — spec pick → upload → result with compliance checklist. */

const $ = (id) => document.getElementById(id);
let specs = [];
let currentSpec = null;

async function loadSpecs() {
  const resp = await fetch("/api/specs");
  specs = await resp.json();
  const grid = $("specGrid");
  grid.innerHTML = "";
  specs.forEach((s) => {
    const card = document.createElement("button");
    card.className = "spec-card";
    const [r, g, b] = s.background_rgb;
    card.innerHTML = `
      <h3>${s.name}</h3>
      <span class="spec-meta">
        <span class="swatch" style="background: rgb(${r},${g},${b})"></span>
        ${s.size_mm[0]}×${s.size_mm[1]} mm
      </span>`;
    card.addEventListener("click", () => pickSpec(s));
    grid.appendChild(card);
  });
}

function pickSpec(spec) {
  currentSpec = spec;
  $("stepSpec").hidden = true;
  $("stepUpload").hidden = false;
  $("stepResult").hidden = true;
  $("chosenSpec").textContent = `— ${spec.name}`;
  $("specNotes").textContent = spec.notes;
  $("status").hidden = true;
  $("status").className = "status";
}

$("backToSpecs").addEventListener("click", () => {
  $("stepUpload").hidden = true;
  $("stepSpec").hidden = false;
});
$("startOver").addEventListener("click", () => {
  $("stepResult").hidden = true;
  $("stepSpec").hidden = false;
});

/* --- upload --- */
const drop = $("drop");
drop.addEventListener("click", () => $("fileInput").click());
$("fileInput").addEventListener("change", (e) => {
  if (e.target.files.length) processPhoto(e.target.files[0]);
});
["dragover", "dragenter"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("dragover"); })
);
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("dragover"); })
);
drop.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) processPhoto(e.dataTransfer.files[0]);
});

async function processPhoto(file) {
  const status = $("status");
  status.hidden = false;
  status.className = "status working";
  status.textContent = "Removing background, cropping to spec, running checks";

  const form = new FormData();
  form.append("file", file);
  form.append("spec_id", currentSpec.id);
  form.append("paper", document.querySelector('input[name="paper"]:checked').value);

  try {
    const resp = await fetch("/api/process", { method: "POST", body: form });
    const body = await resp.json();
    if (!resp.ok) throw new Error(body.detail || "Processing failed.");
    showResult(body);
  } catch (err) {
    status.className = "status error";
    status.textContent = err.message;
  }
}

function showResult(body) {
  $("stepUpload").hidden = true;
  $("stepResult").hidden = false;

  $("resultImg").src = body.photo_url;
  $("dlPhoto").href = body.photo_url;
  $("dlSheet").href = body.sheet_url;
  $("copies").textContent = `· ${body.sheet_copies} copies`;

  const list = $("checkList");
  list.innerHTML = "";
  body.compliance.checks.forEach((c) => {
    const li = document.createElement("li");
    li.className = c.passed ? "pass" : "fail";
    li.innerHTML = `<span class="mark">${c.passed ? "✓" : "✗"}</span>
      <span>${c.label}<span class="detail">${c.detail}</span></span>`;
    list.appendChild(li);
  });

  const verdict = $("verdict");
  if (body.compliance.passed) {
    verdict.className = "verdict pass";
    verdict.textContent = "All checks passed — ready to print or submit.";
  } else {
    verdict.className = "verdict fail";
    verdict.textContent =
      "Some checks failed — retake the photo following the tips above and try again.";
  }
}

loadSpecs();
