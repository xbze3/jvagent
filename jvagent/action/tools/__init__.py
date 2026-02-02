"""Parameter-bound tools module.

This module provides ToolContext and ToolResult for parameter-bound tool execution,
enabling tools to be attached to parameters and executed when those parameters match.
"""

from jvagent.action.tools.context import ToolContext
from jvagent.action.tools.result import ToolResult

__all__ = ["ToolContext", "ToolResult"]
