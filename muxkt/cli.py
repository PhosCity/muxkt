import os
import re
import click
import subprocess
from time import sleep
from iterfzf import iterfzf
from configparser import ConfigParser
from shutil import which

VERSION = "0.1.1"
CONF = ConfigParser()
PYMUX_FOLDER = click.get_app_dir("muxkt")
CONFIG = os.path.join(PYMUX_FOLDER, "config")
DEPENDENCIES = ["java", "mkvmerge"]


class Config:
    def __init__(self):
        if not os.path.exists(PYMUX_FOLDER):
            os.makedirs(PYMUX_FOLDER)

    def config_exists(self):
        """Checks if config file exists"""
        return os.path.exists(CONFIG)

    def config_add(self):
        """Add projects to config."""
        if not self.config_exists():
            click.secho(("Creating new config..."), fg="blue")
        CONF.read(CONFIG)
        if not CONF.has_section("Project"):
            CONF.add_section("Project")
        while True:
            # Ask user for project informtation
            click.clear()
            project = click.prompt("Name of Project", type=str)
            path = click.prompt("Path of the project", type=str)
            if os.path.exists(path):
                if not path_is_subkt(path):
                    click.secho(
                        ("Please add a path that has the subkt configs."), fg="red"
                    )
                else:
                    click.secho((f"\nAdded a new project {project}"), fg="green")
                    CONF.set("Project", project, path)

                    with open(CONFIG, "w") as c:
                        CONF.write(c)
            else:
                click.secho((f"\n {path} is not a valid path"), fg="red")
            if not click.confirm("Do you want to continue adding project to config?"):
                break

    def config_remove(self):
        """Remove projects from the config."""
        if not self.config_exists():
            exit_with_msg("Config does not exist. Exiting.")
        CONF.read(CONFIG)
        if CONF.has_section("Project"):
            project = iterfzf(
                selection(CONF["Project"]), prompt="Select a project to remove:"
            )
            if project:
                CONF.remove_option("Project", project)
                with open(CONFIG, "w") as c:
                    CONF.write(c)
            else:
                exit_with_msg("No project selected.")

    def config_read(self, name):
        """Read projects from config and allows the user to choose from all the availabe projects.
        If project name is passed as an argument, then it auto-chooses from the config.
        Finally, once project is chosen, it reads the path of the project.
        If config does not exist, it prompts the user to add one.
        """
        if not self.config_exists():
            click.secho(("Config does not exists."), fg="red")
            if click.confirm("\nDo you want to add a new config?"):
                self.config_add()
            else:
                exit_with_msg("\nCannot proceed without config. Exiting!")

        CONF.read(CONFIG)
        if name:
            project = name
        else:
            project = iterfzf(selection(CONF["Project"]), prompt="Select a project:")

        try:
            path = CONF["Project"][project]
        except KeyError:
            click.secho(
                (f'The project "{name}" does not exist in the config.'), fg="red"
            )
            click.echo("\nThe valid project names are:")
            for i in CONF["Project"]:
                click.echo(i)
            exit()

        return project, path

    def config_edit(self):
        """Manually edit the config fileself.
        It auto-chooses a default editor of your computer."""
        if not self.config_exists():
            click.echo("Config does not exists.")
        else:
            try:
                click.edit(filename=CONFIG)
            except Exception:
                click.echo("Editor could not be found.")

    def config_history(self):
        """Reads the muxing history saved in config."""
        if not self.config_exists():
            exit_with_msg("Could not retrieve history becuase config does not exist.")
        CONF.read(CONFIG)
        try:
            project_hist = list(CONF["History"])
        except KeyError:
            exit_with_msg("History could not be found in the config.")
        project = project_hist[0]
        path_episodes_hist = CONF["History"][project]
        path_episodes = path_episodes_hist.split(";")
        path = path_episodes[0]
        chosen_episodes = path_episodes[1].split(",")
        return (project, path, chosen_episodes)

    def add_history(self, project, path, episode):
        episode = ",".join([str(x) for x in episode])
        CONF.remove_section("History")
        CONF.add_section("History")
        hist = path + ";" + episode
        CONF.set("History", project, hist)
        with open(CONFIG, "w") as c:
            CONF.write(c)


class Mux:
    def __init__(self) -> None:
        self.output_file = os.path.join(PYMUX_FOLDER, "output.txt")

    def mux_episodes(self, project, path, chosen_episodes):
        click.clear()
        # Add history
        Config().add_history(project, path, chosen_episodes)
        for ep in chosen_episodes:
            click.secho((f'Muxing "{project}" - Episode {ep}'), fg="blue")
            cmdfile = "./gradlew" if os.name == "posix" else "gradlew"
            command = [cmdfile, "--console=plain", "mux." + str(ep)]

            with open(self.output_file, "w") as f:
                p1 = subprocess.run(command, stdout=f, stderr=f, text=True)
                if p1.returncode == 0:
                    (
                        font_list,
                        task_list,
                        chapter_list,
                        track_list,
                        output_list,
                    ) = self.parse_output()
                    font_list.sort()
                    results_list = [task_list, chapter_list, track_list, font_list]
                    results_headers = [
                        "TASKS PERFORMED:",
                        "CHAPTERS CREATED:",
                        "MKV TRACKS:",
                        "FONTS ATTACHED:",
                    ]
                    # Print the results
                    for items, headers in zip(results_list, results_headers):
                        if items:
                            click.secho((headers), fg="green", bold=True)
                            for i in items:
                                click.echo(i)
                            click.echo("")

                    # Print the warnings
                    self.mux_warning()

                    # Not a subkt feature but warn if there are duplicate fonts attached(at least the names)
                    duplicate_fonts = [x for x in font_list if font_list.count(x) > 1]
                    unique_duplicates = list(set(duplicate_fonts))
                    if unique_duplicates:
                        click.secho(
                            (
                                "The following fonts' name seems to be duplicated. You might want to take a look:"
                            ),
                            fg="red",
                        )
                        for i in unique_duplicates:
                            click.echo(i)
                        click.echo("")

                    # Pring the muxed episode name
                    if output_list:
                        click.secho("OUTPUT:", fg="green", bold=True)
                        click.echo(output_list[0])
                        click.echo("")
                    click.secho(("BUILD SUCCESSFUL"), fg="green")
                else:
                    self.mux_warning()
                    self.mux_failure()

    def parse_output(self):
        font_list = []
        task_list = []
        chapter_list = []
        track_list = []
        output_list = []
        raw_strings = [
            r"Attaching (.*[otOT][tT][fF])",
            r"> Task :([^S].*)",
            r"(CHAPTER.*)",
            r"(Track .*])",
            r"Output: (.*\.mkv)",
        ]
        list_of_lists = [font_list, task_list, chapter_list, track_list, output_list]

        with open(self.output_file) as f:
            lines = f.read()

            for r, l in zip(raw_strings, list_of_lists):
                pattern = re.compile(r)
                match = pattern.finditer(lines)
                for item in match:
                    l.append(item.group(1))
        return (font_list, task_list, chapter_list, track_list, output_list)

    def mux_warning(self):
        warning_list = []
        with open(self.output_file, "r") as f:
            for line in f:
                if re.search(r"[vV]alidating fonts for.*", line):
                    warning_list.append(line.strip())
                elif re.search(r"warning: .*", line):
                    warning = re.sub("^.*warning: (.*).*$", "\\1", line)
                    warning_list.append(warning.strip())

        if warning_list:
            click.secho(("WARNINGS:"), fg="green", bold=True, nl=False)
            for i in warning_list:
                if "Validating" in i or "validating" in i:
                    click.echo("")
                    click.secho(i, fg="blue", bold=True)
                elif "not found" in i:
                    click.secho((i), fg="red", bold=True)
                else:
                    click.echo(i)
            click.echo("")

    def mux_failure(self):
        failure_options = [
            r"(What went wrong.*)",
            r"(A problem occurred.*)",
            r"(Execution failed for task.*)",
            r"(Error resolving.*)",
            r"(not found in root project.*)",
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
        with open(self.output_file) as f:
            lines = f.read()

            for r in failure_options:
                pattern = re.compile(r)
                match = pattern.finditer(lines)
                for item in match:
                    click.echo(item.group(1))
                    click.echo("")


def selection(_list):
    """Takes in a list and allows the user to choose among the list using fzf"""
    for item in _list:
        yield item.strip()
        sleep(0.01)


def path_is_subkt(_path):
    """Takes path and checks if that path is a Subkt directory or not"""
    if os.path.exists(os.path.join(_path, "build.gradle.kts")) is False:
        click.secho(("\nThis folder does not appear to be a Subkt folder."), fg="red")
        return False
    else:
        return True


def exit_if_empty_variable(var_name, variable):
    """Takes a variable and exits if that variable is empty"""
    if not variable:
        exit_with_msg(f"{var_name} could not be determined. Exiting.")


def exit_with_msg(msg):
    """Takes a message, displays it and exits the program"""
    click.secho((msg), err=True, fg="red")
    exit()


def select_episode(episode, alt_folder):
    """Selects episode to mux. If alternate folder structure is chosen, arc as well as episodes is chosen."""
    chosen_episode = []
    episode_list = []
    arc = ""
    if alt_folder:
        arc = select_folder(".", "Select an arc: ", False)
    if episode:
        # If episode given by user is single digit, pad it with 0
        episode = episode if episode > 9 else f"{episode:02}"
        episode_list.append(str(episode))
        # chosen_episode.append(episode)
    else:
        episode_folder = os.path.join(os.path.abspath("."), arc)
        episode_list = select_folder(
            episode_folder, "Select single or multiple episode: ", True
        )
    if alt_folder:
        # Clean up arc name
        arc = arc[3:]
        arc = arc.replace(" ", "")
        arc = arc.lower()
        # Read exceptions from history for arcname
        CONF.read(CONFIG)
        try:
            arc = CONF["Exceptions"][arc]
        except KeyError:
            pass
        for i in episode_list:
            chosen_episode.append(arc + "_" + i)
    else:
        chosen_episode = episode_list

    return chosen_episode


def select_folder(path, _prompt, _multi):
    """Takes in a path and allows the user to choose folders in that path that starts with number.
    Therefore, both arcs and episodes sould start with a digit."""
    folder_list = os.listdir(path)
    _list = []
    for item in folder_list:
        if os.path.isdir(os.path.join(path, item)) and item[0].isdigit():
            _list.append(item)

    _list.sort()
    choice = iterfzf(selection(_list), prompt=_prompt, multi=_multi)
    return choice


def check_dependency():
    missing_dependency = []
    for item in DEPENDENCIES:
        if which(item) is None:
            missing_dependency.append(item)
    if missing_dependency:
        click.secho(("The following dependecies are missing:"), fg="red")
        for i in missing_dependency:
            click.echo(i)
        exit(1)


@click.group()
@click.version_option(version=VERSION)
def main():
    """Wrapper for Subkt written in Python."""
    pass


@main.command()
@click.option(
    "-p", "--path", type=click.Path(exists=True), help="Path to the project directory."
)
@click.option(
    "-a", "--alt_folder", is_flag=True, help="Altenate folder structure(./arc/episode)"
)
@click.option("-n", "--name", type=str, help="Name of the project saved in config.")
@click.option("-e", "--episode", type=int, help="Episode you want to mux.")
@click.option("-r", "--repeat", is_flag=True, help="Repeat last muxing action.")
@click.option(
    "-o",
    "--output",
    is_flag=True,
    help="See whole output of Subkt.",
)
def mux(path, episode, name, repeat, alt_folder, output):
    """Mux the episodes."""
    chosen_episodes = []
    check_dependency()

    if output:
        f = open(os.path.join(PYMUX_FOLDER, "output.txt"), "r")
        content = f.read()
        print(content)
        f.close()
        exit()

    if repeat:
        # Read the History section of config and get path and list of chosen_episodes that was muxed the last time.
        project, path, chosen_episodes = Config().config_history()
    elif path:
        if not path_is_subkt(path):
            exit()
        project = path
    elif name:
        project, path = Config().config_read(name)
    else:
        try:
            project, path = Config().config_read("")
        except AttributeError:
            exit_with_msg("You need to choose a project to continue.")
    exit_if_empty_variable("Project", project)
    exit_if_empty_variable("Path", path)

    # Change directory to the project path
    try:
        os.chdir(path)
    except FileNotFoundError as error:
        exit_with_msg(error)

    # Get a list of episodes to mux
    if not chosen_episodes:
        chosen_episodes = select_episode(episode, alt_folder)

    exit_if_empty_variable("Episodes", chosen_episodes)

    # Mux the chosen episodes
    Mux().mux_episodes(project, path, chosen_episodes)


@main.group()
def config():
    """Add, remove, edit projects in the config."""
    pass


@config.command()
def add():
    """Add projects to config."""
    Config().config_add()


@config.command()
def remove():
    """Remove projects from the config."""
    Config().config_remove()


@config.command()
def edit():
    """Manually edit the config."""
    Config().config_edit()
