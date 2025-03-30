# Twitter/X Tweet Scraper

A powerful Python script to scrape tweets and replies from any Twitter/X user without using the Twitter API. This tool can collect months of historical tweets, including engagement metrics.

## Features

- Scrapes tweets and replies from any Twitter/X user
- Handles login walls automatically (with manual or automatic login)
- Saves data incrementally to prevent data loss
- Includes timestamps, tweet IDs, engagement stats, and URLs
- Creates a CSV file that can be opened in Excel or any spreadsheet program
- Implements human-like behavior to avoid detection
- Includes debugging options for troubleshooting

## Setup

1. Make sure you have Python 3.7+ installed
2. Install Chrome browser if not already installed

### Windows Users

Windows users can use the included batch files for easier setup:

1. Run `setup_windows.bat` to set up the environment automatically:

   ```
   setup_windows.bat
   ```

2. After setup, run the Windows-specific version using:
   ```
   run_windows.bat username --max-scrolls 500 --login
   ```

This Windows version uses undetected-chromedriver which avoids common Windows ChromeDriver errors.

### Manual Setup (All Platforms)

If you prefer manual setup:

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the scraper directly:
   ```
   python twitter_scraper_undetected.py username --max-scrolls 500 --login
   ```

## Usage

The basic usage requires at least one parameter - the Twitter username to scrape:

```
python twitter_scraper_undetected.py username
```

### Command-line Arguments

- First argument: Twitter username to scrape (without @ symbol)
- `--max-scrolls`: Maximum number of times to scroll (default: 500)
- `--pause-time`: Time to wait between scrolls in seconds (default: 2.5)
- `--login`: Add this flag if you want to be prompted for login credentials
- `--debug`: Enable debug mode with additional output
- `--save-html`: Save HTML of the page for debugging

### Examples

Scrape a user's tweets with default settings:

```
python twitter_scraper_undetected.py elonmusk
```

Scrape tweets with more scrolls (for accounts with many tweets):

```
python twitter_scraper_undetected.py twitter --max-scrolls 1000
```

Scrape tweets with manual login (recommended for private accounts or to avoid rate limits):

```
python twitter_scraper_undetected.py jack --login
```

## Debug Mode

If you're experiencing issues, use the debug mode:

```
python twitter_scraper_undetected.py username --debug --save-html
```

Or use the Windows debug batch file:

```
run_windows_debug.bat username
```

This will:

- Print more detailed logs
- Save the HTML of the page to help diagnose parsing issues
- Try multiple tweet extraction methods

## Output Format

The CSV file contains these fields:

- `tweet_id`: Unique identifier for the tweet
- `timestamp`: Date and time when the tweet was posted
- `text`: Content of the tweet
- `replies`: Number of replies
- `retweets`: Number of retweets
- `likes`: Number of likes
- `url`: Link to the original tweet

## Notes

- Twitter/X may rate limit or block automated scraping attempts if you scrape too aggressively
- The script adds randomized behavior to appear more human-like and bypass detection
- The script checks for login walls and will wait for you to log in if needed
- For 8 months of tweets, try starting with `MAX_SCROLLS = 500` and increase if needed

## Troubleshooting

- If no tweets are found, try increasing the scroll wait time (e.g., `--pause-time 3.5`)
- If you're getting logged out or blocked, use the `--login` flag to login manually
- For better results, consider logging in with an account that follows the user you're scraping
- If Chrome is crashing, make sure you have the latest version installed
