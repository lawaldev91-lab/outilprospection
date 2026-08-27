#!/usr/bin/env python3
"""
Démonstration du Custom URL Scraper
Exemples concrets d'utilisation
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.custom_scraper import scrape_url, scrape_multiple_urls


def demo_single_url():
    """Démonstration avec une seule URL."""
    print("=" * 60)
    print(" DÉMO : Scraping d'une seule URL")
    print("=" * 60)
    
    # URL d'exemple (job board)
    url = "https://www.welcometothejungle.com/fr/companies/ovhcloud/jobs"
    
    print(f"\n📡 Analyse de : {url}\n")
    
    # Mode strict (filtrage français)
    result = scrape_url(url, strict=True)
    
    print(f"✅ Succès : {result['success']}")
    print(f"📄 Type de page : {result['page_type']}")
    print(f"️  Titre : {result['page_title']}")
    print(f"🔗 Liens trouvés : {result['total_links']}")
    print(f"🎯 Opportunités : {len(result['opportunities'])}")
    
    if result['error']:
        print(f"❌ Erreur : {result['error']}")
    
    if result['opportunities']:
        print("\n Opportunités trouvées :")
        for i, opp in enumerate(result['opportunities'][:5], 1):
            print(f"\n  {i}. {opp['title'][:80]}")
            print(f"     Score : {opp.get('score', 'N/A')}/10")
            print(f"     Source : {opp['source']}")
            print(f"     URL : {opp['url'][:60]}...")
            
            if opp.get('categories'):
                cats = ', '.join(f"{c['icon']} {c['name']}" for c in opp['categories'])
                print(f"     Catégories : {cats}")
    
    print("\n" + "=" * 60)


def demo_multiple_urls():
    """Démonstration avec plusieurs URLs."""
    print("\n" + "=" * 60)
    print(" DÉMO : Scraping de plusieurs URLs")
    print("=" * 60)
    
    urls = [
        "https://www.freelance-info.fr/missions",
        "https://emploi.alsacreations.com/offres.html",
        "https://www.welcometothejungle.com/fr/jobs",
    ]
    
    print(f"\n📡 Analyse de {len(urls)} URLs :\n")
    for url in urls:
        print(f"  • {url}")
    
    print()
    
    # Mode flexible pour voir plus de résultats
    result = scrape_multiple_urls(urls, strict=False)
    
    print(f"✅ Pages analysées : {result['pages_scanned']}")
    print(f"🎯 Total opportunités : {result['total_opportunities']}")
    
    if result['errors']:
        print(f"\n⚠️  Erreurs :")
        for error in result['errors']:
            print(f"  • {error['url'][:50]}... : {error['error']}")
    
    if result['opportunities']:
        print(f"\n📋 Top 5 opportunités :")
        for i, opp in enumerate(result['opportunities'][:5], 1):
            print(f"\n  {i}. {opp['title'][:70]}")
            print(f"     Score : {opp.get('score', 'N/A')}")
            print(f"     URL : {opp['url'][:50]}...")
    
    print("\n" + "=" * 60)


def demo_with_classification():
    """Démonstration avec classification stricte."""
    print("\n" + "=" * 60)
    print("🔍 DÉMO : Scraping avec classification stricte")
    print("=" * 60)
    
    url = "https://www.freelance-info.fr/missions"
    
    print(f"\n📡 Analyse avec filtrage strict : {url}\n")
    
    # Mode strict
    result = scrape_url(url, strict=True)
    
    print(f"✅ Succès : {result['success']}")
    print(f"🎯 Opportunités après filtrage : {len(result['opportunities'])}")
    
    if result['opportunities']:
        print("\n Résultats classifiés :")
        for opp in result['opportunities'][:3]:
            score = opp.get('score', 0)
            cats = ', '.join(c['name'] for c in opp.get('categories', []))
            print(f"  • [{score}/10] {opp['title'][:60]}")
            print(f"    Catégories : {cats}")
    
    print("\n" + "=" * 60)


def demo_error_handling():
    """Démonstration de la gestion d'erreurs."""
    print("\n" + "=" * 60)
    print("🔍 DÉMO : Gestion d'erreurs")
    print("=" * 60)
    
    # URL invalide
    print("\n Test avec URL invalide :")
    result = scrape_url("not-a-valid-url", strict=True)
    print(f"  Success : {result['success']}")
    print(f"  Error : {result['error']}")
    
    # URL avec fichier non supporté
    print("\n❌ Test avec PDF :")
    result = scrape_url("https://exemple.com/document.pdf", strict=True)
    print(f"  Success : {result['success']}")
    print(f"  Error : {result['error']}")
    
    # URL inaccessible
    print("\n❌ Test avec domaine inexistant :")
    result = scrape_url("https://this-domain-does-not-exist-12345.com", strict=True)
    print(f"  Success : {result['success']}")
    print(f"  Error : {result['error']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n DÉMONSTRATION DU CUSTOM URL SCRAPER\n")
    
    demo_single_url()
    demo_multiple_urls()
    demo_with_classification()
    demo_error_handling()
    
    print("\n✅ Démonstration terminée !\n")
    print("💡 Pour utiliser dans votre application :")
    print("   python3 app.py")
    print("   Puis allez sur http://localhost:5000")
    print("   Section 'Scraping d'URL personnalisée'\n")
