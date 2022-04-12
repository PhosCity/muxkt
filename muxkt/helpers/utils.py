import os
import click
from iterfzf import iterfzf
from time import sleep


def selection(_list):
    """Takes in a list and allows the user to choose among the list using fzf"""

    for item in _list:
        yield item.strip()
        sleep(0.01)


def fzf(iterable, _prompt):

    return iterfzf(selection(iterable), prompt=_prompt)


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


def select_episode(episode, project_name, alt_folder):
    """Selects episode to mux. If alternate folder structure is chosen, arc as well as episodes is chosen."""
    from configparser import ConfigParser

    CONF = ConfigParser()
    PYMUX_FOLDER = click.get_app_dir("muxkt")
    CONFIG = os.path.join(PYMUX_FOLDER, "config")
    # Read exceptions from history for arcname
    CONF.read(CONFIG)

    try:
        alt_folder = CONF["Alt-Folder"][project_name]
    except KeyError:
        pass

    if episode:
        if type(episode) is tuple:
            episode = [f"{item:02}" for item in episode]
        else:
            episode = [f"{episode:02}"]

    if episode and not alt_folder:
        chosen_episodes = episode
    elif not episode and not alt_folder:
        chosen_episodes = select_folder(
            ".", "Select single or multiple episode: ", True
        )
    else:
        arc = select_folder(".", "Select an arc: ", False)
        if not episode:
            # Select episodes
            episode_folder = os.path.join(os.path.abspath("."), arc)
            episode = select_folder(
                episode_folder, "Select single or multiple episode: ", True
            )
        # Clean up arc name
        arc = arc[3:]
        arc = arc.replace(" ", "")
        arc = arc.lower()
        try:
            arc = CONF["Exceptions"][arc]
        except KeyError:
            pass
        chosen_episodes = [arc + "_" + str(i) for i in episode]

    return chosen_episodes


def select_folder(path, _prompt, _multi):
    """Takes in a path and allows the user to choose folders in that path that starts with number.
    Therefore, both arcs and episodes sould start with a digit."""
    folder_list = os.listdir(path)
    _list = sorted(
        item
        for item in folder_list
        if os.path.isdir(os.path.join(path, item)) and item[0].isdigit()
    )
    choice = iterfzf(selection(_list), prompt=_prompt, multi=_multi)
    return choice


def check_dependency():
    from shutil import which

    DEPENDENCIES = ["java", "mkvmerge"]
    missing_dependency = [item for item in DEPENDENCIES if which(item) is None]
    if missing_dependency:
        click.secho(("The following dependecies are missing:"), fg="red")
        for i in missing_dependency:
            click.echo(i)
        exit(1)


def check_for_updates():
    import requests
    import re
    from muxkt.helpers import __version__

    current_version = __version__.VERSION

    git_version_url = "https://raw.githubusercontent.com/PhosCity/muxkt/main/muxkt/helpers/__version__.py"
    regex = re.compile(r"VERSION\s*=\s*[\"'](\d+\.\d+\.\d+)[\"']")
    r = requests.get(git_version_url)
    remote_version = re.match(regex, r.text).group(1)
    if remote_version > current_version:
        print(
            "New version (on GitHub) is available: {} -> {}\n".format(
                current_version, remote_version
            )
        )
        sleep(2)
