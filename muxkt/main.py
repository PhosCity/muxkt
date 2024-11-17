import os
import click
import configparser

from .config import config
from .mux import mux

from rich.traceback import install

install(show_locals=True, suppress=[click])


@click.group()
@click.version_option()
@click.help_option("--help", "-h")
@click.pass_context
def cli(ctx: click.Context) -> None:
    config_file_path = click.get_app_dir("muxkt")

    if not os.path.exists(config_file_path):
        os.makedirs(config_file_path)

    config_file = os.path.join(config_file_path, "config")
    output_file = os.path.join(config_file_path, "output.txt")

    config = configparser.ConfigParser()

    if not os.path.exists(config_file):
        with open(config_file, "w") as c:
            config.write(c)

    config.read(config_file)

    ctx.obj = {
        "config_file_path": config_file_path,
        "config_file": config_file,
        "config": config,
        "output_file": output_file,
    }


cli.add_command(config)
cli.add_command(mux)
