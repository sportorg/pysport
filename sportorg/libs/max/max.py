import requests


class Max:
    URL = "https://platform-api.max.ru/"

    def __init__(self, access_token: str):
        self._access_token = access_token

    def _get_api_url(self, path: str = "") -> str:
        return "{}{}".format(self.URL, path)

    def send_message(self, chat_id: str, text: str, parse_mode: str = ""):
        json_data = {
            "text": text,
        }

        if parse_mode in ["Markdown", "HTML"]:
            json_data["format"] = parse_mode.lower()

        return requests.post(
            self._get_api_url("messages"),
            params={"chat_id": chat_id},
            json=json_data,
            headers={"Authorization": self._access_token},
        )
