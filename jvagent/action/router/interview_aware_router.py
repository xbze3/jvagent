"""InterviewAwareRouter for interview-aware routing and delegation.

Extends InteractRouter to add interview activation and delegation logic while
keeping the base router generic.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from jvspatial.core.annotations import attribute
from jvagent.action.router.interact_router import InteractRouter
from jvagent.action.parameter.matcher import ParameterMatcher, ParameterMatchResult

if TYPE_CHECKING:
    from jvagent.action.interact.interact_walker import InteractWalker
    from jvagent.memory.interaction import Interaction
    from jvagent.memory.conversation import Conversation

logger = logging.getLogger(__name__)


class InterviewAwareRouter(InteractRouter):
    """Router that adds interview activation and delegation logic.
    
    Extends InteractRouter to:
    1. Evaluate activation_conditions for interviews
    2. Delegate to active interviews when appropriate
    3. Start new interviews when activation conditions match
    4. Handle exclusive interview modes
    
    The base routing logic (intent classification, anchor matching) is preserved.
    Interview delegation is added as a post-routing step.
    
    Attributes:
        enable_parameter_matching: Whether to run ParameterMatcher during routing
        parameter_matcher_strategy: Strategy for ParameterMatcher ("rule", "llm", "hybrid")
    """
    
    enable_parameter_matching: bool = attribute(
        default=False,
        description="Whether to run ParameterMatcher during routing (Phase 2)"
    )
    
    parameter_matcher_strategy: str = attribute(
        default="rule",
        description="Strategy for ParameterMatcher: 'rule', 'llm', or 'hybrid'"
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize interview-aware router."""
        super().__init__(*args, **kwargs)
        self._parameter_matcher: Optional[ParameterMatcher] = None
    
    @property
    def parameter_matcher(self) -> ParameterMatcher:
        """Get or create ParameterMatcher instance."""
        if self._parameter_matcher is None:
            self._parameter_matcher = ParameterMatcher(strategy=self.parameter_matcher_strategy)
        return self._parameter_matcher
    
    async def execute(self, visitor: "InteractWalker") -> None:
        """Execute interview-aware routing.
        
        Runs base InteractRouter logic, then adds interview delegation.
        
        Args:
            visitor: The InteractWalker visiting this action
        """
        # Run base routing (intent classification, anchor matching)
        await super().execute(visitor)
        
        # Add interview delegation logic
        interaction = visitor.interaction
        if not interaction:
            logger.warning("InterviewAwareRouter: No interaction available")
            return
        
        try:
            # Get conversation for active interview tracking
            conversation = visitor.conversation
            if not conversation:
                logger.warning("InterviewAwareRouter: No conversation available for interview tracking")
                return
            
            # Evaluate interview activation and delegation
            await self._handle_interview_delegation(visitor, interaction, conversation)
            
            # Optionally run parameter matching
            if self.enable_parameter_matching:
                await self._handle_parameter_matching(visitor, interaction, conversation)
        
        except Exception as e:
            logger.error(f"InterviewAwareRouter: Error during interview delegation: {e}", exc_info=True)
    
    async def _handle_interview_delegation(
        self,
        visitor: "InteractWalker",
        interaction: "Interaction",
        conversation: "Conversation",
    ) -> None:
        """Handle interview activation conditions and delegation.
        
        Args:
            visitor: The InteractWalker
            interaction: Current interaction
            conversation: Current conversation
        """
        from jvagent.action.interview.interview_interact_action import InterviewInteractAction
        
        agent = await self.get_agent()
        if not agent:
            return
        
        actions_manager = await agent.get_actions_manager()
        if not actions_manager:
            return
        
        # Get all InterviewInteractActions
        all_interviews = await actions_manager.get_actions(
            enabled_only=True,
            entity=InterviewInteractAction
        )
        
        if not all_interviews:
            logger.debug("InterviewAwareRouter: No interview actions found")
            return
        
        # Check which interviews should be active
        active_interview_types = conversation.get_all_active_interview_types()
        logger.debug(f"InterviewAwareRouter: Currently active interviews: {active_interview_types}")
        
        # Evaluate activation conditions for inactive interviews
        for interview in all_interviews:
            interview_type = interview.get_class_name()
            
            # Skip if already active
            if conversation.is_interview_active(interview_type):
                continue
            
            # Check activation conditions
            if await self._should_activate_interview(interview, interaction, conversation):
                logger.info(f"InterviewAwareRouter: Activating interview {interview_type}")
                
                # Handle exclusive mode
                if interview.exclusive:
                    # Deactivate other interviews
                    for active_type in active_interview_types:
                        conversation.remove_active_interview(active_type)
                        logger.info(f"InterviewAwareRouter: Deactivated {active_type} (exclusive mode)")
                
                # Add to routed actions if not already present
                if interview_type not in interaction.anchors:
                    interaction.anchors.append(interview_type)
                    await interaction.save()
                    logger.debug(f"InterviewAwareRouter: Added {interview_type} to routed actions")
        
        # Delegate to active interviews (ensure they're in routed actions)
        for active_type in conversation.get_all_active_interview_types():
            if active_type not in interaction.anchors:
                interaction.anchors.append(active_type)
                logger.debug(f"InterviewAwareRouter: Delegated to active interview {active_type}")
        
        if interaction.anchors:
            await interaction.save()
    
    async def _should_activate_interview(
        self,
        interview: Any,
        interaction: "Interaction",
        conversation: "Conversation",
    ) -> bool:
        """Evaluate whether an interview should be activated.
        
        Args:
            interview: InterviewInteractAction instance
            interaction: Current interaction
            conversation: Current conversation
        
        Returns:
            True if interview should activate, False otherwise
        """
        activation_conditions = getattr(interview, "activation_conditions", [])
        
        if not activation_conditions:
            # No activation conditions means manual activation only
            return False
        
        # Simple heuristic for now: Check if any activation condition appears in utterance
        # In production, this would use ParameterMatcher or similar LLM evaluation
        utterance_lower = interaction.utterance.lower()
        
        for condition in activation_conditions:
            # Simple substring match for now
            if condition.lower() in utterance_lower:
                logger.debug(f"InterviewAwareRouter: Condition matched: '{condition}'")
                return True
        
        # TODO: Use ParameterMatcher or LLM-based evaluation for more sophisticated matching
        return False
    
    async def _handle_parameter_matching(
        self,
        visitor: "InteractWalker",
        interaction: "Interaction",
        conversation: "Conversation",
    ) -> None:
        """Run ParameterMatcher to select applicable parameters.
        
        Args:
            visitor: The InteractWalker
            interaction: Current interaction
            conversation: Current conversation
        """
        # Collect all parameters with match_mode="matched" from actions
        agent = await self.get_agent()
        if not agent:
            return
        
        actions_manager = await agent.get_actions_manager()
        if not actions_manager:
            return
        
        from jvagent.action.interact.base import InteractAction
        from jvagent.action.persona.persona_action import PersonaAction
        
        # Get all enabled actions
        all_actions = await actions_manager.get_actions(enabled_only=True)
        
        # Collect parameters with match_mode="matched"
        matchable_parameters = []
        for action in all_actions:
            if hasattr(action, "parameters") and action.parameters:
                for param in action.parameters:
                    if param.get("match_mode") == "matched":
                        matchable_parameters.append(param)
        
        if not matchable_parameters:
            logger.debug("InterviewAwareRouter: No matchable parameters found")
            return
        
        # Run matcher
        active_interview_types = conversation.get_all_active_interview_types()
        match_results = await self.parameter_matcher.match_parameters(
            parameters=matchable_parameters,
            interaction=interaction,
            conversation=conversation,
            active_interview_types=active_interview_types,
        )
        
        # Store matched parameters on interaction
        matched = ParameterMatcher.get_matched_parameters(match_results)
        if matched:
            interaction.add_matched_parameters(matched)
            await interaction.save()
            logger.info(f"InterviewAwareRouter: Matched {len(matched)} parameters")
