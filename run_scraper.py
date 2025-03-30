#!/usr/bin/env python3
"""
Quick start script for the Twitter scraper.
This allows users to run the scraper without modifying the main script.
"""

import argparse
import importlib.util
import os
import sys

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Twitter/X Scraper')
    parser.add_argument('username', type=str, help='Twitter username to scrape (without @)')
    parser.add_argument('--max-scrolls', type=int, default=500, help='Maximum number of scrolls (default: 500)')
    parser.add_argument('--pause-time', type=float, default=2.5, help='Pause time between scrolls in seconds (default: 2.5)')
    parser.add_argument('--login', action='store_true', help='Enable auto-login prompt')
    args = parser.parse_args()
    
    # Check if the main script exists
    if not os.path.exists('twitter_scraper.py'):
        print("Error: twitter_scraper.py not found in the current directory!")
        sys.exit(1)
    
    # Import the script as a module
    spec = importlib.util.spec_from_file_location("twitter_scraper", "twitter_scraper.py")
    scraper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scraper)
    
    # Set the configuration variables
    scraper.TWITTER_USERNAME = args.username
    scraper.TARGET_URL = f"https://x.com/{args.username}/with_replies"
    scraper.MAX_SCROLLS = args.max_scrolls
    scraper.SCROLL_PAUSE_TIME = args.pause_time
    
    # Handle login if requested
    if args.login:
        scraper.AUTO_LOGIN = True
        email = input("Enter your Twitter email/username: ")
        password = input("Enter your Twitter password: ")
        scraper.TWITTER_EMAIL = email
        scraper.TWITTER_PASSWORD = password
    
    # Run the scraper
    print(f"Starting to scrape tweets for @{args.username}")
    print(f"Max scrolls: {args.max_scrolls}, Pause time: {args.pause_time}s")
    scraper.main()

if __name__ == "__main__":
    main() 