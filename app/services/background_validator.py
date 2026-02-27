import time

from app.utils.logging import get_json_logger


def background_task(poll_interval: int = 5):
    log = get_json_logger("app.background_validator")

    log.info(f"Polling database every {poll_interval} seconds")
    while True:
        log.info("hi")
        time.sleep(poll_interval)


if __name__ == "__main__":
    background_task()
