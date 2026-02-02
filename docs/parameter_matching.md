# Parameter Matching and Multi-Interview Support

This document describes the parameter matching system and multi-interview coexistence features added to jvagent, inspired by Parlant's guideline and journey architecture.

## Overview

JVAgent now supports:
1. **Parameter Matching**: Select which parameters apply per turn (context-managed prompting)
2. **Multi-Interview Coexistence**: Multiple active interviews running simultaneously
3. **Parameter-Bound Tools**: Tools attached to parameters, executed when matched
4. **Interview Activation Conditions**: Automatic interview activation based on user intent

## Architecture

### Parameter Matching

Parameters can now have a `match_mode` field:
- `"always"` (default): Current push-based behavior - always included in prompt
- `"matched"`: Requires ParameterMatcher to evaluate condition per turn

```python
{
    "condition": "User asks about weather",
    "response": "Check weather API and provide forecast",
    "match_mode": "matched",  # Requires matching
    "tools": ["get_weather"],  # Optional: tools to call when matched
    "interview_scope": "TravelInterview",  # Optional: only apply when this interview is active
}
```

### ParameterMatcher

The `ParameterMatcher` service evaluates parameter conditions and returns matched parameters:

```python
from jvagent.action.parameter import ParameterMatcher

matcher = ParameterMatcher(strategy="rule")  # or "llm", "hybrid"
results = await matcher.match_parameters(
    parameters=parameters,
    interaction=interaction,
    conversation=conversation,
    active_interview_types=["SignupInterview"],
)

matched = ParameterMatcher.get_matched_parameters(results)
```

Matched parameters are stored on `interaction.matched_parameters` and used by PersonaAction.

### Multi-Interview Coexistence

Conversations now track active interviews via `active_interviews: Dict[str, str]` (maps interview_type → session_id).

```python
# Check if interview is active
if conversation.is_interview_active("SignupInterview"):
    session_id = conversation.get_active_interview_session_id("SignupInterview")

# Get all active types
active_types = conversation.get_all_active_interview_types()
```

Multiple interviews can be active simultaneously, each contributing directives to the prompt.

### Interview Activation Conditions

InterviewInteractAction now supports `activation_conditions`:

```python
class FlightBookingInterview(InterviewInteractAction):
    activation_conditions = [
        "user wants to book a flight",
        "user asks about flight booking",
    ]
    
    exclusive = False  # Allow coexistence with other interviews
```

When activation conditions match, the interview is automatically started (if using InterviewAwareRouter).

### Interview Lifecycle

1. **Start**: Activation conditions match → create InterviewSession → add to `active_interviews`
2. **Active**: InterviewSession.state == ACTIVE or REVIEW
3. **Complete**: InterviewSession.state == COMPLETED or CANCELLED → remove from `active_interviews`

## Usage

### Option 1: With InterviewAwareRouter (Automatic)

```python
# agent.yaml
actions:
  - entity: InterviewAwareRouter
    label: router
    weight: -100
    enable_parameter_matching: true
    parameter_matcher_strategy: "rule"
  
  - entity: SignupInterviewAction
    label: signup_interview
    activation_conditions:
      - "user wants to sign up"
      - "user creates account"
    exclusive: false
```

The router automatically:
- Evaluates activation conditions
- Delegates to active interviews
- Runs ParameterMatcher if enabled

### Option 2: Manual Control

Without InterviewAwareRouter, current behavior is preserved:
- Parameters with `match_mode="always"` (or absent) always apply
- Interviews start when explicitly routed
- Use InteractRouter for standard routing

## Backward Compatibility

All changes are backward compatible:
- Existing parameters without `match_mode` default to "always" (current behavior)
- Existing interviews without `activation_conditions` work as before
- PersonaAction falls back to `get_unexecuted_parameters()` if no matching performed
- Custom InteractActions continue to work unchanged

## Implementation Phases

Completed:
- ✅ Phase 1: Extended parameter schema and Interaction/Conversation fields
- ✅ Phase 2: ParameterMatcher service
- ✅ Phase 3: InterviewAwareRouter and activation conditions
- ✅ Phase 4: Multi-interview coexistence tracking
- ✅ Phase 5: Context-managed prompting in PersonaAction

Remaining:
- Phase 6: Parameter-bound tool execution and preparation loop
- Future: LLM-based parameter matching (currently rule-based placeholder)
- Future: Advanced interview state summarization for prompt context
