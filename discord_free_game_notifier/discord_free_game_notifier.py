import typer
from dhooks import Webhook

from epic import get_free_epic_games
from settings import Settings

hook = Webhook(Settings.webhook_url)


def main():
    try:
        embed = get_free_epic_games()
        for game in embed:
            hook.send(embed=game)
    except Exception as e:
        hook.send(f"Error: {e}")
        typer.echo(e)


if __name__ == "__main__":
    typer.run(main)
