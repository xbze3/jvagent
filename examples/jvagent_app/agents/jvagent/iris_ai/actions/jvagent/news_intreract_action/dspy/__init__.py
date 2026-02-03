"""DSPy integration for persona response generation.

This module provides DSPy signatures and modules for generating persona responses
with optimization capabilities via DSPy teleprompters.
"""

from jvagent.action.news.dspy.modules import DailyNewsModule, NewsSummaryModule
from jvagent.action.news.dspy.signatures import create_news_summary_signature

__all__ = ["DailyNewsModule", "NewsSummaryModule", "create_news_summary_signature"]
