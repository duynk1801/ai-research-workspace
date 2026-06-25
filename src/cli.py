import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.live import Live
from rich.spinner import Spinner

from src.db.schema import init_db
from src.modules.knowledge import KnowledgeBase
from src.modules.clarification import (
    quick_search, analyze_results, get_problem_definition_questions,
    format_problem_definition, is_problem_defined
)
from src.modules.search import multi_search, fetch_github_readme
from src.modules.extractor import extract_from_github, extract_from_arxiv, extract_from_web, query_kb, generate_ideas

app = typer.Typer(help="AI Research Workspace - Research & Learn")
kb_app = typer.Typer(help="Knowledge Base commands")
app.add_typer(kb_app, name="kb")
console = Console()

kb = KnowledgeBase()


def detect_topic_type(topic: str, requirements: dict = None) -> dict:
    topic_lower = topic.lower()
    problem_def = (requirements or {}).get("problem_definition", {})
    scope = problem_def.get("scope", "").lower()
    what = problem_def.get("what", "").lower()
    combined = f"{topic_lower} {scope} {what}"

    is_code = any(w in combined for w in ["code", "github", "repo", "library", "framework", "tool", "cli", "api", "sdk", "package", "pip", "npm", "build", "develop", "implement", "app", "web", "server", "python", "javascript", "tối ưu", "optimize", "fix", "bug"])
    is_paper = any(w in combined for w in ["paper", "research", "study", "academic", "arxiv", "survey", "review", "theory", "algorithm", "model", "dataset", "benchmark", "scientific", "review", "so sánh", "compare"])
    is_product = any(w in combined for w in ["phone", "điện thoại", "laptop", "product", "device", "review", "spec", "feature", "tiger", "galaxy", "iphone"])

    if is_product:
        sources = ["web", "stackoverflow"]
    elif is_code and is_paper:
        sources = ["github", "arxiv", "web"]
    elif is_code:
        sources = ["github", "web", "stackoverflow"]
    elif is_paper:
        sources = ["arxiv", "web"]
    else:
        sources = ["github", "arxiv", "web"]

    return {"sources": sources, "is_code": is_code, "is_paper": is_paper, "is_product": is_product}


@app.command()
def research(topic: str = typer.Argument(..., help="Research topic or idea")):
    init_db()
    console.print(f"\n[bold cyan]🔬 Starting research session...[/bold cyan]")
    console.print(f"[bold]Topic:[/bold] {topic}\n")

    start_time = time.time()

    stage_start = time.time()
    console.print(f"[bold cyan]📥 Stage 0: Quick Search & Problem Definition[/bold cyan]")
    console.print(f"[dim]Searching '{topic}' to see what's out there...[/dim]")

    quick_results = quick_search(topic)
    analysis = analyze_results(topic, quick_results)

    console.print(f"\n[bold]Found {len(quick_results)} results:[/bold]")
    for i, r in enumerate(quick_results, 1):
        stars = f" ⭐{r['stars']}" if r.get("stars") is not None else ""
        console.print(f"   {i}. [{r['source']}] [bold]{r['title'][:60]}[/bold]{stars}")
        if r["description"]:
            console.print(f"      {r['description'][:100]}")

    console.print(f"\n   [dim]Languages: {', '.join(analysis['top_languages']) or 'N/A'}[/dim]")
    if analysis["related_topics"]:
        console.print(f"   [dim]Topics: {', '.join(analysis['related_topics'][:5])}[/dim]")

    console.print(f"\n[bold]📋 Problem Definition (5 factors):[/bold]")
    console.print(f"[dim]Answer these to define your problem clearly before deep search.[/dim]")

    questions = get_problem_definition_questions(topic, analysis)
    answers = {}

    for q in questions:
        if q["context"]:
            console.print(f"\n   [dim]{q['context']}[/dim]")
        console.print(f"\n[bold cyan]{q['label']}:[/bold cyan] {q['question']}")
        console.print(f"   [dim]{q['hint']}[/dim]")
        answer = console.input(f"   → ").strip()
        if answer.lower() in ("done", "ok", "xong", "skip", ""):
            break
        answers[q["id"]] = answer

    if not is_problem_defined(answers):
        console.print(f"\n[bold yellow]⚠️ Problem not fully defined. Using defaults...[/bold yellow]")
        answers.setdefault("what", topic)
        answers.setdefault("why", "general research")
        answers.setdefault("who", "self-use")
        answers.setdefault("scope", "no restrictions")
        answers.setdefault("depth", "overview")

    problem_text = format_problem_definition(answers)
    console.print(f"\n[bold]📝 Problem Definition:[/bold]")
    console.print(problem_text)

    console.print(f"   [dim]({time.time() - stage_start:.1f}s)[/dim]")

    search_keywords = [topic]
    if answers.get("scope") and answers["scope"].lower() not in ("no restrictions", "none", "không", "all"):
        search_keywords.append(answers["scope"])

    session_data = {
        "topic": topic,
        "problem_definition": answers,
    }
    session_id = kb.start_session(topic, json.dumps(session_data, ensure_ascii=False))
    console.print(f"\n[green]✅ Session #{session_id} created[/green]\n")

    topic_type = detect_topic_type(topic)
    console.print(f"   Topic type: {'Code' if topic_type['is_code'] else ''}{' + ' if topic_type['is_code'] and topic_type['is_paper'] else ''}{'Paper' if topic_type['is_paper'] else ''}")
    console.print(f"   Sources: {', '.join(topic_type['sources'])}")

    stage_start = time.time()
    console.print("[bold cyan]📥 Stage 1: Query KB[/bold cyan]")
    existing_insights = kb.get_all_insights()
    if existing_insights:
        console.print(f"   Found {len(existing_insights)} existing insights in KB")
        kb_result = query_kb(topic, {}, existing_insights)
        relevant = kb_result.get("relevant_insights", [])
        gaps = kb_result.get("gaps", [])
        if relevant:
            console.print(f"   [green]→ {len(relevant)} relevant insights found[/green]")
        if gaps:
            console.print(f"   [yellow]→ {len(gaps)} gaps identified[/yellow]")
    else:
        console.print("   [dim]KB is empty, skipping query[/dim]")
        gaps = []
    console.print(f"   [dim]({time.time() - stage_start:.1f}s)[/dim]")

    stage_start = time.time()
    console.print(f"\n[bold cyan]🔍 Stage 2: External Search[/bold cyan]")
    console.print(f"[dim]Sources: {', '.join(topic_type['sources'])}[/dim]")

    all_results = {s: [] for s in topic_type["sources"]}
    for keyword in search_keywords[:2]:
        results = multi_search(keyword, topic_type["sources"], limit=3)
        for source, items in results.get("sources", {}).items():
            all_results[source].extend(items)

    github_repos = [r for r in all_results.get("github", []) if r.get("type") != "error"]
    arxiv_papers = [r for r in all_results.get("arxiv", []) if r.get("type") != "error"]
    web_results = [r for r in all_results.get("web", []) if r.get("type") != "error"]
    so_results = [r for r in all_results.get("stackoverflow", []) if r.get("type") != "error"]

    console.print(f"\n   [bold]GitHub:[/bold] {len(github_repos)} repos")
    for r in github_repos[:3]:
        stars = f" ⭐{r['stars']}" if r.get("stars") else ""
        console.print(f"      - {r['title']}{stars}")

    console.print(f"   [bold]Arxiv:[/bold] {len(arxiv_papers)} papers")
    for r in arxiv_papers[:3]:
        console.print(f"      - {r['title'][:70]}")

    console.print(f"   [bold]Web:[/bold] {len(web_results)} results")
    for r in web_results[:3]:
        console.print(f"      - {r['title'][:70]}")

    console.print(f"   [bold]StackOverflow:[/bold] {len(so_results)} results")
    for r in so_results[:3]:
        score = f" (score:{r.get('score', 0)})" if r.get("score") else ""
        console.print(f"      - {r['title'][:70]}{score}")

    all_sources = github_repos[:2] + arxiv_papers[:2]
    console.print(f"   [dim]({time.time() - stage_start:.1f}s)[/dim]")

    stage_start = time.time()
    console.print(f"\n[bold cyan]📖 Stage 3: Extract Insights (parallel)[/bold cyan]")
    all_insights = []
    sources_to_read = []

    for repo in github_repos[:2]:
        sources_to_read.append(("github", repo))
    for paper in arxiv_papers[:2]:
        sources_to_read.append(("arxiv", paper))

    def extract_one(source_type, item):
        if source_type == "github":
            readme = fetch_github_readme(item["url"])
            if readme:
                return extract_from_github(item, readme)
            return []
        elif source_type == "arxiv":
            return extract_from_arxiv(item)
        elif source_type == "web":
            return extract_from_web(item)
        return []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        for source_type, item in sources_to_read:
            name = item["title"][:50]
            console.print(f"   [dim]Queued: {name}...[/dim]")
            future = executor.submit(extract_one, source_type, item)
            futures[future] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                insights = future.result()
                all_insights.extend(insights)
                console.print(f"   [green]✓ {name} → {len(insights)} insights[/green]")
            except Exception as e:
                console.print(f"   [red]✗ {name} → Error: {e}[/red]")

    console.print(f"   [dim]({time.time() - stage_start:.1f}s)[/dim]")

    stage_start = time.time()
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
    console.print(f"   [dim]({time.time() - stage_start:.1f}s)[/dim]")

    console.print(f"\n[bold yellow]📊 Stage 5: Review & Discuss[/bold yellow]")

    if web_results:
        console.print(f"\n[bold]🌐 Web Summary:[/bold]")
        for i, r in enumerate(web_results[:5], 1):
            console.print(f"   {i}. [bold]{r['title'][:70]}[/bold]")
            if r.get("description"):
                console.print(f"      {r['description'][:120]}")
            console.print(f"      [dim]{r['url'][:80]}[/dim]")

    maturity_counts = {}
    for insight in all_insights:
        m = insight.get("maturity", "S1")
        maturity_counts[m] = maturity_counts.get(m, 0) + 1

    if all_insights:
        console.print(f"\n[bold]💡 Insights from sources ({len(all_insights)} total):[/bold]")
        for i, insight in enumerate(all_insights, 1):
            console.print(f"\n   [bold cyan]{i}. [{insight['maturity']}] [{insight['type']}] {insight['title']}[/bold cyan]")
            if insight.get("main_idea"):
                console.print(f"      {insight['main_idea'][:120]}")
            if insight.get("source_url"):
                console.print(f"      [dim]{insight['source_url'][:80]}[/dim]")

        for m, c in sorted(maturity_counts.items()):
            console.print(f"   {m}: {c} insights")

        console.print(f"\n[bold]What do you want to do?[/bold]")
        console.print(f"   [bold]1.[/bold] Save all insights to KB")
        console.print(f"   [bold]2.[/bold] Save only selected (type: 1,3,5)")
        console.print(f"   [bold]3.[/bold] Discard")
        console.print(f"   [bold]4.[/bold] Search more on a subtopic")

        action = console.input("\n📝 Your choice: ").strip()

        if action == "4":
            subtopic = console.input("📝 What subtopic? ").strip()
            if subtopic:
                console.print(f"[dim]Run: python -m src.cli research \"{subtopic}\"[/dim]")
        elif action == "3":
            console.print("   [dim]Discarded.[/dim]")
        elif action == "2":
            selected = console.input("📝 Numbers (e.g. 1,3,5): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in selected.split(",")]
                selected_insights = [all_insights[i] for i in indices if 0 <= i < len(all_insights)]
                if selected_insights:
                    saved_ids = kb.save_insights(selected_insights)
                    console.print(f"   [green]✅ {len(saved_ids)} saved[/green]")
            except (ValueError, IndexError):
                console.print("   [red]Invalid input[/red]")
        elif action == "1":
            saved_ids = kb.save_insights(all_insights)
            console.print(f"   [green]✅ {len(saved_ids)} saved[/green]")
    else:
        console.print(f"\n[bold yellow]⚠️ No structured insights extracted from sources.[/bold yellow]")
        console.print(f"   GitHub repos and Arxiv papers may not be relevant to this topic.")
        console.print(f"   Web results above contain the most useful information.\n")

        console.print(f"[bold]What do you want to do?[/bold]")
        console.print(f"   [bold]1.[/bold] Search with different keywords")
        console.print(f"   [bold]2.[/bold] Save web results as reference to KB")
        console.print(f"   [bold]3.[/bold] End session")

        action = console.input("\n📝 Your choice: ").strip()

        if action == "1":
            new_keywords = console.input("📝 New keywords: ").strip()
            if new_keywords:
                console.print(f"\n[dim]Run: python -m src.cli research \"{new_keywords}\"[/dim]")
        elif action == "2":
            web_insights = []
            for r in web_results[:5]:
                web_insights.append({
                    "type": "IDEA",
                    "title": r["title"],
                    "main_idea": r.get("description", "")[:200],
                    "maturity": "S1",
                    "tags": ["web-reference"],
                    "source_url": r.get("url", ""),
                    "source_type": "web",
                })
            saved_ids = kb.save_insights(web_insights)
            console.print(f"   [green]✅ {len(saved_ids)} web references saved[/green]")
        else:
            console.print("   [dim]Session ended.[/dim]")

    kb.finish_session(json.dumps(session_data, ensure_ascii=False))

    elapsed = time.time() - start_time
    console.print(f"\n[bold]📊 Session Summary[/bold]")
    console.print(f"   Sources: {len(github_repos)} repos + {len(arxiv_papers)} papers + {len(web_results)} web + {len(so_results)} SO")
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
