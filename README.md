# Steam Friend Bot

This repository contains a Python script that automates the process of adding friends on Steam. The script is designed to run on Windows (and other platforms) and uses the Steam Web API to handle friend requests.

## Features

- ✅ **Add friends from a file**: Read Steam IDs from a text file and send friend requests
- ✅ **Add mutual friends**: One-click feature to add all friends of a specific user who are not already your friends
- ✅ **Add Steam Community group members**: Add all members of a Steam Community group who are not already your friends
- ✅ **Add Steam Chat group members**: Add members from a Steam Chat group via its invite link (Mode 4)
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

   **For Mode 4 with private Chat Groups** (optional), also add:
   ```
   STEAM_USERNAME=your_steam_username_here
   STEAM_PASSWORD=your_steam_password_here
   ```
   These credentials are used only when fetching members of private Steam Chat
   groups.  They are never logged or written to disk.  If your account uses
   Steam Guard (email or mobile authenticator), you will be prompted to enter
   the code at runtime.

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

### Mode 2: Add All Friends of a User

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

### Mode 3: Add All Members of a Steam Community Group

This feature lets you add all members of a Steam **Community Group** as friends.
Steam Community Groups are public groups with URLs like
`https://steamcommunity.com/groups/<name>` and expose a public XML member list.

> **Note**: If you have a Steam **Chat** invite link
> (`steamcommunity.com/chat/invite/<code>`), use **Mode 4** instead.
> Entering a chat invite link in Mode 3 will be detected automatically and
> re-routed to the chat handler, but using Mode 4 directly is clearer.

1. **Run the script**:
   ```bash
   python steam_friend_adder.py
   ```

2. **Choose mode 3** when prompted.

3. **Enter the group identifier** – either the group's URL name (e.g. `valve` from
   `https://steamcommunity.com/groups/valve`) or its numeric Group ID.

4. The script will:
   - Fetch all group members (handles pagination for large groups)
   - Retrieve your current friend list
   - Skip members who are already your friends or are yourself
   - Attempt to add each remaining member
   - Log all results

**Use Cases for Mode 3:**
- Join a gaming community and instantly connect with all members
- Add everyone in your clan or team
- Expand your network through Steam Community group membership

### Mode 4: Add All Members of a Steam Chat Group (NEW!)

This feature lets you add friends from a Steam **Chat group** using its invite link.
Steam Chat groups use invite links like
`https://steamcommunity.com/chat/invite/<code>` and do **not** expose a public
XML member list.

1. **Run the script**:
   ```bash
   python steam_friend_adder.py
   ```

2. **Choose mode 4** when prompted.

3. **Enter the invite link or code**:
   - Full URL: `https://steamcommunity.com/chat/invite/ZiMUFTC2`
   - Or just the code: `ZiMUFTC2`

4. The script will:
   - Resolve the invite link via the Steam Web API
   - If the chat group is **linked to a Community Group** (clan), fetch members
     via the Community Group XML API — no extra authentication required
   - If the chat group is **private-only** (not linked to a Community Group),
     and `STEAM_USERNAME`/`STEAM_PASSWORD` are configured in `.env`, perform
     automatic Steam web login and fetch members via the authenticated API
     (Steam Guard code is prompted interactively when required)
   - If credentials are not configured, explain next steps
   - Skip members already on your friend list and attempt to add the rest

**Use Cases for Mode 4:**
- Add members from a gaming squad's chat room
- Batch-add people from a private invite-only Steam group chat

**Authentication note for private chat groups:**

Steam does not expose the member list of private chat groups through the public
Web API.  Mode 4 supports **fully managed authentication** ("全托管") for
private groups:

- **Fully managed (recommended)** – Set `STEAM_USERNAME` and `STEAM_PASSWORD`
  in your `.env` file.  The script will authenticate automatically and fetch
  the member list.  If your account uses Steam Guard, the code will be prompted
  at runtime (it is never logged or stored).
  ```
  STEAM_USERNAME=your_username
  STEAM_PASSWORD=your_password
  ```

- **Manual fallback A** – If the group admin can share the Community Group URL
  (`/groups/<name>`), use Mode 3 instead.
- **Manual fallback B** – Use the [`steam` Python library](https://github.com/ValvePython/steam)
  to authenticate with your Steam credentials, join the chat, and retrieve member
  SteamIDs manually. Then save those IDs to `steam_ids.txt` and use Mode 1.
  ```bash
  pip install steam
  ```
  See the library's documentation for SteamClient authentication and chat room
  enumeration.

---

## Steam Chat vs Community Group

| Feature | Community Group | Steam Chat Group |
|---------|----------------|-----------------|
| URL format | `steamcommunity.com/groups/<name>` | `steamcommunity.com/chat/invite/<code>` |
| Public member list | ✅ Yes (XML API) | ❌ No |
| Mode to use | Mode 3 | Mode 4 |
| Requires Steam auth | No (API key only) | Only for private-only chats (set `STEAM_USERNAME`/`STEAM_PASSWORD`) |

---

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

**Problem**: "Failed to parse group XML response" when entering a chat invite link
- **Solution**: You entered a Steam **Chat** invite link (`/chat/invite/...`) in Mode 3,
  which expects a **Community Group** URL or name. Use **Mode 4** instead, or provide the
  Community Group URL (e.g. `valve` or `https://steamcommunity.com/groups/valve`).

**Problem**: Mode 4 says "full Steam authentication is required"
- **Solution**: Set `STEAM_USERNAME` and `STEAM_PASSWORD` in your `.env` file.
  The script will authenticate automatically and prompt for a Steam Guard code
  when required. See the *Authentication note for private chat groups* section above.

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