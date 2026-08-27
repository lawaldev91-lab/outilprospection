#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║    OUTIL DE PROSPECTION v2.0 — Application Web       ║
║    Usage : python app.py                              ║
╚══════════════════════════════════════════════════════╝
"""
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Configuration .env chargée")
except ImportError:
    pass

# Configuration du logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import du moteur de scraping
from core.engine import ScrapingEngine

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.urandom(24)
app.config['JSON_AS_ASCII'] = False

# Instance globale du moteur
engine = ScrapingEngine()


@app.route('/')
def index():
    """Page d'accueil — dashboard principal."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Retourne l'état actuel du moteur."""
    return jsonify({
        'running': engine.is_running,
        'progress': engine.get_progress(),
        'results_count': len(engine.results),
        'start_time': engine.start_time.isoformat() if engine.start_time else None,
    })


@app.route('/api/start', methods=['POST'])
def start_scraping():
    """Démarre le scraping."""
    if engine.is_running:
        return jsonify({'success': False, 'error': 'Scraping déjà en cours'}), 400
    
    # Lancer dans un thread séparé
    thread = threading.Thread(target=engine.run)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Scraping démarré'})


@app.route('/api/stop', methods=['POST'])
def stop_scraping():
    """Arrête le scraping."""
    if not engine.is_running:
        return jsonify({'success': False, 'error': 'Aucun scraping en cours'}), 400
    
    engine.stop()
    return jsonify({'success': True, 'message': 'Arrêt demandé'})


@app.route('/api/results')
def get_results():
    """Retourne les résultats du dernier scraping."""
    results = engine.get_results()
    
    # Si pas de résultats en mémoire, charger le dernier scan
    if not results:
        results = _load_latest_results()
    
    # Filtrage optionnel par source ou catégorie
    source_filter = request.args.get('source')
    category_filter = request.args.get('category')
    
    if source_filter:
        results = [r for r in results if r['source'] == source_filter]
    
    if category_filter:
        results = [r for r in results if any(c['name'] == category_filter for c in r['categories'])]
    
    return jsonify({
        'results': results,
        'total': len(results),
        'generated_at': engine.end_time.isoformat() if engine.end_time else None,
    })


def _load_latest_results():
    """Charge les résultats du dernier scan sauvegardé."""
    import json
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    if not os.path.exists(results_dir):
        return []
    
    json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    if not json_files:
        return []
    
    latest = sorted(json_files)[-1]
    try:
        with open(os.path.join(results_dir, latest), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


@app.route('/api/results/latest')
def get_latest_results():
    """Retourne les résultats du dernier scan sauvegardé."""
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    if not os.path.exists(results_dir):
        return jsonify({'results': [], 'total': 0})
    
    # Trouver le dernier fichier JSON
    json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    if not json_files:
        return jsonify({'results': [], 'total': 0})
    
    latest = sorted(json_files)[-1]
    with open(os.path.join(results_dir, latest), 'r', encoding='utf-8') as f:
        import json
        results = json.load(f)
    
    return jsonify({
        'results': results,
        'total': len(results),
        'generated_at': latest.replace('.json', ''),
    })


@app.route('/api/results/history')
def get_results_history():
    """Retourne l'historique des scans (anciens fichiers JSON)."""
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    if not os.path.exists(results_dir):
        return jsonify({'history': []})
    
    json_files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')], reverse=True)
    history = []
    
    for f in json_files[:10]:  # 10 derniers scans max
        filepath = os.path.join(results_dir, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            import json
            results = json.load(file)
            history.append({
                'date': f.replace('.json', ''),
                'count': len(results),
                'sources': list(set(r['source'] for r in results)),
            })
    
    return jsonify({'history': history})


@app.route('/report/<date>')
def view_report(date):
    """Affiche un rapport HTML d'une date spécifique."""
    report_path = os.path.join('results', f'report_{date}.html')
    if os.path.exists(report_path):
        return send_from_directory('results', f'report_{date}.html')
    return "Rapport non trouvé", 404


@app.route('/api/history')
def get_history():
    """Retourne l'historique des sessions de prospection."""
    from core.history import HistoryManager
    
    days = request.args.get('days', 30, type=int)
    history = HistoryManager()
    data = history.get_history(days)
    
    return jsonify({
        'history': data,
        'count': len(data),
        'period': days
    })


@app.route('/api/history/comparison')
def get_comparison():
    """Retourne les statistiques comparatives."""
    from core.history import HistoryManager
    
    days = request.args.get('days', 7, type=int)
    history = HistoryManager()
    data = history.get_comparison(days)
    
    return jsonify(data)


@app.route('/api/history/sources')
def get_source_stats():
    """Retourne les statistiques par source."""
    from core.history import HistoryManager
    
    days = request.args.get('days', 30, type=int)
    history = HistoryManager()
    data = history.get_source_stats(days)
    
    return jsonify({
        'sources': data,
        'period': days
    })


@app.route('/history')
def history_page():
    """Page d'historique avec graphiques."""
    return render_template('history.html')


@app.route('/api/custom-scrape', methods=['POST'])
def custom_scrape():
    """Scrape une ou plusieurs URLs personnalisées."""
    from core.custom_scraper import scrape_url, scrape_multiple_urls
    
    data = request.json
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    urls = data.get('urls', [])
    strict = data.get('strict', True)
    
    if not urls:
        return jsonify({'error': 'Aucune URL fournie'}), 400
    
    if not isinstance(urls, list):
        urls = [urls]
    
    # Limite de sécurité
    if len(urls) > 10:
        return jsonify({'error': 'Maximum 10 URLs par requête'}), 400
    
    if len(urls) == 1:
        result = scrape_url(urls[0], strict=strict)
    else:
        result = scrape_multiple_urls(urls, strict=strict)
    
    return jsonify(result)


@app.route('/api/export/csv')
def export_csv():
    """Exporte les résultats en CSV."""
    import csv
    import io
    
    results = engine.get_results()
    if not results:
        return jsonify({'error': 'Aucun résultat à exporter'}), 404
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Titre', 'URL', 'Source', 'Date', 'Score', 'Catégories', 'Contact'])
    
    for r in results:
        writer.writerow([
            r['title'],
            r['url'],
            r['source'],
            r.get('date', ''),
            r['score'],
            ' | '.join(c['name'] for c in r['categories']),
            r.get('contact', ''),
        ])
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=prospection_{datetime.now().strftime("%Y-%m-%d")}.csv'}
    )


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔍 Outil de Prospection v2.0")
    print("="*60)
    print(f"\n🌐 Interface web : http://localhost:5000")
    print(f"📅 Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Port pour Render.com (utilise PORT env var)
    port = int(os.environ.get('PORT', 5000))
    
    # Debug mode pour le développement local
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
