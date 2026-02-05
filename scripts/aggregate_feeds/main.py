#!/usr/bin/env python3
"""
Blog Aggregator Script
Fetches posts from multiple RSS feeds and generates Hugo content files.
"""

import feedparser
import json
import re
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


def load_config(config_path='feeds.json'):
    """Load feed configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def sanitize_filename(title):
    """Convert title to a safe filename."""
    # Remove special characters and convert to lowercase
    safe_name = re.sub(r'[^\w\s-]', '', title.lower())
    safe_name = re.sub(r'[-\s]+', '-', safe_name)
    return safe_name[:100]  # Limit length


def extract_image(entry):
    """Extract the main image from a feed entry."""
    # Try media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url')

    # Try media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url')

    # Try enclosure
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image/'):
                return enclosure.get('href')

    # Try to find image in content
    if hasattr(entry, 'content') and entry.content:
        soup = BeautifulSoup(entry.content[0].value, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img.get('src')

    # Try summary
    if hasattr(entry, 'summary'):
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img.get('src')

    return None


def extract_summary(entry, max_length=200):
    """Extract and clean summary text from entry."""
    summary_text = ''

    if hasattr(entry, 'summary'):
        summary_text = entry.summary
    elif hasattr(entry, 'description'):
        summary_text = entry.description
    elif hasattr(entry, 'content') and entry.content:
        summary_text = entry.content[0].value

    # Remove HTML tags
    soup = BeautifulSoup(summary_text, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)

    # Truncate to max length
    if len(clean_text) > max_length:
        clean_text = clean_text[:max_length].rsplit(' ', 1)[0] + '...'

    return clean_text


def generate_post_id(url):
    """Generate a unique ID for a post based on URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def create_hugo_post(entry, author_name, output_dir, existing_posts, feed_config=None):
    """Create a Hugo markdown file for a blog post."""
    # Extract data
    title = entry.get('title', 'Untitled Post')
    link = entry.get('link', '')

    # Get linkedin_url from feed_config if provided
    linkedin_url = feed_config.get('linkedin_url') if feed_config else None

    # Skip if we've already created this post
    post_id = generate_post_id(link)
    if post_id in existing_posts:
        return None

    # Parse date
    pub_date = entry.get('published', entry.get('updated', ''))
    try:
        if pub_date:
            date_obj = date_parser.parse(pub_date)
        else:
            date_obj = datetime.now()
    except:
        date_obj = datetime.now()

    # Skip posts older than 12 months
    twelve_months_ago = datetime.now() - timedelta(days=365)
    if date_obj.replace(tzinfo=None) < twelve_months_ago:
        return None

    # Extract image and summary
    image = extract_image(entry)
    summary = extract_summary(entry)

    # Extract tags/categories
    tags = []
    if hasattr(entry, 'tags'):
        tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]

    # Apply tag filtering if feed_config is provided
    if feed_config:
        include_tags = feed_config.get('include_tags', [])
        exclude_tags = feed_config.get('exclude_tags', [])

        # If include_tags is specified, only keep tags in that list
        if include_tags:
            tags = [tag for tag in tags if tag.lower() in [t.lower() for t in include_tags]]

        # Remove any excluded tags
        if exclude_tags:
            tags = [tag for tag in tags if tag.lower() not in [t.lower() for t in exclude_tags]]

        # If post has no tags after filtering and include_tags was specified, skip it
        if include_tags and not tags:
            return None

    # Create filename
    date_prefix = date_obj.strftime('%Y-%m-%d')
    filename = f"{date_prefix}-{sanitize_filename(title)}-{post_id}.md"
    filepath = Path(output_dir) / filename

    # Prepare frontmatter
    frontmatter = f"""+++
title = "{title.replace('"', '\\"')}"
date = "{date_obj.isoformat()}"
authors = ["{author_name}"]
external_url = "{link}"
draft = false
"""

    if linkedin_url:
        frontmatter += f'linkedin_url = "{linkedin_url}"\n'

    if tags:
        tags_str = ', '.join([f'"{tag}"' for tag in tags[:5]])  # Limit to 5 tags
        frontmatter += f"tags = [{tags_str}]\n"

    if image:
        frontmatter += f'featured_image = "{image}"\n'

    frontmatter += "+++\n\n"

    # Create content
    content = frontmatter
    content += f"{summary}\n\n"
    # content += f"[Read the full article on {author_name}'s blog →]({link})\n"

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filename


def get_existing_posts(output_dir):
    """Get set of post IDs that already exist."""
    existing = set()
    output_path = Path(output_dir)

    if not output_path.exists():
        return existing

    for filepath in output_path.glob('*.md'):
        # Extract post ID from filename
        match = re.search(r'-([a-f0-9]{12})\.md$', filepath.name)
        if match:
            existing.add(match.group(1))

    return existing


def fetch_feed(feed_config, output_dir, existing_posts):
    """Fetch and process a single RSS feed."""
    name = feed_config['name']
    url = feed_config.get('feed_url') or feed_config.get('url')  # Support both feed_url and legacy url

    print(f"Fetching feed for {name}...")

    try:
        import ssl
        import urllib.request
        
        # Create SSL context that doesn't verify certificates (for feeds with cert issues)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create custom opener with SSL context and realistic user agent
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl_context)
        )
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            ('Accept', 'application/rss+xml, application/xml, text/xml, */*'),
            ('Accept-Language', 'en-US,en;q=0.9'),
        ]
        
        # Use the custom opener to fetch and parse the feed
        response = opener.open(url, timeout=30)
        feed = feedparser.parse(response.read())

        if feed.bozo and not feed.entries:
            print(f"  ⚠️  Warning: Failed to parse feed for {name}")
            if hasattr(feed, 'bozo_exception'):
                print(f"     Error: {feed.bozo_exception}")
            return 0

        posts_created = 0
        max_posts = feed_config.get('max_posts', 10)

        for entry in feed.entries[:max_posts]:
            result = create_hugo_post(entry, name, output_dir, existing_posts, feed_config)
            if result:
                print(f"  ✓ Created: {result}")
                posts_created += 1

        if posts_created == 0:
            print(f"  → No new posts from {name}")
        else:
            print(f"  ✓ Created {posts_created} new post(s) from {name}")

        return posts_created

    except Exception as e:
        print(f"  ✗ Error fetching {name}: {str(e)}")
        return 0


def generate_author_data(config):
    """Generate author data file from feeds configuration."""
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    authors = []
    for feed_config in config['feeds']:
        if not feed_config.get('enabled', True):
            continue

        author = {
            'name': feed_config.get('name', 'Unknown'),
            'url': feed_config.get('url', ''),
            'feed_url': feed_config.get('feed_url', ''),
            'linkedin_url': feed_config.get('linkedin_url', ''),
            'profile_picture_url': feed_config.get('profile_picture_url', '')
        }
        authors.append(author)

    # Write authors data to JSON file
    authors_file = data_dir / 'authors.json'
    with open(authors_file, 'w') as f:
        json.dump({'authors': authors}, f, indent=2)

    print(f"Generated author data for {len(authors)} author(s)")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Blog Aggregator - Fetching RSS Feeds")
    print("=" * 60)

    # Load configuration
    config = load_config()
    settings = config.get('settings', {})
    output_dir = settings.get('output_directory', 'content/posts')

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate author data
    generate_author_data(config)

    # Get existing posts
    existing_posts = get_existing_posts(output_dir)
    print(f"\nFound {len(existing_posts)} existing post(s)\n")

    # Process each feed
    total_created = 0
    enabled_feeds = [f for f in config['feeds'] if f.get('enabled', True)]
    
    for idx, feed_config in enumerate(enabled_feeds):
        created = fetch_feed(feed_config, output_dir, existing_posts)
        total_created += created
        
        # Add delay between requests to avoid rate limiting (except for last feed)
        if idx < len(enabled_feeds) - 1:
            delay = 2  # 2 seconds between feeds
            print(f"  ⏱️  Waiting {delay}s before next feed...")
            time.sleep(delay)

    print("\n" + "=" * 60)
    print(f"Aggregation complete! Created {total_created} new post(s)")
    print("=" * 60)


if __name__ == '__main__':
    main()
