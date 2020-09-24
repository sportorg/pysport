import requests


class Telegram:
    URL = 'https://api.telegram.org/'

    def __init__(self, bot_token):
        self._bot_token = bot_token

    def _get_api_url(self, path=''):
        return '{}bot{}/{}'.format(self.URL, self._bot_token, path)

    def send_message(self, chat_id, text, parse_mode=''):
        json_data = {
            'chat_id': chat_id,
            'text': text,
        }
        if parse_mode in ['Markdown', 'HTML']:
            json_data['parse_mode'] = parse_mode
        res = requests.post(self._get_api_url('sendMessage'), json=json_data)

        return res
