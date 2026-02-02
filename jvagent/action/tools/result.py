"""ToolResult for parameter-bound tool execution.

Provides result encapsulation for tools attached to parameters, supporting
data, metadata, and control directives similar to Parlant's ToolResult.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ToolResult:
    """Result returned by parameter-bound tools.
    
    Encapsulates the result of a tool execution with optional metadata
    and control directives.
    
    Attributes:
        data: Main result data (JSON-serializable)
        metadata: Optional metadata (e.g., sources, URLs, for frontend display)
        control: Optional control directives (e.g., lifespan, mode)
    """
    
    def __init__(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        control: Optional[Dict[str, Any]] = None,
    ):
        """Initialize tool result.
        
        Args:
            data: Main result data (required, JSON-serializable)
            metadata: Optional metadata about the result
            control: Optional control directives (lifespan, mode)
        """
        self.data = data
        self.metadata = metadata or {}
        self.control = control or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage.
        
        Returns:
            Dict representation of the result
        """
        return {
            "data": self.data,
            "metadata": self.metadata,
            "control": self.control,
        }
    
    def get_lifespan(self) -> str:
        """Get the lifespan setting from control.
        
        Returns:
            "session" (default) or "response"
        """
        return self.control.get("lifespan", "session")
    
    def get_mode(self) -> Optional[str]:
        """Get the mode setting from control (e.g., for session mode changes).
        
        Returns:
            Mode string if set, None otherwise
        """
        return self.control.get("mode")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        """Create ToolResult from dictionary.
        
        Args:
            data: Dictionary with data, metadata, control keys
        
        Returns:
            ToolResult instance
        """
        return cls(
            data=data.get("data"),
            metadata=data.get("metadata"),
            control=data.get("control"),
        )
