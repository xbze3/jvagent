# Iris AI Agent

Iris is a witty, citizen-companion AI designed to provide helpful information, daily news summaries, and engaging conversation, with a specific focus on knowledge about Guyana.

## Overview

Iris interacts with users primarily through WhatsApp, acting as a personal assistant that is both knowledgeable and personable.

**Key Features:**
- **Daily News Summaries**: Automatically fetches RSS news feeds, summarizes them using LLMs, and delivers them with shortened links.
- **WhatsApp Integration**: Full 2-way messaging support via WhatsApp (sending and receiving).
- **Knowledge Retrieval**: Utilizes a vector store (Typesense) to answer questions with specific context about Guyana.
- **Persona-Driven**: Maintains a consistent "witty and bubbly" personality.

## Structure

```
iris_ai/
├── actions/              # Local actions specific to Iris
│   └── jvagent/
│       ├── news/         # News fetching, summarization, and URL shortening
│       ├── persona/      # Local persona extensions
│       └── ...
├── agent.yaml            # Main configuration and action wiring
└── README.md             # This file
```

## Configuration

### Environment Variables

Ensure the following environment variables are set in your `.env` file:

- `OPENAI_API_KEY`: Required for the LLM (GPT-4o) and embeddings.
- `TYPESENSE_API_KEY`: Required for the vector store knowledge base.

### Agent Configuration (`agent.yaml`)

The `agent.yaml` defines the agent's behavior and connects its actions.

**Key Actions Configured:**

- **`jvagent/whatsapp`**: Connects to the WhatsApp provider (e.g., `wwebjs`).
  - *Provider*: `wwebjs` (or `ultramsg`/`wppconnect`)
  - *Session*: `Iris`
  - *Base URL*: Your secure tunnel URL (e.g., ngrok) for webhooks.

- **`jvagent/news_interact_action`**: Handles "get news" requests.
  - *Anchors*: Triggers on phrases like "What's the latest news?" or "User requests news articles".

- **`jvagent/retrieval_interact_action`**: RAG capability.
  - *Collection*: Queries the configured Typesense collection for persistent knowledge.

- **`jvagent/persona`**: Defines the "Iris" personality.
  - *Model*: `gpt-4o-mini` with a low temperature for consistent character.

## Usage

### Starting the Agent

1.  Ensure your WhatsApp provider service (e.g., `wwebjs-api`) is running and the session `Iris` is connected.
2.  Start the jvagent application.
3.  Iris will be available to respond to messages sent to the connected WhatsApp number.

### Interaction Examples

- **News**: "What's the news today?" or "Give me a summary of the latest headlines."
    - *Iris will respond with a summarized list of articles and short links.*
- **General Knowledge**: "Tell me about Kaieteur Falls."
    - *Iris will search its vector store and provide a contextual answer.*
- **Chat**: "How are you doing today?"
    - *Iris will respond with her signature witty personality.*

## Troubleshooting

- **WhatsApp Connection**: If Iris doesn't respond, check the provider logs (`wwebjs`) to ensure the session `Iris` is `CONNECTED`.
- **Webhook Errors**: Ensure your `base_url` in `agent.yaml` matches your active ngrok tunnel and that the webhook endpoint is reachable.
- **News Errors**: If news isn't fetching, check the logs for RSS feed accessibility or specific error messages from the `news` action.
