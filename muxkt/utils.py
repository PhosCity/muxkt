import os
import sys
from shutil import which

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

console = Console()


def path_is_valid_subkt(path: str) -> bool:
    """
    Checks if the given path contains a file named 'build.gradle.kts'.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if 'build.gradle.kts' exists in the path, False otherwise.
    """

    if not os.path.isdir(path):
        console.print(
            f"[red]Error:[/red] The provided path '{path}' is not a valid directory."
        )
        return False

    if not os.path.isfile(os.path.join(path, "build.gradle.kts")):
        console.print(
            f"[red]Error:[/red] The provided path '{path}' does not appear to be a valid path that has subkt files."
        )
        return False
    return True


def exit_with_msg(message: str) -> None:
    """
    Exit the program with a styled error message.

    Args:
        message (str): Message to show before exiting.

    Returns:
        None
    """

    console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)


def check_dependencies() -> bool:
    """
    Check if required dependencies are installed and accessible.

    Returns:
        bool: Returns True if all dependencies are met; otherwise exits the program after showing the list of dependencies that are not installed.
    """

    dependencies = ["java", "mkvmerge"]
    missing_dependencies = [dep for dep in dependencies if which(dep) is None]

    if missing_dependencies:
        console.print("[bold red]The following dependencies are missing:[/bold red]")

        # Display missing dependencies in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=4)
        table.add_column("Dependency", style="bold")

        for i, dep in enumerate(missing_dependencies, start=1):
            table.add_row(str(i), dep)

        console.print(table)
        sys.exit(1)
    else:
        return True


def msg_in_box(title: str, message: str) -> None:
    """
    Print text in a box with title

    Args:
        title (str): Title of the box
        message (str): Message to be shown inside the box

    Returns:
        None
    """

    console.print(
        Panel.fit(
            message,
            box=box.ROUNDED,
            padding=(1, 2),
            title=title,
            border_style="bright_blue",
            title_align="left",
        ),
    )
