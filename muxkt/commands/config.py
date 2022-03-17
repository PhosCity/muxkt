import click
import os
from configparser import ConfigParser
from muxkt.helpers.utils import exit_with_msg, fzf, path_is_subkt


PYMUX_FOLDER = click.get_app_dir("muxkt")
CONFIG = os.path.join(PYMUX_FOLDER, "config")
CONF = ConfigParser()


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
            project = fzf(CONF["Project"], "Select a project to remove:")
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
            project = fzf(CONF["Project"], "Select a project:")

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


@click.group()
@click.help_option("--help", "-h")
def muxkt_config():
    """Add, remove, edit projects in the config."""
    pass


@muxkt_config.command()
def add():
    """Add projects to config."""
    Config().config_add()


@muxkt_config.command()
def remove():
    """Remove projects from the config."""
    Config().config_remove()


@muxkt_config.command()
def edit():
    """Manually edit the config."""
    Config().config_edit()
