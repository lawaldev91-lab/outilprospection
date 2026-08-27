#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║         OUTIL DE PROSPECTION — Point d'entrée        ║
║  Usage : python main.py                              ║
╚══════════════════════════════════════════════════════╝
"""
import os
import sys
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

# Vérification des dépendances
try:
    import requests
    from bs4 import BeautifulSoup
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError:
    print("\n❌ Dépendances manquantes. Lancez :\n")
    print("   python3 -m pip install -r requirements.txt\n")
    sys.exit(1)

from config import SOURCES, RESULTS_DIR
from classifier import filter_relevant
import report as report_module

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold #6366f1]🔍 Outil de Prospection[/bold #6366f1]\n"
        "[dim]Recherche de demandes de prestataires sur sources publiques[/dim]",
        border_style="#2a3040",
        padding=(1, 4),
    ))
    console.print()


def run_scraper(name: str) -> tuple[str, list[dict]]:
    """Lance un scraper et retourne (nom, résultats)."""
    try:
        if name == "hackernews":
            from scrapers.hackernews import fetch
        elif name == "reddit":
            from scrapers.reddit import fetch
        elif name == "devto":
            from scrapers.devto import fetch
        elif name == "malt":
            from scrapers.malt import fetch
        elif name == "indiehackers":
            from scrapers.indiehackers import fetch
        elif name == "alsacreations":
            from scrapers.alsacreations import fetch
        elif name == "freework":
            from scrapers.freework import fetch
        elif name == "remotive":
            from scrapers.remotive import fetch
        elif name == "remoteok":
            from scrapers.remoteok import fetch
        elif name == "himalayas":
            from scrapers.himalayas import fetch
        else:
            return name, []
        return name, fetch()
    except Exception as e:
        return name, []


def main():
    print_banner()

    # ── 1. Collecte ──────────────────────────────────────────────
    active_sources = [name for name, enabled in SOURCES.items() if enabled]

    console.print(f"[bold]📡 Sources actives :[/bold] {', '.join(active_sources)}")
    console.print()

    all_raw: list[dict] = []
    source_counts: dict[str, int] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[bold white]{task.fields[count]}[/bold white] posts"),
        console=console,
        transient=True,
    ) as progress:

        tasks_map = {}
        for src in active_sources:
            task_id = progress.add_task(
                f"[cyan]  {src:<18}[/cyan]", total=None, count="…"
            )
            tasks_map[src] = task_id

        start = time.time()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(run_scraper, src): src
                for src in active_sources
            }
            for future in as_completed(futures):
                src = futures[future]
                name, results = future.result()
                source_counts[name] = len(results)
                all_raw.extend(results)
                progress.update(
                    tasks_map[src],
                    completed=1, total=1,
                    description=f"[green]✓ {src:<18}[/green]",
                    count=len(results),
                )

    elapsed = time.time() - start
    console.print(f"[dim]Collecte terminée en {elapsed:.1f}s — {len(all_raw)} posts bruts[/dim]")
    console.print()

    # ── 2. Déduplication globale ─────────────────────────────────
    seen_ids = set()
    unique_raw = []
    for p in all_raw:
        if p["id"] not in seen_ids:
            seen_ids.add(p["id"])
            unique_raw.append(p)

    # ── 3. Classification & scoring ──────────────────────────────
    console.print("[bold]🎯 Classification et scoring...[/bold]")
    filtered = filter_relevant(unique_raw)
    console.print(
        f"  → [bold #10b981]{len(filtered)}[/bold #10b981] résultats pertinents "
        f"sur {len(unique_raw)} uniques\n"
    )

    if not filtered:
        console.print(
            "[yellow]⚠  Aucun résultat pertinent trouvé. "
            "Essayez d'ajuster RELEVANCE_THRESHOLD dans config.py[/yellow]"
        )
        sys.exit(0)

    # ── 4. Résumé par source ──────────────────────────────────────
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold #6366f1")
    table.add_column("Source", style="cyan")
    table.add_column("Posts bruts", justify="right")
    table.add_column("Pertinents", justify="right", style="green")

    for src in active_sources:
        raw_c = source_counts.get(src, 0)
        relevant_c = sum(1 for p in filtered if src.replace("-", "").lower() in p["source"].replace("-", "").lower())
        table.add_row(src, str(raw_c), str(relevant_c))

    console.print(table)

    # ── 5. Résumé par catégorie ───────────────────────────────────
    cat_counts: dict[str, int] = {}
    for p in filtered:
        for c in p["categories"]:
            cat_counts[c["name"]] = cat_counts.get(c["name"], 0) + 1

    cat_table = Table(box=box.SIMPLE, show_header=True, header_style="bold #8b5cf6")
    cat_table.add_column("Catégorie", style="white")
    cat_table.add_column("Résultats", justify="right", style="bold")

    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        cat_table.add_row(cat, str(count))

    console.print(cat_table)

    # ── 6. Génération du rapport ──────────────────────────────────
    console.print("[bold]📄 Génération du rapport HTML...[/bold]")
    html_path = report_module.generate(filtered)
    console.print(f"  → [bold #6366f1]{html_path}[/bold #6366f1]\n")

    # ── 7. Ouverture dans le navigateur ──────────────────────────
    console.print("[dim]Ouverture dans le navigateur...[/dim]")
    webbrowser.open(f"file://{html_path}")

    console.print()
    console.print(Panel.fit(
        f"[bold #10b981]✅ Prospection terminée ![/bold #10b981]\n"
        f"[dim]{len(filtered)} opportunités trouvées · rapport sauvegardé dans {RESULTS_DIR}/[/dim]",
        border_style="#2a3040",
        padding=(1, 4),
    ))


if __name__ == "__main__":
    main()
