"""
Simple demo to test Agent-as-a-Judge functionality
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from agent_as_a_judge.agent import JudgeAgent
from agent_as_a_judge.config import AgentConfig
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Load environment variables
load_dotenv()

console = Console()

def main():
    # Setup paths
    workspace = Path("benchmark/workspaces/OpenHands/39_Drug_Response_Prediction_SVM_GDSC_ML")
    judge_dir = Path("demo_output")
    judge_dir.mkdir(exist_ok=True)
    
    console.print(Panel.fit(
        "[bold green]Agent-as-a-Judge Demo[/bold green]\n"
        f"Workspace: {workspace}\n"
        "Testing 'Ask Anything' functionality...",
        border_style="cyan"
    ))
    
    # Create config
    config = AgentConfig(
        include_dirs=["src", "results", "models", "data"],
        exclude_dirs=["__pycache__", "env"],
        exclude_files=[".DS_Store"],
        setting="black_box",
        planning="efficient (no planning)",
        judge_dir=judge_dir,
        workspace_dir=workspace,
        instance_dir=None,
        trajectory_file=None
    )
    
    # Initialize agent
    console.print("\n[yellow]Initializing Agent...[/yellow]")
    agent = JudgeAgent(
        workspace=workspace,
        instance=None,
        judge_dir=judge_dir,
        trajectory_file=None,
        config=config
    )
    
    # Ask a question
    question = "What does this workspace contain?"
    console.print(f"\n[cyan]Question:[/cyan] {question}")
    console.print("\n[yellow]Agent is analyzing the workspace...[/yellow]")
    
    # Note: This will fail without a valid OpenAI API key
    try:
        answer = agent.ask_anything(question)
        
        console.print(Panel(
            Markdown(f"**Answer:**\n\n{answer}"),
            title="[bold green]Response[/bold green]",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]Error:[/red] {str(e)}\n\n"
            "[yellow]Note:[/yellow] Make sure to set your OPENAI_API_KEY in the .env file",
            title="[bold red]Demo Failed[/bold red]",
            border_style="red"
        ))
        console.print("\n[dim]The project setup is complete. Update .env with your API key to run demos.[/dim]")

if __name__ == "__main__":
    main()
