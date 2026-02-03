"""DSPy modules for persona response generation.

This module provides DSPy Module classes that can be optimized using
DSPy's teleprompters and evaluators.
"""

import logging
from typing import Any, Dict, List, Optional

import dspy

from jvagent.action.news.dspy.signatures import create_news_summary_signature
from jvagent.action.news.prompts import DAILY_SUMMARY_TEMPLATE, SUMMARY_TEMPLATE

logger = logging.getLogger(__name__)


class DailyNewsModule(dspy.Module):
    """DSPy module for generating daily news summaries with complete prompt element modeling.

    This module uses a DSPy ChainOfThought module with the DailyNews signature to generate
    responses with step-by-step reasoning. It can be optimized using DSPy's teleprompters
    (BootstrapFewShot, MIPROv2, etc.) to improve directive and parameter following consistency.

    Example:
        >>> module = DailyNewsModule()
        >>> response = await module.aforward(
        ...     news_articles=[{"title": "news title", "link": "link to article"}],
        ...     date="Monday, 15 January, 2024"
        ... )
    """

    def __init__(self, action_instance=None):
        """Initialize the module with a ChainOfThought module for better reasoning.

        Args:
            action_instance: Optional NewsAction instance. If provided,
                uses the signature docstring from action_instance.news_summary_signature.
                If None, uses the default from prompts.py.
        """
        super().__init__()
        if action_instance and hasattr(action_instance, 'news_summary_signature'):
            docstring = action_instance.news_summary_signature
        else:
            docstring = DAILY_SUMMARY_TEMPLATE
        signature_class = create_news_summary_signature(docstring)
        self.generate = dspy.ChainOfThought(signature_class)

    async def aforward(
        self,
        news_articles: List[str],
        date: str
    ) -> str:
        """Generate response using DSPy with all prompt elements.

        Args:
            news_articles: List of news article titles

        Returns:
            Generated response string
        """
        try:
            classify_kwargs = {
                "news_articles": news_articles
            }

            # Call DSPy ChainOfThought module (use acall for async)
            prediction = await self.generate.acall(**classify_kwargs)

            # ChainOfThought adds a 'reasoning' field along with 'response'
            # We need to extract only the 'response' field, not the reasoning
            # Handle different types: Prediction object, dict, or string
            if isinstance(prediction, str):
                # If prediction is already a string, use it directly
                response = prediction
            elif hasattr(prediction, 'response'):
                # Prediction object with response attribute
                response = prediction.response
            elif isinstance(prediction, dict) and 'response' in prediction:
                # Dictionary with response key
                response = prediction['response']
            elif hasattr(prediction, '__getitem__') and 'response' in prediction:
                # Object that supports dictionary-like access
                response = prediction['response']
            else:
                # Fallback: try to get response from prediction store
                response = None
                if hasattr(prediction, 'get'):
                    response = prediction.get('response', None)
                if response is None:
                    response = getattr(prediction, 'response', None)
                if response is None:
                    logger.warning(
                        f"NewsSummaryModule: Prediction does not contain 'response' field. "
                        f"Prediction type: {type(prediction)}, "
                        f"Available fields: {list(prediction.keys()) if hasattr(prediction, 'keys') else 'unknown'}"
                    )
                    # If no response field, use the prediction string representation
                    response = str(prediction)

            return response

        except Exception as e:
            logger.error(
                f"NewsSummaryModule: Error during response generation: {e}",
                exc_info=True
            )
            raise


class NewsSummaryModule(dspy.Module):
    """DSPy module for generating daily news summaries with complete prompt element modeling.

    This module uses a DSPy ChainOfThought module with the DailyNews signature to generate
    responses with step-by-step reasoning. It can be optimized using DSPy's teleprompters
    (BootstrapFewShot, MIPROv2, etc.) to improve directive and parameter following consistency.

    Example:
        >>> module = NewsSummaryModule()
        >>> response = await module.aforward(
        ...     news_articles=[{"title": "news title", "link": "link to article"}],
        ... )
    """

    def __init__(self, action_instance=None):
        """Initialize the module with a ChainOfThought module for better reasoning.

        Args:
            action_instance: Optional NewsAction instance. If provided,
                uses the signature docstring from action_instance.news_summary_signature.
                If None, uses the default from prompts.py.
        """
        super().__init__()
        if action_instance and hasattr(action_instance, 'news_summary_signature'):
            docstring = action_instance.news_summary_signature
        else:
            docstring = SUMMARY_TEMPLATE
        signature_class = create_news_summary_signature(docstring)
        self.generate = dspy.ChainOfThought(signature_class)

    async def aforward(
        self,
        news_articles: List[str]
    ) -> str:
        """Generate response using DSPy with all prompt elements.

        Args:
            news_articles: List of news article titles

        Returns:
            Generated response string
        """
        try:
            classify_kwargs = {
                "news_articles": news_articles
            }

            # Call DSPy ChainOfThought module (use acall for async)
            prediction = await self.generate.acall(**classify_kwargs)

            # ChainOfThought adds a 'reasoning' field along with 'response'
            # We need to extract only the 'response' field, not the reasoning
            # Handle different types: Prediction object, dict, or string
            if isinstance(prediction, str):
                # If prediction is already a string, use it directly
                response = prediction
            elif hasattr(prediction, 'response'):
                # Prediction object with response attribute
                response = prediction.response
            elif isinstance(prediction, dict) and 'response' in prediction:
                # Dictionary with response key
                response = prediction['response']
            elif hasattr(prediction, '__getitem__') and 'response' in prediction:
                # Object that supports dictionary-like access
                response = prediction['response']
            else:
                # Fallback: try to get response from prediction store
                response = None
                if hasattr(prediction, 'get'):
                    response = prediction.get('response', None)
                if response is None:
                    response = getattr(prediction, 'response', None)
                if response is None:
                    logger.warning(
                        f"NewsSummaryModule: Prediction does not contain 'response' field. "
                        f"Prediction type: {type(prediction)}, "
                        f"Available fields: {list(prediction.keys()) if hasattr(prediction, 'keys') else 'unknown'}"
                    )
                    # If no response field, use the prediction string representation
                    response = str(prediction)

            return response

        except Exception as e:
            logger.error(
                f"NewsSummaryModule: Error during response generation: {e}",
                exc_info=True
            )
            raise
