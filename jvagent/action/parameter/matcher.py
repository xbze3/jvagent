"""ParameterMatcher for selecting applicable parameters per turn.

This module provides the ParameterMatcher service that evaluates parameter conditions
against the current interaction context and selects which parameters should be applied.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from jvagent.memory.interaction import Interaction
    from jvagent.memory.conversation import Conversation

logger = logging.getLogger(__name__)


@dataclass
class ParameterMatchResult:
    """Result of parameter matching for a single parameter.
    
    Attributes:
        parameter: The original parameter dict
        matched: Whether this parameter matched the current context
        score: Optional confidence score (0.0-1.0)
        rationale: Optional explanation of why it matched/didn't match
    """
    parameter: Dict[str, Any]
    matched: bool
    score: Optional[float] = None
    rationale: Optional[str] = None


class ParameterMatcher:
    """Service for matching parameters to the current interaction context.
    
    The ParameterMatcher evaluates parameter conditions against the current turn
    and returns which parameters should be applied. Supports multiple matching strategies:
    - Rule-based: Simple pattern matching on condition strings
    - LLM-based: Uses language model to evaluate conditions (future)
    - Hybrid: Combines rule and LLM approaches (future)
    
    Parameters with match_mode="always" bypass matching and are always included.
    Parameters with match_mode="matched" are evaluated by this matcher.
    """
    
    def __init__(self, strategy: str = "rule"):
        """Initialize the matcher.
        
        Args:
            strategy: Matching strategy ("rule", "llm", "hybrid")
        """
        self.strategy = strategy
        if strategy not in ("rule", "llm", "hybrid"):
            logger.warning(f"Unknown strategy '{strategy}', defaulting to 'rule'")
            self.strategy = "rule"
    
    async def match_parameters(
        self,
        parameters: List[Dict[str, Any]],
        interaction: "Interaction",
        conversation: Optional["Conversation"] = None,
        active_interview_types: Optional[List[str]] = None,
    ) -> List[ParameterMatchResult]:
        """Match parameters against the current interaction context.
        
        Args:
            parameters: List of parameters to evaluate (should have match_mode="matched")
            interaction: Current interaction with utterance, history, etc.
            conversation: Optional conversation for additional context
            active_interview_types: Optional list of currently active interview types for filtering
        
        Returns:
            List of ParameterMatchResult for each parameter
        """
        if not parameters:
            return []
        
        # Filter by interview_scope if active_interview_types provided
        filtered_params = self._filter_by_interview_scope(parameters, active_interview_types)
        
        # Apply matching strategy
        if self.strategy == "rule":
            return await self._match_rule_based(filtered_params, interaction, conversation)
        elif self.strategy == "llm":
            return await self._match_llm_based(filtered_params, interaction, conversation)
        elif self.strategy == "hybrid":
            return await self._match_hybrid(filtered_params, interaction, conversation)
        else:
            # Fallback to rule-based
            return await self._match_rule_based(filtered_params, interaction, conversation)
    
    def _filter_by_interview_scope(
        self,
        parameters: List[Dict[str, Any]],
        active_interview_types: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Filter parameters by interview_scope if present.
        
        Args:
            parameters: Parameters to filter
            active_interview_types: List of active interview types (class names)
        
        Returns:
            Filtered parameters
        """
        if not active_interview_types:
            # No active interviews, only return params without interview_scope
            return [p for p in parameters if not p.get("interview_scope")]
        
        filtered = []
        for param in parameters:
            scope = param.get("interview_scope")
            if not scope:
                # No scope restriction, always include
                filtered.append(param)
            elif scope in active_interview_types:
                # Scope matches an active interview
                filtered.append(param)
            # else: scope doesn't match, exclude
        
        return filtered
    
    async def _match_rule_based(
        self,
        parameters: List[Dict[str, Any]],
        interaction: "Interaction",
        conversation: Optional["Conversation"],
    ) -> List[ParameterMatchResult]:
        """Rule-based matching using simple heuristics.
        
        For now, this implements a simple always-match strategy for testing.
        In production, this would use pattern matching, keyword detection, etc.
        
        Args:
            parameters: Parameters to match
            interaction: Current interaction
            conversation: Optional conversation context
        
        Returns:
            List of match results
        """
        results = []
        
        for param in parameters:
            condition = param.get("condition", "")
            
            # Simple heuristic: For now, match all parameters with valid conditions
            # This allows the system to work while we develop more sophisticated matching
            if condition and isinstance(condition, str) and len(condition) > 0:
                results.append(ParameterMatchResult(
                    parameter=param,
                    matched=True,
                    score=0.8,  # Medium confidence for rule-based
                    rationale="Rule-based match: parameter has valid condition"
                ))
            else:
                results.append(ParameterMatchResult(
                    parameter=param,
                    matched=False,
                    score=0.0,
                    rationale="No valid condition specified"
                ))
        
        return results
    
    async def _match_llm_based(
        self,
        parameters: List[Dict[str, Any]],
        interaction: "Interaction",
        conversation: Optional["Conversation"],
    ) -> List[ParameterMatchResult]:
        """LLM-based matching using language model evaluation.
        
        Future implementation: Use LLM to evaluate each parameter's condition
        against the current interaction context.
        
        Args:
            parameters: Parameters to match
            interaction: Current interaction
            conversation: Optional conversation context
        
        Returns:
            List of match results
        """
        # TODO: Implement LLM-based matching
        # For now, fall back to rule-based
        logger.warning("LLM-based matching not yet implemented, falling back to rule-based")
        return await self._match_rule_based(parameters, interaction, conversation)
    
    async def _match_hybrid(
        self,
        parameters: List[Dict[str, Any]],
        interaction: "Interaction",
        conversation: Optional["Conversation"],
    ) -> List[ParameterMatchResult]:
        """Hybrid matching combining rule and LLM approaches.
        
        Future implementation: Use rules for quick filtering, then LLM for ambiguous cases.
        
        Args:
            parameters: Parameters to match
            interaction: Current interaction
            conversation: Optional conversation context
        
        Returns:
            List of match results
        """
        # TODO: Implement hybrid matching
        # For now, fall back to rule-based
        logger.warning("Hybrid matching not yet implemented, falling back to rule-based")
        return await self._match_rule_based(parameters, interaction, conversation)
    
    @staticmethod
    def get_matched_parameters(results: List[ParameterMatchResult]) -> List[Dict[str, Any]]:
        """Extract just the parameters that matched from results.
        
        Args:
            results: List of match results
        
        Returns:
            List of parameters that matched (with optional score/rationale added)
        """
        matched = []
        for result in results:
            if result.matched:
                # Add match metadata to parameter
                param_copy = dict(result.parameter)
                if result.score is not None:
                    param_copy["_match_score"] = result.score
                if result.rationale:
                    param_copy["_match_rationale"] = result.rationale
                matched.append(param_copy)
        return matched
