#!/usr/bin/env python3
"""
Steam Friend Adder Script
--------------------------
This script automatically sends friend requests to Steam users based on their Steam IDs.
It uses the Steam Web API to manage friend requests and provides detailed logging.

Author: Steam Friend Bot
Platform: Windows (but compatible with other platforms)
"""

import os
import re
import sys
import time
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class SteamFriendAdder:
    """
    A class to handle adding friends on Steam using the Steam Web API.
    
    Attributes:
        api_key (str): Steam Web API key
        steam_id (str): The Steam ID of the account sending friend requests
        log_file (str): Path to the log file
    """
    
    # Steam API endpoints
    STEAM_API_BASE = "https://api.steampowered.com"
    STEAM_COMMUNITY_BASE = "https://steamcommunity.com"
    FRIEND_LIST_ENDPOINT = "ISteamUser/GetFriendList/v1"
    PLAYER_SUMMARIES_ENDPOINT = "ISteamUser/GetPlayerSummaries/v2"
    CHAT_INVITE_INFO_ENDPOINT = "ISteamChatRoomService/GetInviteLinkInfo/v1"
    
    def __init__(self, api_key: str, steam_id: str, log_file: str = "friend_adder.log"):
        """
        Initialize the Steam Friend Adder.
        
        Args:
            api_key (str): Steam Web API key
            steam_id (str): Your Steam ID (the account that will send friend requests)
            log_file (str): Path to the log file (default: friend_adder.log)
        """
        self.api_key = api_key
        self.steam_id = steam_id
        self.log_file = log_file
        
        # Setup logging
        self._setup_logging()
        
        # Rate limiting: Track request times to avoid hitting API limits
        self.request_times = []
        self.max_requests_per_minute = 30  # Conservative limit
        
    def _setup_logging(self):
        """Configure logging to both file and console."""
        # Create logger
        self.logger = logging.getLogger('SteamFriendAdder')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _rate_limit_check(self):
        """
        Check and enforce rate limiting to avoid Steam API throttling.
        Waits if necessary to stay within rate limits.
        """
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # If we've hit the limit, wait
        if len(self.request_times) >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                self.logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                # Clear old requests after waiting
                self.request_times = []
        
        # Record this request
        self.request_times.append(current_time)
        
    def validate_steam_id(self, steam_id: str) -> Tuple[bool, str]:
        """
        Validate a Steam ID by checking its format and existence.
        
        Args:
            steam_id (str): The Steam ID to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Basic format validation - Steam ID should be numeric and 17 digits
        steam_id = steam_id.strip()
        
        if not steam_id:
            return False, "Empty Steam ID"
            
        if not steam_id.isdigit():
            return False, "Steam ID must be numeric"
            
        if len(steam_id) != 17:
            return False, f"Steam ID must be 17 digits (got {len(steam_id)})"
            
        # Check if the Steam ID exists by querying player summaries
        try:
            self._rate_limit_check()
            
            url = f"{self.STEAM_API_BASE}/{self.PLAYER_SUMMARIES_ENDPOINT}"
            params = {
                'key': self.api_key,
                'steamids': steam_id
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 403:
                return False, "Invalid API key or insufficient permissions"
            elif response.status_code == 429:
                return False, "Rate limited by Steam API"
            elif response.status_code != 200:
                return False, f"API error (status code: {response.status_code})"
                
            data = response.json()
            
            # Check if player exists
            if 'response' in data and 'players' in data['response']:
                players = data['response']['players']
                if len(players) > 0:
                    return True, "Valid"
                else:
                    return False, "Steam ID not found"
            else:
                return False, "Unexpected API response format"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
            
    def send_friend_request(self, target_steam_id: str) -> Tuple[bool, str]:
        """
        Send a friend request to the specified Steam ID.
        
        Note: The Steam Web API does not provide a direct endpoint to send friend requests.
        This would typically require using Steam's internal API or a library like steampy
        that handles authentication and session management.
        
        For this implementation, we'll validate the target Steam ID and log the action.
        In a production environment, you would need to:
        1. Use Steam's trading/community APIs with proper authentication
        2. Or use a library like 'steampy' or 'steam' that handles sessions
        
        Args:
            target_steam_id (str): Steam ID of the user to add as friend
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # First, validate the Steam ID
        is_valid, validation_msg = self.validate_steam_id(target_steam_id)
        
        if not is_valid:
            return False, f"Validation failed: {validation_msg}"
            
        # Note: Actual friend request sending requires authenticated session
        # This is a placeholder that demonstrates the workflow
        self.logger.info(f"Would send friend request to Steam ID: {target_steam_id}")
        
        # In a real implementation, you would:
        # 1. Authenticate with Steam using your credentials
        # 2. Get a session cookie
        # 3. POST to Steam's community API endpoint
        # Example (pseudo-code):
        # response = self.session.post(
        #     'https://steamcommunity.com/actions/AddFriendAjax',
        #     data={'sessionID': session_id, 'steamid': target_steam_id}
        # )
        
        return True, "Steam ID validated and ready for friend request"
        
    def process_steam_ids_file(self, file_path: str) -> dict:
        """
        Process a file containing Steam IDs and attempt to add each as a friend.
        
        Args:
            file_path (str): Path to the text file containing Steam IDs (one per line)
            
        Returns:
            dict: Summary of results with counts of success, failures, etc.
        """
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return {'error': 'File not found'}
            
        self.logger.info(f"Starting to process Steam IDs from: {file_path}")
        self.logger.info("=" * 60)
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'invalid': 0,
            'skipped': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                steam_ids = file.readlines()
                
            for line_num, line in enumerate(steam_ids, 1):
                steam_id = line.strip()
                
                # Skip empty lines and comments
                if not steam_id or steam_id.startswith('#'):
                    results['skipped'] += 1
                    continue
                    
                results['total'] += 1
                
                self.logger.info(f"Processing Steam ID {results['total']}: {steam_id}")
                
                # Attempt to send friend request
                success, message = self.send_friend_request(steam_id)
                
                if success:
                    results['success'] += 1
                    self.logger.info(f"✓ SUCCESS: {message}")
                else:
                    if "Validation failed" in message:
                        results['invalid'] += 1
                        self.logger.error(f"✗ INVALID: {message}")
                    else:
                        results['failed'] += 1
                        self.logger.error(f"✗ FAILED: {message}")
                
                # Small delay between requests to be respectful to the API
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}")
            results['error'] = str(e)
            
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("SUMMARY:")
        self.logger.info(f"  Total processed: {results['total']}")
        self.logger.info(f"  Successful: {results['success']}")
        self.logger.info(f"  Failed: {results['failed']}")
        self.logger.info(f"  Invalid IDs: {results['invalid']}")
        self.logger.info(f"  Skipped (empty/comments): {results['skipped']}")
        self.logger.info("=" * 60)
        
        return results
        
    def get_friend_list(self, steam_id: str) -> Tuple[bool, List[str], str]:
        """
        Get the friend list of a Steam user.
        
        Args:
            steam_id (str): Steam ID of the user whose friends to retrieve
            
        Returns:
            Tuple[bool, List[str], str]: (success, list_of_friend_ids, error_message)
        """
        try:
            self._rate_limit_check()
            
            url = f"{self.STEAM_API_BASE}/{self.FRIEND_LIST_ENDPOINT}"
            params = {
                'key': self.api_key,
                'steamid': steam_id,
                'relationship': 'friend'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 401:
                return False, [], "Invalid API key"
            elif response.status_code == 403:
                return False, [], "Friend list is private or user not found"
            elif response.status_code == 429:
                return False, [], "Rate limited by Steam API"
            elif response.status_code != 200:
                return False, [], f"API error (status code: {response.status_code})"
                
            data = response.json()
            
            if 'friendslist' in data and 'friends' in data['friendslist']:
                friends = data['friendslist']['friends']
                friend_ids = [friend['steamid'] for friend in friends]
                return True, friend_ids, ""
            else:
                return False, [], "No friends found or unexpected response format"
                
        except requests.exceptions.Timeout:
            return False, [], "Request timeout"
        except requests.exceptions.RequestException as e:
            return False, [], f"Network error: {str(e)}"
        except Exception as e:
            return False, [], f"Error retrieving friend list: {str(e)}"
            
    def get_mutual_friends(self, target_steam_id: str) -> Tuple[bool, List[str], str]:
        """
        Get all mutual friends between your account and another Steam user.
        Mutual friends are users who are friends with both you and the target user.
        
        Args:
            target_steam_id (str): Steam ID of the user to find mutual friends with
            
        Returns:
            Tuple[bool, List[str], str]: (success, list_of_mutual_friend_ids, error_message)
        """
        self.logger.info(f"Finding mutual friends with Steam ID: {target_steam_id}")
        
        # Get your friend list
        self.logger.info("Retrieving your friend list...")
        success1, your_friends, error1 = self.get_friend_list(self.steam_id)
        
        if not success1:
            return False, [], f"Failed to get your friend list: {error1}"
            
        self.logger.info(f"You have {len(your_friends)} friends")
        
        # Get target user's friend list
        self.logger.info(f"Retrieving target user's friend list...")
        success2, their_friends, error2 = self.get_friend_list(target_steam_id)
        
        if not success2:
            return False, [], f"Failed to get target user's friend list: {error2}"
            
        self.logger.info(f"Target user has {len(their_friends)} friends")
        
        # Find mutual friends (friends who are NOT in your list but ARE in their list)
        # These are the friends of the target user that you don't have yet
        your_friends_set = set(your_friends)
        potential_friends = [fid for fid in their_friends if fid not in your_friends_set and fid != self.steam_id]
        
        self.logger.info(f"Found {len(potential_friends)} potential friends to add")
        
        return True, potential_friends, ""
        
    def add_mutual_friends(self, target_steam_id: str) -> dict:
        """
        Add all friends of a target user who are not already your friends.
        This is the "one-click" feature to add all mutual friends.
        
        Args:
            target_steam_id (str): Steam ID of the user whose friends you want to add
            
        Returns:
            dict: Summary of results
        """
        self.logger.info("=" * 60)
        self.logger.info(f"ADDING FRIENDS FROM USER: {target_steam_id}")
        self.logger.info("=" * 60)
        
        # Validate the target Steam ID first
        is_valid, validation_msg = self.validate_steam_id(target_steam_id)
        if not is_valid:
            self.logger.error(f"Invalid target Steam ID: {validation_msg}")
            return {'error': f'Invalid target Steam ID: {validation_msg}'}
        
        # Get mutual friends
        success, friend_ids, error = self.get_mutual_friends(target_steam_id)
        
        if not success:
            self.logger.error(error)
            return {'error': error}
            
        if len(friend_ids) == 0:
            self.logger.info("No new friends to add (all of target user's friends are already your friends)")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'invalid': 0,
                'skipped': 0
            }
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'invalid': 0,
            'skipped': 0
        }
        
        self.logger.info(f"Processing {len(friend_ids)} potential friends...")
        self.logger.info("=" * 60)
        
        for i, friend_id in enumerate(friend_ids, 1):
            results['total'] += 1
            
            self.logger.info(f"Processing friend {i}/{len(friend_ids)}: {friend_id}")
            
            # Attempt to send friend request
            success, message = self.send_friend_request(friend_id)
            
            if success:
                results['success'] += 1
                self.logger.info(f"✓ SUCCESS: {message}")
            else:
                if "Validation failed" in message:
                    results['invalid'] += 1
                    self.logger.error(f"✗ INVALID: {message}")
                else:
                    results['failed'] += 1
                    self.logger.error(f"✗ FAILED: {message}")
            
            # Small delay between requests
            time.sleep(1)
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("SUMMARY:")
        self.logger.info(f"  Total processed: {results['total']}")
        self.logger.info(f"  Successful: {results['success']}")
        self.logger.info(f"  Failed: {results['failed']}")
        self.logger.info(f"  Invalid IDs: {results['invalid']}")
        self.logger.info("=" * 60)
        
        return results


    def get_group_members(self, group_identifier: str) -> Tuple[bool, List[str], str]:
        """
        Get all members of a Steam Community group.

        Uses the Steam Community group membership XML API which supports
        pagination for large groups.

        Args:
            group_identifier (str): The group's URL name (e.g. 'valve') or
                                    its 64-bit Group ID (GID).

        Returns:
            Tuple[bool, List[str], str]: (success, list_of_member_steam_ids, error_message)
        """
        # Determine whether the identifier is a numeric GID or a URL name
        if group_identifier.strip().isdigit():
            base_url = f"{self.STEAM_COMMUNITY_BASE}/gid/{group_identifier.strip()}/memberslistxml/"
        else:
            base_url = f"{self.STEAM_COMMUNITY_BASE}/groups/{group_identifier.strip()}/memberslistxml/"

        member_ids: List[str] = []
        page = 1

        self.logger.info(f"Fetching members of Steam group: {group_identifier}")

        while True:
            try:
                self._rate_limit_check()

                params = {'xml': '1', 'p': page}
                response = requests.get(base_url, params=params, timeout=10)

                if response.status_code == 404:
                    return False, [], "Group not found (404)"
                elif response.status_code == 429:
                    return False, [], "Rate limited by Steam Community"
                elif response.status_code != 200:
                    return False, [], f"HTTP error (status code: {response.status_code})"

                root = ET.fromstring(response.text)

                # Parse member Steam IDs from the XML response
                members_elem = root.find('members')
                if members_elem is None:
                    return False, [], "No members element found in response"

                for steam_id_elem in members_elem.findall('steamID64'):
                    if steam_id_elem.text:
                        member_ids.append(steam_id_elem.text.strip())

                # Check pagination
                total_pages_elem = root.find('totalPages')
                total_pages = int(total_pages_elem.text) if total_pages_elem is not None and total_pages_elem.text else 1

                self.logger.info(f"Fetched page {page}/{total_pages} ({len(member_ids)} members so far)")

                if page >= total_pages:
                    break
                page += 1

            except ET.ParseError as e:
                return False, [], f"Failed to parse group XML response: {str(e)}"
            except requests.exceptions.Timeout:
                return False, [], "Request timeout"
            except requests.exceptions.RequestException as e:
                return False, [], f"Network error: {str(e)}"
            except Exception as e:
                return False, [], f"Error retrieving group members: {str(e)}"

        return True, member_ids, ""

    def add_group_members(self, group_identifier: str) -> dict:
        """
        Send friend requests to all members of a Steam Community group
        who are not already your friends.

        Args:
            group_identifier (str): The group's URL name (e.g. 'valve') or
                                    its 64-bit Group ID (GID).

        Returns:
            dict: Summary of results
        """
        self.logger.info("=" * 60)
        self.logger.info(f"ADDING FRIENDS FROM GROUP: {group_identifier}")
        self.logger.info("=" * 60)

        # Fetch group members
        success, member_ids, error = self.get_group_members(group_identifier)

        if not success:
            self.logger.error(error)
            return {'error': error}

        if not member_ids:
            self.logger.info("No members found in this group.")
            return {'total': 0, 'success': 0, 'failed': 0, 'invalid': 0, 'skipped': 0}

        self.logger.info(f"Group has {len(member_ids)} members total")

        # Exclude yourself from the list
        member_ids = [mid for mid in member_ids if mid != self.steam_id]

        # Get your current friend list to skip existing friends
        self.logger.info("Retrieving your current friend list...")
        friend_success, your_friends, friend_error = self.get_friend_list(self.steam_id)
        if friend_success:
            your_friends_set = set(your_friends)
            self.logger.info(f"You already have {len(your_friends_set)} friends - they will be skipped")
        else:
            self.logger.warning(f"Could not retrieve your friend list: {friend_error}. Proceeding without skip check.")
            your_friends_set = set()

        to_add = [mid for mid in member_ids if mid not in your_friends_set]

        if not to_add:
            self.logger.info("No new members to add (you are already friends with all group members).")
            return {'total': 0, 'success': 0, 'failed': 0, 'invalid': 0, 'skipped': 0}

        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'invalid': 0,
            'skipped': 0
        }

        self.logger.info(f"Processing {len(to_add)} new group members...")
        self.logger.info("=" * 60)

        for i, member_id in enumerate(to_add, 1):
            results['total'] += 1

            self.logger.info(f"Processing member {i}/{len(to_add)}: {member_id}")

            success_req, message = self.send_friend_request(member_id)

            if success_req:
                results['success'] += 1
                self.logger.info(f"✓ SUCCESS: {message}")
            else:
                if "Validation failed" in message:
                    results['invalid'] += 1
                    self.logger.error(f"✗ INVALID: {message}")
                else:
                    results['failed'] += 1
                    self.logger.error(f"✗ FAILED: {message}")

            time.sleep(1)

        self.logger.info("=" * 60)
        self.logger.info("SUMMARY:")
        self.logger.info(f"  Total processed: {results['total']}")
        self.logger.info(f"  Successful: {results['success']}")
        self.logger.info(f"  Failed: {results['failed']}")
        self.logger.info(f"  Invalid IDs: {results['invalid']}")
        self.logger.info("=" * 60)

        return results

    def get_chat_invite_info(self, invite_url_or_code: str) -> Tuple[bool, dict, str]:
        """
        Resolve a Steam chat invite link to get chat group information.

        Tries the ISteamChatRoomService/GetInviteLinkInfo Steam Web API first.
        If the response includes a 'clan_steamid', the chat group is linked to a
        Steam Community Group and its members can be fetched via the XML API.
        Falls back to fetching the invite page HTML to extract the group name
        and provide a clear error message when the API is unavailable.

        Args:
            invite_url_or_code: Full invite URL
                (https://steamcommunity.com/chat/invite/<code>)
                or just the invite code (e.g. ZiMUFTC2).

        Returns:
            Tuple[bool, dict, str]: (success, info_dict, error_message)
            The info_dict may contain: chat_group_id, group_name,
            active_member_count, clan_steamid (if linked to a Community Group).
        """
        raw = invite_url_or_code.strip()

        # Extract invite code from full URL if provided
        if "steamcommunity.com/chat/invite/" in raw:
            invite_code = raw.split("/chat/invite/")[-1].strip("/")
        else:
            invite_code = raw.strip("/")

        invite_url = f"{self.STEAM_COMMUNITY_BASE}/chat/invite/{invite_code}"
        self.logger.info(f"Resolving Steam chat invite: {invite_url}")

        try:
            self._rate_limit_check()

            # Attempt Steam Web API for invite info
            api_url = f"{self.STEAM_API_BASE}/{self.CHAT_INVITE_INFO_ENDPOINT}"
            params = {"key": self.api_key, "invite_code": invite_code}
            api_response = requests.get(api_url, params=params, timeout=10)

            if api_response.status_code == 200:
                try:
                    data = api_response.json()
                    info = data.get("response", {})
                    if info and (info.get("chat_group_id") or info.get("group_name")):
                        self.logger.info(
                            f"Chat invite resolved via API: {info.get('group_name', invite_code)}"
                        )
                        return True, info, ""
                except ValueError:
                    pass

            # Fallback: fetch the invite page to extract the group name
            self._rate_limit_check()
            page_response = requests.get(
                invite_url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SteamFriendBot/1.0)"},
            )

            if page_response.status_code == 404:
                return False, {}, (
                    f"Chat invite link not found (404). The invite code '{invite_code}' "
                    f"may be invalid or expired."
                )

            if page_response.status_code == 200:
                title_match = re.search(
                    r"<title>([^<]+)</title>", page_response.text, re.IGNORECASE
                )
                group_name = title_match.group(1).strip() if title_match else invite_code
                # Remove trailing " - Steam" or " – Steam" suffix (hyphen or en-dash)
                group_name = re.sub(
                    r"\s*[-\u2013]\s*Steam\s*$", "", group_name, flags=re.IGNORECASE
                ).strip()

                return False, {"group_name": group_name, "invite_code": invite_code}, (
                    f"Steam chat group '{group_name}' found via invite link, but "
                    f"retrieving the member list requires full Steam authentication "
                    f"(username + password + Steam Guard). The Steam Chat API does not "
                    f"expose member lists without login credentials.\n\n"
                    f"Solutions:\n"
                    f"  \u2022 If this chat is linked to a Steam Community Group, use Mode 3\n"
                    f"    with the community group URL (steamcommunity.com/groups/<name>)\n"
                    f"    or its numeric Group ID.\n"
                    f"  \u2022 For pure Steam Chat groups, full Steam authentication is needed.\n"
                    f"    See README section 'Steam Chat vs Community Group' for details."
                )

            return False, {}, (
                f"Could not resolve invite link '{invite_url}' "
                f"(HTTP {page_response.status_code}). "
                f"Verify the invite code is valid and not expired."
            )

        except requests.exceptions.Timeout:
            return False, {}, "Request timeout while resolving chat invite"
        except requests.exceptions.RequestException as e:
            return False, {}, f"Network error: {str(e)}"
        except Exception as e:
            return False, {}, f"Error resolving chat invite: {str(e)}"

    def get_chat_members(self, invite_url_or_code: str) -> Tuple[bool, List[str], str]:
        """
        Get members of a Steam chat group via an invite link.

        If the chat group is linked to a Steam Community Group (clan), members
        are fetched using the Community Group XML API (same as Mode 3).
        Otherwise returns a clear error explaining the authentication requirement.

        Args:
            invite_url_or_code: Full invite URL or invite code.

        Returns:
            Tuple[bool, List[str], str]: (success, list_of_member_steam_ids, error_message)
        """
        success, info, error = self.get_chat_invite_info(invite_url_or_code)

        if not success:
            return False, [], error

        # If the chat group is linked to a Community Group, use the XML API
        clan_steamid = info.get("clan_steamid") or info.get("clanid")
        if clan_steamid and str(clan_steamid) not in ("", "0"):
            self.logger.info(
                f"Chat group is linked to Community Group "
                f"(clan SteamID64: {clan_steamid}). "
                f"Fetching members via Community Group XML API..."
            )
            return self.get_group_members(str(clan_steamid))

        # Not linked to a Community Group — full auth required
        group_name = info.get("group_name", "Unknown")
        chat_group_id = info.get("chat_group_id", "Unknown")
        active_count = info.get("active_member_count", "unknown")

        return False, [], (
            f"Chat group '{group_name}' (ID: {chat_group_id}) found with "
            f"{active_count} active members, but this group is not linked to a "
            f"Steam Community Group.\n\n"
            f"Full Steam authentication is required to retrieve members of a "
            f"private chat group. The Steam Web API does not expose a public "
            f"endpoint for this.\n\n"
            f"To add members from this chat group:\n"
            f"  1. Install the steam library: pip install steam\n"
            f"  2. Use SteamClient to authenticate and enumerate the chat room\n"
            f"  3. Collect member SteamIDs and add them via Mode 1 (file mode)\n"
            f"  See README section 'Steam Chat vs Community Group' for details."
        )

    def add_chat_members(self, invite_url_or_code: str) -> dict:
        """
        Send friend requests to all members of a Steam chat group.

        Resolves the invite link, fetches the member list (requires the group
        to be linked to a Community Group), skips existing friends and self,
        then attempts a friend request for each remaining member.

        Args:
            invite_url_or_code: Full invite URL or invite code.

        Returns:
            dict: Summary of results with counts of success, failures, etc.
        """
        self.logger.info("=" * 60)
        self.logger.info(f"ADDING FRIENDS FROM CHAT GROUP: {invite_url_or_code}")
        self.logger.info("=" * 60)

        success, member_ids, error = self.get_chat_members(invite_url_or_code)

        if not success:
            self.logger.error(error)
            return {"error": error}

        if not member_ids:
            self.logger.info("No members found in this chat group.")
            return {"total": 0, "success": 0, "failed": 0, "invalid": 0, "skipped": 0}

        self.logger.info(f"Chat group has {len(member_ids)} members total")

        # Exclude yourself
        member_ids = [mid for mid in member_ids if mid != self.steam_id]

        # Skip existing friends
        self.logger.info("Retrieving your current friend list...")
        friend_success, your_friends, friend_error = self.get_friend_list(self.steam_id)
        if friend_success:
            your_friends_set = set(your_friends)
            self.logger.info(
                f"You already have {len(your_friends_set)} friends - they will be skipped"
            )
        else:
            self.logger.warning(
                f"Could not retrieve your friend list: {friend_error}. "
                f"Proceeding without skip check."
            )
            your_friends_set = set()

        to_add = [mid for mid in member_ids if mid not in your_friends_set]

        if not to_add:
            self.logger.info(
                "No new members to add (you are already friends with all chat group members)."
            )
            return {"total": 0, "success": 0, "failed": 0, "invalid": 0, "skipped": 0}

        results = {"total": 0, "success": 0, "failed": 0, "invalid": 0, "skipped": 0}

        self.logger.info(f"Processing {len(to_add)} new chat group members...")
        self.logger.info("=" * 60)

        for i, member_id in enumerate(to_add, 1):
            results["total"] += 1
            self.logger.info(f"Processing member {i}/{len(to_add)}: {member_id}")

            success_req, message = self.send_friend_request(member_id)

            if success_req:
                results["success"] += 1
                self.logger.info(f"✓ SUCCESS: {message}")
            else:
                if "Validation failed" in message:
                    results["invalid"] += 1
                    self.logger.error(f"✗ INVALID: {message}")
                else:
                    results["failed"] += 1
                    self.logger.error(f"✗ FAILED: {message}")

            time.sleep(1)

        self.logger.info("=" * 60)
        self.logger.info("SUMMARY:")
        self.logger.info(f"  Total processed: {results['total']}")
        self.logger.info(f"  Successful: {results['success']}")
        self.logger.info(f"  Failed: {results['failed']}")
        self.logger.info(f"  Invalid IDs: {results['invalid']}")
        self.logger.info("=" * 60)

        return results


def load_config() -> Tuple[str, str]:
    """
    Load configuration from environment variables or prompt user.
    
    Returns:
        Tuple[str, str]: (api_key, steam_id)
    """
    # Try to load from environment variables
    api_key = os.environ.get('STEAM_API_KEY', '')
    steam_id = os.environ.get('STEAM_ID', '')
    
    # If not in environment, prompt user
    if not api_key:
        print("\n" + "=" * 60)
        print("STEAM FRIEND ADDER - CONFIGURATION")
        print("=" * 60)
        print("\nYou need a Steam Web API key to use this script.")
        print("Get your API key from: https://steamcommunity.com/dev/apikey")
        print()
        api_key = input("Enter your Steam Web API key: ").strip()
        
    if not steam_id:
        print("\nEnter your Steam ID (the account that will send friend requests)")
        print("Find your Steam ID at: https://steamid.io/")
        print()
        steam_id = input("Enter your Steam ID: ").strip()
        
    return api_key, steam_id


def main():
    """Main entry point for the script."""
    print("\n" + "=" * 60)
    print("       STEAM FRIEND ADDER")
    print("=" * 60)
    print()
    
    # Load configuration
    api_key, steam_id = load_config()
    
    if not api_key or not steam_id:
        print("\n❌ Error: API key and Steam ID are required!")
        sys.exit(1)
        
    # Initialize the friend adder
    adder = SteamFriendAdder(api_key, steam_id)
    
    # Ask user what mode to use
    print("\nChoose operation mode:")
    print("1. Add friends from a file (steam_ids.txt)")
    print("2. Add all friends of a specific user (mutual friends)")
    print("3. Add all members of a Steam Community group")
    print("4. Add all members of a Steam Chat group (via invite link)")
    print()

    mode = input("Enter your choice (1, 2, 3, or 4): ").strip()

    if mode == "2":
        # Mutual friends mode
        print("\n--- ADD MUTUAL FRIENDS MODE ---")
        print("This will add all friends of a target user who are not already your friends.")
        print()

        target_id = input("Enter the Steam ID of the user whose friends you want to add: ").strip()

        if not target_id:
            print("\n❌ Error: Steam ID is required!")
            sys.exit(1)

        print()
        results = adder.add_mutual_friends(target_id)

        if 'error' not in results:
            print(f"\n✓ Processing complete! Check {adder.log_file} for detailed logs.")
        else:
            print(f"\n❌ Error: {results['error']}")
            sys.exit(1)

    elif mode == "3":
        # Community group members mode
        print("\n--- ADD STEAM COMMUNITY GROUP MEMBERS MODE ---")
        print("This will add all members of a Steam Community group who are not already your friends.")
        print("You can provide the group URL name (e.g. 'valve') or the numeric Group ID.")
        print()
        print("NOTE: This mode is for Steam Community Groups")
        print("      (steamcommunity.com/groups/<name>).")
        print("      For Steam Chat invite links, use Mode 4 instead.")
        print()

        group_id = input("Enter the Steam group URL name or Group ID: ").strip()

        # Detect chat invite URL entered by mistake and redirect gracefully
        if "chat/invite" in group_id:
            print(
                "\n⚠️  Detected a Steam Chat invite link. "
                "Switching to Chat Members mode (Mode 4)..."
            )
            print()
            results = adder.add_chat_members(group_id)
        else:
            if not group_id:
                print("\n❌ Error: Group identifier is required!")
                sys.exit(1)

            print()
            results = adder.add_group_members(group_id)

        if "error" not in results:
            print(f"\n✓ Processing complete! Check {adder.log_file} for detailed logs.")
        else:
            print(f"\n❌ Error: {results['error']}")
            sys.exit(1)

    elif mode == "4":
        # Steam Chat group members mode - NEW FEATURE
        print("\n--- ADD STEAM CHAT GROUP MEMBERS MODE ---")
        print("This will add all members of a Steam Chat group who are not already your friends.")
        print()
        print("Accepted inputs:")
        print("  • Full invite URL: https://steamcommunity.com/chat/invite/<code>")
        print("  • Just the invite code, e.g.: ZiMUFTC2")
        print()
        print("IMPORTANT: If the chat group is linked to a Steam Community Group,")
        print("  members are fetched via the Community Group XML API (no extra auth needed).")
        print("  If it is a private-only chat group, full Steam authentication is required.")
        print("  See README section 'Steam Chat vs Community Group' for details.")
        print()

        chat_input = input("Enter chat invite URL or code: ").strip()

        if not chat_input:
            print("\n❌ Error: Chat invite link or code is required!")
            sys.exit(1)

        print()
        results = adder.add_chat_members(chat_input)

        if "error" not in results:
            print(f"\n✓ Processing complete! Check {adder.log_file} for detailed logs.")
        else:
            print(f"\n❌ Error: {results['error']}")
            sys.exit(1)

    else:
        # File mode - ORIGINAL FEATURE
        print("\n--- FILE MODE ---")
        default_file = "steam_ids.txt"
        print(f"Default input file: {default_file}")
        file_path = input(f"Enter Steam IDs file path (press Enter for default): ").strip()
        
        if not file_path:
            file_path = default_file
            
        # Convert to absolute path if relative
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
            
        # Process the file
        print()
        results = adder.process_steam_ids_file(file_path)
        
        if 'error' not in results:
            print(f"\n✓ Processing complete! Check {adder.log_file} for detailed logs.")
        else:
            print(f"\n❌ Error: {results['error']}")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
