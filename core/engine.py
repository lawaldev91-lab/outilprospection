"""
Moteur de scraping avec contrôle start/stop et tracking en temps réel.
"""
import threading
import time
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class ScrapingEngine:
    """Moteur de scraping avec contrôle d'exécution."""
    
    def __init__(self):
        self.is_running = False
        self.stop_event = threading.Event()
        self.results = []
        self.start_time = None
        self.end_time = None
        self.progress = {
            'current_source': '',
            'completed_sources': [],
            'total_sources': 0,
            'posts_scraped': 0,
        }
        self.progress['completed_sources'] = []
        self.progress['posts_scraped'] = 0
        self._lock = threading.Lock()
    
    def run(self):
        """Exécute le scraping complet."""
        from core.config import SOURCES
        from core.classifier import filter_relevant
        
        self.is_running = True
        self.stop_event.clear()
        self.results = []
        self.start_time = datetime.now()
        self.end_time = None
        
        # Réinitialiser la progression
        with self._lock:
            self.progress = {
                'current_source': '',
                'completed_sources': [],
                'total_sources': 0,
                'posts_scraped': 0,
            }
        
        try:
            # Sources actives
            active_sources = [name for name, enabled in SOURCES.items() if enabled]
            self.progress['total_sources'] = len(active_sources)
            
            print(f"\n🚀 Démarrage du scraping — {len(active_sources)} sources actives")
            
            # Collecte parallèle
            all_raw = []
            source_counts = {}
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._run_scraper, src): src
                    for src in active_sources
                }
                
                for future in as_completed(futures):
                    # Vérifier si on doit arrêter
                    if self.stop_event.is_set():
                        print("\n⏹️  Arrêt demandé — finalisation...")
                        break
                    
                    src = futures[future]
                    try:
                        name, results = future.result(timeout=30)
                        source_counts[name] = len(results)
                        all_raw.extend(results)
                        
                        with self._lock:
                            self.progress['completed_sources'].append(name)
                            self.progress['posts_scraped'] += len(results)
                        
                        print(f"  ✓ {name}: {len(results)} posts")
                        
                    except Exception as e:
                        print(f"  ✗ {src}: Erreur — {e}")
            
            # Vérifier arrêt
            if self.stop_event.is_set():
                print("⏹️  Scraping arrêté par l'utilisateur")
                # Sauvegarder les résultats partiels
                if all_raw:
                    seen_ids = set()
                    unique_raw = []
                    for p in all_raw:
                        if p["id"] not in seen_ids:
                            seen_ids.add(p["id"])
                            unique_raw.append(p)
                    
                    filtered = filter_relevant(unique_raw)
                    self.results = filtered
                    self._save_results(filtered)
                    print(f"💾 {len(filtered)} résultats partiels sauvegardés")
                
                self.end_time = datetime.now()
                self.is_running = False
                return
            
            print(f"\n📊 Collecte terminée — {len(all_raw)} posts bruts")
            
            # Déduplication
            seen_ids = set()
            unique_raw = []
            for p in all_raw:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    unique_raw.append(p)
            
            print(f"🎯 Classification et filtrage strict...")
            filtered = filter_relevant(unique_raw)
            print(f"  → {len(filtered)} résultats pertinents (filtrage strict FR)")
            
            # Sauvegarder
            self.results = filtered
            self._save_results(filtered)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"\n✅ Terminé en {duration:.1f}s — {len(filtered)} opportunités")
            
            # Sauvegarder l'historique
            try:
                from core.history import HistoryManager
                history = HistoryManager()
                session_id = history.save_session(filtered, duration)
                print(f"📈 Historique sauvegardé (session #{session_id})")
            except Exception as e:
                print(f"⚠️  Erreur historique: {e}")
            
            # Envoyer notification email
            try:
                from core.notifier import EmailNotifier
                notifier = EmailNotifier()
                if notifier.is_configured():
                    print("📧 Envoi de la notification email...")
                    notifier.send_results(filtered, duration)
            except Exception as e:
                print(f"⚠️  Erreur notification: {e}")
            
            print()
            
        except Exception as e:
            print(f"\n❌ Erreur critique: {e}")
        finally:
            self.is_running = False
    
    def _run_scraper(self, name: str):
        """Lance un scraper individuel."""
        # Vérifier arrêt avant de commencer
        if self.stop_event.is_set():
            return name, []
        
        with self._lock:
            self.progress['current_source'] = name
        
        try:
            if name == "hackernews":
                from core.scrapers.hackernews import fetch
            elif name == "reddit":
                from core.scrapers.reddit import fetch
            elif name == "devto":
                from core.scrapers.devto import fetch
            elif name == "malt":
                from core.scrapers.malt import fetch
            elif name == "indiehackers":
                from core.scrapers.indiehackers import fetch
            elif name == "alsacreations":
                from core.scrapers.alsacreations import fetch
            elif name == "freework":
                from core.scrapers.freework import fetch
            elif name == "remotive":
                from core.scrapers.remotive import fetch
            elif name == "remoteok":
                from core.scrapers.remoteok import fetch
            elif name == "himalayas":
                from core.scrapers.himalayas import fetch
            else:
                return name, []
            
            results = fetch()
            return name, results
            
        except Exception as e:
            print(f"  ✗ [{name}] Erreur: {e}")
            return name, []
    
    def stop(self):
        """Demande l'arrêt du scraping."""
        print("\n⏹️  Demande d'arrêt...")
        self.stop_event.set()
    
    def get_progress(self):
        """Retourne la progression actuelle."""
        with self._lock:
            return self.progress.copy()
    
    def get_results(self):
        """Retourne les résultats."""
        with self._lock:
            return self.results.copy()
    
    def _save_results(self, results):
        """Sauvegarde les résultats en JSON et HTML."""
        from core.config import RESULTS_DIR
        
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # JSON
        json_path = os.path.join(RESULTS_DIR, f"{date_str}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Résultats sauvegardés: {json_path}")
        
        # HTML (rapport)
        try:
            from core.report import generate
            html_path = generate(results)
            print(f"📄 Rapport HTML généré: {html_path}")
        except Exception as e:
            print(f"⚠️  Erreur génération rapport: {e}")
