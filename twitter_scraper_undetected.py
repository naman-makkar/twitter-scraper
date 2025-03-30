#!/usr/bin/env python3
"""
Twitter Scraper with Undetected ChromeDriver
This version is specifically optimized for Windows and avoiding Twitter's detection mechanisms.
"""

import time
import csv
import re
import os
import random
import sys
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configuration
TWITTER_USERNAME = "example_user"  # Default placeholder - will be overridden by command line args
TARGET_URL = f"https://x.com/{TWITTER_USERNAME}/with_replies"
SCROLL_PAUSE_TIME = 2.5  # Increased for reliability
SCROLL_VARIATION = 1.0  # Random variation in scroll time to appear more human-like
MAX_SCROLLS = 500  # Default value, can be overridden by command-line args
OUTPUT_FILE = f"{TWITTER_USERNAME}_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
AUTO_LOGIN = False  # Set to True if you want to use automatic login

# Twitter login credentials - only needed if AUTO_LOGIN is True
TWITTER_EMAIL = None
TWITTER_PASSWORD = None

def setup_driver():
    """Setup and return an Undetected ChromeDriver instance."""
    print("Initializing undetected ChromeDriver...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        print("Successfully initialized ChromeDriver")
        return driver
    except Exception as e:
        print(f"Failed to initialize undetected ChromeDriver: {e}")
        print("Make sure Chrome browser is properly installed and up to date")
        sys.exit(1)

def login_to_twitter(driver):
    """Attempt to log in to Twitter account."""
    if not AUTO_LOGIN or not TWITTER_EMAIL or not TWITTER_PASSWORD:
        print("Automatic login is disabled. Please log in manually if prompted.")
        print("The script will wait 45 seconds for you to login...")
        time.sleep(45)  # Wait for manual login
        return
    
    try:
        print("Attempting to log in to Twitter...")
        driver.get("https://twitter.com/login")
        
        # Wait for the login form to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        
        # Enter email/username
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys(TWITTER_EMAIL)
        username_field.send_keys(Keys.RETURN)
        
        # Wait for password field
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        
        # Enter password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        time.sleep(5)
        print("Login completed")
    except Exception as e:
        print(f"Error during login: {e}")
        print("Please log in manually in the browser window.")
        time.sleep(30)  # Give time for manual login

def clean_tweet_text(text):
    """Clean the tweet text by removing extra spaces and newlines."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def check_for_login_wall(driver):
    """Check if we've hit a login wall and need to log in."""
    try:
        login_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Log in')]")
        signup_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Sign up')]")
        
        if login_elements or signup_elements:
            print("Detected a login wall. Attempting to bypass...")
            login_to_twitter(driver)
            return True
    except Exception as e:
        print(f"Error checking for login wall: {e}")
    
    return False

def random_scroll(driver):
    """Perform a random scroll to appear more human-like."""
    scroll_height = random.randint(300, 1000)
    driver.execute_script(f"window.scrollBy(0, {scroll_height});")

def extract_tweet_data(article, username):
    """Extract data from a tweet article element."""
    try:
        # Extract timestamp
        time_element = article.find('time')
        timestamp = time_element['datetime'] if time_element else "Unknown"
        
        # Extract tweet URL/ID
        tweet_id = "Unknown"
        tweet_link = None
        
        # Try multiple approaches to get the tweet ID
        if time_element and time_element.parent:
            link_element = time_element.parent
            # Try to navigate up to find the link
            for _ in range(3):  # Try up to 3 levels up
                if link_element.name == 'a' and link_element.has_attr('href'):
                    tweet_link = link_element['href']
                    break
                if link_element.parent:
                    link_element = link_element.parent
                else:
                    break
                    
        # Try another approach - look for any link with status in the URL
        if not tweet_link:
            status_links = article.select('a[href*="status"]')
            if status_links:
                tweet_link = status_links[0]['href']
        
        # Extract tweet ID from the link
        if tweet_link:
            # Look for /status/123456789 pattern
            match = re.search(r'/status/(\d+)', tweet_link)
            if match:
                tweet_id = match.group(1)
        
        # Extract tweet text - try multiple selectors
        tweet_text = "No text found"
        
        # First try the standard data-testid attribute
        tweet_text_div = article.find('div', {'data-testid': 'tweetText'})
        if tweet_text_div:
            tweet_text = clean_tweet_text(tweet_text_div.get_text())
        else:
            # Try alternative approaches
            # Look for the main text element
            lang_spans = article.select('[lang]')
            if lang_spans:
                tweet_text = clean_tweet_text(lang_spans[0].get_text())
            else:
                # Try to get all text from the article
                all_text = article.get_text()
                if all_text:
                    tweet_text = clean_tweet_text(all_text)
        
        # Extract likes, retweets, replies
        stats = {'replies': 0, 'retweets': 0, 'likes': 0}
        
        # Try multiple approaches for stats
        stats_divs = article.find_all('div', {'role': 'group'})
        if stats_divs:
            stats_elements = stats_divs[0].find_all('div')
            for i, stat_type in enumerate(['replies', 'retweets', 'likes']):
                if i < len(stats_elements):
                    stat_text = stats_elements[i].get_text()
                    stat_value = re.search(r'\d+', stat_text)
                    stats[stat_type] = int(stat_value.group()) if stat_value else 0
        
        # Alternative approach - look for the specific aria-labels
        aria_labels = {
            'aria-label*="replies"': 'replies',
            'aria-label*="Retweet"': 'retweets',
            'aria-label*="Like"': 'likes'
        }
        
        for selector, stat_type in aria_labels.items():
            elements = article.select(f'[{selector}]')
            if elements:
                for el in elements:
                    label = el.get('aria-label', '')
                    match = re.search(r'\d+', label)
                    if match:
                        stats[stat_type] = int(match.group())
                        break
        
        # Add tweet to our list
        tweet_data = {
            'tweet_id': tweet_id,
            'timestamp': timestamp,
            'text': tweet_text,
            'replies': stats.get('replies', 0),
            'retweets': stats.get('retweets', 0),
            'likes': stats.get('likes', 0),
            'url': f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id != "Unknown" else "Unknown"
        }
        
        return tweet_data
    except Exception as e:
        print(f"Error extracting tweet data: {e}")
        return None

def extract_tweets_using_js(driver, username):
    """Use JavaScript to extract tweets directly from the page DOM."""
    print("Using JavaScript method to extract tweets...")
    
    js_script = """
    function extractTweets() {
        // Find all tweet articles
        const articles = document.querySelectorAll('article[data-testid="tweet"]');
        const tweets = [];
        
        articles.forEach((article) => {
            try {
                // Extract timestamp
                const timeElement = article.querySelector('time');
                const timestamp = timeElement ? timeElement.getAttribute('datetime') : 'Unknown';
                
                // Extract tweet ID
                let tweetId = 'Unknown';
                const statusLinks = article.querySelectorAll('a[href*="/status/"]');
                if (statusLinks.length > 0) {
                    const href = statusLinks[0].getAttribute('href');
                    const match = href.match(/\\/status\\/(\\d+)/);
                    if (match) {
                        tweetId = match[1];
                    }
                }
                
                // Extract tweet text
                let tweetText = 'No text found';
                const tweetTextDiv = article.querySelector('div[data-testid="tweetText"]');
                if (tweetTextDiv) {
                    tweetText = tweetTextDiv.innerText;
                } else {
                    // Try alternative method
                    const langSpans = article.querySelectorAll('[lang]');
                    if (langSpans.length > 0) {
                        tweetText = langSpans[0].innerText;
                    } else {
                        tweetText = article.innerText.substring(0, 280); // Limit length
                    }
                }
                
                // Extract engagement stats
                const statsGroup = article.querySelector('div[role="group"]');
                let replies = 0, retweets = 0, likes = 0;
                
                if (statsGroup) {
                    const statDivs = statsGroup.querySelectorAll('div');
                    // Usually in order: replies, retweets, likes
                    if (statDivs.length >= 3) {
                        for (let i = 0; i < 3; i++) {
                            const statText = statDivs[i].innerText;
                            const statValue = parseInt(statText.replace(/[^0-9]/g, '')) || 0;
                            
                            if (i === 0) replies = statValue;
                            if (i === 1) retweets = statValue;
                            if (i === 2) likes = statValue;
                        }
                    }
                }
                
                tweets.push({
                    tweet_id: tweetId,
                    timestamp: timestamp,
                    text: tweetText,
                    replies: replies,
                    retweets: retweets,
                    likes: likes,
                    url: `https://twitter.com/user/status/${tweetId}`
                });
            } catch (e) {
                console.error('Error extracting tweet:', e);
            }
        });
        
        return tweets;
    }
    
    return extractTweets();
    """
    
    try:
        tweets_data = driver.execute_script(js_script)
        print(f"JavaScript extracted {len(tweets_data)} tweets")
        
        # Fix the URLs with correct username
        for tweet in tweets_data:
            if tweet['tweet_id'] != "Unknown":
                tweet['url'] = f"https://twitter.com/{username}/status/{tweet['tweet_id']}"
        
        return tweets_data
    except Exception as e:
        print(f"JavaScript extraction failed: {e}")
        return []

def scrape_tweets(driver, username):
    """Scrape tweets by scrolling through the timeline."""
    tweets = []
    unique_tweet_ids = set()  # To check for duplicates based on ID
    unique_tweet_texts = set()  # Fallback for duplicate detection
    scroll_count = 0
    consecutive_no_new_tweets = 0
    
    print(f"Starting to scrape tweets from {TARGET_URL}")
    driver.get(TARGET_URL)
    
    # Check for login wall before proceeding
    if check_for_login_wall(driver):
        driver.get(TARGET_URL)  # Reload the target page after login
    
    # Wait for the timeline to load
    try:
        WebDriverWait(driver, 15).until(  # Increased timeout for slower connections
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
        )
    except TimeoutException:
        print("Timeout while waiting for the timeline to load.")
        print("Checking if we need to log in...")
        if check_for_login_wall(driver):
            driver.get(TARGET_URL)
            time.sleep(5)
        else:
            print("Still can't find any tweets. Twitter might be blocking the scraper.")
            return tweets
    
    time.sleep(5)  # Allow more time for the page to fully load
    
    print("Starting to scroll and scrape tweets...")
    
    # Try JavaScript extraction first to see if it works
    js_tweets = extract_tweets_using_js(driver, username)
    if js_tweets:
        for tweet_data in js_tweets:
            if tweet_data['tweet_id'] not in unique_tweet_ids and tweet_data['text'] not in unique_tweet_texts:
                tweets.append(tweet_data)
                unique_tweet_ids.add(tweet_data['tweet_id'])
                unique_tweet_texts.add(tweet_data['text'])
                print(f"JS method scraped tweet: {tweet_data['text'][:50]}...")
    
    # Scroll and scrape
    while scroll_count < MAX_SCROLLS:
        # Every 10 scrolls, perform some random actions to appear more human-like
        if scroll_count % 10 == 0:
            random_scroll(driver)
            time.sleep(random.uniform(1.0, 3.0))
        
        # Try JavaScript method every 5 scrolls as it might be more reliable
        if scroll_count % 5 == 0:
            js_tweets = extract_tweets_using_js(driver, username)
            if js_tweets:
                prev_count = len(tweets)
                for tweet_data in js_tweets:
                    if tweet_data['tweet_id'] not in unique_tweet_ids and tweet_data['text'] not in unique_tweet_texts:
                        tweets.append(tweet_data)
                        unique_tweet_ids.add(tweet_data['tweet_id'])
                        unique_tweet_texts.add(tweet_data['text'])
                
                new_tweets = len(tweets) - prev_count
                if new_tweets > 0:
                    print(f"JS method found {new_tweets} new tweets")
                    consecutive_no_new_tweets = 0
        
        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all tweet articles - use a more specific selector that targets tweets
        tweet_articles = soup.find_all('article')
        prev_count = len(tweets)
        
        print(f"Found {len(tweet_articles)} tweet articles on the current page")
        
        for article in tweet_articles:
            tweet_data = extract_tweet_data(article, username)
            
            if not tweet_data:
                continue
                
            # Skip if we've already seen this tweet (by ID or by text)
            if tweet_data['tweet_id'] in unique_tweet_ids or tweet_data['text'] in unique_tweet_texts:
                continue
            
            tweets.append(tweet_data)
            unique_tweet_ids.add(tweet_data['tweet_id'])
            unique_tweet_texts.add(tweet_data['text'])
            
            print(f"Scraped tweet: {tweet_data['text'][:50]}...")
            
            # Save progress incrementally every 50 tweets
            if len(tweets) % 50 == 0:
                save_tweets_to_csv(tweets, OUTPUT_FILE)
                print(f"Saved progress: {len(tweets)} tweets so far.")
        
        # Scroll down using a more reliable method
        # Execute multiple smaller scrolls instead of one big scroll
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down to a random position between 70-90% of the page height
        scroll_position = int(last_height * random.uniform(0.7, 0.9))
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        
        # Add a small pause
        time.sleep(1)
        
        # Then scroll all the way down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait for new content to load
        scroll_time = SCROLL_PAUSE_TIME + random.uniform(-SCROLL_VARIATION, SCROLL_VARIATION)
        time.sleep(max(1.0, scroll_time))  # Ensure minimum pause time is longer
        
        # Check if scroll was successful
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        scroll_count += 1
        print(f"Scrolled {scroll_count} times. Found {len(tweets)} tweets so far.")
        
        # Check if we actually scrolled (page height changed)
        if new_height == last_height:
            print("Scroll didn't increase page height. Maybe we reached the end.")
            consecutive_no_new_tweets += 1
        else:
            print(f"Scroll changed page height from {last_height} to {new_height}")
        
        # Check if we found any new tweets in this scroll
        if prev_count == len(tweets):
            consecutive_no_new_tweets += 1
            print(f"No new tweets found in this scroll. ({consecutive_no_new_tweets}/5)")
            
            # Try a different scroll method if we're not finding tweets
            if consecutive_no_new_tweets == 3:
                print("Trying different scroll method...")
                # Execute scroll with JS to ensure it works
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)
            
            # If we haven't found new tweets for 5 consecutive scrolls, we might have reached the end
            if consecutive_no_new_tweets >= 5:
                print("Reached 5 consecutive scrolls with no new tweets. We might have reached the end.")
                
                # One final attempt to find more tweets - reload the page and try a few more times
                if len(tweets) < 10:  # If we haven't found many tweets, try reloading
                    print("Found very few tweets. Trying to reload the page...")
                    driver.get(TARGET_URL)
                    time.sleep(5)
                    consecutive_no_new_tweets = 0
                else:
                    break
        else:
            consecutive_no_new_tweets = 0  # Reset the counter
            
            # If we found a lot of new tweets at once, save progress immediately
            if len(tweets) - prev_count > 10:
                save_tweets_to_csv(tweets, OUTPUT_FILE)
                print(f"Found {len(tweets) - prev_count} new tweets! Saved progress.")
    
    return tweets

def save_tweets_to_csv(tweets, filename):
    """Save the scraped tweets to a CSV file."""
    fields = ['tweet_id', 'timestamp', 'text', 'replies', 'retweets', 'likes', 'url']
    
    # Check if we should append or write a new file
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        
        if not file_exists:
            writer.writeheader()
        
        for tweet in tweets:
            writer.writerow(tweet)
    
    print(f"Saved {len(tweets)} tweets to {filename}")

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Twitter/X Scraper with undetected ChromeDriver')
    parser.add_argument('username', type=str, nargs='?', default=TWITTER_USERNAME, 
                        help='Twitter username to scrape (without @)')
    parser.add_argument('--max-scrolls', type=int, default=MAX_SCROLLS, 
                        help=f'Maximum number of scrolls (default: {MAX_SCROLLS})')
    parser.add_argument('--pause-time', type=float, default=SCROLL_PAUSE_TIME, 
                        help=f'Pause time between scrolls in seconds (default: {SCROLL_PAUSE_TIME})')
    parser.add_argument('--login', action='store_true', 
                        help='Enable auto-login prompt')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with additional output')
    parser.add_argument('--save-html', action='store_true',
                        help='Save HTML of the page for debugging')
    args = parser.parse_args()
    return args

def main():
    """Main function to run the scraper."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Update global variables based on arguments
    global TWITTER_USERNAME, TARGET_URL, MAX_SCROLLS, SCROLL_PAUSE_TIME, OUTPUT_FILE, AUTO_LOGIN, TWITTER_EMAIL, TWITTER_PASSWORD
    
    TWITTER_USERNAME = args.username
    TARGET_URL = f"https://x.com/{TWITTER_USERNAME}/with_replies"
    MAX_SCROLLS = args.max_scrolls
    SCROLL_PAUSE_TIME = args.pause_time
    OUTPUT_FILE = f"{TWITTER_USERNAME}_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Handle login if requested
    if args.login:
        AUTO_LOGIN = True
        TWITTER_EMAIL = input("Enter your Twitter email/username: ")
        TWITTER_PASSWORD = input("Enter your Twitter password: ")
    
    print(f"Starting Twitter scraper for user: {TWITTER_USERNAME}")
    print(f"Max scrolls: {MAX_SCROLLS}, Pause time: {SCROLL_PAUSE_TIME}s")
    print(f"Output will be saved to: {OUTPUT_FILE}")
    
    # Configure debug logs if requested
    if args.debug:
        print("Debug mode enabled - will print detailed information")
    
    # Display Chrome version
    try:
        import subprocess
        if sys.platform == 'win32':
            # Windows
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            alt_chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            
            if os.path.exists(chrome_path):
                version_cmd = f'"{chrome_path}" --version'
            elif os.path.exists(alt_chrome_path):
                version_cmd = f'"{alt_chrome_path}" --version'
            else:
                # Try to find Chrome in registry
                import winreg
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                        chrome_path = winreg.QueryValue(key, None)
                        version_cmd = f'"{chrome_path}" --version'
                except:
                    version_cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
        else:
            # Linux/Mac
            version_cmd = 'google-chrome --version || chrome --version'
        
        result = subprocess.run(version_cmd, shell=True, capture_output=True, text=True)
        chrome_version = result.stdout.strip()
        print(f"Chrome version: {chrome_version}")
    except Exception as e:
        print(f"Could not determine Chrome version: {e}")
    
    try:
        driver = setup_driver()
        
        # Save HTML if requested
        if args.save_html:
            def save_page_html():
                html_file = f"{TWITTER_USERNAME}_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"Saved page HTML to {html_file}")
            
            # Register this as a function to call when there's an issue
            import atexit
            atexit.register(save_page_html)
        
        try:
            tweets = scrape_tweets(driver, TWITTER_USERNAME)
            if tweets:
                save_tweets_to_csv(tweets, OUTPUT_FILE)
                print(f"Scraping completed! Total tweets scraped: {len(tweets)}")
            else:
                print("No tweets were scraped.")
                
                if args.save_html:
                    html_file = f"{TWITTER_USERNAME}_error_page.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    print(f"Saved error page HTML to {html_file}")
        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            import traceback
            traceback.print_exc()
            
            if args.save_html:
                html_file = f"{TWITTER_USERNAME}_error_page.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"Saved error page HTML to {html_file}")
    except Exception as e:
        print(f"An error occurred while setting up the driver: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except:
            pass
        
        print("Scraper finished")

if __name__ == "__main__":
    main() 