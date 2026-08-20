import sys
import uuid
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from config.settings import settings
from data.generate_docs import main as generate_mock_docs
from graph.graph_builder import compiled_guarded_graph
from services.redis_service import redis_service
from services.memory_service import mem0_service

console = Console()


def print_banner():
    console.clear()
    console.print(
        Panel.fit(
            f"[bold cyan]{settings.PROJECT_NAME}[/bold cyan] [bold green](Phase 9 LangSmith Observability)[/bold green]\n"
            f"[dim]Real-time Workflow Tracing • Failure Diagnostics • Automated Evaluations[/dim]",
            border_style="cyan",
        )
    )


def run_guarded_orchestration(query: str, user_name: str, department: str, thread_id: str):
    user_id = user_name.lower().replace(" ", "_")

    # 1. Redis Cache Check
    cached_payload = redis_service.get_cached_solution(query, user_id)
    if cached_payload:
        console.print("\n[bold green]⚡ [REDIS CACHE HIT] Served from Cache![/bold green]")
        return cached_payload, True

    # 2. Fetch Mem0 User Preferences
    console.print("\n[bold blue]🧠 [MEM0] Retrieving long-term user preferences...[/bold blue]")
    user_prefs = mem0_service.get_user_memories(user_id)

    initial_state = {
        "user_name": user_name,
        "user_id": user_id,
        "department": department,
        "raw_query": query,
        "sanitized_query": "",
        "user_preferences": user_prefs,
        "guardrail_passed": True,
        "guardrail_violation_reason": "",
        "intent": "Unclassified",
        "sub_category": "",
        "retrieved_docs": [],
        "telemetry_data": {},
        "code_analysis_data": {},
        "billing_data": {},
        "solution": "",
        "confidence_score": 0,
        "is_cached_response": False,
        "retry_count": 0,
        "human_approved": False,
        "human_feedback": "",
        "visited_nodes": ["START"],
        "execution_logs": [f"Session started for {user_id}"],
    }

    # Pass LangSmith Tracing Configuration via RunnableConfig
    config = {
        "configurable": {"thread_id": thread_id},
        "tags": [f"user:{user_id}", f"dept:{department}", "production_cli"],
        "metadata": {
            "session_id": thread_id,
            "user_id": user_id,
            "department": department,
            "project_version": settings.VERSION
        }
    }

    console.print(f"\n[bold green]Executing Thread ID:[/bold green] [magenta]{thread_id}[/magenta]")
    console.print("[dim]Streaming Node Transitions (Traces sent to LangSmith)...[/dim]\n")

    # 3. Stream LangGraph Workflow
    for event in compiled_guarded_graph.stream(initial_state, config=config):
        for node_name, state_update in event.items():
            console.print(f" ➔ Executed Node: [bold cyan]{node_name}[/bold cyan]")

    final_state = compiled_guarded_graph.get_state(config).values

    # 4. Save to Redis Cache
    if final_state.get("guardrail_passed", True) and final_state.get("confidence_score", 0) >= settings.CONFIDENCE_THRESHOLD:
        redis_service.set_cached_solution(query, user_id, final_state)

    # 5. Persist to Mem0
    if final_state.get("guardrail_passed", True):
        mem0_service.add_user_memory(user_id, f"Query: {query} | Passed Security Guardrails")

    return final_state, False


def render_summary(final_state: dict, is_cached: bool, thread_id: str):
    table = Table(title="Guardrail Security & Observability Trace Summary", border_style="green")
    table.add_column("Security / Execution Property", style="bold white")
    table.add_column("Value / Status", style="green")

    table.add_row("Session Thread ID", thread_id)
    table.add_row("User / Department", f"{final_state.get('user_name')} ({final_state.get('department')})")
    
    passed_flag = final_state.get("guardrail_passed", True)
    table.add_row("Guardrail Security Check", "[bold green]PASSED[/bold green]" if passed_flag else "[bold red]BLOCKED[/bold red]")
    
    if not passed_flag:
        table.add_row("Violation Reason", f"[red]{final_state.get('guardrail_violation_reason')}[/red]")

    table.add_row("Execution Strategy", "Redis Cache" if is_cached else "LangGraph Engine")
    table.add_row("Path Executed", " ➔ ".join(final_state.get("visited_nodes", [])))
    table.add_row("LangSmith Project", settings.LANGCHAIN_PROJECT)

    console.print("\n")
    console.print(table)

    console.print("\n[bold cyan]Final Output:[/bold cyan]")
    border_color = "bold green" if passed_flag else "bold red"
    console.print(Panel(final_state.get("solution", "No output produced."), border_style=border_color))


def main():
    print_banner()

    if not settings.KB_FILE_PATH.exists():
        generate_mock_docs()

    thread_id = str(uuid.uuid4())[:8]

    user_name = Prompt.ask("Enter user name", default="Neeraj")
    department = Prompt.ask("Enter department", default="Infrastructure")

    console.print("\n[bold cyan]Enter Incident Query or Ticket Description:[/bold cyan]")
    query = Prompt.ask(
        "Incident Description", 
        default="Production EC2 instance CPU utilization is continuously above 95%."
    )

    try:
        final_state, is_cached = run_guarded_orchestration(query, user_name, department, thread_id)
        render_summary(final_state, is_cached, thread_id)
    finally:
        if hasattr(mem0_service, "close"):
            mem0_service.close()


if __name__ == "__main__":
    main()
