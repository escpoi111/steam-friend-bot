# Usage Examples

This document provides practical examples of using the Steam Friend Adder script.

## Example 1: Adding Friends from a File

### Step 1: Prepare your Steam IDs file

Create `steam_ids.txt`:
```
# Gaming friends
76561198012345678
76561198087654321

# Community members
76561198098765432
76561198011111111
```

### Step 2: Run the script

```bash
python steam_friend_adder.py
```

### Step 3: Follow prompts

```
============================================================
       STEAM FRIEND ADDER
============================================================

Choose operation mode:
1. Add friends from a file (steam_ids.txt)
2. Add all friends of a specific user (mutual friends)

Enter your choice (1 or 2): 1

--- FILE MODE ---
Default input file: steam_ids.txt
Enter Steam IDs file path (press Enter for default): [press Enter]
```

### Expected Output

```
2025-12-29 12:00:00 - INFO - Starting to process Steam IDs from: steam_ids.txt
2025-12-29 12:00:01 - INFO - Processing Steam ID 1: 76561198012345678
2025-12-29 12:00:02 - INFO - ✓ SUCCESS: Steam ID validated and ready for friend request
2025-12-29 12:00:03 - INFO - Processing Steam ID 2: 76561198087654321
2025-12-29 12:00:04 - INFO - ✓ SUCCESS: Steam ID validated and ready for friend request
...
2025-12-29 12:00:15 - INFO - SUMMARY:
2025-12-29 12:00:15 - INFO -   Total processed: 4
2025-12-29 12:00:15 - INFO -   Successful: 4
2025-12-29 12:00:15 - INFO -   Failed: 0
2025-12-29 12:00:15 - INFO -   Invalid IDs: 0
```

## Example 2: Adding All Friends of a User (Mutual Friends Mode)

This is the NEW feature that allows you to add all friends from a specific Steam user.

### Scenario

You meet a cool player and want to add all their friends to expand your network.

### Step 1: Get the user's Steam ID

Visit https://steamid.io/ and get their Steam ID (e.g., `76561198099999999`)

### Step 2: Run the script

```bash
python steam_friend_adder.py
```

### Step 3: Choose Mode 2

```
============================================================
       STEAM FRIEND ADDER
============================================================

Choose operation mode:
1. Add friends from a file (steam_ids.txt)
2. Add all friends of a specific user (mutual friends)

Enter your choice (1 or 2): 2

--- ADD MUTUAL FRIENDS MODE ---
This will add all friends of a target user who are not already your friends.

Enter the Steam ID of the user whose friends you want to add: 76561198099999999
```

### Expected Output

```
2025-12-29 12:00:00 - INFO - Finding mutual friends with Steam ID: 76561198099999999
2025-12-29 12:00:01 - INFO - Retrieving your friend list...
2025-12-29 12:00:02 - INFO - You have 50 friends
2025-12-29 12:00:03 - INFO - Retrieving target user's friend list...
2025-12-29 12:00:04 - INFO - Target user has 100 friends
2025-12-29 12:00:05 - INFO - Found 60 potential friends to add
2025-12-29 12:00:06 - INFO - Processing 60 potential friends...
2025-12-29 12:00:07 - INFO - Processing friend 1/60: 76561198011111111
2025-12-29 12:00:08 - INFO - ✓ SUCCESS: Steam ID validated and ready for friend request
...
2025-12-29 12:05:00 - INFO - SUMMARY:
2025-12-29 12:05:00 - INFO -   Total processed: 60
2025-12-29 12:05:00 - INFO -   Successful: 58
2025-12-29 12:05:00 - INFO -   Failed: 0
2025-12-29 12:05:00 - INFO -   Invalid IDs: 2
```

## Example 3: Using Environment Variables

### Create a .env file

Instead of entering credentials every time, create a `.env` file:

```bash
# Copy the example file
copy .env.example .env
```

Edit `.env`:
```
STEAM_API_KEY=ABC123XYZ789YOUR_REAL_API_KEY
STEAM_ID=76561198012345678
```

### Run the script

The script will automatically load your credentials:

```bash
python steam_friend_adder.py
```

No need to enter API key or Steam ID - it goes straight to mode selection!

## Example 4: Handling Errors

### Invalid Steam ID

```
2025-12-29 12:00:00 - INFO - Processing Steam ID 1: 123
2025-12-29 12:00:01 - ERROR - ✗ INVALID: Validation failed: Steam ID must be 17 digits (got 3)
```

### Private Friend List

```
2025-12-29 12:00:00 - INFO - Retrieving target user's friend list...
2025-12-29 12:00:01 - ERROR - Failed to get target user's friend list: Friend list is private or user not found
```

### Rate Limited

```
2025-12-29 12:00:00 - WARNING - Rate limit reached. Waiting 30.5 seconds...
```

## Tips for Best Results

### 1. Keep Your Friend List Public (for Mode 2)

If you want others to be able to use Mode 2 with your profile, make sure your friend list is public:
- Go to Steam Privacy Settings
- Set "Friend List" to "Public"

### 2. Use Comments in steam_ids.txt

Organize your Steam IDs with comments:

```
# Competitive teammates
76561198012345678
76561198087654321

# Casual gaming friends
76561198098765432

# Streamers and content creators
76561198011111111
```

### 3. Monitor the Log File

Check `friend_adder.log` for detailed information:

```bash
# On Windows
type friend_adder.log

# On Linux/Mac
cat friend_adder.log
```

### 4. Respect Rate Limits

The script has built-in rate limiting, but be patient:
- Don't try to add hundreds of friends at once
- If you get rate limited, wait before trying again
- Steam has daily limits on friend requests

## Troubleshooting Examples

### Problem: "File not found: steam_ids.txt"

**Solution**: Create the file in the same directory as the script:

```bash
# Copy the example
copy steam_ids.txt.example steam_ids.txt

# Edit and add your Steam IDs
notepad steam_ids.txt
```

### Problem: "Invalid API key"

**Solution**: Get a new API key:

1. Visit https://steamcommunity.com/dev/apikey
2. Register for a new key
3. Update your `.env` file or enter it when prompted

### Problem: Script runs but no friends are added

**Explanation**: The Steam Web API doesn't provide a direct endpoint for sending friend requests. This script:
- ✓ Validates Steam IDs
- ✓ Retrieves friend lists
- ✓ Identifies who to add
- ✗ Cannot actually send friend requests without additional authentication

**Next Steps**: 
- Use the validated list from the log file
- Manually visit each profile to send requests
- Or integrate with a library that handles Steam authentication (like `steampy`)

## Advanced Usage

### Running with Custom Log File

Edit the script or set a custom log file name in your code:

```python
adder = SteamFriendAdder(api_key, steam_id, log_file="custom_log.log")
```

### Automating with Task Scheduler (Windows)

Create a batch file `run_friend_adder.bat`:

```batch
@echo off
cd C:\path\to\steam-friend-bot
python steam_friend_adder.py
pause
```

Schedule it to run daily in Windows Task Scheduler.

### Using with Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run script
python steam_friend_adder.py
```

## Need Help?

- Check the main README.md for setup instructions
- Review the log file for detailed error messages
- Make sure your API key and Steam ID are correct
- Verify that friend lists are public when using Mode 2
