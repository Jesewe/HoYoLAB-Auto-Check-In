import json
import requests
import urllib.parse
from typing import List, Dict, Any
from pathlib import Path

CONFIG_FILE = Path("config.json")
DEFAULT_CONFIG = {
    "accounts": [
        {
            "cookie": "",
            "games": []
        }
    ],
    "discord": {
        "webhook_url": "",
        "user_id": ""
    }
}

class CheckInClient:
    def __init__(self):
        self.config = self.load_config()
        self.endpoints = {
            'zzz': 'https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/sign?act_id=e202406031448091',
            'gi': 'https://sg-hk4e-api.hoyolab.com/event/sol/sign?act_id=e202102251931481',
            'hsr': 'https://sg-public-api.hoyolab.com/event/luna/os/sign?act_id=e202303301540311',
            'hi3': 'https://sg-public-api.hoyolab.com/event/mani/sign?act_id=e202110291205111',
            'tot': 'https://sg-public-api.hoyolab.com/event/luna/os/sign?act_id=e202202281857121'
        }
        self.messages: List[Dict[str, str]] = []
        self.has_errors = False

    def load_config(self) -> Dict[str, Any]:
        """Load or create config.json."""
        if not CONFIG_FILE.exists():
            with CONFIG_FILE.open('w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            print(f"Created default config file at {CONFIG_FILE}")
        try:
            with CONFIG_FILE.open('r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {CONFIG_FILE}. Using default config.")
            return DEFAULT_CONFIG

    def log(self, type: str, *data: Any) -> None:
        """Log messages with a clean format."""
        if type == 'error':
            self.has_errors = True
        message = ' '.join(str(item) for item in data)
        if data and data[0].lower() in self.endpoints:
            message = f"[{data[0].upper()}] {message}"
        self.messages.append({'type': type, 'message': message})
        if type != 'debug':
            print(f"{'ERROR' if type == 'error' else 'INFO'}: {message}")

    def check_in(self, cookie: str, games: List[str], account_index: int) -> None:
        """Perform check-in for specified games."""
        self.log('info', f"Processing account {account_index + 1}")
        
        for game in games:
            game = game.lower()
            if game not in self.endpoints:
                self.log('error', f"Invalid game: {game}. Valid options: {', '.join(self.endpoints.keys())}")
                continue

            endpoint = self.endpoints[game]
            parsed_url = urllib.parse.urlparse(endpoint)
            query_params = dict(urllib.parse.parse_qsl(parsed_url.query))
            act_id = query_params.get('act_id')

            params = {'lang': 'en-us', 'act_id': act_id}
            body = json.dumps({'lang': 'en-us', 'act_id': act_id})

            headers = {
                'accept': 'application/json, text/plain, */*',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': cookie,
                'x-rpc-signgame': game,
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }

            try:
                response = requests.post(endpoint, headers=headers, data=body, params=params)
                response.raise_for_status()
                json_data = response.json()
                code = str(json_data.get('retcode', ''))

                success_codes = {
                    '0': 'Check-in successful!',
                    '-5003': 'Already checked in today'
                }
                error_codes = {
                    '-100': 'Invalid cookie. Please update your cookie.',
                    '-10002': "Game not found. You haven't played this game."
                }

                if code in success_codes:
                    self.log('info', game, success_codes[code])
                elif code in error_codes:
                    self.log('error', game, error_codes[code])
                else:
                    self.log('error', game, f"Unknown error (code: {code}). Please report if this persists.")

            except requests.RequestException as e:
                self.log('error', game, f"Request failed: {str(e)}")

    def send_discord_webhook(self) -> None:
        """Send messages to Discord webhook."""
        discord_config = self.config.get('discord', {})
        webhook_url = discord_config.get('webhook_url', '')
        user_id = discord_config.get('user_id', '')

        if not webhook_url.startswith('https://discord.com/api/webhooks/'):
            self.log('error', 'Invalid Discord webhook URL.')
            return

        discord_msg = f"<@{user_id}>\n" if user_id else ""
        discord_msg += '\n'.join(f"[{msg['type'].upper()}] {msg['message']}" for msg in self.messages)

        try:
            response = requests.post(webhook_url, json={'content': discord_msg})
            response.raise_for_status()
            self.log('info', 'Discord webhook sent successfully!')
        except requests.RequestException:
            self.log('error', 'Failed to send Discord webhook. Check URL and permissions.')

    def run(self) -> None:
        """Main execution method."""
        accounts = self.config.get('accounts', [])
        if not accounts:
            raise ValueError("No accounts configured in config.json")

        for index, account in enumerate(accounts):
            cookie = account.get('cookie', '')
            games = account.get('games', [])
            if not cookie or not games:
                self.log('error', f"Account {index + 1}: Missing cookie or games in config.json")
                continue
            self.check_in(cookie, games, index)

        if self.config.get('discord', {}).get('webhook_url'):
            self.send_discord_webhook()

        if self.has_errors:
            raise RuntimeError("Errors occurred during execution. Check logs for details.")

if __name__ == '__main__':
    client = CheckInClient()
    client.run()