import click
import configparser

from .selection import fzf
from .utils import path_is_valid_subkt, exit_with_msg

from rich.tree import Tree
from rich.table import Table
from rich.console import Console

console = Console()


@click.group()
@click.help_option("--help", "-h")
@click.pass_context
def config(ctx: click.Context) -> None:
    """Add, remove, edit projects in the config."""
    """
    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        None
    """
    pass


@config.command()
@click.pass_context
def add(ctx: click.Context) -> None:
    """
    Add projects to config interactively.

    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        None
    """

    config = ctx.obj["config"]

    while True:
        click.clear()

        project_name = click.prompt("Name of the project", type=str)

        if " " in project_name:
            console.print("Space in project name is not valid.")
            if not click.confirm("Do you want to add another project?", default=False):
                break
            continue

        while True:
            project_path = click.prompt("Path to the project", type=click.Path())

            if path_is_valid_subkt(project_path):
                break

        # Ask for folder structure type
        give_folder_structure_info()
        folder_structure = click.prompt(
            "Choose folder structure (normal/alternate)",
            type=click.Choice(["normal", "alternate"], case_sensitive=False),
        )

        exceptions = {}
        if folder_structure == "alternate":
            console.print(
                "Add exceptions when folder name does not match what you put in sub.properties.\n"
                "For more info on exceptions, read alternate folder section [underline][link=https://github.com/PhosCity/muxkt]in this link[/link][/underline]!"
            )

            while True:
                exception_key = click.prompt(
                    "Enter exception key (or press Enter to finish)",
                    type=str,
                    default="",
                )
                if not exception_key.strip():  # Exit the loop if input is blank
                    break
                exception_value = click.prompt(
                    f"Enter exception value'{exception_key}'", type=str, default=""
                )
                if not exception_value.strip():  # Handle blank values
                    console.print(
                        f"[red]Error:[/red] Value for '{exception_key}' cannot be blank."
                    )
                    continue
                exceptions[exception_key] = exception_value

        config = add_to_configparser(config, "Project", {project_name: project_path})
        config = add_to_configparser(
            config, "Folder Structure", {project_name: folder_structure}
        )
        if folder_structure == "alternate":
            config = add_to_configparser(
                config, f"{project_name}_exceptions", exceptions
            )

        if not click.confirm("Do you want to add another project?", default=False):
            break

    save_config(config, ctx.obj["config_file"])


@config.command()
@click.pass_context
def remove(ctx: click.Context) -> None:
    """
    Remove a project from the config.

    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        None
    """

    config = ctx.obj["config"]

    if not config.has_section("Project"):
        exit_with_msg("No projects exist in the configuration.")

    project_list = config.options("Project")
    project_to_remove = fzf(
        project_list, "Select project to remove", choose_multiple=False
    )
    if not project_to_remove:
        exit_with_msg("No project selected for removal.")

    config.remove_option("Project", project_to_remove)
    save_config(config, ctx.obj["config_file"])


@config.command()
@click.pass_context
def edit_manual(ctx: click.Context) -> None:
    """
    Manually edit the config file using the default editor on your computer.

    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        None
    """

    config_file = ctx.obj["config_file"]

    try:
        click.edit(filename=config_file)
    except click.exceptions.ClickException as e:
        exit_with_msg(f"Could not open editor: {e}")
    except Exception as e:
        exit_with_msg(e)


@config.command()
@click.pass_context
def edit(ctx: click.Context) -> None:
    """
    Edit the config file interactively.

    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        None
    """

    config = ctx.obj["config"]

    sections = config.sections()
    section = fzf(sections, "Select Section to Edit", choose_multiple=False)

    if not section:
        exit_with_msg("No section selected for editing.")

    def edit_key_value(section, key, value_type=str):
        """Edit a single key-value pair interactively."""
        new_key = click.prompt(
            f"Change name of the key (current: {key})",
            type=str,
            default="",
            show_default=False,
        )
        if not new_key:
            console.print("[cyan]No changes made to the key name.[/cyan]")
            new_key = key

        new_value = click.prompt(
            f"Change value for '{new_key}' (current: {config.get(section, key)})",
            type=value_type,
            default="",
            show_default=False,
        )
        if not new_value:
            console.print("[cyan]No changes made to the value.[/cyan]")
            new_value = config.get(section, key)

        return new_key, new_value

    if section == "Folder Structure":
        key = fzf(
            config.options(section),
            "Choose project you want to edit the folder structure of.",
            choose_multiple=False,
        )
        folder_structure_choice = fzf(
            ["normal", "alternate"],
            f"Change folder structure for '{key}' (current: {config.get("Folder Structure", key)})",
            choose_multiple=False,
        )

        if folder_structure_choice:
            config.set("Folder Structure", key, folder_structure_choice)
    elif section == "Project":
        keys = fzf(
            config.options(section),
            "Choose all keys you want to edit using tab key",
            choose_multiple=True,
        )
        for key in keys:
            while True:
                new_key, new_value = edit_key_value(
                    section, key, value_type=click.Path()
                )
                if path_is_valid_subkt(new_value):
                    config.remove_option(section, key)
                    config.set(section, new_key, new_value)
                    break
    else:
        keys = fzf(
            config.options(section),
            "Choose all keys you want to edit using tab key",
            choose_multiple=True,
        )

        for key in keys:
            new_key, new_value = edit_key_value(section, key)
            config.remove_option(section, key)
            config.set(section, new_key, new_value)

    save_config(config, ctx.obj["config_file"])


def add_history(
    ctx: click.Context,
    project: str,
    path: str,
    episode: list,
    custom_flag: tuple,
) -> None:
    """
    Replaces the 'History' section with new project, path and episodes.

    Args:
        ctx (click.Context): Context passed by click from the entry point.
        project (str): The name of the project.
        path (str): The path associated with the project.
        episode (list): The list of episodes.
        custom_flag (tuple): The custom flags for the muxing command.

    Returns:
        None
    """

    config = ctx.obj["config"]

    if config.has_section("History"):
        config.remove_section("History")

    config.add_section("History")

    serialized_episode = ",".join(str(x) for x in episode)
    serialized_flags = ",".join(str(x) for x in custom_flag)

    config.set("History", "project", project)
    config.set("History", "path", path)
    config.set("History", "episode", serialized_episode)
    config.set("History", "custom_flags", serialized_flags)

    save_config(config, ctx.obj["config_file"])


def get_history(
    ctx: click.Context,
) -> tuple[str, str, list[str], list[str]]:
    """
    Retrieve the history from the config file.

    Args:
        ctx (click.Context): Context passed by click from the entry point.

    Returns:
        str: Name of the project muxed last time.
        str: Path of the project muxed last time.
        list: Episodes of the project that were muxed last time.
        list: Custom flags for the last mux.
    """

    config = ctx.obj["config"]

    if not config.has_section("History"):
        exit_with_msg("No history found in the configuration.")

    project = config.get("History", "project")
    path = config.get("History", "path")

    serialized_episode = config.get("History", "episode")
    episode = serialized_episode.split(",")

    serialized_flags = config.get("History", "custom_flags")
    flags = serialized_flags.split(",") if serialized_flags else []

    return project, path, episode, flags


def read_config(
    config: configparser.ConfigParser,
    project: str | None,
) -> tuple[str, str]:
    """
    Read the config and collects the project's name and its path.

    Args:
        config (configparser.ConfigParser): The configuration object.
        project (str | None): Name of the project whose path to find in config; None if user wants to select project and its path interactively from config.

    Returns:
        str: Name of the project muxed last time.
        str: Path of the project muxed last time.
    """

    if not config.has_section("Project"):
        exit_with_msg(
            "No projects found in the config. Run 'muxkt config add' to add projects."
        )

    if not project:
        project = fzf(
            config.options("Project"),
            "Select a project",
            choose_multiple=False,
        )
        if not project:
            exit_with_msg("No project selected.")

    try:
        path = config.get("Project", project)
    except configparser.NoOptionError:
        exit_with_msg(f"No project named '{project}' found in the config")
    return project, path


def add_to_configparser(
    config: configparser.ConfigParser,
    section_name: str,
    section_options: dict,
) -> configparser.ConfigParser:
    """
    Add sections to the config object

    Args:
        config (configparser.ConfigParser): The configuration object.
        section_name (str): Name of the section to add to the config.
        section_options(dict): Options to add to the config

    Returns:
        config (configparser.ConfigParser): The configuration object.
    """

    if not config.has_section(f"{section_name}"):
        config.add_section(f"{section_name}")

    for key, value in section_options.items():
        config.set(f"{section_name}", key, value)

    return config


def save_config(
    config: configparser.ConfigParser,
    config_file: str,
) -> None:
    """
    Saves the current configuration to the config file.

    Args:
        config (configparser.ConfigParser): The configuration object.
        config_file (str): Path of the config file

    Returns:
        None
    """

    with open(config_file, "w") as config_file:
        config.write(config_file)


def give_folder_structure_info() -> None:
    """
    Prints the information about folder structures

    Args:
        None

    Returns:
        None
    """

    normal = Tree(".")
    for item in ["01", "02", "03", "...", "Subkt Configs"]:
        normal.add(item)

    alternate = Tree(".")
    arc_1 = alternate.add("01 Name of Arc 1/ Season 1")
    for item in ["01", "02", "..."]:
        arc_1.add(item)

    arc_2 = alternate.add("01 Name of Arc 1/ Season 1")
    for item in ["01", "02", "..."]:
        arc_2.add(item)

    alternate.add("Subkt Configs")

    table = Table(show_lines=True)

    table.add_column("Folder Type", justify="left", no_wrap=True)
    table.add_column("Folder Tree", justify="left", no_wrap=True)

    table.add_row("normal", normal)
    table.add_row("alternate", alternate)
    console.print(table)
    console.print(
        "For more info on folder structure, read alternate folder section [underline][link=https://github.com/PhosCity/muxkt]in this link[/link][/underline]!"
    )
