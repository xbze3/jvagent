# NewsInteractAction

NewsInteractAction is a specialized InteractAction that fetches, filters, and summarizes news from specific RSS feeds (focused on Guyana), providing the agent with up-to-date information to share with users.

## Overview

This action enables the agent to:
1.  **Fetch News**: Retrieve articles from a curated list of RSS feeds (e.g., Stabroek News, News Room).
2.  **Summarize**: Use an LLM to generate concise summaries of current events.
3.  **Shorten Links**: Generate internal short URLs for articles to keep messages clean.
4.  **Cache**: Store daily summaries to minimize API usage and latency.
5.  **Schedule**: Automatically fetch and discuss news at specific times (configured via `NewsFetcher`).

## Architecture

### Components

-   **`NewsInteractAction`**: The main interface for the agent. It interprets user intent (e.g., "get news"), retrieves the summary (fresh or cached), and adds it to the conversation.
-   **`NewsFetcher` (in `endpoints.py`)**: A singleton helper class that handles:
    -   Parsing RSS feeds using `feedparser`.
    -   Filtering articles by date.
    -   Managing the `summary_cache.json`.
    -   Running the background scheduler.
-   **`URLShortener`**: Maps long article URLs to short codes (e.g., `/api/n/news-xyz123`) for easier sharing.

### Flow

1.  **User Request**: "What's the news today?"
2.  **Routing**: `InteractRouter` routes to `NewsInteractAction`.
3.  **Check Cache**: Action checks `summary_cache.json` for today's date.
4.  **Fetch (if miss)**: `NewsFetcher` pulls RSS feeds, filters for today's articles.
5.  **Summarize**: LLM (GPT-4o) generates a JSON summary with headlines and short links.
6.  **Respond**: Agent presents the summary to the user.

## Configuration

### Action Attributes

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model_action_type` | str | `"OpenAILanguageModelAction"` | The entity type for the LLM action. |
| `model` | str | `"gpt-4o"` | The specific model to use for summarization. |
| `model_temperature` | float | `0.1` | Low temperature for factual consistency. |
| `use_dspy` | bool | `True` | Whether to use DSPy for optimized prompt handling. |
| `parameters` | list | `[...]` | Fallback responses (e.g., if no news is found). |

### RSS Sources (Hardcoded in `endpoints.py`)

-   Stabroek News
-   News Room
-   Guyana Times
-   Guyana Chronicle
-   Demerara Waves
-   iNews Guyana
-   HGPTV
-   Kaieteur News
-   News Source

To modify sources, edit the `news_feeds` dictionary in `jvagent/news/endpoints.py`.

## Endpoints

### `GET /api/n/{code}`
Redirects a short URL code (e.g., `news-abc1`) to the original article URL.
-   **Response**: `307 Temporary Redirect`

### `GET /api/news/fetch`
*Debug Endpoint*. Forces a fresh fetch of articles from the RSS feeds.
-   **Query Params**: `source` (optional), `max_articles` (optional)

## Usage

### Agent Configuration (`agent.yaml`)

```yaml
  - action: jvagent/news_interact_action
    context:
      enabled: true
      description: "Retrieves news articles and creates a summary"
      weight: -50
      anchors:
        - "User requests news articles"
        - "What is the news"
        - "Latest headlines"
```

### Automatic Scheduling
The `NewsFetcher` starts a background scheduler (if enabled in `endpoints.py`) to fetch news automatically at a specific time (default `10:40`).

## Dependencies

-   `feedparser`: For RSS parsing.
-   `beautifulsoup4`: For cleaning HTML content.
-   `schedule`: For background task scheduling.
-   `fastapi`: For the redirect endpoints.
