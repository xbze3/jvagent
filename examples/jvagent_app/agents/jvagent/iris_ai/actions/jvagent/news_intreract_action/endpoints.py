"""News fetching endpoints for searching news websites or RSS feeds.

This module provides endpoints to fetch news articles from RSS feeds
without storing them. It fetches and returns news articles on demand.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import feedparser
from bs4 import BeautifulSoup
from jvspatial.api import endpoint
from jvspatial.api.endpoints.response import ResponseField, success_response
from jvspatial.core.context import GraphContext
from jvagent.core.agent import Agent
from jvspatial.db import get_prime_database
from jvagent.action.model.language.openai.openai import OpenAILanguageModelAction
from .prompts import SUMMARY_TEMPLATE, INTENT_EXTRACTION_TEMPLATE, DIRECTIVE_TEMPLATE, DAILY_SUMMARY_TEMPLATE

from jvspatial.api.auth.api_key_service import APIKeyService
from jvspatial.api.auth.models import APIKey

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Class to handle fetching news from RSS feeds."""

    # Guyanese news feeds (adapted from the jac file)
    news_feeds: Dict[str, str] = {
        "stabroek news": "https://www.stabroeknews.com/feed/",
        "news room": "https://newsroom.gy/feed/",
        "guyana times": "https://guyanatimesgy.com/feed/",
        "guyana chronicle": "https://guyanachronicle.com/feed/",
        "demerara waves": "https://demerarawaves.com/feed/",
        "inews guyana": "https://www.inewsguyana.com/feed/",
        "hgptv": "https://www.hgptv.com/feed/",
        "kaieteur news": "https://www.kaieteurnewsonline.com/feed/",
        "news source": "https://newssourcegy.com/feed/"
    }
    time = "10:40"
    base_url: Optional[str] = "http://localhost:8000"

    webhook_url: Optional[str] = None

    webhook_api_key_id: Optional[str] = None

    agent_id: Optional[str] = None


    max_articles: int = 10  # maximum number of articles to fetch from each source
    summary_cache: Dict[str, str] = {}
    model_action: Optional[OpenAILanguageModelAction] = None

    _scheduler_thread: Optional[Any] = None
    _scheduler_running: bool = False

    url_shortener: "URLShortener"

    def __init__(self):
        self.url_shortener = URLShortener()
        self.load_cache()


    def load_cache(self):
        """Load summary cache from JSON file."""
        cache_file = os.path.join(os.path.dirname(__file__), 'summary_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.summary_cache = json.load(f)
                logger.info("Loaded summary cache from file")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.summary_cache = {}
        else:
            self.summary_cache = {}

    def save_cache(self):
        """Save summary cache to JSON file."""
        cache_file = os.path.join(os.path.dirname(__file__), 'summary_cache.json')
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.summary_cache, f, indent=2)
            logger.debug("Saved summary cache to file")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _fetch_news_sync(self):
        """Synchronous wrapper to call async get_summary from schedule."""
        import asyncio
        logger.info("Scheduled news fetch triggered...")
        try:
            # Create new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async function
            result = loop.run_until_complete(self.get_summary())

            if result.get("error"):
                logger.error(f"Scheduled fetch failed: {result['error']}")
            else:
                logger.info(f"Scheduled fetch successful for {result.get('date')}")
                from .news_interact_action import NewsInteractAction
                news_interact_action = loop.run_until_complete(NewsInteractAction.find_one({
                    "context.enabled": True
                }))
                loop.run_until_complete(news_interact_action.send_news(result))

        except Exception as e:
            logger.error(f"Error in scheduled news fetch: {e}", exc_info=True)

    def start_scheduler(self):
        """Start the background scheduler thread."""
        import schedule
        import threading
        import time

        if self._scheduler_running:
            logger.info("News scheduler already running")
            return

        # Schedule the job - runs every day at 8:30 AM
        schedule.every().day.at(self.time).do(self._fetch_news_sync)
        logger.info(f"Scheduled news fetch for {self.time} daily")

        # Background thread to run pending jobs
        def run_scheduler():
            logger.info("News scheduler thread started")
            while self._scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            logger.info("News scheduler thread stopped")

        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._scheduler_thread.start()
        logger.info("News scheduler background thread started")

    def stop_scheduler(self):
        """Stop the background scheduler thread."""
        import schedule
        self._scheduler_running = False
        schedule.clear()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2)
        logger.info("News scheduler stopped")

    async def summarize_news(self, articles: List[Dict[str, Any]], model_action: Optional[OpenAILanguageModelAction] = None) -> Optional[str]:
        """Summarize news articles using LLM.

        Args:
            articles: List of articles to summarize
            model_action: Optional model action to use

        Returns:
            Summary string or None
        """
        try:
            if not articles:
                return None

            # Determine model action to use
            action_to_use = model_action or self.model_action
            if not action_to_use:
                logger.warning("No model action provided, creating new OpenAILanguageModelAction")
                # action_to_use = OpenAILanguageModelAction()
                action_to_use = await OpenAILanguageModelAction.find_one({})
                self.model_action = action_to_use

            # # Check if API key is configured
            # if hasattr(action_to_use, 'api_key'):
            #     if not action_to_use.api_key or action_to_use.api_key.strip() == "":
            #         # Try to get API key from agent settings
            #         api_key = await self._get_openai_api_key()
            #         if api_key:
            #             action_to_use.api_key = api_key
            #             logger.info("Retrieved OpenAI API key from agent settings")
            #         else:
            #             logger.error("OpenAI API key is not configured. Cannot summarize news.")
            #             logger.error("Please configure OPENAI_API_KEY in the agent settings.")
            #             return None

            # Format articles
            results_parts = []
            titles = []
            for article in articles:
                source = article.get("source", "")
                title = article.get("title", "")
                content = article.get("content", "")
                link = article.get("link", "")
                short_link = article.get("short_link", "")
                published = article.get("published", "")
                if content:
                    results_parts.append(f"Source: {source}\nDate: {published}\nTitle: {title}\nContent: {content}\nLink: {link}")
                    titles.append(f"Title: {title}\nShort Link: {short_link}")

            results_str = "\n\n".join(results_parts)
            titles_str = "\n\n".join(titles)

            # Use super concise template as per user preference (or consistent with recent changes)
            prompt = DAILY_SUMMARY_TEMPLATE.format(results=titles_str, current_date=articles[0].get("published", datetime.now().date()))

            result_str = await action_to_use.generate(
                prompt=prompt,
                stream=False,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            if not result_str:
                return {}

            result_str = result_str.strip()
            if result_str.startswith("```"):
                result_str = result_str.strip("`").strip()
                if result_str.startswith("json"):
                    result_str = result_str[4:].strip()
            summary = json.loads(result_str)

            return summary

        except Exception as e:
            logger.error(f"Error summarizing news: {e}", exc_info=True)
            return None

    async def get_summary(self, date_filter: Optional[str] = None, model_action: Optional[OpenAILanguageModelAction] = None, news_source: Optional[str] = None) -> Dict[str, Any]:
        """Fetch and summarize news, managing cache.

        Args:
            date_filter: Optional date string
            model_action: Optional model action instance

        Returns:
            Dict dict with summary, date, cached status
        """
        try:
            today_date = datetime.now().date()
            target_date = today_date

            # Parse date_filter if provided
            if date_filter:
                date_filter = date_filter.lower().strip()
                fmt_date = self._detect_and_convert_date_format(date_filter, "%Y-%m-%d")
                if fmt_date:
                    target_date = datetime.strptime(fmt_date, "%Y-%m-%d").date()
                else:
                    try:
                        target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Could not parse date_filter '{date_filter}', defaulting to today")

            target_date_str = target_date.strftime("%Y-%m-%d")

            # Check cache
            if target_date_str in self.summary_cache:
                logger.info(f"Returning cached news summary for {target_date_str}")
                return {
                    "summary": self.summary_cache[target_date_str],
                    "date": target_date_str,
                    "from_cache": True
                }

            # If target date is NOT today, we cannot fetch RSS for it
            if target_date != today_date:
                return {
                    "summary": f"No summary available for {target_date_str}. I can only fetch current news.",
                    "date": target_date_str,
                    "from_cache": False
                }

            if news_source:
                articles = await self.fetch_rss_news(source=news_source)
            else:
                articles = await self.fetch_rss_news()

            if not articles:
                return {
                    "summary": "No news articles found for today.",
                    "date": target_date_str,
                    "from_cache": False
                }

            # Summarize
            summary = await self.summarize_news(articles, model_action=model_action)

            if news_source:
                # no caching for specificnews source
                return {
                    "summary": summary.get("summary", ""),
                    "links": summary.get("links", []),
                    "date": target_date_str,
                    "from_cache": False
                }

            if summary:
                # Cache the result
                self.summary_cache[target_date_str] = summary
                self.save_cache()
                logger.info(f"Cached news summary for {target_date_str}")

                return {
                    "summary": summary.get("summary", ""),
                    "links": summary.get("links", []),
                    "date": target_date_str,
                    "from_cache": False
                }
            else:
                 return {
                    "summary": "Failed to generate summary.",
                    "links": [],
                    "date": target_date_str,
                    "from_cache": False,
                    "error": "Summarization failed"
                }

        except Exception as e:
            logger.error(f"Error in get_summary: {e}", exc_info=True)
            return {
                "summary": "Error generating summary.",
                "links": [],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "from_cache": False,
                "error": str(e)
            }

    async def fetch_rss_news(self, source: str = "", query: str = "", specific_field: str = "", date_filter: str = "") -> List[Dict[str, Any]]:
        """Fetch news articles from RSS feeds.

        Returns:
            List of news articles with title, link, published, description, source
        """
        news_articles = []

        try:
            for source_name, feed_url in self.news_feeds.items():
                if source and source_name.lower() != source.lower():
                    continue
                n = 1
                feed = feedparser.parse(feed_url)

                for news_entry in feed.entries:
                    # Extract summary/description
                    soup = BeautifulSoup(news_entry.summary, 'html.parser')
                    summary = ""
                    if soup.find("p"):
                        summary = soup.find("p").get_text()
                    else:
                        summary = news_entry.summary

                    # Check if current date
                    published = news_entry.get("published", "").replace(" +0000", "")
                    if not published:
                        today = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
                        logger.warning(f"No published date found for {news_entry.title}. Using current datetime: {today}")
                        published = today
                    if not self._is_current_date(published, "%a, %d %b %Y %H:%M:%S"):
                        continue

                    if summary:
                        # Shorten URL
                        short_link = self.url_shortener.shorten(news_entry.link, news_entry.title)

                        news_articles.append({
                            "source": source_name,
                            "title": news_entry.title,
                            "link": news_entry.link,
                            "short_link": short_link,
                            "published": published,
                            "content": summary
                        })

                    if n >= self.max_articles:
                        break
                    n += 1

        except Exception as e:
            logger.error(f"Error parsing RSS feeds: {e}")

        return news_articles

    def _is_current_date(self, date_str: str, date_format: str = "") -> bool:
        """Check if a date string is today's date.

        Args:
            date_str: Date string to check
            date_format: Format of the date string

        Returns:
            True if the date is today, False otherwise
        """
        try:
            if not date_format:
                # Try common formats
                date_str = self._detect_and_convert_date_format(date_str, "%a, %d %b %Y")
                date_format = "%a, %d %b %Y"

            input_date = datetime.strptime(date_str, date_format).date()
            today = datetime.now().date()
            return input_date == today
        except ValueError:
            logger.debug(f"Could not parse date: {date_str}")
            return False

    def _detect_and_convert_date_format(self, date_str: str, new_format: str = "%a, %d %b %Y") -> str:
        """Try to detect the format of date_str and convert it to new_format.

        Args:
            date_str: Date string to convert
            new_format: Target format

        Returns:
            Converted date string
        """
        common_formats = [
            "%a, %d %b %Y %H:%M:%S",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%b %d, %Y",
            "%B %d, %Y",
            "%d %b %Y",
            "%Y.%m.%d",
            "%m/%d/%Y",
            "%a, %d %b %Y",
            "%d %B %Y"
        ]

        for fmt in common_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(new_format)
            except ValueError:
                continue

        logger.warning(f"Could not detect date format for: {date_str}")
        return ""


    async def _get_openai_api_key(self) -> str:
        """Retrieve OpenAI API key from agent settings."""
        if self.agent_id:
            prime_db = get_prime_database()
            context = GraphContext(database=prime_db)
            existing_key = await context.get(APIKey, self.webhook_api_key_id)
            # agent = await context.get(Agent, self.agent_id)
            if existing_key:
                return existing_key.key or ""
        return ""

class URLShortener:
    """Handles URL shortening and redirection."""

    def __init__(self, filename="url_map.json"):
        self.filename = os.path.join(os.path.dirname(__file__), filename)
        self.url_map = {}
        self.load_map()

    def load_map(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.url_map = json.load(f)
            except Exception as e:
                logger.error(f"Error loading URL map: {e}")

    def save_map(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.url_map, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving URL map: {e}")

    def shorten(self, url: str, title: str) -> str:
        """Create a short URL code based on title words."""
        # Check if URL already exists
        for code, mapped_url in self.url_map.items():
            if mapped_url == url:
                return f"{NewsFetcher.base_url}/api/n/{code}"

        # Clean title to get first 2 words
        import re
        import random
        import string

        # Remove special chars and extra spaces
        clean_title = re.sub(r'[^\w\s]', '', title)
        words = clean_title.split()

        slug_parts = []
        for word in words[:2]:
            slug_parts.append(word.lower())

        slug_base = "-".join(slug_parts) if slug_parts else "news"

        # Add random suffix for uniqueness
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        code = f"{slug_base}-{suffix}"

        # Check for collision (unlikely with random suffix, but good practice)
        while code in self.url_map:
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            code = f"{slug_base}-{suffix}"

        self.url_map[code] = url
        self.save_map()

        return f"{NewsFetcher.base_url}/api/n/{code}"

    def get_original(self, code: str) -> Optional[str]:
        return self.url_map.get(code)

# Global fetcher instance
news_fetcher = NewsFetcher()


@endpoint(
    "/news/fetch",
    methods=["GET"],
    auth=False,  # Anonymous access for news fetching
    tags=["News"],
    response=success_response(
        data={
            "articles": ResponseField(
                field_type=List[Dict[str, Any]],
                description="List of news articles",
                example=[
                    {
                        "source": "stabroek news",
                        "title": "Breaking News Story",
                        "link": "https://example.com/article",
                        "published": "Mon, 01 Jan 2024 12:00:00",
                        "content": "Article summary text..."
                    }
                ]
            ),
            "total": ResponseField(
                field_type=int,
                description="Total number of articles fetched",
                example=25
            )
        }
    ),
)
async def fetch_news(
    max_articles: Optional[int] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch news articles from RSS feeds.

    This endpoint fetches current news articles from various Guyanese news sources
    via RSS feeds. Articles are fetched fresh on each request and not stored.

    **Features:**
    - Fetches from multiple RSS feeds simultaneously
    - Filters to current date articles only
    - Extracts clean article summaries
    - No data persistence - fresh fetch each time

    **Args:**
    - max_articles: Maximum articles per source (optional, default: 5)
    - source: Specific source to fetch from (optional, fetches all if not specified)

    **Returns:**
    Dictionary containing:
    - **articles**: List of article objects with source, title, link, published, description
    - **total**: Total number of articles fetched

    **Supported Sources:**
    - Stabroek News
    - News Room GY
    - Guyana Times - Not currently working
    - Guyana Chronicle
    - Demerara Waves
    - iNews Guyana
    - HGPTV
    - Kaieteur News
    - News Source - Not currently working

    """
    try:
        # Update max_articles if provided
        if max_articles is not None:
            news_fetcher.max_articles = max(1, min(max_articles, 40))  # Limit to reasonable range

        # Fetch news
        if source and source in news_fetcher.news_feeds:
            # Fetch from specific source
            articles = await news_fetcher.fetch_rss_news()
            articles = [a for a in articles if a["source"] == source]
        else:
            # Fetch from all sources
            articles = await news_fetcher.fetch_rss_news()

        return {
            "articles": articles,
            "total": len(articles)
        }

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return {
            "articles": [],
            "total": 0,
            "error": str(e)
        }


@endpoint(
    "/n/{code}",
    methods=["GET"],
    auth=False,
    tags=["News"],
    response=success_response(
        data={
            "status": ResponseField(
                field_type=str,
                description="Redirect status",
                example="redirecting"
            ),
            "url": ResponseField(
                field_type=str,
                description="Original URL",
                example="https://example.com"
            )
        }
    )
)
async def redirect_short_url(code: str) -> Any:
    """Redirect a short URL code to the original long URL."""
    try:
        original_url = news_fetcher.url_shortener.get_original(code)
        logger.info(f"Redirecting short URL {code} to {original_url}")

        if original_url:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=original_url)
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Short URL not found")

    except Exception as e:
        logger.error(f"Error in short URL redirect: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Error redirecting")


@endpoint(
    "/news/cache-summary",
    methods=["POST"],
    auth=False,
    tags=["News"],
    response=success_response(
        data={
            "summary": ResponseField(
                field_type=str,
                description="Cached summary of news articles",
                example="Today's news highlights include..."
            ),
            "links": ResponseField(
                field_type=list,
                description="List of links to news articles",
                example=["https://example.com/article1", "https://example.com/article2"]
            ),
            "date": ResponseField(
                field_type=str,
                description="Date of the summary",
                example="2024-01-01"
            ),
            "from_cache": ResponseField(
                field_type=bool,
                description="Whether the response was served from cache",
                example=True
            )
        }
    )
)
async def cache_news_summary(
    categories: Optional[List[str]] = None,
    date_filter: Optional[str] = None,
    agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """Fetch, summarize, and cache news articles.

    This endpoint fetches news, summarizes it using an LLM, and caches the result
    keyed by the current date. Future requests for the same date return the cached summary.

    **Args:**
    - categories: Optional list of categories to focus the summary on.
    - date_filter: Optional specific date to retrieve summary for (e.g. "today", "yesterday", "2024-01-01").
    - agent_id: Optional agent ID to retrieve OpenAI API key from.

    **Returns:**
    - **summary**: The generated news summary.
    - **date**: The date key for the cache.
    - **from_cache**: Boolean indicating if result was from cache.
    """
    return await news_fetcher.get_summary(date_filter=date_filter)


# Auto-start the news scheduler when this module loads
# news_fetcher.start_scheduler()
