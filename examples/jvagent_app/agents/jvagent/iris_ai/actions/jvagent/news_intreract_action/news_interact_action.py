"""NewsInteractAction for fetching and summarizing news articles.

This module provides NewsInteractAction, an InteractAction that fetches
current news articles from RSS feeds, summarizes them using a language model,
and composes a structured directive for PersonaAction.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime

import dspy

from jvspatial.core.annotations import attribute

from jvagent.action.interact.base import InteractAction
from jvagent.action.interact.interact_walker import InteractWalker
from jvagent.action.model.language.base import LanguageModelAction
from .endpoints import news_fetcher, cache_news_summary
from .prompts import DIRECTIVE_TEMPLATE, SUMMARY_TEMPLATE, LINKS_TEMPLATE, DAILY_SUMMARY_TEMPLATE

if TYPE_CHECKING:
    from jvagent.memory.interaction import Interaction

logger = logging.getLogger(__name__)


class NewsInteractAction(InteractAction):
    """InteractAction that fetches news articles and creates directives.

    NewsInteractAction:
    1. Fetches current news articles from RSS feeds
    2. Summarizes the articles using DSPy or legacy language model calls
    3. Formats the summary into a structured directive
    4. Adds the directive to the interaction for PersonaAction to use

    Attributes:
        model_action_type: Type of LanguageModelAction to use for summarization
        model: Optional model identifier to override
        model_temperature: Temperature for LLM generation
        model_max_tokens: Maximum tokens for LLM generation
        use_dspy: Whether to use DSPy for summarization (default: True)
        weight: Execution weight (default: -50, runs after InteractRouter but before PersonaAction)
        summary_template: Template for formatting the summary prompt
        directive: Template for formatting the directive with placeholder: {summary}
        parameters: List of conditions and responses for customizing behavior
    """

    model_action_type: str = attribute(
        default="OpenAILanguageModelAction",
        description="Type of LanguageModelAction to use for summarization (e.g., 'OpenAILanguageModelAction')."
    )
    model: Optional[str] = attribute(
        default="gpt-4o",
        description="Model identifier to use for summarization."
    )
    model_temperature: float = attribute(
        default=0.1,
        description="Temperature for LLM summarization."
    )
    model_max_tokens: int = attribute(
        default=1000,
        description="Max tokens for LLM summarization."
    )
    use_dspy: bool = attribute(
        default=True,
        description="Whether to use DSPy for summarization."
    )
    weight: int = attribute(
        default=-50,
        description="Execution weight (runs after InteractRouter but before other Interact Actions)",
    )
    summary_template: str = attribute(
        default=SUMMARY_TEMPLATE,
        description="Template for formatting the summary prompt. Placeholder: {results}",
    )
    links_template: str = attribute(
        default=LINKS_TEMPLATE,
        description="Template for formatting the links prompt. Placeholder: {links}",
    )
    directive_template: str = attribute(
        default=DIRECTIVE_TEMPLATE,
        description="Template for formatting the directive. Placeholder: {summary}",
    )
    parameters: List[Dict[str, Any]] = attribute(
        default=[{"condition":"There is no news summary","response": "Apologize and inform the user that you were unable to get the news but they can try again later."}],
        description="A list of conditions and response to customize behavior based on parameters."
    )


    def __init__(self, *args, **kwargs):
        """Initialize PersonaAction."""
        super().__init__(*args, **kwargs)
        # Cache DSPy module instance for reuse across calls
        self._dspy_module = None

    async def send_news(self, summary: str) -> None:
        """Respond to the user with the summary at scheduled time."""
        logger.info(f"NewsInteractAction: Responding with summary: {summary}")
        agent = await self.get_agent()
        from jvagent.memory.user import User

        memory_node = await agent.node(node="Memory")
        user_node = await memory_node.nodes(node=User)
        conversations = await user_node[0].list_conversations()
        interaction = await conversations[0].get_first_interaction()
        session_id = getattr(interaction, "session_id", None)
        logger.debug(f"session_id: {session_id}")

        interaction_attributes = interaction.id
        logger.debug(f"interaction_attributes: {interaction_attributes}")

        current_interaction = await conversations[0].create_interaction(utterance='daily news summary')
        logger.debug(f"current_interaction: {current_interaction}")

        current_interaction.set_response(summary)
        await current_interaction.save()
        # await self.respond(
        #     visitor=conversations[0],
        #     directives=[summary] if summary else None,
        #     parameters=self.parameters if self.parameters else None
        # )


    async def execute(self, visitor: "InteractWalker") -> None:
        """Execute news fetching, summarization, and add directive to interaction.

        Args:
            visitor: The InteractWalker visiting this action
        """
        interaction = visitor.interaction
        if not interaction:
            logger.warning("NewsInteractAction: No interaction available")
            return

        try:
            # Extract user intent
            user_input = visitor.utterance
            intent = await self._extract_intent(user_input, interaction) if user_input else {}

            target_source = intent.get("source", "")
            query = intent.get("query", "")
            date_filter = intent.get("date_filter", "")

            # Get model action for summarization/intent extraction
            model_action = await self.get_model_action()
            if not model_action:
                logger.warning("NewsInteractAction: Model action not found")
                return

            # Fetch news articles
            logger.debug(f"NewsInteractAction: Checking for news (Source: {target_source})")

            # Use current date or date_filter
            today_date_str = datetime.now().strftime("%Y-%m-%d")
            check_date = date_filter if date_filter else today_date_str

            cached_data = news_fetcher.summary_cache.get(check_date)

            if cached_data and not (target_source or query):
                logger.info(f"NewsInteractAction: Found cached summary for {check_date}")
                summary_content = cached_data
            elif (not target_source) and (not query):
                # If no cached summary and no specific source/field, use the general summary cache
                summary_content = await news_fetcher.get_summary(check_date)
                logger.info(f"NewsInteractAction: Created cached summary for {check_date}")
            elif target_source or query:
                # Inform user that we are gathering news articles as this process may take a while
                await self.publish(visitor, content="Please wait while I gather the relevant news articles.")

                articles = await news_fetcher.fetch_rss_news(source=target_source)

                # Format articles for summarization
                results_parts = []
                for article in articles:
                    source = article.get("source", "")
                    title = article.get("title", "")
                    content = article.get("content", "")
                    link = article.get("link", "")
                    short_link = article.get("short_link", "")
                    published = article.get("published", "")

                    if content:
                        results_parts.append(f"Source: {source}\nDate: {published}\nTitle: {title}\nContent: {content}\nLink: {link}\nShort Link: {short_link}")

                results_str = "\n\n".join(results_parts)

                if not results_str:
                    # No articles to summarize
                    directive = "No news articles found matching the user's criteria."
                else:
                    # Summarize
                    if self.use_dspy:
                        summary_content = await self._summarize_with_dspy(results_str, interaction)
                        if summary_content is None:
                            logger.warning("NewsInteractAction: DSPy summarization failed, falling back to legacy")
                            summary_content = await self._summarize_legacy(results_str, model_action, visitor)
                    else:
                        summary_content = await self._summarize_legacy(results_str, model_action, visitor)

                        if not summary_content:
                            logger.warning("NewsInteractAction: Failed to generate summary")
                            return

            if isinstance(summary_content, dict):
                summary = summary_content.get("summary", "")
                links = summary_content.get("links", "")

                logger.debug("NewsInteractAction: Prepared directive")

                await self.publish(
                    visitor,
                    content=summary,
                    message_type="adhoc"
                )

                links_directive = self.links_template.format(links=links)
                links_string = "\n\n".join(links)
                links_string = "Check out the following links for more information:\n\n" + links_string
                logger.debug(f"NewsInteractAction: Prepared links: {links_string}")

                # await self.publish(
                #     visitor,
                #     content=links_string,
                #     message_type="adhoc"
                # )

                await self.respond(
                    visitor,
                    directives=[links_directive] if links else None,
                    parameters=self.parameters if self.parameters else None
                )
            elif isinstance(summary_content, str):
                directive = self.directive_template.format(summary=summary_content)

                await self.respond(
                    visitor,
                    directives=[directive],
                    parameters=self.parameters if self.parameters else None
                )

        except Exception as e:
            logger.error(f"NewsInteractAction: Error during news fetching and summarization: {e}", exc_info=True)


    async def _extract_intent(self, user_input: str, interaction: "Interaction") -> Dict[str, Any]:
        """Extract user intent using LLM.

        Args:
            user_input: The user's input text
            interaction: Current interaction context

        Returns:
            Dictionary with k specific field was requested, we might want to adjust the prompt?
                    For now,eys: query, source, specific_field, date_filter
        """
        try:
            model_action = await self.get_model_action()
            if not model_action:
                return {}

            from .prompts import INTENT_EXTRACTION_TEMPLATE
            prompt = INTENT_EXTRACTION_TEMPLATE.format(sources=news_fetcher.news_feeds.keys(), current_date=datetime.now().strftime("%a, %d %b %Y"))

            # Extract intent
            result_str = await model_action.generate(
                prompt=user_input,
                stream=False,
                system=prompt,
                model=self.model,
                temperature=self.model_temperature,
                max_tokens=self.model_max_tokens,
                response_format={"type": "json_object"}
            )
            logger.debug(f"result_str: {result_str}")

            if not result_str:
                return {}

            result_str = result_str.strip()
            if result_str.startswith("```"):
                result_str = result_str.strip("`").strip()
                if result_str.startswith("json"):
                    result_str = result_str[4:].strip()
            return json.loads(result_str)


        except Exception as e:
            logger.error(f"NewsInteractAction: Error extracting intent: {e}")
            return {}

    async def _summarize_with_dspy(self, results_str: str, interaction: "Interaction") -> Optional[str]:
        """Summarize news articles using DSPy.

        Args:
            results_str: Formatted string of news articles

        Returns:
            Summary string or None on error
        """
        try:
            import dspy
            from jvagent.action.model.dspy import DSPyLM
            from jvagent.action.news.dspy import NewsSummaryModule
            # Get model action
            model_action = await self.get_model_action(required=True)
            if not model_action:
                logger.warning("NewsInteractAction: Could not get model action for DSPy summarization")
                return None

            # Create DSPy LM adapter
            lm = DSPyLM(
                model_action=model_action,
                model_type="chat",
                model=self.model,
                temperature=self.model_temperature,
                max_tokens=self.model_max_tokens,
                cache=False,
            )

            # Create a simple summarization module
            if self._dspy_module is None:
                self._dspy_module = NewsSummaryModule(action_instance=self)

            module = self._dspy_module

            # Set LM on module for module-level configuration
            module.set_lm(lm)

            # Configure DSPy with explicit adapter and LM
            from dspy.adapters import ChatAdapter
            # ChatAdapter defaults to use_json_adapter_fallback=True, so we can use default
            adapter = ChatAdapter()

            # Configure DSPy with the adapter
            with dspy.context(lm=lm, adapter=adapter):
                result = await module.aforward(news_articles=results_str)
                print(f"\033[92mresult: {result}\033[0m")
                return result

        except Exception as e:
            logger.error(f"NewsInteractAction: Failed to summarize via DSPy: {e}", exc_info=True)
            return None

    async def _summarize_legacy(self, results_str: str, model_action: Any, visitor: "InteractWalker") -> Optional[str]:
        """Summarize news articles using legacy prompt-based approach.

        Args:
            results_str: Formatted string of news articles
            model_action: The LanguageModelAction instance to use

        Returns:
            Summary string or None on error
        """
        try:
            # Build summary prompt
            prompt = self.summary_template.format(results=results_str)

            # Determine model parameters
            model_param = self.model if self.model is not None else getattr(model_action, "model", None)
            temperature = self.model_temperature
            max_tokens = self.model_max_tokens

            summary = await model_action.generate(
                prompt=visitor.utterance,
                stream=False,
                system=prompt,
                calling_action_name=self.get_class_name(),
                model=model_param,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return summary

        except Exception as e:
            logger.error(f"NewsInteractAction: Failed to summarize via legacy path: {e}", exc_info=True)
            return None
