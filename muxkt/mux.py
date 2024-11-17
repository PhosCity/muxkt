import os
import re
import sys
import click
import subprocess

from .selection import fzf
from .utils import exit_with_msg, check_dependencies
from .config import add_history, get_history, read_config

from rich import box
from rich.text import Text
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command()
@click.pass_context
@click.help_option("--help", "-h")
@click.argument(
    "project",
    required=False,
    nargs=1,
)
@click.argument(
    "episode",
    required=False,
    nargs=-1,
    type=int,
)
@click.option(
    "-r",
    "--repeat",
    is_flag=True,
    help="Repeat last muxing action.",
)
@click.option(
    "-o",
    "--output",
    is_flag=True,
    help="See original output of previous mux",
)
@click.option(
    "-c",
    "--custom_flag",
    type=str,
    multiple=True,
    help="Provide multiple custom Gradle flags (e.g., -Pkey=value).",
)
def mux(
    ctx: click.Context,
    project: str | None,
    episode: tuple | None,
    repeat: bool,
    output: bool,
    custom_flag: str,
) -> None:
    """Mux the episodes using the arguments and the options provided by the user."""
    """
    Args:
        ctx (click.Context): Context passed by click from the entry point.
        project (str | None): Name of the project. None if no argument provided.
        episode (tuple | None): Tuple of episodes that user provided as an argument. None if no agrument provided.

    Options:
        repeat_last (bool): Mux using last mux settings. True if user used --repeat or --r option; otherwise False
        output (bool): Show output of last mux verbatim and exit. True if user used --output or --o; otherwise False
        custom_flag (str): Custom flag that user wants to append to the gradle command

    Returns:
        None
    """

    if output:
        cat_output(ctx)

    check_dependencies()

    project_name, path, episode = get_project_info(ctx, project, episode, repeat)

    add_history(ctx, project_name, path, episode)

    output_file = ctx.obj["output_file"]

    try:
        os.chdir(path)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] The path '{path}' does not exist.")
    except PermissionError:
        console.print(
            f"[red]Error:[/red] You do not have permission to access '{path}'."
        )

    # click.clear()
    for ep in episode:
        cmdfile = "./gradlew" if os.name == "posix" else "gradlew.bat"
        command = [cmdfile, "--console=plain"]
        if custom_flag:
            command.extend(custom_flag)
        command.append(f"mux.{ep}")

        try:
            with console.status(f'[cyan]Muxing "{project_name}" - Episode {ep}[/cyan]'):
                with open(output_file, "w") as f:
                    result = subprocess.run(command, stdout=f, stderr=f, text=True)

            if result.returncode == 0:
                mux_success(output_file)
            else:
                mux_warning(output_file)
                mux_failure(output_file)

        except Exception as e:
            console.print(f"[red]Error during muxing: {e}[/red]")


def mux_success(output_file: str) -> None:
    """
    Process the muxing outpt file and display categorized results.

    Args:
        output_file (str): The path to the file where output of the mux is stored.

    Returns:
        None
    """

    try:
        with open(output_file, "r") as f:
            lines = f.read()

        patterns_and_headers = [
            (r"> Task :([^S].*)", "TASKS PERFORMED:"),
            (r"(CHAPTER.*)", "CHAPTERS GENERATED:"),
            (r"(Track.*])", "TRACK LIST:"),
            (r"Attaching (.*[otOT][tT][fF])", "FONTS ATTACHED:"),
            (r"(Validating fonts.*|warning: .*)", "WARNINGS:"),
            (r"Attaching (.*[otOT][tT][fF])", "DUPLICATE FONTS ATTACHED:"),
            (r"Output: (.*mkv)", "OUTPUT:"),
            (r"(\d+ actionable tasks:.*)", ""),
            (r"(BUILD SUCCESSFUL in .*s)", ""),
        ]

        for pattern, header in patterns_and_headers:
            matches = [match.group(1) for match in re.finditer(pattern, lines)]
            if not matches:
                continue

            # Process results based on the header
            if header == "WARNINGS:":
                mux_warning(output_file)
                continue

            if header == "TASKS PERFORMED:":
                console.rule(Text(header, style="bold green"))
                matches = [match.replace(".default", "") for match in matches]

                table = Table(row_styles=["dim", "none"])
                table.add_column(style="dim")

                for i, item in enumerate(matches):
                    match = re.compile(r"([^.]+)\.([^\s]+)( UP-TO-DATE)?").match(item)
                    if match:
                        number_padded = str(i + 1)
                        name_part = match.group(1)
                        after_dot_part = match.group(2)
                        status = match.group(3) or "COMPLETED"
                        if i == 0:  # Set the header only once
                            table.add_column(f"Task performed for {after_dot_part}")
                            table.add_column("Status")
                        table.add_row(number_padded, name_part, status)
                console.print(table)

            elif header == "FONTS ATTACHED:":
                console.rule(Text(header, style="bold green"))
                matches.sort()
                table = Table(show_header=False, row_styles=["dim", "none"])

                for index, font in enumerate(matches, start=1):
                    table.add_row(str(index), font)

                console.print(table)

            elif header == "DUPLICATE FONTS ATTACHED:":
                matches = list(set(item for item in matches if matches.count(item) > 1))
                # matches.sort()
                if matches:
                    console.rule(Text(header, style="bold green"))
                    table = Table(show_header=False, row_styles=["dim", "none"])

                    for index, font in enumerate(matches, start=1):
                        table.add_row(str(index), font)

                    console.print(table)

            elif header == "TRACK LIST:":
                console.rule(Text(header, style="bold green"))
                table = Table(row_styles=["dim", "none"])
                table.add_column("Track")
                table.add_column("Metadata")
                table.add_column("File")

                pattern = r"Track (\w+) \((.*?)\) \[(.*?)\]$"

                for item in matches:
                    match = re.search(pattern, item)
                    if match:
                        table.add_row(match.group(1), match.group(2), match.group(3))

                console.print(table)

            elif header == "CHAPTERS GENERATED:":
                console.rule(Text(header, style="bold green"))
                table = Table(row_styles=["dim", "none"])
                table.add_column("Name", justify="left")
                table.add_column("Timestamp", justify="left")

                for i in range(0, len(matches), 2):
                    line1 = matches[i]
                    line2 = matches[i + 1]

                    _, value1 = line1.split("=")
                    _, value2 = line2.split("=")

                    table.add_row(value2, value1)
                console.print(table)

            else:
                if header:
                    console.rule(Text(header, style="bold green"))
                for match in matches:
                    click.echo(match)
            console.print()

    except FileNotFoundError:
        exit_with_msg("Output file not found.")


def mux_warning(output_file: str) -> None:
    """
    Process the muxing outpt file and display the warnings found in the file.
    Warnings include font validation messages and general warning messages.

    Args:
        output_file (str): The path to the file where output of the mux is stored.

    Returns:
        None
    """

    def in_box(title, message):
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

    grouped = []
    current_group = []

    try:
        with open(output_file, "r") as f:
            for line in f:
                if re.search(r"[vV]alidating fonts for.*", line):
                    if current_group:
                        grouped.append(current_group)
                    current_group = [line.strip()[:-3]]
                elif re.search(r"[wW]arning: .*", line):
                    warning = re.sub(r"^.*[wW]arning: (.*).*$", r"\1", line)
                    if current_group:
                        current_group.append(warning.strip())

        if current_group:
            grouped.append(current_group)

    except FileNotFoundError:
        exit_with_msg("Output file not found.")

    if grouped:
        console.rule(Text("WARNINGS:", style="bold green"))
        for group in grouped:
            title = group.pop(0)

            text = Text()
            if not group:
                group.append("No issues were found.")

            for txt in group:
                style = "bold magenta" if "not found" in txt else None
                text.append(txt, style=style)
                text.append("\n")

            in_box(title, text)
            console.print()


def mux_failure(output_file: str) -> None:
    """
    Process the muxing outpt file and display the reasons why the mux failed.

    Args:
        output_file (str): The path to the file where output of the mux is stored.

    Returns:
        None: Prints out the formatted mux output.
    """

    failure_patterns = [
        r"(What went wrong.*)",
        r"(A problem occurred.*)",
        r"(Execution failed for task.*)",
        r"(Error resolving.*)",
        r"(.*not found in root project.*)",
        r"(style already exists.*)",
        r"(one or more fatal font-related issues encountered.*)",
        r"(FileNotFoundException.*)",
        r"(mkvmerge -J command failed.*)",
        r"(mkvmerge -J command timed out for file.*)",
        r"(malformed property.*)",
        r"(mkvmerge failed:.*)",
        r"(Error: .*)",
        r"(FAILURE: .*)",
        r"(is ambiguous in root project.*)",
        r"(could not find target sync line.*)",
        r"(could not find property file.*)",
        r"(Could not create task.*)",
        r"(no chapter definitions found;.*)",
        r"(Negative time after shifting line from.*)",
        r"(Could not resolve.*)",
        r"(Could not list available versions.*)",
        r"(duplicate target sync lines with value.*)",
        r"(could not post to webhook:.*)",
        r"(Unexpected CRC for.*)",
        r"(not a valid CRC:.*)",
        r"(malformed line in.*)",
        r"(Recursive property dependency detected:.*)",
        r"(Attempting to access unfinished task.*)",
        r"(Attempted to access entry.*)",
        r"(more than one file added, but no root set, or conflicting roots..*)",
        r"(couldn't upload torrent:.*)",
        r"(request failed:.*)",
        r"(could not upload.*)",
        r"(can't convert type to destination directory:.*)",
        r"(Invalid SSL Session.*)",
        r"(Could not create directory:.*)",
        r"(ssh command failed.*)",
        r"(no conversion available from String to.*)",
        r"(Invalid value for Collisions:.*)",
        r"(too few fields in section.*)",
        r"(could not parse.*)",
        r"(no match for property name.*)",
        r"(not a valid time:.*)",
        r"(not a valid color:.*)",
        r"(not a valid boolean:.*)",
        r"(not a valid boolean:.*)",
        r"(BUILD FAILED.*)",
    ]
    with open(output_file) as f:
        lines = f.read()

    for pattern in failure_patterns:
        matches = re.finditer(pattern, lines)
        for match in matches:
            console.print(match.group(1))
            console.print()


def cat_output(ctx: click.Context) -> None:
    """
    Print out the actual subkt output of previous mux

    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        None: Prints out the previous output and exits the program.
    """

    try:
        output_file = os.path.join(ctx.obj["config_file_path"], "output.txt")

        with open(output_file, "r") as f:
            content = f.read()

        console.print("[bold cyan]Output File Content:[/bold cyan]")
        console.print(content)
        sys.exit(0)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] File not found: {output_file}")
        sys.exit(1)
    except IOError as e:
        console.print(f"[bold red]Error:[/bold red] Could not read file: {e}")
        sys.exit(1)


def get_project_info(
    ctx: click.Context,
    project: str | None,
    episode: tuple | None,
    repeat_last: bool,
) -> tuple[str, str, tuple | None]:
    """
    Gets the info about the project.

    Args:
        project (str | None): Project argument given by user
                              None if no argument provided.
        episode (tuple | None): Tuple of episodes that user provided as an argument.
                                None if no agrument provided.
        repeat_last (bool): True if user used --repeat or --r option; otherwise False

    Returns:
        project_name (str): Name of the project either from history or from config
        path (str): Path of the project either from history or from config
        episode (tuple | None): Episode to mux. Tuple if grabbed from history or provided as an argument by user; otherwise None.
    """

    if repeat_last:
        return get_history(ctx)
    else:
        project_name, path = read_config(ctx.obj["config"], project)
        episode = get_episodes(ctx, project_name, path, episode)
        return project_name, path, episode


def get_episodes(
    ctx: click.Context,
    project_name: str,
    path: str,
    episode: tuple | None,
) -> list[str]:
    """
    Gets all the episodes for the chosen project.

    If the config has set the project's folder structure as alternate, first asks the user to select arc/season folder.
    For alternate folders, asks the user to select the episodes inside the arc/season folder.

    For non-alternate folders, asks the user to select the episodes inside the path itself.

    Args:
        project_name (str): The name of the project from the config.
        path (str): The directory path to search for episodes/arcs/seasons.
        episode (tuple | None): None if user does not provide episode as an argument or does not repeat last mux.
                                Tuple of episodes that user provided as an argument or retrieved from last mux's history.

    Returns:
        list[str]: List of all the episodes that needs to be muxed.
    """

    config = ctx.obj["config"]

    alternate_folder = config.get("Folder Structure", project_name) == "alternate"

    if episode:
        episode = [f"{ep:02}" for ep in sorted(episode)]

    if episode and not alternate_folder:
        return episode

    elif not episode and not alternate_folder:
        return select_folder(path, "Select single or multiple episode: ", True)

    else:
        arc = select_folder(path, "Select an arc/season: ", False)
        if not episode:
            episode = select_folder(
                os.path.join(path, arc),
                "Select single or multiple episode: ",
                True,
            )
        arc = arc[3:].replace(" ", "").lower()

        exceptions_section = f"{project_name}_exceptions"
        if config.has_option(exceptions_section, arc):
            arc = config.get(exceptions_section, arc)

        return [arc + "_" + str(ep) for ep in episode]


def select_folder(
    path: str,
    prompt: str,
    multi: bool,
) -> list[str] | str:
    """
    Allows the user to select folders within the given path that start with a number.

    Args:
        path (str): The directory path to search for folders.
        prompt (str): The prompt message to display to the user.
        multi (bool): Whether to allow multiple selections.

    Returns:
        list or str: The selected folder(s). Returns a list if `multi` is True; otherwise, a single folder name.
    """

    # Get a sorted list of directories in the given path that start with a digit
    valid_folders = sorted(
        folder
        for folder in os.listdir(path)
        if os.path.isdir(os.path.join(path, folder)) and folder[0].isdigit()
    )
    selected_folders = fzf(valid_folders, prompt=prompt, choose_multiple=multi)

    if not selected_folders:
        exit_with_msg("User did not select anything. Exiting.")
    return selected_folders
