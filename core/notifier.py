"""
Module de notification email — envoie les résultats par email après chaque scraping.
Supporte Gmail SMTP (gratuit) ou tout serveur SMTP personnalisé.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict


class EmailNotifier:
    """Envoie des notifications email avec les résultats de prospection."""
    
    def __init__(self):
        # Configuration depuis variables d'environnement
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.recipient_email = os.getenv('NOTIFICATION_EMAIL', '')
        self.enabled = os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
        
    def is_configured(self) -> bool:
        """Vérifie si l'email est configuré."""
        return all([
            self.enabled,
            self.smtp_user,
            self.smtp_password,
            self.recipient_email
        ])
    
    def send_results(self, results: List[Dict], duration: float) -> bool:
        """
        Envoie les résultats par email.
        
        Args:
            results: Liste des résultats de prospection
            duration: Durée du scraping en secondes
            
        Returns:
            True si l'email a été envoyé avec succès
        """
        if not self.is_configured():
            print("⚠️  Notifications email non configurées")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔍 Prospection : {len(results)} opportunités trouvées"
            msg['From'] = self.smtp_user
            msg['To'] = self.recipient_email
            
            # Version texte
            text_content = self._build_text_content(results, duration)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Version HTML
            html_content = self._build_html_content(results, duration)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Envoyer
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email envoyé à {self.recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
            return False
    
    def _build_text_content(self, results: List[Dict], duration: float) -> str:
        """Construit le contenu texte de l'email."""
        date_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
        
        content = f"""
🔍 RAPPORT DE PROSPECTION
{date_str}

✅ {len(results)} opportunités trouvées en {duration:.1f}s

"""
        
        # Top 10 résultats
        content += "📊 TOP 10 DES OPPORTUNITÉS :\n"
        content += "=" * 60 + "\n\n"
        
        for i, r in enumerate(results[:10], 1):
            cats = ', '.join(f"{c['icon']} {c['name']}" for c in r['categories'])
            content += f"{i}. [{r['score']}/10] {r['title']}\n"
            content += f"   Source: {r['source']} | Catégories: {cats}\n"
            content += f"   Lien: {r['url']}\n\n"
        
        # Statistiques par source
        content += "\n📈 STATISTIQUES PAR SOURCE :\n"
        content += "=" * 60 + "\n\n"
        
        sources = {}
        for r in results:
            src = r['source']
            sources[src] = sources.get(src, 0) + 1
        
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            content += f"  • {src}: {count} résultat(s)\n"
        
        content += f"""

---
Outil de Prospection v2.0
{date_str}
"""
        
        return content.strip()
    
    def _build_html_content(self, results: List[Dict], duration: float) -> str:
        """Construit le contenu HTML de l'email."""
        date_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
        
        # Top 10 résultats
        results_html = ""
        for i, r in enumerate(results[:10], 1):
            cats = ', '.join(f"{c['icon']} {c['name']}" for c in r['categories'])
            score_color = "#10b981" if r['score'] >= 7 else "#f59e0b" if r['score'] >= 4 else "#64748b"
            
            results_html += f"""
            <div style="background:#f8fafc;border-left:4px solid {score_color};padding:16px;margin-bottom:12px;border-radius:8px;">
                <div style="font-weight:600;color:#1e293b;margin-bottom:8px;">
                    {i}. {r['title']}
                </div>
                <div style="font-size:14px;color:#64748b;margin-bottom:8px;">
                    <span style="display:inline-block;background:{score_color};color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">
                        {r['score']}/10
                    </span>
                    <span style="margin-left:8px;">{r['source']}</span>
                </div>
                <div style="font-size:13px;color:#94a3b8;margin-bottom:8px;">
                    {cats}
                </div>
                <a href="{r['url']}" style="color:#6366f1;text-decoration:none;font-size:13px;">
                    Voir l'opportunité →
                </a>
            </div>
            """
        
        # Statistiques par source
        sources = {}
        for r in results:
            src = r['source']
            sources[src] = sources.get(src, 0) + 1
        
        sources_html = ""
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            sources_html += f"""
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e2e8f0;">
                <span style="color:#475569;">{src}</span>
                <span style="color:#6366f1;font-weight:600;">{count}</span>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
            <div style="max-width:600px;margin:0 auto;background:white;">
                <!-- Header -->
                <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px;text-align:center;">
                    <h1 style="color:white;margin:0;font-size:28px;">🔍 Prospection Terminée</h1>
                    <p style="color:rgba(255,255,255,0.9);margin:8px 0 0 0;font-size:14px;">
                        {date_str}
                    </p>
                </div>
                
                <!-- Stats principales -->
                <div style="padding:32px;text-align:center;background:#f8fafc;">
                    <div style="display:inline-block;margin:0 24px;">
                        <div style="font-size:42px;font-weight:700;color:#6366f1;">{len(results)}</div>
                        <div style="color:#64748b;font-size:14px;">Opportunités</div>
                    </div>
                    <div style="display:inline-block;margin:0 24px;">
                        <div style="font-size:42px;font-weight:700;color:#10b981;">{duration:.1f}s</div>
                        <div style="color:#64748b;font-size:14px;">Durée</div>
                    </div>
                </div>
                
                <!-- Top résultats -->
                <div style="padding:32px;">
                    <h2 style="color:#1e293b;font-size:20px;margin:0 0 20px 0;">📊 Top 10 des opportunités</h2>
                    {results_html}
                </div>
                
                <!-- Statistiques par source -->
                <div style="padding:32px;background:#f8fafc;">
                    <h2 style="color:#1e293b;font-size:20px;margin:0 0 20px 0;">📈 Répartition par source</h2>
                    {sources_html}
                </div>
                
                <!-- Footer -->
                <div style="padding:24px;text-align:center;background:#1e293b;color:#94a3b8;font-size:12px;">
                    <p style="margin:0;">Outil de Prospection v2.0</p>
                    <p style="margin:8px 0 0 0;">{date_str}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
