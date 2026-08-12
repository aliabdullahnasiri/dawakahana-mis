import click
from flask import Flask

from src.app import create_app


@click.group(help="Dawakahana MIS backend command-line interface.")
def main() -> None:
    """Manage and run the MyPorto backend."""
    pass


@main.command()
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host address to run the application on.",
)
@click.option(
    "--port",
    default=5000,
    type=int,
    show_default=True,
    help="Port to run the application on.",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable or disable Flask debug mode.",
)
def run(host: str, port: int, debug: bool) -> None:
    """Run the MyPorto development server."""
    app: Flask = create_app()

    click.echo(f"Starting MyPorto backend on http://{host}:{port}")

    app.run(
        host=host,
        port=port,
        debug=debug,
    )


if __name__ == "__main__":
    main()
