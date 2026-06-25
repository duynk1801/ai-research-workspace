import json
import time
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from src.db.schema import init_db
from src.modules.knowledge import KnowledgeBase
from src.modules.clarification import analyze_input, generate_questions, synthesize_requirements
from src.modules.search import multi_search, fetch_github_readme
from src.modules.extractor import extract_from_github, extract_from_arxiv, query_kb, generate_ideas

app = typer.Typer(help="AI Research Workspace - Research & Learn")
kb_app = typer.Typer(help="Knowledge Base commands")
app.add_typer(kb_app, name="kb")
console = Console()

kb = KnowledgeBase()


def detect_topic_type(topic: str, requirements: dict = None) -> dict:
    topic_lower = topic.lower()
    summary = (requirements or {}).get("summary", "").lower()
    keywords = (requirements or {}).get("search_keywords", [])
    keywords_str = " ".join(keywords).lower() if keywords else ""
    combined = f"{topic_lower} {summary} {keywords_str}"

    is_code = any(w in combined for w in ["code", "github", "repo", "library", "framework", "tool", "cli", "api", "sdk", "package", "pip", "npm", "build", "develop", "implement", "app", "web", "server", "code python", "code javascript", "repo git"])
    is_paper = any(w in combined for w in ["paper", "research", "study", "academic", "arxiv", "survey", "review", "theory", "algorithm", "model", "dataset", "benchmark", "scientific"])
    is_news = any(w in combined for w in ["news", "trending", "latest", "new", "update", "release", "announcement", "2024", "2025", "2026"])

    if not is_code and not is_paper:
        is_code = True
        is_paper = True

    sources = []
    if is_code:
        sources.append("github")
    if is_paper:
        sources.append("arxiv")

    return {"sources": sources, "is_code": is_code, "is_paper": is_paper}


@app.command()
def research(topic: str = typer.Argument(..., help="Research topic or idea")):
    init_db()
    console.print(f"\n[bold cyan]🔬 Starting research session...[/bold cyan]")
    console.print(f"[bold]Topic:[/bold] {topic}\n")

    start_time = time.time()
    conversation = [{"role": "user", "content": topic}]

    while True:
        console.print("[dim]Analyzing your input...[/dim]")
        analysis = analyze_input(topic)

        missing = analysis.get("missing", []) if isinstance(analysis, dict) else []
        questions_list = analysis.get("suggested_questions", []) if isinstance(analysis, dict) else []

        if not missing or not questions_list:
            break

        console.print(f"\n[bold green]🤖 I need some clarification:[/bold green]")
        for i, q in enumerate(questions_list[:5], 1):
            console.print(f"   {i}. {q}")

        console.print(f"\n[bold]Options:[/bold]")
        console.print(f"   [bold]1.[/bold] Answer the questions above")
        console.print(f"   [bold]2.[/bold] Re-explain your idea (type 're-explain')")
        console.print(f"   [bold]3.[/bold] Skip clarification (type 'done')")

        user_reply = console.input("\n📝 Your response: ").strip()

        if user_reply.lower() in ("done", "ok", "xong", "skip", "3"):
            break

        if user_reply.lower() in ("re-explain", "re", "2"):
            new_topic = console.input("\n📝 Re-explain your idea: ").strip()
            if new_topic:
                topic = new_topic
                conversation = [{"role": "user", "content": topic}]
                console.print(f"\n[bold]Updated topic:[/bold] {topic}")
                continue

        conversation.append({"role": "assistant", "content": "\n".join(questions_list[:5])})
        conversation.append({"role": "user", "content": user_reply})

        console.print("[dim]Processing your answers...[/dim]")
        followup = generate_questions(conversation)
        console.print(f"\n[green]🤖 {followup}[/green]")

        more = console.input("\n📝 Add more details? (or 'done'): ").strip()
        if more.lower() in ("done", "ok", "xong", "skip", ""):
            break
        conversation.append({"role": "assistant", "content": followup})
        conversation.append({"role": "user", "content": more})

    console.print("\n[dim]Synthesizing requirements...[/dim]")
    requirements = synthesize_requirements(conversation)

    if not isinstance(requirements, dict) or requirements.get("parse_error"):
        requirements = {"topic": topic, "summary": topic, "search_keywords": [topic]}

    console.print(f"\n[bold]📋 Requirements:[/bold]")
    console.print(f"   Summary: {requirements.get('summary', 'N/A')}")
    console.print(f"   Keywords: {requirements.get('search_keywords', [topic])}")

    topic_type = detect_topic_type(topic, requirements)
    console.print(f"   Topic type: {'Code' if topic_type['is_code'] else ''}{' + ' if topic_type['is_code'] and topic_type['is_paper'] else ''}{'Paper' if topic_type['is_paper'] else ''}")
    console.print(f"   Sources: {', '.join(topic_type['sources'])}")

    session_id = kb.start_session(topic, json.dumps(requirements, ensure_ascii=False))
    console.print(f"\n[green]✅ Session #{session_id} created[/green]\n")

    console.print("[bold cyan]📥 Stage 1: Query KB[/bold cyan]")
    existing_insights = kb.get_all_insights()
    if existing_insights:
        console.print(f"   Found {len(existing_insights)} existing insights in KB")
        kb_result = query_kb(topic, requirements, existing_insights)
        relevant = kb_result.get("relevant_insights", [])
        gaps = kb_result.get("gaps", [])
        if relevant:
            console.print(f"   [green]→ {len(relevant)} relevant insights found[/green]")
        if gaps:
            console.print(f"   [yellow]→ {len(gaps)} gaps identified[/yellow]")
    else:
        console.print("   [dim]KB is empty, skipping query[/dim]")
        gaps = []

    console.print(f"\n[bold cyan]🔍 Stage 2: External Search[/bold cyan]")
    search_keywords = requirements.get("search_keywords", [topic])
    if isinstance(search_keywords, str):
        search_keywords = [search_keywords]

    all_results = {s: [] for s in topic_type["sources"]}
    for keyword in search_keywords[:2]:
        console.print(f"   Searching: {keyword}")
        results = multi_search(keyword, topic_type["sources"], limit=3)
        for source, items in results.get("sources", {}).items():
            all_results[source].extend(items)

    github_repos = [r for r in all_results.get("github", []) if r.get("type") != "error"]
    arxiv_papers = [r for r in all_results.get("arxiv", []) if r.get("type") != "error"]

    console.print(f"   [bold]Found:[/bold] {len(github_repos)} repos, {len(arxiv_papers)} papers")

    console.print(f"\n[bold cyan]📖 Stage 3: Extract Insights[/bold cyan]")
    all_insights = []

    for repo in github_repos[:3]:
        console.print(f"   Reading {repo['title']}...")
        try:
            readme = fetch_github_readme(repo["url"])
            if readme:
                insights = extract_from_github(repo, readme)
                all_insights.extend(insights)
                console.print(f"      [green]→ {len(insights)} insights[/green]")
            else:
                console.print(f"      [yellow]→ No README found[/yellow]")
        except Exception as e:
            console.print(f"      [red]→ Error: {e}[/red]")

    for paper in arxiv_papers[:3]:
        console.print(f"   Reading {paper['title'][:60]}...")
        try:
            insights = extract_from_arxiv(paper)
            all_insights.extend(insights)
            console.print(f"      [green]→ {len(insights)} insights[/green]")
        except Exception as e:
            console.print(f"      [red]→ Error: {e}[/red]")

    console.print(f"\n[bold cyan]💡 Stage 4: Generate Ideas[/bold cyan]")
    if all_insights or gaps:
        ideate_result = generate_ideas(topic, all_insights, gaps)
        generated_ideas = ideate_result.get("ideas", [])
        if generated_ideas:
            console.print(f"   [green]→ {len(generated_ideas)} ideas generated[/green]")
            for i, idea in enumerate(generated_ideas[:3], 1):
                console.print(f"   {i}. {idea.get('title', 'N/A')}")
        else:
            console.print("   [dim]No new ideas generated[/dim]")
    else:
        console.print("   [dim]No insights or gaps to generate ideas from[/dim]")

    console.print(f"\n[bold yellow]📊 Stage 5: Review[/bold yellow]")
    console.print(f"   Total insights: {len(all_insights)}")
    maturity_counts = {}
    for insight in all_insights:
        m = insight.get("maturity", "S1")
        maturity_counts[m] = maturity_counts.get(m, 0) + 1
    for m, c in sorted(maturity_counts.items()):
        console.print(f"   {m}: {c} insights")

    console.print(f"\n[bold cyan]💾 Stage 6: Save[/bold cyan]")
    if all_insights:
        for i, insight in enumerate(all_insights, 1):
            console.print(f"   {i}. [{insight['maturity']}] [{insight['type']}] {insight['title']}")

        if Confirm.ask("\n💾 Save insights to Knowledge Base?"):
            saved_ids = kb.save_insights(all_insights)
            console.print(f"   [green]✅ {len(saved_ids)} insights saved[/green]")
        else:
            console.print("   [dim]⏭️ Skipped[/dim]")

    kb.finish_session(json.dumps(requirements, ensure_ascii=False))

    elapsed = time.time() - start_time
    console.print(f"\n[bold]📊 Session Summary[/bold]")
    console.print(f"   Sources: {len(github_repos)} repos + {len(arxiv_papers)} papers")
    console.print(f"   Insights: {len(all_insights)}")
    console.print(f"   Maturity: {maturity_counts}")
    console.print(f"   Time: {elapsed:.1f}s")


@kb_app.command("search")
def kb_search(query: str = typer.Argument(..., help="Search query"), limit: int = typer.Option(10, help="Max results")):
    init_db()
    console.print(f"\n[bold]🔍 Searching KB: {query}[/bold]\n")

    results = kb.search(query, limit)

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    table = Table(title=f"Found {len(results)} insights")
    table.add_column("ID", style="dim")
    table.add_column("Maturity", style="cyan")
    table.add_column("Type", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Tags")
    table.add_column("Created", style="dim")

    for r in results:
        tags = json.loads(r["tags"]) if isinstance(r["tags"], str) else r["tags"]
        table.add_row(
            str(r["id"]), r.get("maturity", "S1"), r["insight_type"], r["title"][:50],
            ", ".join(tags[:3]), r["created_at"][:10]
        )
    console.print(table)


@kb_app.command("list")
def kb_list(limit: int = typer.Option(20), offset: int = typer.Option(0)):
    init_db()
    results = kb.list_all(limit, offset)

    if not results:
        console.print("[dim]Knowledge base is empty.[/dim]")
        return

    table = Table(title="Knowledge Base")
    table.add_column("ID", style="dim")
    table.add_column("Maturity", style="cyan")
    table.add_column("Type", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Main Idea")
    table.add_column("Source")
    table.add_column("Created", style="dim")

    for r in results:
        table.add_row(
            str(r["id"]), r.get("maturity", "S1"), r["insight_type"], r["title"][:40],
            (r.get("main_idea") or "")[:40], r["source_type"], r["created_at"][:10]
        )
    console.print(table)


@kb_app.command("show")
def kb_show(insight_id: int = typer.Argument(..., help="Insight ID")):
    init_db()
    insight = kb.get(insight_id)

    if not insight:
        console.print(f"[red]Insight #{insight_id} not found.[/red]")
        return

    tags = json.loads(insight["tags"]) if isinstance(insight["tags"], str) else insight["tags"]
    strengths = json.loads(insight["strengths"]) if isinstance(insight["strengths"], str) else insight["strengths"]
    limitations = json.loads(insight["limitations"]) if isinstance(insight["limitations"], str) else insight["limitations"]
    gaps_list = json.loads(insight["gaps"]) if isinstance(insight["gaps"], str) else insight["gaps"]

    content = f"""[bold]Title:[/bold] {insight['title']}
[bold]Type:[/bold] {insight['insight_type']}
[bold]Maturity:[/bold] {insight.get('maturity', 'S1')}
[bold]Source:[/bold] {insight['source_type']} - {insight['source_url']}
[bold]Tags:[/bold] {', '.join(tags)}
[bold]Created:[/bold] {insight['created_at']}

[bold]Main Idea:[/bold]
{insight.get('main_idea', 'N/A')}

[bold]Core Approach:[/bold]
{insight.get('core_approach', 'N/A')}

[bold]Strengths:[/bold]
{chr(10).join(f'  - {s}' for s in strengths) if strengths else '  N/A'}

[bold]Limitations:[/bold]
{chr(10).join(f'  - {l}' for l in limitations) if limitations else '  N/A'}

[bold]Gaps:[/bold]
{chr(10).join(f'  - {g}' for g in gaps_list) if gaps_list else '  N/A'}

[bold]Relevance:[/bold]
{insight.get('relevance', 'N/A')}"""
    console.print(Panel(content, title=f"Insight #{insight_id}"))


@kb_app.command("stats")
def kb_stats():
    init_db()
    stats = kb.stats()
    console.print(f"\n[bold]📊 Knowledge Base Stats[/bold]")
    console.print(f"   Total insights: {stats['total_insights']}")
    console.print(f"   Total sessions: {stats['total_sessions']}")
    if stats["by_type"]:
        console.print(f"   By type:")
        for t, c in stats["by_type"].items():
            console.print(f"     - {t}: {c}")
    if stats.get("by_maturity"):
        console.print(f"   By maturity:")
        for m, c in stats["by_maturity"].items():
            console.print(f"     - {m}: {c}")


if __name__ == "__main__":
    app()
