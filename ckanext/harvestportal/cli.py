import click


@click.group(short_help="harvestportal CLI.")
def harvestportal():
    """harvestportal CLI.
    """
    pass


@harvestportal.command()
@click.argument("name", default="harvestportal")
def command(name):
    """Docs.
    """
    click.echo("Hello, {name}!".format(name=name))


def get_commands():
    return [harvestportal]
