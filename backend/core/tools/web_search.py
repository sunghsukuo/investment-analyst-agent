import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime

def fetch_rss_news(feed_url: str, max_items: int = 8) -> list:
    """Helper function to fetch and parse an RSS XML feed into a clean list of news articles."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(feed_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        # Parse XML using Python standard library (100% robust and independent of external lxml parsers)
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        articles = []
        for item in items[:max_items]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            description = item.find("description").text if item.find("description") is not None else ""
            
            # Clean HTML tags from description if present
            if description:
                desc_soup = BeautifulSoup(description, "html.parser")
                description = desc_soup.get_text()
                
            articles.append({
                "title": title.strip(),
                "link": link.strip(),
                "pub_date": pub_date.strip(),
                "summary": description.strip()[:300]  # Limit length for LLM processing
            })
            
        return articles
    except Exception as e:
        print(f"Error fetching RSS from {feed_url}: {e}")
        return []

def get_stock_news(ticker: str, max_items: int = 5) -> list:
    """Fetches real-time stock-specific news using the Yahoo Finance RSS feed."""
    clean_ticker = ticker.strip().upper()
    # Yahoo Finance RSS Feed for a specific ticker
    feed_url = f"https://feeds.finance.yahoo.com/rss/2.0?s={clean_ticker}"
    
    news = fetch_rss_news(feed_url, max_items)
    # If Yahoo RSS is empty, fallback to Google News RSS search
    if not news:
        query = f"{clean_ticker} stock news"
        news = search_news(query, max_items)
        
    return news

def search_news(query: str, max_items: int = 6, language: str = "zh-TW", region: str = "TW") -> list:
    """Searches Google News RSS for macroeconomic topics or industry trends."""
    encoded_query = urllib.parse.quote(query)
    
    # Configure language/region suffixes
    if language == "zh-TW":
        feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    else:
        feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
    return fetch_rss_news(feed_url, max_items)

def get_macro_news(region_code: str, max_items: int = 5) -> list:
    """Fetches top macroeconomic and financial policy news for a given region."""
    if region_code == "US":
        # Search for major US economic events
        query = "US Federal Reserve interest rates inflation CPI market"
        return search_news(query, max_items, language="en-US", region="US")
    elif region_code == "Taiwan":
        # Search for major Taiwan economic events
        query = "台灣 總體經濟 出口 央行 景氣燈號"
        return search_news(query, max_items, language="zh-TW", region="TW")
    else:
        query = f"{region_code} macroeconomic financial news"
        return search_news(query, max_items, language="en-US", region="US")
