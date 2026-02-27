import os
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from app.utils.logging import get_json_logger


class BackgroundValidator:
    def __init__(self):
        self.api_endpoint = os.getenv("APP_API_ENDPOINT", "").rstrip("/")
        self.log = get_json_logger("app.services.BackgroundValidator")

        if not self.api_endpoint:
            raise ValueError("APP_API_ENDPOINT is not set")

    def run(self, poll_interval: int = 5) -> None:
        self.log.info(
            f"Polling database every {poll_interval} seconds"
            f"using api {self.api_endpoint}"
        )

        while True:
            modifications = self.get_pending_modifications()
            self.log.info(f"Fetched {len(modifications)} pending modifications")

            if len(modifications) > 0:
                for m in modifications:
                    id = int(m.get("id", ""))

                    response = self.validate_modification(id)
                    is_reversible = response.get("is_reversible")

                    self.log.info(f"Verified mod {id}, is_reversible: {is_reversible}")

            time.sleep(poll_interval)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=20),
        reraise=True,
    )
    def get_pending_modifications(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str = "pending",
    ) -> list[dict[str, int | str]]:
        """
        Fetches pending modifications from api.
        """
        url = f"{self.api_endpoint}/api/modifications"

        params: dict[str, int | str] = {
            "skip": skip,
            "limit": limit,
            "status": status,
        }

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        return response.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=20),
        reraise=True,
    )
    def validate_modification(
        self, modification_id: int, should_save_reversed_img: bool = False
    ) -> dict[str, str]:
        """
        Calls POST /api/modifications/{modification_id}/reverse/
        """
        url = f"{self.api_endpoint}/api/modifications/{modification_id}/reverse/"

        payload = {"should_save_reversed_img": should_save_reversed_img}

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            self.log.error(f"Failed to validate modification {modification_id}: {e}")
            raise RuntimeError(
                f"Failed to validate modification {modification_id}: {e}"
            ) from e

        return response.json()


if __name__ == "__main__":
    BackgroundValidator().run()
