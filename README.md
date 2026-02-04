# Voice of Engineering Blog Aggregator

A Hugo-powered blog aggregator that collects and showcases engineering blog posts from multiple sources with CGI corporate branding.

## Features

- Fetches posts from RSS feeds (Medium, Dev.to, custom feeds)
- Links to original posts (preserves author traffic)
- Extracts featured images and summaries
- Preserves tags and categories
- Author profiles with LinkedIn integration
- CGI corporate theme and branding
- Filter by author or category
- Automatic 12-month rolling archive
- Tag filtering per feed (include/exclude)
- Fast static site generation with Hugo
- Automated deployment to GitHub Pages

## Getting Started

### Prerequisites

- Hugo v0.155.2+extended
- Python 3.13+
- pip

### Installation

1. Install Python dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r scripts/aggregate_feeds/requirements.txt
```

2. Configure your feeds in `scripts/aggregate_feeds/feeds.json`:
```json
{
  "feeds": [
    {
      "name": "Author Name",
      "url": "https://author.com",
      "feed_url": "https://medium.com/feed/@username",
      "type": "medium",
      "enabled": true,
      "linkedin_url": "https://www.linkedin.com/in/username/",
      "profile_picture_url": "",
      "include_tags": ["python", "cloud"],
      "exclude_tags": ["sponsored"]
    }
  ],
  "settings": {
    "max_posts_per_feed": 10,
    "summary_length": 200,
    "output_directory": "content/posts"
  }
}
```

## Usage

### Aggregate feeds and build site
```bash
./scripts/aggregate_feeds/build.sh
```

Or run steps individually:

### 1. Fetch RSS feeds
```bash
python3 scripts/aggregate_feeds/main.py
```

### 2. Build Hugo site
```bash
hugo
```

### 3. Start development server

For local development, override the baseURL to match the same path structure as production:
```bash
hugo server --baseURL http://localhost:1313/voice-of-engineering-blog-aggregator/
```

This ensures all navigation links work correctly with the `/voice-of-engineering-blog-aggregator/` path prefix.

## Configuration

### feeds.json

Add your colleagues' blog feeds:

- **Medium**: `feed_url: https://medium.com/feed/@username`
- **Dev.to**: `feed_url: https://dev.to/feed/username`
- **Custom RSS**: Any valid RSS/Atom feed URL

#### Feed Properties:
- `name`: Author's display name
- `url`: Author's website/blog homepage
- `feed_url`: RSS/Atom feed URL
- `type`: Feed type (medium, devto, custom)
- `enabled`: Enable/disable this feed
- `linkedin_url`: Author's LinkedIn profile (optional)
- `profile_picture_url`: URL to author's profile picture (optional)
- `include_tags`: Array of tags to include (optional, case-insensitive)
- `exclude_tags`: Array of tags to exclude (optional, case-insensitive)

#### Settings:
- `max_posts_per_feed`: Maximum posts to fetch per feed (default: 10)
- `summary_length`: Character limit for summaries (default: 200)
- `output_directory`: Where to save generated posts (default: content/posts)

### Tag Filtering

You can filter which posts are aggregated based on their tags:

```json
{
  "name": "Jane Doe",
  "feed_url": "https://example.com/feed",
  "include_tags": ["python", "javascript", "devops"],
  "exclude_tags": ["sponsored", "advertisement"]
}
```

- `include_tags`: Only aggregate posts with at least one of these tags (if specified)
- `exclude_tags`: Skip posts with any of these tags
- Both filters are optional and case-insensitive
- Filters work together: inclusion is applied first, then exclusion

## How It Works

1. The `scripts/aggregate_feeds/main.py` script fetches RSS feeds from configured sources
2. For each post, it extracts:
   - Title
   - Publication date
   - Featured image
   - Summary (truncated to avoid duplicate content)
   - Original URL
   - Tags/categories (with optional filtering)
   - Author information
3. Generates Hugo-compatible markdown files with frontmatter
4. Creates author profile data from feeds.json
5. Posts older than 12 months are automatically excluded
6. Hugo builds the static site with CGI branding
7. Visitors click through to read full articles on the original blogs

## Site Structure

- **Home**: All blog posts from enabled feeds
- **Authors**: Browse contributors with profile cards
- **Categories**: Browse posts by tag/category

## Deployment

### GitHub Pages (Automated)

The site automatically deploys to GitHub Pages via GitHub Actions:

1. Enable GitHub Pages in repository settings:
   - Go to Settings → Pages
   - Source: GitHub Actions

2. The workflow runs automatically:
   - On push to main branch
   - Daily at 6 AM UTC (scheduled)
   - Manually via "Run workflow" button

3. Manual deployment:
   - Go to Actions tab
   - Select "Build and Deploy to GitHub Pages"
   - Click "Run workflow"

### Manual Deployment

Build the production site:
```bash
./scripts/aggregate_feeds/build.sh
```

Deploy the `public/` directory to any static hosting:
- GitHub Pages
- Netlify
- Vercel
- AWS S3
- Cloudflare Pages

## Development

The site uses:
- **Hugo v0.155.2+extended**: Static site generator
- **Python 3.11+**: Feed aggregation
- **CGI Theme**: Custom theme matching cgi.com/blogs
- **Taxonomies**: Authors and tags for filtering

## Project Structure

```
voice-of-engineering-blog-aggregator/
├── scripts/
│   └── aggregate_feeds/
│       ├── main.py              # Feed aggregation script
│       ├── build.sh             # Build script
│       └── requirements.txt     # Python dependencies
├── themes/
│   └── cgi-theme/               # Custom CGI theme
│       ├── layouts/             # Hugo templates
│       └── static/              # CSS, images
├── content/
│   └── posts/                   # Generated blog posts
├── data/
│   └── authors.json             # Generated author data
├── i18n/
│   └── en.toml                  # Internationalization strings
├── feeds.json                   # Feed configuration
└── hugo.toml                    # Hugo configuration
```

## License

Copyright CGI© 2026. All rights reserved.
