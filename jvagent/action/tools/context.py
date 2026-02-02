"""ToolContext for parameter-bound tool execution.

Provides context information and utilities for tools attached to parameters.
Similar to Parlant's ToolContext but adapted for jvagent's architecture.
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from jvagent.memory.conversation import Conversation
    from jvagent.memory.interaction import Interaction
    from jvagent.core.agent import Agent

logger = logging.getLogger(__name__)


class ToolContext:
    """Context provided to parameter-bound tools during execution.
    
    Provides access to session information, user context, and utilities
    for emitting messages or status updates during tool execution.
    
    Attributes:
        session_id: Session identifier
        user_id: User identifier
        agent_id: Agent identifier
        conversation: Conversation node (for accessing history, context)
        interaction: Current interaction node
        conversation_id: Conversation identifier
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        agent_id: str,
        conversation: Optional["Conversation"] = None,
        interaction: Optional["Interaction"] = None,
    ):
        """Initialize tool context.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            agent_id: Agent identifier
            conversation: Optional conversation node
            interaction: Optional interaction node
        """
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.conversation = conversation
        self.interaction = interaction
        self.conversation_id = conversation.id if conversation else ""
    
    async def emit_message(self, message: str) -> None:
        """Emit a message during tool execution.
        
        This can be used to send progress updates or intermediate messages
        to the user while a long-running tool executes.
        
        Args:
            message: Message to emit
        """
        # TODO: Implement message emission via ResponseBus
        # For now, log it
        logger.info(f"ToolContext.emit_message: {message}")
    
    async def emit_status(self, status: str, data: Optional[Any] = None) -> None:
        """Emit a status update during tool execution.
        
        Args:
            status: Status message (e.g., "processing", "thinking")
            data: Optional additional status data
        """
        # TODO: Implement status emission via ResponseBus
        # For now, log it
        logger.info(f"ToolContext.emit_status: {status} - {data}")
    
    async def get_agent(self) -> Optional["Agent"]:
        """Get the agent associated with this context.
        
        Returns:
            Agent node if found, None otherwise
        """
        if self.conversation:
            return await self.conversation.get_agent()
        return None
    
    async def get_conversation_context(self, key: str) -> Optional[Any]:
        """Get a value from the conversation context dict.
        
        Args:
            key: Context key
        
        Returns:
            Context value if found, None otherwise
        """
        if self.conversation:
            return self.conversation.context.get(key)
        return None
    
    async def set_conversation_context(self, key: str, value: Any) -> None:
        """Set a value in the conversation context dict.
        
        Args:
            key: Context key
            value: Context value
        """
        if self.conversation:
            self.conversation.context[key] = value
            await self.conversation.save()
