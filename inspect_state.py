import sys
from rich.console import Console
from rich.table import Table
from graph.graph_builder import compiled_graph

console = Console()


def inspect_thread_history(thread_id: str):
    """Retrieves and prints all historical checkpoints for a given thread_id."""
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        history = list(compiled_graph.get_state_history(config))
        
        if not history:
            console.print(f"[yellow]No checkpoint history found for thread_id: '{thread_id}'[/yellow]")
            return

        table = Table(title=f"Checkpoint State History for Thread: {thread_id}", border_style="cyan")
        table.add_column("Step / Config", style="bold white")
        table.add_column("Next Node", style="yellow")
        table.add_column("Current Intent", style="green")
        table.add_column("Visited Nodes", style="magenta")

        for idx, state_snapshot in enumerate(history):
            values = state_snapshot.values
            next_node = str(state_snapshot.next)
            intent = values.get("intent", "N/A")
            visited = ", ".join(values.get("visited_nodes", []))
            
            table.add_row(f"Checkpoint #{idx}", next_node, intent, visited)

        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error inspecting state history: {str(e)}[/red]")


if __name__ == "__main__":
    thread_input = sys.argv[1] if len(sys.argv) > 1 else "default_thread"
    inspect_thread_history(thread_input)

