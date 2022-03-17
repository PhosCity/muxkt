import os
import re
import click
import subprocess

from muxkt.commands.config import Config
from muxkt.helpers.utils import (
    check_dependency,
    exit_if_empty_variable,
    exit_with_msg,
    path_is_subkt,
    select_episode,
)

PYMUX_FOLDER = click.get_app_dir("muxkt")


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


@click.command()
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
