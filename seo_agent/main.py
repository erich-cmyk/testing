"""
SEO AI Agent — Main Orchestrator
Runs the full pipeline: Research → Competitors → Keywords → Website Updates

Usage:
    python -m seo_agent.main --help
    python -m seo_agent.main run --help
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import anthropic
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import config
from .agents import competitor_agent, keyword_agent, research_agent, website_agent
from .models.seo_data import ClientProfile
from .tools.cms_connector import DryRunCMSConnector, WordPressCMSConnector

app = typer.Typer(
    name="seo-agent",
    help="AI-powered SEO research and website optimization agent.",
    add_completion=False,
)
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)


@app.command()
def run(
    business_name: str = typer.Option(..., "--business", "-b", help="Client business name"),
    industry: str = typer.Option(..., "--industry", "-i", help="Industry/niche"),
    website_url: str = typer.Option(..., "--url", "-u", help="Client website URL"),
    services: str = typer.Option(..., "--services", "-s", help="Comma-separated list of services/products"),
    audience: str = typer.Option(..., "--audience", "-a", help="Target audience description"),
    goals: str = typer.Option("Increase organic traffic and conversions", "--goals", "-g", help="SEO goals"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Business location (for local SEO)"),
    usps: str = typer.Option("Quality service, expert team", "--usps", help="Comma-separated unique selling points"),
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Dry run (no CMS changes) vs live mode"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Save full report to JSON file"),
    skip_research: bool = typer.Option(False, "--skip-research", help="Skip research phase (use cached)"),
    research_cache: Optional[Path] = typer.Option(None, "--research-cache", help="Path to cached research JSON"),
):
    """
    Run the full SEO agent pipeline for a client.

    Example:
        python -m seo_agent.main run \\
          --business "Apex Plumbing" \\
          --industry "Plumbing Services" \\
          --url "https://apexplumbing.com" \\
          --services "Drain cleaning,Water heater installation,Leak repair" \\
          --audience "Homeowners aged 30-60 in the Dallas metro area" \\
          --location "Dallas, TX" \\
          --goals "Rank #1 for local plumbing searches in Dallas"
    """
    profile = ClientProfile(
        business_name=business_name,
        industry=industry,
        website_url=website_url,
        primary_services=[s.strip() for s in services.split(",")],
        target_audience=audience,
        goals=goals,
        location=location,
        unique_selling_points=[u.strip() for u in usps.split(",")],
    )

    ai_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    console.print(
        Panel.fit(
            f"[bold cyan]SEO AI Agent[/bold cyan]\n"
            f"Client: [yellow]{profile.business_name}[/yellow]\n"
            f"Industry: {profile.industry}\n"
            f"Mode: [{'green]DRY RUN' if dry_run else 'red]LIVE — WILL UPDATE CMS'}]",
        )
    )

    # ── Phase 1: Research ──────────────────────────────────────────────────────
    research_data: dict = {}
    if skip_research and research_cache and research_cache.exists():
        console.print("[dim]Loading cached research...[/dim]")
        research_data = json.loads(research_cache.read_text())
    else:
        console.rule("[bold]Phase 1: Industry & Audience Research")
        console.print("[dim]Searching the web for industry insights...[/dim]\n")
        research_data = research_agent.run(ai_client, profile)
        if output_file:
            _save_partial(output_file, "research", research_data)

    # ── Phase 2: Competitor Analysis ───────────────────────────────────────────
    console.rule("[bold]Phase 2: Competitor Analysis")
    console.print("[dim]Identifying and analyzing top competitors...[/dim]\n")
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Analyzing competitors...", total=None)
        competitor_report = competitor_agent.run(
            ai_client, profile, research_data, max_competitors=config.MAX_COMPETITORS
        )
        progress.update(task, description="Competitor analysis complete ✓")

    _print_competitor_table(competitor_report)

    # ── Phase 3: Keyword Strategy ──────────────────────────────────────────────
    console.rule("[bold]Phase 3: Keyword Strategy")
    console.print("[dim]Building keyword list from research + competitive data...[/dim]\n")
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Generating keywords...", total=None)
        keyword_list = keyword_agent.run(
            ai_client, profile, research_data, competitor_report,
            target_count=config.KEYWORD_TARGET_COUNT,
        )
        progress.update(task, description="Keyword strategy complete ✓")

    _print_keyword_table(keyword_list)

    # ── Phase 4: Website Updates ───────────────────────────────────────────────
    console.rule("[bold]Phase 4: Website SEO Updates")
    cms = _build_cms_connector(dry_run)

    console.print(
        f"[dim]{'[DRY RUN] Generating update plan...' if dry_run else 'Applying updates to CMS...'}[/dim]\n"
    )
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Generating SEO update plan...", total=None)
        website_result = website_agent.run(
            ai_client, profile, keyword_list, cms, dry_run=dry_run
        )
        progress.update(task, description="Website update plan complete ✓")

    _print_update_results(website_result)

    # ── Final Report ───────────────────────────────────────────────────────────
    full_report = {
        "client": profile.model_dump(),
        "research": research_data,
        "competitor_report": competitor_report.model_dump(),
        "keyword_list": keyword_list.model_dump(),
        "website_updates": website_result,
    }

    if output_file:
        output_file.write_text(json.dumps(full_report, indent=2, default=str))
        console.print(f"\n[green]Full report saved to: {output_file}[/green]")

    console.print(
        Panel.fit(
            f"[bold green]Pipeline Complete[/bold green]\n"
            f"Competitors analyzed: {len(competitor_report.competitors)}\n"
            f"Primary keywords: {len(keyword_list.primary_keywords)}\n"
            f"Secondary keywords: {len(keyword_list.secondary_keywords)}\n"
            f"Pages updated: {website_result['pages_processed']}\n"
            f"Mode: {'DRY RUN — no changes made' if dry_run else 'LIVE — CMS updated'}"
        )
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_cms_connector(dry_run: bool):
    if dry_run:
        return DryRunCMSConnector()
    if not all([config.CMS_BASE_URL, config.CMS_USERNAME, config.CMS_APP_PASSWORD]):
        console.print("[yellow]CMS credentials not fully configured; falling back to dry run.[/yellow]")
        return DryRunCMSConnector()
    return WordPressCMSConnector(
        base_url=config.CMS_BASE_URL,
        username=config.CMS_USERNAME,
        app_password=config.CMS_APP_PASSWORD,
        seo_plugin=config.CMS_SEO_PLUGIN,
    )


def _print_competitor_table(report) -> None:
    if not report.competitors:
        console.print("[yellow]No competitors found.[/yellow]")
        return
    table = Table(title="Top Competitors", show_lines=True)
    table.add_column("Competitor", style="cyan")
    table.add_column("Domain")
    table.add_column("Top Keywords")
    table.add_column("Content Gaps")
    for comp in report.competitors:
        table.add_row(
            comp.name,
            comp.domain,
            "\n".join(f"• {k}" for k in comp.top_keywords[:3]),
            "\n".join(f"• {g}" for g in comp.content_gaps[:2]),
        )
    console.print(table)
    console.print(f"\n[italic]{report.market_positioning_advice}[/italic]\n")


def _print_keyword_table(kw_list) -> None:
    table = Table(title="Primary Keywords", show_lines=True)
    table.add_column("Keyword", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Intent")
    table.add_column("Difficulty")
    table.add_column("Rationale")
    for kw in kw_list.primary_keywords:
        table.add_row(
            kw.term,
            str(kw.relevance_score),
            kw.search_intent,
            kw.estimated_difficulty,
            kw.rationale[:80] + "..." if len(kw.rationale) > 80 else kw.rationale,
        )
    console.print(table)
    console.print(
        f"[dim]+{len(kw_list.secondary_keywords)} secondary keywords[/dim]\n"
    )


def _print_update_results(result: dict) -> None:
    plan = result.get("update_plan", {})
    pages = plan.get("pages", [])
    if not pages:
        return

    table = Table(title="Page SEO Updates", show_lines=True)
    table.add_column("Page", style="cyan")
    table.add_column("Proposed Title")
    table.add_column("Schema?")
    table.add_column("Status")

    update_results = {r["page_id"]: r["status"] for r in result.get("update_results", [])}

    for p in pages[:20]:
        status = update_results.get(str(p.get("page_id", "")), "pending")
        status_color = {"success": "green", "dry_run": "yellow", "failed": "red"}.get(status, "white")
        table.add_row(
            p.get("page_url", "")[-40:],
            p.get("proposed_meta_title", ""),
            "✓" if p.get("schema_markup") else "—",
            f"[{status_color}]{status}[/{status_color}]",
        )
    console.print(table)

    notes = plan.get("implementation_notes", "")
    if notes:
        console.print(f"\n[italic]{notes}[/italic]")


def _save_partial(output_file: Path, section: str, data: dict) -> None:
    existing = {}
    if output_file.exists():
        try:
            existing = json.loads(output_file.read_text())
        except json.JSONDecodeError:
            pass
    existing[section] = data
    output_file.write_text(json.dumps(existing, indent=2, default=str))


if __name__ == "__main__":
    app()
