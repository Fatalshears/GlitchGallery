let allNotes = [];

async function init() {
  try {
    const res = await fetch("manifest.json");
    if (!res.ok) throw new Error("manifest.json not found");
    allNotes = await res.json();
  } catch {
    document.getElementById("empty-state").textContent =
      "Could not load manifest.json. Make sure the file exists.";
    document.getElementById("empty-state").classList.remove("hidden");
    return;
  }
  renderGallery(allNotes);
}

function formatDate(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function renderGallery(notes) {
  const gallery = document.getElementById("gallery");
  const emptyState = document.getElementById("empty-state");
  const count = document.getElementById("count");

  if (notes.length === 0) {
    gallery.innerHTML = "";
    count.textContent = "";
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  count.textContent =
    notes.length === allNotes.length
      ? `${allNotes.length} note${allNotes.length !== 1 ? "s" : ""}`
      : `${notes.length} of ${allNotes.length} notes`;

  gallery.innerHTML = notes
    .map(
      (note) => `
      <div class="card" data-filename="${escapeAttr(note.filename)}">
        <div class="card-header">
          <span class="card-title">${escapeHtml(note.title)}</span>
          <span class="card-date">${formatDate(note.date)}</span>
        </div>
        <div class="card-preview">${marked.parse(note.preview)}</div>
      </div>`
    )
    .join("");

  gallery.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("click", () => openModal(card.dataset.filename));
  });
}

async function openModal(filename) {
  const note = allNotes.find((n) => n.filename === filename);
  if (!note) return;

  let content;
  try {
    const res = await fetch(`notes/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error();
    content = await res.text();
  } catch {
    content = `_Could not load \`${filename}\`._`;
  }

  document.getElementById("modal-title").textContent = note.title;
  document.getElementById("modal-body").innerHTML = marked.parse(content);
  document.getElementById("modal-body").scrollTop = 0;
  document.getElementById("modal-overlay").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
  document.body.style.overflow = "";
}

// ── Search ──

let searchTimeout;
document.getElementById("search").addEventListener("input", (e) => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    const query = e.target.value.toLowerCase().trim();
    if (!query) {
      renderGallery(allNotes);
      return;
    }
    const filtered = allNotes.filter(
      (note) =>
        note.title.toLowerCase().includes(query) ||
        note.preview.toLowerCase().includes(query)
    );
    renderGallery(filtered);
  }, 150);
});

// ── Modal close ──

document.getElementById("modal-close").addEventListener("click", closeModal);

document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target === document.getElementById("modal-overlay")) closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

// ── Helpers ──

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(str) {
  return str.replace(/"/g, "&quot;");
}

init();
