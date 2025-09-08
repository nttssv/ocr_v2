#!/usr/bin/env python3
"""
OCR API Command Line Client

A simple command-line interface for testing the OCR API.
Allows users to quickly process PDF files and view results.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class OCRClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_server(self):
        """Check if the OCR API server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def process_document(self, file_path, language="eng", enable_handwriting=False):
        """Process a PDF document through the OCR API"""
        if not os.path.exists(file_path):
            console.print(f"[red]Error: File '{file_path}' not found[/red]")
            return None
        
        files = {'file': open(file_path, 'rb')}
        data = {
            'language': language,
            'enable_handwriting_detection': str(enable_handwriting).lower()
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Processing document...", total=None)
                
                response = self.session.post(
                    f"{self.base_url}/documents/transform",
                    files=files,
                    data=data,
                    timeout=300  # 5 minute timeout
                )
            
            files['file'].close()
            
            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red]Error: API returned status {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                return None
                
        except requests.exceptions.Timeout:
            console.print("[red]Error: Request timed out[/red]")
            return None
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return None
        finally:
            if 'file' in files:
                files['file'].close()
    
    def display_results(self, result, file_path):
        """Display OCR results in a formatted way"""
        if not result:
            return
        
        # Main info panel
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Key", style="cyan")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("File", os.path.basename(file_path))
        info_table.add_row("Status", result.get('status', 'Unknown'))
        processing_time = result.get('processing_time', 0)
        if processing_time is not None:
            info_table.add_row("Processing Time", f"{processing_time:.2f}s")
        else:
            info_table.add_row("Processing Time", "N/A")
        info_table.add_row("Total Pages", str(result.get('total_pages', 0)))
        info_table.add_row("Language", result.get('language', 'Unknown'))
        
        console.print(Panel(info_table, title="📄 Document Information", border_style="blue"))
        
        # Pages results
        if 'pages' in result and result['pages'] is not None:
            pages_table = Table()
            pages_table.add_column("Page", justify="center", style="cyan")
            pages_table.add_column("Processing Time", justify="center", style="green")
            pages_table.add_column("Text Preview", style="white")
            pages_table.add_column("Issues", style="yellow")
            
            for page in result['pages']:
                page_num = page.get('page_number', 'N/A')
                page_proc_time = page.get('processing_time', 0)
                proc_time = f"{page_proc_time:.2f}s" if page_proc_time is not None else "N/A"
                text_preview = page.get('extracted_text', '')[:50] + "..." if len(page.get('extracted_text', '')) > 50 else page.get('extracted_text', '')
                issues = str(len(page.get('issues_detected', [])))
                
                pages_table.add_row(str(page_num), proc_time, text_preview, issues)
            
            console.print(Panel(pages_table, title="📑 Page Results", border_style="green"))
        
        # Quality analysis
        if 'quality_analysis' in result and result['quality_analysis'] is not None:
            qa = result['quality_analysis']
            quality_table = Table(show_header=False, box=None)
            quality_table.add_column("Metric", style="cyan")
            quality_table.add_column("Value", style="white")
            
            overall_score = qa.get('overall_score', 0)
            text_clarity = qa.get('text_clarity_score', 0)
            layout_score = qa.get('layout_score', 0)
            
            quality_table.add_row("Overall Score", f"{overall_score:.1f}/10" if overall_score is not None else "N/A")
            quality_table.add_row("Text Clarity", f"{text_clarity:.1f}/10" if text_clarity is not None else "N/A")
            quality_table.add_row("Layout Score", f"{layout_score:.1f}/10" if layout_score is not None else "N/A")
            quality_table.add_row("Issues Found", str(len(qa.get('issues_detected', []))))
            
            console.print(Panel(quality_table, title="🔍 Quality Analysis", border_style="yellow"))
        
        # Output files info
        if 'output_files' in result and result['output_files'] is not None:
            output_info = "\n".join([
                f"📁 Output Directory: {result['output_files'].get('output_directory', 'N/A')}",
                f"📄 Processed PDF: {result['output_files'].get('processed_pdf', 'N/A')}",
                f"📊 Analysis JSON: {result['output_files'].get('analysis_json', 'N/A')}"
            ])
            console.print(Panel(output_info, title="💾 Output Files", border_style="magenta"))

def main():
    parser = argparse.ArgumentParser(
        description="OCR API Command Line Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # Process with default settings
  %(prog)s document.pdf -l vie             # Process Vietnamese document
  %(prog)s document.pdf -l eng --handwriting # Enable handwriting detection
  %(prog)s samples/*.pdf -l vie            # Process multiple files
        """
    )
    
    parser.add_argument('files', nargs='+', help='PDF file(s) to process')
    parser.add_argument('-l', '--language', default='eng', 
                       help='OCR language code (default: eng)')
    parser.add_argument('--handwriting', action='store_true',
                       help='Enable handwriting detection')
    parser.add_argument('--url', default='http://localhost:8000',
                       help='OCR API base URL (default: http://localhost:8000)')
    parser.add_argument('--json', action='store_true',
                       help='Output raw JSON results')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress progress output')
    
    args = parser.parse_args()
    
    if args.quiet:
        console.quiet = True
    
    client = OCRClient(args.url)
    
    # Check if server is running
    if not client.check_server():
        console.print(f"[red]Error: OCR API server is not running at {args.url}[/red]")
        console.print("[yellow]Make sure to start the API server first:[/yellow]")
        console.print("[cyan]python api.py[/cyan]")
        sys.exit(1)
    
    console.print(f"[green]✓ Connected to OCR API at {args.url}[/green]")
    
    # Process files
    for file_path in args.files:
        # Handle glob patterns
        if '*' in file_path:
            import glob
            matching_files = glob.glob(file_path)
            if not matching_files:
                console.print(f"[yellow]No files found matching pattern: {file_path}[/yellow]")
                continue
        else:
            matching_files = [file_path]
        
        for file_to_process in matching_files:
            console.print(f"\n[bold blue]Processing: {file_to_process}[/bold blue]")
            
            start_time = time.time()
            result = client.process_document(
                file_to_process, 
                args.language, 
                args.handwriting
            )
            end_time = time.time()
            
            if result:
                if args.json:
                    console.print(json.dumps(result, indent=2))
                else:
                    client.display_results(result, file_to_process)
                    console.print(f"[dim]Total time: {end_time - start_time:.2f}s[/dim]")
            else:
                console.print(f"[red]Failed to process {file_to_process}[/red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1)