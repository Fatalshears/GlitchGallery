const COLORS = [
  { bg: '#FF6F61', fade: '#FF6F61' }, // coral
  { bg: '#26A69A', fade: '#26A69A' }, // teal
  { bg: '#FFC107', fade: '#FFC107' }, // yellow
  { bg: '#C2185B', fade: '#C2185B' }, // magenta
];

let allNotes = [];

async function init() {
  try {
    const res = await fetch('manifest.json');
    if (!res.ok) throw new Error();
    allNotes = await res.json();
  } catch {
    showEmpty('Could not load manifest.json — make sure the file exists.');
    return;
  }
  renderGallery(allNotes);
  setupSearch();
  setupModal();
}

// ── Render ──

function renderGallery(notes) {
  const gallery  = document.getElementById('gallery');
  const empty    = document.getElementById('empty-state');
  const count    = document.getElementById('count');

  gallery.innerHTML = '';

  if (notes.length === 0) {
    empty.classList.remove('hidden');
    count.textContent = '';
    return;
  }

  empty.classList.add('hidden');
  count.textContent = notes.length === allNotes.length
    ? `${allNotes.length} note${allNotes.length !== 1 ? 's' : ''}`
    : `${notes.length} of ${allNotes.length} notes`;

  notes.forEach((note) => {
    gallery.appendChild(createCard(note));
  });
}

function createCard(note) {
  // Color index is tied to the note's position in the *original* list so it
  // stays stable when the user searches and cards are re-rendered.
  const colorIndex = allNotes.indexOf(note) % 4;
  const { fade } = COLORS[colorIndex];

  const card = document.createElement('div');
  card.className = 'card';
  card.dataset.colorIndex = colorIndex;
  card.dataset.filename   = note.filename;

  card.innerHTML = `
    <div class="card-title">${escapeHtml(note.title)}</div>
    <div class="card-date">${formatDate(note.date)}</div>
    <div class="card-preview-wrapper">
      <div class="card-preview">${marked.parse(note.preview || '')}</div>
      <div class="card-fade" style="background: linear-gradient(transparent, ${fade})"></div>
    </div>
  `;

  card.addEventListener('click', () => openModal(note));
  return card;
}

// ── Modal ──

function setupModal() {
  document.getElementById('modal-close').addEventListener('click', closeModal);

  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal-overlay')) closeModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });
}

async function openModal(note) {
  document.getElementById('modal-title').textContent = note.title;
  document.getElementById('modal-body').innerHTML = '<p style="color:#999;font-size:.9rem">Loading…</p>';
  document.getElementById('modal-overlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  try {
    const res = await fetch(`notes/${encodeURIComponent(note.filename)}`);
    if (!res.ok) throw new Error();
    const md = await res.text();
    document.getElementById('modal-body').innerHTML = marked.parse(md);
  } catch {
    document.getElementById('modal-body').innerHTML =
      `<p style="color:#c00">Could not load <code>${escapeHtml(note.filename)}</code>.</p>`;
  }

  document.getElementById('modal-body').scrollTop = 0;
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.body.style.overflow = '';
}

// ── Search ──

function setupSearch() {
  let timer;
  document.getElementById('search').addEventListener('input', (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = e.target.value.trim().toLowerCase();
      renderGallery(
        q ? allNotes.filter(n =>
              n.title.toLowerCase().includes(q) ||
              (n.preview || '').toLowerCase().includes(q)
            )
          : allNotes
      );
    }, 150);
  });
}

// ── Helpers ──

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function showEmpty(msg) {
  const el = document.getElementById('empty-state');
  el.querySelector('p').textContent = msg;
  el.classList.remove('hidden');
}

init();
