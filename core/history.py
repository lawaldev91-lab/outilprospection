"""
Module d'historique — stocke et compare les résultats de prospection jour après jour.
Utilise SQLite pour la persistance locale.
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class HistoryManager:
    """Gère l'historique des sessions de prospection."""
    
    def __init__(self, db_path: str = "results/history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialise la base de données."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    results_count INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    sources JSON NOT NULL,
                    categories JSON NOT NULL,
                    top_results JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def save_session(
        self,
        results: List[Dict],
        duration: float,
        date: Optional[str] = None
    ) -> int:
        """
        Sauvegarde une session de prospection.
        
        Args:
            results: Liste des résultats
            duration: Durée en secondes
            date: Date de la session (format YYYY-MM-DD), par défaut aujourd'hui
            
        Returns:
            ID de la session
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Statistiques
        sources = {}
        categories = {}
        for r in results:
            src = r['source']
            sources[src] = sources.get(src, 0) + 1
            
            for cat in r['categories']:
                cat_name = cat['name']
                categories[cat_name] = categories.get(cat_name, 0) + 1
        
        # Top 10 résultats
        top_results = [
            {
                'title': r['title'][:100],
                'score': r['score'],
                'source': r['source'],
                'url': r['url'],
                'categories': [c['name'] for c in r['categories']]
            }
            for r in results[:10]
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            # Mettre à jour si la date existe déjà, sinon insérer
            existing = conn.execute(
                "SELECT id FROM sessions WHERE date = ?", (date,)
            ).fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE sessions
                    SET results_count = ?, duration = ?, sources = ?, 
                        categories = ?, top_results = ?
                    WHERE date = ?
                """, (
                    len(results), duration, json.dumps(sources),
                    json.dumps(categories), json.dumps(top_results), date
                ))
                session_id = existing[0]
            else:
                cursor = conn.execute("""
                    INSERT INTO sessions (date, results_count, duration, sources, categories, top_results)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    date, len(results), duration, json.dumps(sources),
                    json.dumps(categories), json.dumps(top_results)
                ))
                session_id = cursor.lastrowid
            
            conn.commit()
        
        return session_id
    
    def get_history(self, days: int = 30) -> List[Dict]:
        """
        Récupère l'historique des N derniers jours.
        
        Args:
            days: Nombre de jours à récupérer (défaut 30)
            
        Returns:
            Liste des sessions triées par date décroissante
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM sessions
                WHERE date >= date('now', ?)
                ORDER BY date DESC
            """, (f'-{days} days',)).fetchall()
            
            return [self._row_to_dict(row) for row in rows]
    
    def get_comparison(self, days: int = 7) -> Dict:
        """
        Compare les statistiques sur les N derniers jours.
        
        Args:
            days: Nombre de jours pour la comparaison
            
        Returns:
            Dictionnaire avec les statistiques comparatives
        """
        history = self.get_history(days)
        
        if not history:
            return {
                'period': days,
                'sessions': 0,
                'avg_results': 0,
                'avg_duration': 0,
                'total_results': 0,
                'best_day': None,
                'sources_trend': {},
                'categories_trend': {},
                'results_evolution': []
            }
        
        # Statistiques globales
        total_results = sum(s['results_count'] for s in history)
        avg_results = total_results / len(history)
        avg_duration = sum(s['duration'] for s in history) / len(history)
        
        # Meilleur jour
        best_day = max(history, key=lambda s: s['results_count'])
        
        # Tendances par source
        sources_trend = {}
        for session in history:
            for src, count in session['sources'].items():
                if src not in sources_trend:
                    sources_trend[src] = []
                sources_trend[src].append({
                    'date': session['date'],
                    'count': count
                })
        
        # Tendances par catégorie
        categories_trend = {}
        for session in history:
            for cat, count in session['categories'].items():
                if cat not in categories_trend:
                    categories_trend[cat] = []
                categories_trend[cat].append({
                    'date': session['date'],
                    'count': count
                })
        
        # Évolution des résultats
        results_evolution = [
            {
                'date': s['date'],
                'count': s['results_count'],
                'duration': s['duration']
            }
            for s in reversed(history)
        ]
        
        return {
            'period': days,
            'sessions': len(history),
            'avg_results': round(avg_results, 1),
            'avg_duration': round(avg_duration, 1),
            'total_results': total_results,
            'best_day': {
                'date': best_day['date'],
                'count': best_day['results_count']
            },
            'sources_trend': sources_trend,
            'categories_trend': categories_trend,
            'results_evolution': results_evolution
        }
    
    def get_source_stats(self, days: int = 30) -> Dict[str, Dict]:
        """
        Statistiques détaillées par source.
        
        Returns:
            Dictionnaire avec stats par source
        """
        history = self.get_history(days)
        
        stats = {}
        for session in history:
            for src, count in session['sources'].items():
                if src not in stats:
                    stats[src] = {
                        'total': 0,
                        'sessions': 0,
                        'avg': 0,
                        'max': 0,
                        'dates': []
                    }
                
                stats[src]['total'] += count
                stats[src]['sessions'] += 1
                stats[src]['max'] = max(stats[src]['max'], count)
                stats[src]['dates'].append({
                    'date': session['date'],
                    'count': count
                })
        
        # Calculer les moyennes
        for src in stats:
            stats[src]['avg'] = round(
                stats[src]['total'] / stats[src]['sessions'], 1
            )
        
        return stats
    
    def _row_to_dict(self, row) -> Dict:
        """Convertit une ligne SQLite en dictionnaire."""
        return {
            'id': row['id'],
            'date': row['date'],
            'results_count': row['results_count'],
            'duration': row['duration'],
            'sources': json.loads(row['sources']),
            'categories': json.loads(row['categories']),
            'top_results': json.loads(row['top_results']),
            'created_at': row['created_at']
        }
    
    def cleanup(self, days: int = 90):
        """
        Supprime les sessions de plus de N jours.
        
        Args:
            days: Nombre de jours à conserver
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM sessions
                WHERE date < date('now', ?)
            """, (f'-{days} days',))
            conn.commit()
