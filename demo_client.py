#!/usr/bin/env python3
"""
OCR Client Demo Script

Demonstrates various ways to use the OCR command line client.
"""

import os
import subprocess
import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

def run_demo_command(description, command):
    """Run a demo command with description"""
    console.print(f"\n[bold blue]{description}[/bold blue]")
    console.print(Panel(command, title="Command", border_style="green"))
    
    # Ask user if they want to run it
    response = input("Press Enter to run this command (or 'q' to quit): ")
    if response.lower() == 'q':
        return False
    
    # Run the command
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            console.print("[green]Output:[/green]")
            console.print(result.stdout)
        if result.stderr:
            console.print("[red]Error:[/red]")
            console.print(result.stderr)
    except Exception as e:
        console.print(f"[red]Error running command: {e}[/red]")
    
    return True

def main():
    console.print("[bold cyan]OCR Client Demo[/bold cyan]")
    console.print("This demo shows various ways to use the OCR command line client.\n")
    
    # Check if API is running
    console.print("[yellow]First, make sure the OCR API is running:[/yellow]")
    console.print("[cyan]python api.py[/cyan]\n")
    
    demos = [
        (
            "1. Show help and available options",
            "python ocr_client.py --help"
        ),
        (
            "2. Process a single PDF with default settings (English)",
            "python ocr_client.py samples/1.pdf"
        ),
        (
            "3. Process a Vietnamese document",
            "python ocr_client.py samples/2.pdf -l vie"
        ),
        (
            "4. Process with handwriting detection enabled",
            "python ocr_client.py samples/3.pdf -l vie --handwriting"
        ),
        (
            "5. Process multiple files at once",
            "python ocr_client.py samples/1.pdf samples/2.pdf -l vie"
        ),
        (
            "6. Process all PDFs in samples directory",
            "python ocr_client.py samples/*.pdf -l vie"
        ),
        (
            "7. Get raw JSON output (useful for scripting)",
            "python ocr_client.py samples/1.pdf -l vie --json"
        ),
        (
            "8. Quiet mode (suppress progress indicators)",
            "python ocr_client.py samples/2.pdf -l vie --quiet"
        ),
        (
            "9. Use custom API URL (if running on different port)",
            "python ocr_client.py samples/1.pdf --url http://localhost:8001"
        )
    ]
    
    for description, command in demos:
        if not run_demo_command(description, command):
            break
        time.sleep(1)  # Brief pause between demos
    
    console.print("\n[bold green]Demo completed![/bold green]")
    console.print("\n[yellow]Tips:[/yellow]")
    console.print("• Use [cyan]-l vie[/cyan] for Vietnamese documents")
    console.print("• Add [cyan]--handwriting[/cyan] for documents with handwritten text")
    console.print("• Use [cyan]--json[/cyan] for machine-readable output")
    console.print("• Use [cyan]--quiet[/cyan] to suppress progress indicators")
    console.print("• Process multiple files: [cyan]ocr_client.py file1.pdf file2.pdf[/cyan]")
    console.print("• Use wildcards: [cyan]ocr_client.py samples/*.pdf[/cyan]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo error: {e}[/red]")