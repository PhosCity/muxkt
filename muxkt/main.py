import click

from .commands import config, mux
from .helpers import __version__

commands = {
    "mux": mux.mux,
    "config": config.muxkt_config,
}


@click.group(commands=commands)
@click.version_option(__version__.VERSION, "-v", "--version")
@click.help_option("-h", "--help")
def cli():
    pass


if __name__ == "__main__":
    cli()
