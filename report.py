"""
Générateur de rapport HTML interactif.
Produit un fichier HTML autonome (tout intégré, pas de dépendances CDN requises)
avec filtres, tri et export CSV.
"""
import json
import os
from datetime import datetime
from config import CATEGORIES, RESULTS_DIR


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rapport Prospection — {date}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  :root {{
    --bg:        #0d0f14;
    --surface:   #161a22;
    --surface2:  #1e2330;
    --border:    #2a3040;
    --accent:    #6366f1;
    --accent2:   #8b5cf6;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --success:   #10b981;
    --warning:   #f59e0b;
    --danger:    #ef4444;
    --radius:    12px;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 0 0 60px;
  }}

  /* ── Header ── */
  .header {{
    background: linear-gradient(135deg, #1a1d2e 0%, #0d0f14 100%);
    border-bottom: 1px solid var(--border);
    padding: 32px 40px 28px;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
  }}
  .header-inner {{
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
  }}
  .logo {{
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    white-space: nowrap;
  }}
  .stats-pill {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 6px 16px;
    font-size: 13px;
    color: var(--muted);
    white-space: nowrap;
  }}
  .stats-pill strong {{ color: var(--text); }}
  .export-btn {{
    margin-left: auto;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity .2s, transform .1s;
    white-space: nowrap;
  }}
  .export-btn:hover {{ opacity: .85; transform: translateY(-1px); }}

  /* ── Filters ── */
  .filters {{
    max-width: 1400px;
    margin: 28px auto 0;
    padding: 0 40px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }}
  .filter-label {{ color: var(--muted); font-size: 12px; font-weight: 500; }}
  .pill-btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 7px 16px;
    font-size: 13px;
    color: var(--muted);
    cursor: pointer;
    transition: all .15s;
    white-space: nowrap;
  }}
  .pill-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
  .pill-btn.active {{
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-color: transparent;
    color: #fff;
    font-weight: 600;
  }}
  .sort-select {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    color: var(--text);
    cursor: pointer;
    outline: none;
    margin-left: auto;
  }}
  .search-input {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    color: var(--text);
    outline: none;
    min-width: 220px;
    transition: border-color .15s;
  }}
  .search-input:focus {{ border-color: var(--accent); }}
  .search-input::placeholder {{ color: var(--muted); }}

  /* ── Grid ── */
  .grid {{
    max-width: 1400px;
    margin: 28px auto 0;
    padding: 0 40px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 18px;
  }}

  /* ── Card ── */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: transform .2s, box-shadow .2s, border-color .2s;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    position: relative;
    overflow: hidden;
  }}
  .card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    opacity: 0;
    transition: opacity .2s;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(99,102,241,.15);
    border-color: rgba(99,102,241,.4);
  }}
  .card:hover::before {{ opacity: 1; }}

  .card-header {{ display: flex; align-items: flex-start; gap: 10px; }}
  .card-title {{
    font-size: 15px;
    font-weight: 600;
    line-height: 1.4;
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .score-badge {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .score-high   {{ border-color: var(--success); color: var(--success); }}
  .score-medium {{ border-color: var(--warning); color: var(--warning); }}
  .score-low    {{ border-color: var(--muted);   color: var(--muted); }}

  .card-body {{
    font-size: 13px;
    color: var(--muted);
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}

  .card-tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .tag {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 500;
    color: var(--muted);
  }}
  .tag-cat {{
    background: rgba(99,102,241,.12);
    border-color: rgba(99,102,241,.3);
    color: #a5b4fc;
  }}

  .card-footer {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--muted);
  }}
  .source-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
  }}
  .contact-badge {{
    margin-left: auto;
    background: rgba(16,185,129,.1);
    border: 1px solid rgba(16,185,129,.3);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    color: var(--success);
    font-weight: 500;
  }}

  /* ── Empty state ── */
  .empty {{
    text-align: center;
    padding: 80px 20px;
    color: var(--muted);
    display: none;
  }}
  .empty h3 {{ font-size: 18px; margin-bottom: 8px; }}

  /* ── Responsive ── */
  @media (max-width: 768px) {{
    .header {{ padding: 20px; }}
    .filters, .grid {{ padding: 0 16px; }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div class="logo">🔍 Prospection</div>
    <div class="stats-pill">
      Généré le <strong>{date}</strong> à <strong>{time}</strong>
    </div>
    <div class="stats-pill">
      <strong id="visible-count">{total}</strong> résultats
    </div>
    <button class="export-btn" onclick="exportCSV()">⬇ Exporter CSV</button>
  </div>
</div>

<div class="filters">
  <span class="filter-label">Catégorie :</span>
  <button class="pill-btn active" onclick="filterCat('all', this)">Toutes</button>
  {cat_buttons}
  <span class="filter-label" style="margin-left:8px">Source :</span>
  {source_buttons}
  <input class="search-input" type="text" placeholder="🔍 Rechercher..." oninput="filterSearch(this.value)">
  <select class="sort-select" onchange="sortCards(this.value)">
    <option value="score">Trier : Score ↓</option>
    <option value="date">Trier : Date ↓</option>
    <option value="source">Trier : Source</option>
  </select>
</div>

<div class="grid" id="grid">
  {cards}
</div>
<div class="empty" id="empty">
  <h3>Aucun résultat</h3>
  <p>Modifiez vos filtres ou relancez une prospection.</p>
</div>

<script>
const ALL_DATA = {json_data};

let currentCat    = 'all';
let currentSource = 'all';
let currentSearch = '';
let currentSort   = 'score';

function filterCat(cat, btn) {{
  currentCat = cat;
  document.querySelectorAll('.pill-cat').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  render();
}}
function filterSource(src, btn) {{
  currentSource = src;
  document.querySelectorAll('.pill-src').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  render();
}}
function filterSearch(val) {{
  currentSearch = val.toLowerCase();
  render();
}}
function sortCards(val) {{
  currentSort = val;
  render();
}}

function render() {{
  let items = [...ALL_DATA];

  if (currentCat !== 'all')
    items = items.filter(d => d.categories.some(c => c.name === currentCat));

  if (currentSource !== 'all')
    items = items.filter(d => d.source === currentSource);

  if (currentSearch)
    items = items.filter(d =>
      d.title.toLowerCase().includes(currentSearch) ||
      d.body.toLowerCase().includes(currentSearch)
    );

  if (currentSort === 'score')
    items.sort((a,b) => b.score - a.score);
  else if (currentSort === 'date')
    items.sort((a,b) => (b.date||'').localeCompare(a.date||''));
  else
    items.sort((a,b) => a.source.localeCompare(b.source));

  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  document.getElementById('visible-count').textContent = items.length;

  if (items.length === 0) {{
    grid.innerHTML = '';
    empty.style.display = 'block';
    return;
  }}
  empty.style.display = 'none';
  grid.innerHTML = items.map(cardHTML).join('');
}}

function cardHTML(d) {{
  const scoreClass = d.score >= 7 ? 'score-high' : d.score >= 4 ? 'score-medium' : 'score-low';
  const cats = d.categories.map(c =>
    `<span class="tag tag-cat">${{c.icon}} ${{c.name}}</span>`
  ).join('');
  const contact = d.contact
    ? `<span class="contact-badge">📧 Contact</span>` : '';
  return `
  <a class="card" href="${{d.url}}" target="_blank" rel="noopener">
    <div class="card-header">
      <div class="card-title">${{escHtml(d.title)}}</div>
      <div class="score-badge ${{scoreClass}}">${{d.score}}/10</div>
    </div>
    ${{d.body ? `<div class="card-body">${{escHtml(d.body)}}</div>` : ''}}
    <div class="card-tags">${{cats}}</div>
    <div class="card-footer">
      <span class="source-dot"></span>
      <span>${{escHtml(d.source)}}</span>
      ${{d.date ? `<span>·</span><span>${{d.date}}</span>` : ''}}
      ${{contact}}
    </div>
  </a>`;
}}

function escHtml(str) {{
  return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function exportCSV() {{
  const items = ALL_DATA;
  const rows = [['Titre','URL','Source','Date','Score','Catégories','Contact']];
  items.forEach(d => {{
    rows.push([
      d.title, d.url, d.source, d.date, d.score,
      d.categories.map(c=>c.name).join(' | '),
      d.contact
    ]);
  }});
  const csv = rows.map(r => r.map(v => `"${{String(v||'').replace(/"/g,'""')}}"`).join(',')).join('\\n');
  const blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'prospection_{date}.csv';
  a.click();
}}
</script>
</body>
</html>"""


def generate(results: list[dict]) -> str:
    """
    Génère le rapport HTML et le sauvegarde dans le dossier results/.
    Retourne le chemin absolu du fichier généré.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Boutons catégories
    all_cats = list(CATEGORIES.keys())
    cat_buttons = "\n".join(
        f'<button class="pill-btn pill-cat" onclick="filterCat({json.dumps(c)}, this)">'
        f'{CATEGORIES[c]["icon"]} {c}</button>'
        for c in all_cats
    )

    # Boutons sources
    sources = sorted({r["source"] for r in results})
    source_buttons = "\n".join(
        f'<button class="pill-btn pill-src" onclick="filterSource({json.dumps(s)}, this)">{s}</button>'
        for s in sources
    )

    # Cards HTML statiques (fallback si JS désactivé)
    cards_html = ""
    for r in results:
        score_class = (
            "score-high" if r["score"] >= 7
            else "score-medium" if r["score"] >= 4
            else "score-low"
        )
        cats_html = "".join(
            f'<span class="tag tag-cat">{c["icon"]} {c["name"]}</span>'
            for c in r["categories"]
        )
        contact_html = (
            '<span class="contact-badge">📧 Contact</span>'
            if r.get("contact") else ""
        )
        cards_html += f"""
        <a class="card" href="{r['url']}" target="_blank" rel="noopener">
          <div class="card-header">
            <div class="card-title">{r['title'][:120]}</div>
            <div class="score-badge {score_class}">{r['score']}/10</div>
          </div>
          {f'<div class="card-body">{r["body"][:300]}</div>' if r.get("body") else ""}
          <div class="card-tags">{cats_html}</div>
          <div class="card-footer">
            <span class="source-dot"></span>
            <span>{r['source']}</span>
            {f'<span>·</span><span>{r["date"]}</span>' if r.get("date") else ""}
            {contact_html}
          </div>
        </a>"""

    # Données JSON pour le JS interactif
    json_data = json.dumps(results, ensure_ascii=False, indent=None)

    html = HTML_TEMPLATE.format(
        date=date_str,
        time=time_str,
        total=len(results),
        cat_buttons=cat_buttons,
        source_buttons=source_buttons,
        cards=cards_html,
        json_data=json_data,
    )

    output_path = os.path.join(RESULTS_DIR, f"report_{date_str}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Également sauvegarder les données brutes en JSON
    json_path = os.path.join(RESULTS_DIR, f"{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return os.path.abspath(output_path)
