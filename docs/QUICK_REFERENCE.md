# Quick Reference: Parameter Matching and Multi-Interview

## Parameter Schema

```python
{
    "condition": str,              # When this applies
    "response": str,               # What to do
    "match_mode": str,             # "always" (default) | "matched"
    "tools": List[str],            # Optional: tools to execute
    "reevaluate_after": List[str], # Optional: re-match after these tools
    "interview_scope": str,        # Optional: only when this interview active
}
```

## InterviewInteractAction Schema

```python
class MyInterview(InterviewInteractAction):
    activation_conditions: List[str]  # When to start automatically
    exclusive: bool                    # Deactivate others when activated
    question_graph: List[Dict]        # Question flow (existing)
    anchors: List[str]                # Routing anchors (existing)
```

## Conversation API

```python
# Check if interview is active
conversation.is_interview_active("SignupInterview")  # → bool

# Get active session ID
conversation.get_active_interview_session_id("SignupInterview")  # → str | None

# Get all active types
conversation.get_all_active_interview_types()  # → List[str]

# Add active interview (done automatically by InterviewInteractAction)
conversation.add_active_interview(interview_type, session_id)

# Remove active interview (done automatically on completion/cancellation)
conversation.remove_active_interview(interview_type)
```

## Interaction API

```python
# Get matched parameters (from ParameterMatcher)
interaction.get_matched_parameters()  # → List[Dict]

# Add matched parameters (done by ParameterMatcher or InterviewAwareRouter)
interaction.add_matched_parameters(params)

# Get tool results
interaction.get_tool_results()  # → List[Dict]

# Add tool result (done by tool executor)
interaction.add_tool_result(tool_id, result, metadata)
```

## Configuration Examples

### Minimal (No Changes)

```yaml
# Existing configuration works unchanged
- entity: InteractRouter
- entity: PersonaAction
  parameters:
    - condition: "X"
      response: "Y"
```

### With Parameter Matching

```yaml
- entity: InterviewAwareRouter
  enable_parameter_matching: true

- entity: PersonaAction
  parameters:
    - condition: "User asks for help"
      response: "Offer assistance"
      match_mode: "matched"  # Only when relevant
```

### With Multi-Interview

```yaml
- entity: InterviewAwareRouter

- entity: SignupInterview
  activation_conditions:
    - "user wants to sign up"
  exclusive: false

- entity: ProfileInterview
  activation_conditions:
    - "user updates profile"
  exclusive: false
```

### Full Stack

```yaml
- entity: InterviewAwareRouter
  enable_parameter_matching: true
  parameter_matcher_strategy: "rule"

- entity: SignupInterview
  activation_conditions: ["user wants to sign up"]
  exclusive: false
  parameters:
    - condition: "Invalid email in signup"
      response: "Explain format"
      match_mode: "matched"
      interview_scope: "SignupInterview"

- entity: PersonaAction
  parameters:
    - condition: "User confused about tasks"
      response: "Clarify"
      match_mode: "matched"
```

## Prompt Sections

New sections available in PersonaAction:

```
{active_interviews_section}  # Current state of active interviews
{tool_results_section}       # Results from parameter-bound tools
```

Existing sections:
```
{directives_section}         # From InteractActions
{parameters_section}         # All parameters or matched
{interpretation_section}     # From InteractRouter
{channel_formatting_section} # Channel-specific guidance
```

## Helper Functions (prompts.py)

```python
from jvagent.action.persona.prompts import (
    format_matched_parameters_section,
    format_active_interviews_section,
    format_tool_results_section,
)

# Format matched parameters
section = format_matched_parameters_section(matched_params)

# Format active interviews
section = format_active_interviews_section([
    {"interview_type": "Signup", "state": "ACTIVE", "directive": "Ask email"},
    {"interview_type": "Profile", "state": "REVIEW", "directive": "Confirm info"},
])

# Format tool results
section = format_tool_results_section([
    {"tool_id": "get_weather", "result": {"data": "Sunny, 72°F"}},
])
```

## Logs to Watch

```
INFO  SignupInterview: Registered as active interview
INFO  InterviewAwareRouter: Matched 3 parameters
DEBUG PersonaAction.respond: Using 3 matched parameters
INFO  SignupInterview: Removed from active interviews (state: COMPLETED)
```

## Common Patterns

### Check Before Activating

```python
# In custom routing logic
if not conversation.is_interview_active("SignupInterview"):
    # Check activation conditions or route
```

### Get Interview State for Custom Logic

```python
session_id = conversation.get_active_interview_session_id("SignupInterview")
if session_id:
    session = await InterviewSession.get(session_id)
    if session.state == InterviewState.REVIEW:
        # Custom logic for review state
```

### Cleanup Completed Interviews

```python
# Done automatically by InterviewInteractAction
# When state → COMPLETED or CANCELLED:
conversation.remove_active_interview(interview_type)
```

## Debugging Checklist

- [ ] Check `conversation.active_interviews` has expected entries
- [ ] Verify `interaction.matched_parameters` populated (if matching enabled)
- [ ] Check InterviewSession.state values
- [ ] Inspect PersonaAction prompt for new sections
- [ ] Look for lifecycle log messages
- [ ] Verify parameters have correct match_mode
- [ ] Check activation_conditions on interviews
- [ ] Ensure exclusive flag set correctly

## Migration Quick Start

1. Add `activation_conditions` to interviews
2. Change `InteractRouter` → `InterviewAwareRouter`
3. Set `enable_parameter_matching: true` (optional)
4. Add `match_mode: "matched"` to select parameters
5. Test with multiple interviews

Done! Your agent now supports coexisting interviews and context-managed prompting.
