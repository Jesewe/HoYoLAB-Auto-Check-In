# HoYoLAB Auto Check-In

A Python script to automate daily check-ins for HoYoLAB games, including Zenless Zone Zero (ZZZ), Genshin Impact (GI), Honkai: Star Rail (HSR), Honkai Impact 3rd (HI3), and Tears of Themis (ToT). The script uses a `config.json` file for configuration and supports Discord webhook notifications.

## Features

- Automates daily check-ins for multiple HoYoLAB accounts and games
- Configurable via a JSON file (`config.json`)
- Supports Discord webhook for status notifications
- Clean console output with clear success and error messages
- Error handling for invalid cookies, network issues, and configuration errors
- Automatically creates a default `config.json` if none exists

## Requirements

- Python 3.8+
- Required packages: `requests`
  ```bash
  pip install requests
  ```

## Installation

1. Clone or download this repository.
2. Install the required packages:
   ```bash
   pip install requests
   ```
3. Run the script to generate a default `config.json`:
   ```bash
   python main.py
   ```
4. Edit `config.json` with your account details (see Configuration section).

## Configuration

The script uses a `config.json` file in the same directory. A default file is created if none exists. The structure is as follows:

```json
{
  "accounts": [
    {
      "cookie": "ltuid_v2=your_ltuid; ltoken_v2=your_ltoken",
      "games": ["zzz", "gi", "hsr", "hi3", "tot"]
    },
    {
      "cookie": "ltuid_v2=another_ltuid; ltoken_v2=another_ltoken",
      "games": ["gi", "tot"]
    }
  ],
  "discord": {
    "webhook_url": "https://discord.com/api/webhooks/...",
    "user_id": "your_discord_user_id"
  }
}
```

- `accounts`: List of accounts, each with a `cookie` and a list of `games` to check in.
- `discord`: Optional Discord webhook URL and user ID for notifications.
- Valid games: `zzz`, `gi`, `hsr`, `hi3`, `tot`.

### Obtaining Your Cookie

To get your HoYoLAB cookie, you must first check in manually. Follow these steps:

1. Visit [HoYoLAB](https://www.hoyolab.com/home) and log in.
2. Open developer tools (press `Ctrl+Shift+I` or right-click and select "Inspect").
3. Navigate to the appropriate tab:
   - For Chromium-based browsers (e.g., Chrome, Edge), go to the **Application** tab. If not visible, click the double-arrow to expand.
   - For Firefox, go to the **Storage** tab.
4. In the filter box, type `v2` to locate relevant cookies.
5. Find `ltoken_v2` and `ltuid_v2`, click each, and copy their values.
6. Format the cookie as: `ltuid_v2=your_ltuid_v2; ltoken_v2=your_ltoken_v2`
   - Example: `ltuid_v2=249806310; ltoken_v2=v2_CAISDG...`
   - Use a semicolon (`;`) between values, not a colon.
7. Copy the formatted string. This is your cookie. Keep it secure and never share it!

## Usage

Run the script using:

```bash
python main.py
```

The script will:

1. Load or create `config.json`.
2. Process check-ins for each account and game.
3. Send Discord notifications if configured.
4. Display concise status messages (e.g., `[ZZZ] Check-in successful!` or `ERROR: [GI] Invalid cookie.`).
5. Exit with an error if any issues occur.

## Output Example

```
INFO: Processing account 1
INFO: [ZZZ] Check-in successful!
INFO: [GI] Already checked in today
ERROR: [HSR] Invalid cookie. Please update your cookie.
INFO: Discord webhook sent successfully!
```

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

Licensed under the MIT License. See the [LICENSE](LICENSE) file for details.