# Steam Friend Bot

This repository contains a Python script that automates the process of adding friends on Steam. The script is designed to run on Windows (and other platforms) and uses the Steam Web API to handle friend requests.

## Features

- ✅ **Add friends from a file**: Read Steam IDs from a text file and send friend requests
- ✅ **Add mutual friends**: One-click feature to add all friends of a specific user who are not already your friends
- ✅ **Steam Web API integration**: Uses official Steam API for validation and friend list retrieval
- ✅ **Comprehensive error handling**: Handles invalid IDs, rate limits, private profiles, and network errors
- ✅ **Detailed logging**: All operations are logged to both console and log file
- ✅ **Rate limiting**: Automatic rate limiting to avoid Steam API throttling

## Requirements

- Python 3.7 or higher
- Steam Web API key
- Your Steam ID

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/escpoi111/steam-friend-bot.git
   cd steam-friend-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your Steam Web API key**:
   - Visit: https://steamcommunity.com/dev/apikey
   - Sign in with your Steam account
   - Register for an API key (you can use any domain name)
   - Copy your API key

4. **Find your Steam ID**:
   - Visit: https://steamid.io/
   - Enter your Steam profile URL or username
   - Copy your Steam ID (the 17-digit number)

## Configuration

You have two options for configuration:

### Option 1: Environment Variables (Recommended)

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac, use `cp .env.example .env`)

2. Edit `.env` and fill in your details:
   ```
   STEAM_API_KEY=your_steam_api_key_here
   STEAM_ID=your_steam_id_here
   ```

### Option 2: Interactive Input

Simply run the script without setting environment variables, and it will prompt you for the required information.

## Usage

### Mode 1: Add Friends from File

1. **Create a Steam IDs file**:
   - Copy `steam_ids.txt.example` to `steam_ids.txt`
   - Add Steam IDs to the file (one per line)
   - Lines starting with `#` are treated as comments
   - Empty lines are ignored

   Example `steam_ids.txt`:
   ```
   # Friends to add
   76561198012345678
   76561198087654321
   76561198098765432
   ```

2. **Run the script**:
   ```bash
   python steam_friend_adder.py
   ```

3. **Choose mode 1** when prompted and follow the instructions.

### Mode 2: Add All Friends of a User (NEW!)

This feature allows you to add all friends of a specific Steam user with one command.

1. **Run the script**:
   ```bash
   python steam_friend_adder.py
   ```

2. **Choose mode 2** when prompted.

3. **Enter the Steam ID** of the user whose friends you want to add.

4. The script will:
   - Retrieve your friend list
   - Retrieve the target user's friend list
   - Find all friends that the target has but you don't
   - Attempt to add each of those friends
   - Log all results

**Use Cases for Mode 2:**
- Quickly expand your friend network
- Add friends from a community member
- Connect with people in your gaming group

## Output

The script creates a log file called `friend_adder.log` with detailed information about each operation:

```
2025-12-29 12:34:56 - INFO - Starting to process Steam IDs from: steam_ids.txt
2025-12-29 12:34:56 - INFO - Processing Steam ID 1: 76561198012345678
2025-12-29 12:34:57 - INFO - ✓ SUCCESS: Steam ID validated and ready for friend request
2025-12-29 12:34:58 - ERROR - ✗ INVALID: Validation failed: Steam ID not found
```

## Error Handling

The script handles various error conditions:

- **Invalid Steam IDs**: Non-numeric, wrong length, or non-existent IDs
- **Rate limiting**: Automatic delays to respect Steam API limits
- **Private profiles**: Detects when friend lists are private
- **Network errors**: Handles timeouts and connection issues
- **API errors**: Handles invalid API keys and permission issues

## Important Notes

### About Friend Requests

⚠️ **Important**: The Steam Web API does not provide a direct endpoint to send friend requests programmatically. This script:

1. **Validates** Steam IDs to ensure they exist
2. **Retrieves** friend lists to find mutual friends
3. **Logs** all operations for your reference

To actually send friend requests, you would need to:
- Manually visit each Steam profile after validation
- Use a third-party library with full Steam authentication (like `steampy`)
- Use Steam's community web interface with proper session management

This script provides the **foundation** for a friend management system and can be extended with proper authentication mechanisms.

### Privacy and Security

- ✅ Never share your API key
- ✅ The `.gitignore` file prevents committing sensitive files
- ✅ Use environment variables for credentials
- ✅ Respect Steam's rate limits and terms of service

## Troubleshooting

**Problem**: "Invalid API key or insufficient permissions"
- **Solution**: Verify your API key at https://steamcommunity.com/dev/apikey

**Problem**: "Friend list is private"
- **Solution**: The target user's friend list must be public for Mode 2 to work

**Problem**: "Rate limited by Steam API"
- **Solution**: Wait a few minutes and try again. The script has built-in rate limiting.

**Problem**: Script says Steam ID not found
- **Solution**: Verify the Steam ID is correct (17-digit number) using https://steamid.io/

## File Structure

```
steam-friend-bot/
├── steam_friend_adder.py      # Main script
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment configuration
├── .gitignore                 # Git ignore rules
├── steam_ids.txt.example      # Example Steam IDs file
├── README.md                  # This file
└── friend_adder.log          # Generated log file (gitignored)
```

## Contributing

Feel free to open issues or submit pull requests to improve this script!

## License

This project is provided as-is for educational purposes.

## Disclaimer

This script is for educational purposes. Always respect Steam's Terms of Service and API usage guidelines. Use responsibly and do not spam friend requests.