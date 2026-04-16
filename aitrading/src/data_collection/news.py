import feedparser

def get_crypto_news(feed_url='https://www.investing.com/rss/news_285.rss'):
    """
    Fetches cryptocurrency news from an RSS feed.
    """
    try:
        feed = feedparser.parse(feed_url)
        news_items = []
        for entry in feed.entries:
            news_items.append({
                'title': getattr(entry, 'title', 'No Title'),
                'link': getattr(entry, 'link', ''),
                'published': getattr(entry, 'published', 'No Date'),
                'summary': getattr(entry, 'summary', 'No Summary')
            })
        return news_items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

if __name__ == '__main__':
    # Example usage
    crypto_news = get_crypto_news()
    if crypto_news:
        print("Latest Crypto News:")
        for i, item in enumerate(crypto_news[:5]):  # Print the first 5 news items
            print(f"  {i+1}. {item['title']}")
            print(f"     Link: {item['link']}")
            print(f"     Published: {item['published']}")
