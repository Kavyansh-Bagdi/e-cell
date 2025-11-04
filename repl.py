#!/usr/bin/env python3
import os
import time
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

# === Import your functions ===
from functions.generate_db import create_and_populate_db
from functions.verify_db import verify

console = Console()

# ====== Banner ======
def show_banner():
    console.clear()
    width = console.size.width

    title_text = Text("SEAT ALLOCATION SYSTEM", style="bold cyan", justify="center")
    subtitle_text = "Manage Exams • Verify Database • Generate Seating • Host Webpage"

    panel = Panel(
        title_text,
        subtitle=subtitle_text,
        style="bold magenta",
        border_style="cyan",
        box=box.DOUBLE_EDGE,
        width=width,
    )

    console.print(panel)


# ====== Utility Functions ======
def pause(seconds=1):
    time.sleep(seconds)


def step(message, color="cyan"):
    console.print(f"[{color}]→ {message}[/{color}]")


def success(message):
    console.print(f"[bold green]✔ {message}[/bold green]")


def failure(message):
    console.print(f"[bold red]✖ {message}[/bold red]")


# ====== Main Flow ======
def main():
    show_banner()
    console.print("\n[bold yellow]Welcome to the interactive REPL interface.[/bold yellow]")
    console.print("Answer the following steps to proceed:\n")

    # Step 1: Generate Database
    if questionary.confirm("1) Generate Database from PDF input?").ask():
        step("Generating database from PDF...")
        try:
            create_and_populate_db()
            success("Database generated successfully!")
        except Exception as e:
            failure(f"Error generating database: {e}")
            return
        pause(1)

    # Step 2: Verify Database Integrity
    if questionary.confirm("2) Verify Database Integrity?").ask():
        step("Verifying database...")
        try:
            result = verify()
            if result is False:
                failure("Database verification failed. Please review errors above.")
            else:
                success("Database verified successfully!")
        except Exception as e:
            failure(f"Verification failed: {e}")
            return
        pause(1)

    # Step 3: Generate Seat Arrangement
    if questionary.confirm("3) Generate Seat Arrangement?").ask():
        step("Generating seat arrangement...")

        generate_pdf = False
        if questionary.confirm("   └── Do you want to generate a PDF as well?").ask():
            generate_pdf = True

        try:
            if generate_pdf:
                os.system("python3 app.py --pdf")
                success("Seat arrangement PDF generated successfully!")
            else:
                os.system("python3 app.py")
                success("Seat arrangement generated successfully!")
        except Exception as e:
            failure(f"Error generating seat arrangement: {e}")
            return
        pause(1)

    # Step 4: Host Webpage Locally
    if questionary.confirm("4) Host Seat Arrangement Webpage locally?").ask():
        step("Starting web server...")
        try:
            os.system("python3 webpage/app.py")
        except Exception as e:
            failure(f"Error starting web server: {e}")
            return

    console.rule("[bold cyan]Process Complete[/bold cyan]")
    console.print("[bold green]All operations finished successfully. Exiting Seat Allocation System.[/bold green]")


# ====== Entry Point ======
if __name__ == "__main__":
    main()
