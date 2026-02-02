"""Tests for ParameterMatcher."""

import pytest
from jvagent.action.parameter.matcher import ParameterMatcher, ParameterMatchResult


class TestParameterMatcher:
    """Test ParameterMatcher functionality."""
    
    @pytest.mark.asyncio
    async def test_rule_based_matching_basic(self):
        """Test basic rule-based matching."""
        matcher = ParameterMatcher(strategy="rule")
        
        parameters = [
            {"condition": "User asks about weather", "response": "Check weather API"},
            {"condition": "User requests help", "response": "Provide assistance"},
            {"condition": "", "response": "Invalid"},  # No condition
        ]
        
        # Mock interaction (we'll just pass None for now since rule-based doesn't use it yet)
        results = await matcher.match_parameters(
            parameters=parameters,
            interaction=None,  # type: ignore
            conversation=None,
        )
        
        assert len(results) == 3
        assert results[0].matched is True  # Valid condition
        assert results[1].matched is True  # Valid condition
        assert results[2].matched is False  # Empty condition
    
    @pytest.mark.asyncio
    async def test_interview_scope_filtering(self):
        """Test filtering by interview_scope."""
        matcher = ParameterMatcher(strategy="rule")
        
        parameters = [
            {"condition": "User provides email", "response": "Validate email", "interview_scope": "SignupInterview"},
            {"condition": "User asks question", "response": "Answer question"},  # No scope
            {"condition": "User provides name", "response": "Store name", "interview_scope": "ProfileInterview"},
        ]
        
        # Only SignupInterview is active
        results = await matcher.match_parameters(
            parameters=parameters,
            interaction=None,  # type: ignore
            conversation=None,
            active_interview_types=["SignupInterview"],
        )
        
        assert len(results) == 2  # Only no-scope and SignupInterview-scoped
        
        # Extract matched
        matched = ParameterMatcher.get_matched_parameters(results)
        assert len(matched) == 2
    
    @pytest.mark.asyncio
    async def test_get_matched_parameters(self):
        """Test extracting matched parameters from results."""
        results = [
            ParameterMatchResult(
                parameter={"condition": "test1", "response": "do this"},
                matched=True,
                score=0.9,
                rationale="High confidence",
            ),
            ParameterMatchResult(
                parameter={"condition": "test2", "response": "do that"},
                matched=False,
            ),
            ParameterMatchResult(
                parameter={"condition": "test3", "response": "do other"},
                matched=True,
                score=0.7,
            ),
        ]
        
        matched = ParameterMatcher.get_matched_parameters(results)
        
        assert len(matched) == 2
        assert matched[0]["_match_score"] == 0.9
        assert matched[0]["_match_rationale"] == "High confidence"
        assert matched[1]["_match_score"] == 0.7
