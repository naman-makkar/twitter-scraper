import time
import csv
import re
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import sys

# Configuration
TWITTER_USERNAME = "example_user"  # Default placeholder - will be overridden by command line args
TARGET_URL = f"https://x.com/{TWITTER_USERNAME}/with_replies"
SCROLL_PAUSE_TIME = 2.5  # Increased for reliability
SCROLL_VARIATION = 1.0  # Random variation in scroll time to appear more human-like
MAX_SCROLLS = 2000  # Adjust based on how many tweets you want to scrape
OUTPUT_FILE = f"{TWITTER_USERNAME}_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
AUTO_LOGIN = False  # Set to True if you want to use automatic login

# Twitter login credentials - only needed if AUTO_LOGIN is True
# TWITTER_EMAIL = "your_email@example.com"
# TWITTER_PASSWORD = "your_password"

def setup_driver():
    """Setup and return a Chrome WebDriver instance with appropriate options."""
    chrome_options = Options()
    # Uncomment the line below to run Chrome in headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--mute-audio")
    
    # Add user agent to appear more like a real browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    try:
        # First approach - Use webdriver manager (should work for most cases)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"First driver initialization approach failed: {e}")
        print("Trying alternative approach...")
        
        try:
            # Second approach - Use Chrome directly without service
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"Second driver initialization approach failed: {e2}")
            print("Please make sure Chrome is installed correctly.")
            print("Trying one last approach with explicit driver path...")
            
            # Third approach - Try to use an explicit path that works on Windows
            try:
                # Get user home directory
                user_home = os.path.expanduser("~")
                cache_dir = os.path.join(user_home, ".wdm", "drivers", "chromedriver")
                
                # Check if the cache directory exists
                if os.path.exists(cache_dir):
                    # Find the most recent driver version directory
                    version_dirs = [d for d in os.listdir(cache_dir) if os.path.isdir(os.path.join(cache_dir, d))]
                    if version_dirs:
                        latest_version = sorted(version_dirs)[-1]
                        driver_path = os.path.join(cache_dir, latest_version, "win32", "chromedriver.exe")
                        
                        if os.path.exists(driver_path):
                            service = Service(driver_path)
                            driver = webdriver.Chrome(service=service, options=chrome_options)
                            return driver
                
                print("Could not find cached driver. Downloading a fresh driver...")
                from webdriver_manager.chrome import ChromeDriverManager
                
                # Force download a new driver with specific version
                driver_path = ChromeDriverManager(version="114.0.5735.90").install()
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
            except Exception as e3:
                print(f"All driver initialization approaches failed: {e3}")
                print("Please install Chrome browser and try again.")
                sys.exit(1)

def login_to_twitter(driver):
    """Attempt to log in to Twitter account."""
    if not AUTO_LOGIN:
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

def extract_tweet_data(article):
    """Extract data from a tweet article element."""
    try:
        # Extract timestamp
        time_element = article.find('time')
        timestamp = time_element['datetime'] if time_element else "Unknown"
        
        # Extract tweet URL/ID
        if time_element and time_element.parent and time_element.parent.parent:
            tweet_link = time_element.parent.parent.get('href')
            tweet_id = tweet_link.split('/')[-1] if tweet_link else "Unknown"
        else:
            tweet_id = "Unknown"
        
        # Extract tweet text
        tweet_text_div = article.find('div', {'data-testid': 'tweetText'})
        if tweet_text_div:
            tweet_text = clean_tweet_text(tweet_text_div.get_text())
        else:
            tweet_text = "No text found"
        
        # Extract likes, retweets, replies
        stats_divs = article.find_all('div', {'role': 'group'})
        stats = {}
        if stats_divs:
            stats_elements = stats_divs[0].find_all('div')
            for i, stat_type in enumerate(['replies', 'retweets', 'likes']):
                if i < len(stats_elements):
                    stat_text = stats_elements[i].get_text()
                    stat_value = re.search(r'\d+', stat_text)
                    stats[stat_type] = int(stat_value.group()) if stat_value else 0
        
        # Add tweet to our list
        tweet_data = {
            'tweet_id': tweet_id,
            'timestamp': timestamp,
            'text': tweet_text,
            'replies': stats.get('replies', 0),
            'retweets': stats.get('retweets', 0),
            'likes': stats.get('likes', 0),
            'url': f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}" if tweet_id != "Unknown" else "Unknown"
        }
        
        return tweet_data
    except Exception as e:
        print(f"Error extracting tweet data: {e}")
        return None

def scrape_tweets(driver):
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
        )
    except TimeoutException:
        print("Timeout while waiting for the timeline to load.")
        return tweets
    
    time.sleep(3)  # Allow some time for the page to fully load
    
    # Scroll and scrape
    while scroll_count < MAX_SCROLLS:
        # Every 10 scrolls, perform some random actions to appear more human-like
        if scroll_count % 10 == 0:
            random_scroll(driver)
            time.sleep(random.uniform(1.0, 3.0))
        
        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all tweet articles
        tweet_articles = soup.find_all('article')
        prev_count = len(tweets)
        
        for article in tweet_articles:
            tweet_data = extract_tweet_data(article)
            
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
        
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        scroll_time = SCROLL_PAUSE_TIME + random.uniform(-SCROLL_VARIATION, SCROLL_VARIATION)
        time.sleep(max(0.5, scroll_time))  # Ensure minimum pause time
        
        scroll_count += 1
        print(f"Scrolled {scroll_count} times. Found {len(tweets)} tweets so far.")
        
        # Check if we found any new tweets in this scroll
        if prev_count == len(tweets):
            consecutive_no_new_tweets += 1
            print(f"No new tweets found in this scroll. ({consecutive_no_new_tweets}/5)")
            
            # If we haven't found new tweets for 5 consecutive scrolls, we might have reached the end
            if consecutive_no_new_tweets >= 5:
                print("Reached 5 consecutive scrolls with no new tweets. We might have reached the end.")
                break
        else:
            consecutive_no_new_tweets = 0  # Reset the counter
    
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

def main():
    """Main function to run the scraper."""
    print(f"Starting Twitter scraper for user: {TWITTER_USERNAME}")
    print(f"Output will be saved to: {OUTPUT_FILE}")
    
    driver = setup_driver()
    try:
        tweets = scrape_tweets(driver)
        if tweets:
            save_tweets_to_csv(tweets, OUTPUT_FILE)
            print(f"Scraping completed! Total tweets scraped: {len(tweets)}")
        else:
            print("No tweets were scraped.")
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 