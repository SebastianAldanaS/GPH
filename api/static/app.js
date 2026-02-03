const form = document.getElementById('searchForm');
const status = document.getElementById('status');
const results = document.getElementById('results');
const suggestionsEl = document.getElementById('suggestions');
const qInput = document.getElementById('q');
const panelEl = document.querySelector('.autocomplete .panel');

let debounceTimer = null;
// Inline preview feature removed for accessibility; suggestions will focus and submit directly.

async function fetchSuggestions(q, cc, limit = 8) {
  if (!q || q.length < 2) {
    panelEl.hidden = true;
    suggestionsEl.innerHTML = '';
    return;
  }

  try {
    const params = new URLSearchParams({ q, cc, limit });
    const resp = await fetch(`/autocomplete?${params.toString()}`);
    if (!resp.ok) return;
    const data = await resp.json();

    suggestionsEl.innerHTML = '';
    if (!data.length) {
      suggestionsEl.hidden = true;
      return;
    }

    for (const s of data) {
      const li = document.createElement('li');
      li.tabIndex = 0;
      li.setAttribute('role', 'option');
      li.dataset.appid = s.appid;
      li.dataset.tiny = s.tiny_image || '';
      li.className = 'suggestion-item';

      // Create thumbnail if available
      if (s.tiny_image) {
        const img = document.createElement('img');
        img.src = s.tiny_image;
        img.alt = s.nombre;
        img.className = 'suggestion-thumb';
        li.appendChild(img);
      }

      const txt = document.createElement('div');
      txt.className = 'suggestion-text';
      txt.textContent = s.nombre;
      li.appendChild(txt);

      li.addEventListener('click', () => {
        qInput.value = s.nombre;
        panelEl.hidden = true;
        // Submit form with the selected suggestion
        form.requestSubmit();
      });

      li.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') {
          ev.preventDefault();
          li.click();
        } else if (ev.key === 'ArrowDown') {
          ev.preventDefault();
          li.nextElementSibling?.focus();
        } else if (ev.key === 'ArrowUp') {
          ev.preventDefault();
          li.previousElementSibling?.focus();
        }
      });

      suggestionsEl.appendChild(li);
    }

    suggestionsEl.hidden = false;
  } catch (err) {
    console.error('suggestions error', err);
    suggestionsEl.hidden = true;

  }
}

qInput.addEventListener('input', (e) => {
  clearTimeout(debounceTimer);
  const q = e.target.value.trim();
  const cc = document.getElementById('cc').value;
  debounceTimer = setTimeout(() => fetchSuggestions(q, cc, 8), 300);
});

qInput.addEventListener('keydown', (ev) => {
  if (ev.key === 'ArrowDown') {
    // move focus to first suggestion
    const first = suggestionsEl.querySelector('li');
    if (first) {
      ev.preventDefault();
      first.focus();
    }
  } else if (ev.key === 'Escape') {
    suggestionsEl.hidden = true;
  }
});

function clearResults() {
  document.getElementById('results-steam').innerHTML = '';
  document.getElementById('results-nuuvem').innerHTML = '';
  document.getElementById('results-fanatical').innerHTML = '';
  document.getElementById('results-greenmangaming').innerHTML = '';
  document.getElementById('results-instantgaming').innerHTML = '';
}

function renderResultsTo(store, data) {
  const container = document.getElementById(`results-${store}`);
  container.innerHTML = '';
  if (!data || !data.length) {
    container.innerHTML = `<li class="none">No hay resultados</li>`;
    return;
  }

  for (const item of data) {
    const li = document.createElement('li');
    li.className = 'result';

    if (item.tiny_image) {
      const img = document.createElement('img');
      img.className = 'thumb';
      img.src = item.tiny_image;
      img.alt = item.nombre;
      li.appendChild(img);
    }

    const meta = document.createElement('div');
    meta.className = 'meta';

    const name = document.createElement('div');
    name.className = 'name';
    name.textContent = item.nombre;

    const sub = document.createElement('div');
    sub.className = 'small';
    sub.innerHTML = `${item.appid ? `AppID: ${item.appid} • ` : ''}${item.moneda || ''}`;

    meta.appendChild(name);
    meta.appendChild(sub);

    const right = document.createElement('div');
    right.style.textAlign = 'right';

    const price = document.createElement('div');
    price.className = 'price';
    price.textContent = item.precio_final != null ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: item.moneda || 'COP' }).format(item.precio_final) : '—';

    // Badge for discount (if any)
    const badge = document.createElement('span');
    badge.className = 'badge-discount';
    const pct = item.porcentaje_descuento != null ? Number(item.porcentaje_descuento) : 0;
    if (pct > 0) {
      badge.textContent = `-${pct}%`;
      badge.setAttribute('aria-label', `Descuento ${pct} por ciento`);
    } else {
      badge.hidden = true;
    }

    const old = document.createElement('div');
    old.className = 'price-original small';
    old.textContent = item.precio_original ? `Antes: ${new Intl.NumberFormat('es-CO', { style: 'currency', currency: item.moneda || 'COP' }).format(item.precio_original)}` : '';

    const link = document.createElement('a');
    link.href = item.steam_url || item.url || '#';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'link small';
    link.textContent = store === 'steam' ? 'Abrir en Steam' : 'Abrir en tienda';

    const priceRow = document.createElement('div');
    priceRow.style.display = 'inline-flex';
    priceRow.style.alignItems = 'center';
    priceRow.style.gap = '8px';
    priceRow.appendChild(price);
    priceRow.appendChild(badge);

    right.appendChild(priceRow);
    right.appendChild(old);
    right.appendChild(link);

    li.appendChild(meta);
    li.appendChild(right);

    container.appendChild(li);
  }
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  suggestionsEl.hidden = true;
  clearResults();
  status.textContent = 'Buscando...';

  const q = document.getElementById('q').value.trim();
  const cc = document.getElementById('cc').value;
  const limit = document.getElementById('limit').value;
  // Siempre buscar en todas las tiendas
  const store = 'all';

  // show per-store busy indicator y log endpoint para depuración
  document.getElementById('results-steam').innerHTML = '<li class="none"><span class="spinner" aria-hidden="true"></span>Buscando...</li>';
  document.getElementById('results-nuuvem').innerHTML = '<li class="none"><span class="spinner" aria-hidden="true"></span>Buscando...</li>';
  document.getElementById('results-fanatical').innerHTML = '<li class="none"><span class="spinner" aria-hidden="true"></span>Buscando...</li>';
  document.getElementById('results-greenmangaming').innerHTML = '<li class="none"><span class="spinner" aria-hidden="true"></span>Buscando...</li>';
  document.getElementById('results-instantgaming').innerHTML = '<li class="none"><span class="spinner" aria-hidden="true"></span>Buscando...</li>';
  console.debug('Search started:', { q, cc, limit, store });

  if (!q) {
    status.textContent = 'Introduce un término de búsqueda.';
    return;
  }

  try {
    const params = new URLSearchParams({ q, cc, limit });

    // Siempre buscar en todas las tiendas
    const [steamRes, nuuRes, fanRes, gmgRes, igRes] = await Promise.allSettled([
      fetch(`/search?${params.toString()}`).then(r => r.ok ? r.json() : r.json().then(e => {throw e})),
      fetch(`/nuuvem?${params.toString()}`).then(r => r.ok ? r.json() : r.json().then(e => {throw e})),
      fetch(`/fanatical?${params.toString()}`).then(r => r.ok ? r.json() : r.json().then(e => {throw e})),
      fetch(`/greenmangaming?${params.toString()}`).then(r => r.ok ? r.json() : r.json().then(e => {throw e})),
      fetch(`/instantgaming?${params.toString()}`).then(r => r.ok ? r.json() : r.json().then(e => {throw e})),
    ]);

    if (steamRes.status === 'fulfilled') {
      renderResultsTo('steam', steamRes.value);
    } else {
      document.getElementById('results-steam').innerHTML = `<li class="error">Error: ${steamRes.reason?.detail || 'Falló Steam'}</li>`;
    }

    if (nuuRes.status === 'fulfilled') {
      renderResultsTo('nuuvem', nuuRes.value);
    } else {
      document.getElementById('results-nuuvem').innerHTML = `<li class="error">Error: ${nuuRes.reason?.detail || 'Falló Nuuvem'}</li>`;
    }

    if (fanRes.status === 'fulfilled') {
      renderResultsTo('fanatical', fanRes.value);
    } else {
      document.getElementById('results-fanatical').innerHTML = `<li class="error">Error: ${fanRes.reason?.detail || 'Falló Fanatical'}</li>`;
    }

    if (gmgRes.status === 'fulfilled') {
      renderResultsTo('greenmangaming', gmgRes.value);
    } else {
      document.getElementById('results-greenmangaming').innerHTML = `<li class="error">Error: ${gmgRes.reason?.detail || 'Falló GreenManGaming'}</li>`;
    }

    if (igRes.status === 'fulfilled') {
      renderResultsTo('instantgaming', igRes.value);
    } else {
      document.getElementById('results-instantgaming').innerHTML = `<li class="error">Error: ${igRes.reason?.detail || 'Falló Instant Gaming'}</li>`;
    }

    status.textContent = 'Búsqueda completada.';
  } catch (err) {
    console.error(err);
    status.textContent = 'Error al consultar la API.';
  }
});