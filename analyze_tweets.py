#!/usr/bin/env python3
"""
Analyze scraped tweets and provide statistics.
This script processes the CSV file created by the Twitter scraper.
"""

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime
import re

def load_tweets(csv_file):
    """Load tweets from the CSV file."""
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} does not exist!")
        sys.exit(1)
        
    tweets = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Convert timestamp to datetime
                if row['timestamp'] != "Unknown":
                    row['datetime'] = datetime.strptime(row['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                else:
                    row['datetime'] = None
                
                # Convert numeric fields
                for field in ['replies', 'retweets', 'likes']:
                    row[field] = int(row[field]) if row[field] else 0
                    
                tweets.append(row)
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
                
    return tweets

def extract_mentions(text):
    """Extract @mentions from tweet text."""
    return re.findall(r'@\w+', text)

def extract_hashtags(text):
    """Extract #hashtags from tweet text."""
    return re.findall(r'#\w+', text)

def print_stats(tweets):
    """Print statistics about the tweets."""
    if not tweets:
        print("No tweets found!")
        return
        
    print(f"\n📊 TWITTER SCRAPER ANALYSIS")
    print(f"📑 Total tweets: {len(tweets)}")
    
    # Date range
    dates = [t['datetime'] for t in tweets if t['datetime']]
    if dates:
        min_date = min(dates)
        max_date = max(dates)
        date_range = (max_date - min_date).days
        print(f"📅 Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({date_range} days)")
    
    # Engagement stats
    total_replies = sum(t['replies'] for t in tweets)
    total_retweets = sum(t['retweets'] for t in tweets)
    total_likes = sum(t['likes'] for t in tweets)
    
    print(f"💬 Total replies: {total_replies}")
    print(f"🔁 Total retweets: {total_retweets}")
    print(f"❤️ Total likes: {total_likes}")
    
    if tweets:
        avg_replies = total_replies / len(tweets)
        avg_retweets = total_retweets / len(tweets)
        avg_likes = total_likes / len(tweets)
        
        print(f"📊 Average engagement per tweet:")
        print(f"   - Replies: {avg_replies:.2f}")
        print(f"   - Retweets: {avg_retweets:.2f}")
        print(f"   - Likes: {avg_likes:.2f}")
    
    # Most popular tweets
    most_liked = max(tweets, key=lambda x: x['likes'])
    most_retweeted = max(tweets, key=lambda x: x['retweets'])
    most_replies = max(tweets, key=lambda x: x['replies'])
    
    print(f"\n🔝 MOST POPULAR TWEETS")
    print(f"\n✨ Most liked ({most_liked['likes']} likes):")
    print(f"   {most_liked['text'][:100]}...")
    
    print(f"\n🔄 Most retweeted ({most_retweeted['retweets']} retweets):")
    print(f"   {most_retweeted['text'][:100]}...")
    
    print(f"\n💬 Most replied to ({most_replies['replies']} replies):")
    print(f"   {most_replies['text'][:100]}...")
    
    # Extract mentions and hashtags
    all_mentions = []
    all_hashtags = []
    
    for tweet in tweets:
        all_mentions.extend(extract_mentions(tweet['text']))
        all_hashtags.extend(extract_hashtags(tweet['text']))
    
    # Count and sort
    mention_counts = Counter(all_mentions).most_common(10)
    hashtag_counts = Counter(all_hashtags).most_common(10)
    
    if mention_counts:
        print(f"\n👥 TOP MENTIONS")
        for mention, count in mention_counts:
            print(f"   {mention}: {count} times")
    
    if hashtag_counts:
        print(f"\n🔖 TOP HASHTAGS")
        for hashtag, count in hashtag_counts:
            print(f"   {hashtag}: {count} times")
    
    # Activity by day of week
    if dates:
        day_counts = Counter([d.strftime('%A') for d in dates])
        
        # Ensure all days are present
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days_of_week:
            if day not in day_counts:
                day_counts[day] = 0
        
        # Sort by day of week
        sorted_days = sorted(day_counts.items(), 
                            key=lambda x: days_of_week.index(x[0]))
        
        print(f"\n📆 ACTIVITY BY DAY OF WEEK")
        for day, count in sorted_days:
            print(f"   {day}: {count} tweets")

def main():
    parser = argparse.ArgumentParser(description='Analyze Twitter scraped data')
    parser.add_argument('file', help='CSV file containing scraped tweets')
    args = parser.parse_args()
    
    tweets = load_tweets(args.file)
    print_stats(tweets)

if __name__ == "__main__":
    main() 