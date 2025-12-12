"""
PDF Tool – Search + Split
Commands:
    search   -> find text/title inside PDF
    split    -> extract page range into new PDF
"""

import sys
import re
import os
from pathlib import Path
import argparse
from rich.console import Console
from rich.progress import Progress
from PyPDF2 import PdfReader, PdfWriter
from rich.prompt import Prompt

console = Console()

# ----------------------------------------
# Helper: normalize text for fuzzy search
# ----------------------------------------
def normalize(text: str):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()

# ----------------------------------------
# SEARCH FUNCTION
# ----------------------------------------
def search_pdf(pdf_path: Path, query: str):
    if not pdf_path.exists():
        console.print(f"[red]❌ File not found: {pdf_path}")
        sys.exit(1)

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        console.print(f"[red]Error opening PDF: {e}")
        sys.exit(1)

    total_pages = len(reader.pages)
    normalized_query = normalize(query)
    matches = []

    console.print(f"[cyan]🔍 Searching '{query}' in {pdf_path.name} ({total_pages} pages)...")

    with Progress() as progress:
        task = progress.add_task("[green]Scanning pages...", total=total_pages)

        for i in range(total_pages):
            text = reader.pages[i].extract_text() or ""
            if normalized_query in normalize(text):
                matches.append(i + 1)
            progress.update(task, advance=1)

    if not matches:
        console.print(f"[red]❌ Not found.")
    else:
        console.print(f"[green]✓ Found on pages: {', '.join(map(str, matches))}")

# ----------------------------------------
# SPLITTER FUNCTION
# ----------------------------------------
def parse_range(r: str, total: int):
    if "-" not in r:
        raise ValueError("Page range must be in start-end format")

    start, end = r.split("-")
    start, end = int(start), int(end)

    if start < 1 or end < 1:
        raise ValueError("Pages must be >= 1")
    if start > end:
        raise ValueError("Start cannot be greater than end")
    if end > total:
        raise ValueError(f"Page range exceeds document length ({total})")

    return start, end


def split_pdf(pdf_path: Path, range_str: str):
    if not pdf_path.exists():
        console.print(f"[red]❌ File not found: {pdf_path}")
        sys.exit(1)

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        console.print(f"[red]Error opening PDF: {e}")
        sys.exit(1)

    total_pages = len(reader.pages)

    try:
        start, end = parse_range(range_str, total_pages)
    except Exception as e:
        console.print(f"[red]❌ {e}")
        sys.exit(1)

    count = end - start + 1
    output_name = str(Prompt.ask('New Filename? '))
    output = f"{output_name}_p_{start}-{end}.pdf"
    writer = PdfWriter()

    console.print(f"[cyan]✂️ Splitting pages {start} → {end}")

    with Progress() as progress:
        task = progress.add_task("[green]Extracting...", total=count)

        for page_index in range(start - 1, end):
            writer.add_page(reader.pages[page_index])
            progress.update(task, advance=1)

    with open(output, "wb") as f:
        writer.write(f)

    size_mb = os.path.getsize(output) / (1024 * 1024)
    console.print(f"[green]✓ Saved as:[/green] {output} ({size_mb:.2f} MB)")

# ----------------------------------------
# CLI ARGPARSE SETUP
# ----------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="PDF Utility Tool – Search & Split",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command")

    # SEARCH COMMAND
    s = sub.add_parser("search", help="Search text/title inside PDF")
    s.add_argument("pdf", type=str, help="PDF file path")
    s.add_argument("query", type=str, help="Text to search")

    # SPLIT COMMAND
    sp = sub.add_parser("split", help="Split PDF by page range")
    sp.add_argument("pdf", type=str, help="PDF file path")
    sp.add_argument("range", type=str, help="Page range, e.g., 10-40")

    args = parser.parse_args()

    if args.command == "search":
        search_pdf(Path(args.pdf), args.query)

    elif args.command == "split":
        split_pdf(Path(args.pdf), args.range)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
