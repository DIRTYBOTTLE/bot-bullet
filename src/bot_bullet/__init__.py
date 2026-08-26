from bot_bullet.graph import app


def main() -> None:
    for message in app.stream_events({}, version="v3").messages:
        for token in message.text:
            print(str(token), end="", flush=True)
