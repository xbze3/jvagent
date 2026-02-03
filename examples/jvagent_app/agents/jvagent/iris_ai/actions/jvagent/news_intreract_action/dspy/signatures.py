"""DSPy signatures for persona response generation.

This module defines typed DSPy signatures that model all elements of the persona prompt,
enabling DSPy to optimize directive and parameter following.
"""

import logging
from typing import Optional, Type

logger = logging.getLogger(__name__)


def create_news_summary_signature(docstring: str) -> Type:
    """Factory function to create NewsSummary signature with custom docstring.

    Args:
        docstring: The docstring to use for the signature class

    Returns:
        A dynamically created signature class with the provided docstring
    """
    try:
        import dspy
    except Exception as e:
        logger.error(f"Failed to import dspy in create_persona_response_signature: {e}")
        raise

    try:
        class NewsSummary(dspy.Signature):
            __doc__ = docstring

            # Core inputs - Agent Identity
            titles: str = dspy.InputField(desc="The titles of various news articles")

            # Output
            response: str = dspy.OutputField(
                desc="Response that faithfully incorporates all applicable directives and parameters. Before finalizing, verify: all directives executed naturally within persona, all applicable parameters applied, no repetition of previous messages, response grounded in provided information (no hallucinations), natural conversational tone maintained, end cleanly without unnecessary closings unless conversation is finished."
            )

        return NewsSummary
    except Exception as e:
        logger.error(f"Failed to create NewsSummary signature: {e}", exc_info=True)
        raise

def create_daily_news_summary_signature(docstring: str) -> Type:
    """Factory function to create NewsSummary signature with custom docstring.

    Args:
        docstring: The docstring to use for the signature class

    Returns:
        A dynamically created signature class with the provided docstring
    """
    try:
        import dspy
    except Exception as e:
        logger.error(f"Failed to import dspy in create_persona_response_signature: {e}")
        raise

    try:
        class DailyNewsSummary(dspy.Signature):
            __doc__ = docstring

            # Core inputs - Agent Identity
            titles: str = dspy.InputField(desc="The titles of various news articles")
            date: str = dspy.InputField(desc="Current date (e.g., 'Monday, 15 January, 2024')")

            # Output
            response: str = dspy.OutputField(
                desc="Response that faithfully incorporates all applicable directives and parameters. Before finalizing, verify: all directives executed naturally within persona, all applicable parameters applied, no repetition of previous messages, response grounded in provided information (no hallucinations), natural conversational tone maintained, end cleanly without unnecessary closings unless conversation is finished."
            )

        return DailyNewsSummary
    except Exception as e:
        logger.error(f"Failed to create DailyNewsSummary signature: {e}", exc_info=True)
        raise
