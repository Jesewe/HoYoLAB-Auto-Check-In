import json
import requests
import urllib.parse
import argparse
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
            'zzz': {
                'sign': 'https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/sign?act_id=e202406031448091',
                'info': 'https://sg-act-nap-api.hoyolab.com/event/luna/zzz/os/info?act_id=e202406031448091'
            },
            'gi': {
                'sign': 'https://sg-hk4e-api.hoyolab.com/event/sol/sign?act_id=e202102251931481',
                'info': 'https://sg-hk4e-api.hoyolab.com/event/sol/info?act_id=e202102251931481'
            },
            'hsr': {
                'sign': 'https://sg-public-api.hoyolab.com/event/luna/os/sign?act_id=e202303301540311',
                'info': 'https://sg-public-api.hoyolab.com/event/luna/os/info?act_id=e202303301540311'
            },
            'hi3': {
                'sign': 'https://sg-public-api.hoyolab.com/event/mani/sign?act_id=e202110291205111',
                'info': 'https://sg-public-api.hoyolab.com/event/mani/info?act_id=e202110291205111'
            },
            'tot': {
                'sign': 'https://sg-public-api.hoyolab.com/event/luna/os/sign?act_id=e202202281857121',
                'info': 'https://sg-public-api.hoyolab.com/event/luna/os/info?act_id=e202202281857121'
            }
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

        game_prefix = ''
        message_parts = []
        if data and data[0].lower() in self.endpoints:
            game = data[0].upper()
            game_prefix = f"({game}) "
            message_parts = [str(item) for item in data[1:]]
        else:
            message_parts = [str(item) for item in data]
        
        message = ' '.join(message_parts)
        full_message = f"{game_prefix}{message}".strip()
        
        self.messages.append({'type': type, 'message': full_message})
        if type != 'debug':
            print(f"{'ERROR' if type == 'error' else 'INFO'}: {full_message}")

    def get_reward_info(self, cookie: str, game: str) -> None:
        """Fetch and display reward information for a game."""
        if game not in self.endpoints:
            self.log('error', f"Invalid game for reward info: {game}")
            return

        endpoint = self.endpoints[game]['info']
        parsed_url = urllib.parse.urlparse(endpoint)
        query_params = dict(urllib.parse.parse_qsl(parsed_url.query))
        act_id = query_params.get('act_id')

        params = {'lang': 'en-us', 'act_id': act_id}
        headers = {
            'accept': 'application/json, text/plain, */*',
            'cookie': cookie,
            'x-rpc-signgame': game,
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            json_data = response.json()
            
            self.log('debug', game, f"Reward info response: {json.dumps(json_data, indent=2)}")

            if json_data.get('retcode', '') == 0:
                data = json_data.get('data', {})
                if not data:
                    self.log('error', game, "No reward data found in response")
                    return
                    
                self.log('info', game, f"Check-in status: {'Signed in today' if data.get('is_sign', False) else 'Not signed in today'}")
                self.log('info', game, f"Total sign-in days: {data.get('total_sign_day', 0)}")
                self.log('info', game, f"Missed sign-in days: {data.get('sign_cnt_missed', 0)}")

                awards = data.get('awards', data.get('rewards', []))
                if not awards:
                    self.log('info', game, "No rewards available or awards/rewards key not found")
                    return

                self.log('info', game, "Available rewards:")
                for award in awards:
                    name = award.get('name', 'Unknown')
                    count = award.get('cnt', award.get('count', 0))
                    self.log('info', game, f"- {name}: {count}")
            else:
                self.log('error', game, f"Failed to fetch reward info: {json_data.get('message', 'Unknown error')}")
        except requests.RequestException as e:
            self.log('error', game, f"Reward info request failed: {str(e)}")

    def check_in(self, cookie: str, games: List[str], account_index: int) -> None:
        """Perform check-in for specified games."""
        self.log('info', f"Processing account {account_index + 1}")
        
        for game in games:
            game = game.lower()
            if game not in self.endpoints:
                self.log('error', f"Invalid game: {game}. Valid options: {', '.join(self.endpoints.keys())}")
                continue

            self.get_reward_info(cookie, game)

            endpoint = self.endpoints[game]['sign']
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

    def run(self, account_indices: List[int] = None, games: List[str] = None) -> None:
        """Main execution method with optional account and game filters."""
        accounts = self.config.get('accounts', [])
        if not accounts:
            raise ValueError("No accounts configured in config.json")

        account_indices = account_indices or list(range(len(accounts)))
        for index in account_indices:
            if index >= len(accounts):
                self.log('error', f"Invalid account index: {index + 1}")
                continue
            account = accounts[index]
            cookie = account.get('cookie', '')
            account_games = games or account.get('games', [])
            if not cookie or not account_games:
                self.log('error', f"Account {index + 1}: Missing cookie or games in config.json")
                continue
            self.check_in(cookie, account_games, index)

        if self.config.get('discord', {}).get('webhook_url'):
            self.send_discord_webhook()

        if self.has_errors:
            raise RuntimeError("Errors occurred during execution. Check logs for details.")

def main():
    parser = argparse.ArgumentParser(description="HoYoLAB Auto Check-In")
    parser.add_argument('--accounts', type=int, nargs='*', 
                        help='Account indices to process (0-based, e.g., 0 1 2)')
    parser.add_argument('--games', nargs='*', 
                        help='Games to check in (e.g., zzz gi hsr hi3 tot)')
    args = parser.parse_args()

    client = CheckInClient()
    client.run(args.accounts, args.games)

if __name__ == '__main__':
    main()