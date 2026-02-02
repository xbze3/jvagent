# Multi-Interview Coexistence

This document describes the multi-interview coexistence feature that allows multiple InterviewInteractActions to run simultaneously within a single conversation.

## Overview

JVAgent now supports multiple active interviews per conversation, similar to Parlant's coexisting journeys. This enables:
- Users to start a signup while also updating their profile
- Handling multiple tasks in parallel without losing context
- Natural conversation flow where users can switch between topics

## Architecture

### Conversation.active_interviews

The Conversation node tracks which interviews are currently active:

```python
active_interviews: Dict[str, str]
# Maps interview_type (class name) → InterviewSession.id
```

### Interview Lifecycle

#### 1. Start
Interview starts when:
- Activation conditions match (with InterviewAwareRouter), OR
- Explicitly routed by InteractRouter

```python
# InterviewInteractAction creates session and registers it:
conversation.add_active_interview(interview_type, session.id)
```

#### 2. Active
Interview is active when its session state is:
- `ACTIVE` (collecting responses)
- `REVIEW` (confirming information)

#### 3. Complete
Interview ends when state becomes:
- `COMPLETED` (successfully finished)
- `CANCELLED` (user cancelled)

```python
# InterviewInteractAction removes from active_interviews:
conversation.remove_active_interview(interview_type)
```

## Activation Conditions

Define when an interview should automatically start:

```python
class FlightBookingInterview(InterviewInteractAction):
    activation_conditions = [
        "user wants to book a flight",
        "user asks about flight booking",
        "user needs to reserve a plane ticket",
    ]
```

With InterviewAwareRouter, these conditions are evaluated against the user's utterance.

## Exclusive Mode

Control whether an interview deactivates others when it starts:

```python
class UrgentSupportInterview(InterviewInteractAction):
    activation_conditions = ["user reports urgent issue"]
    exclusive = True  # Deactivates other interviews when activated
```

Default is `exclusive = False` (allows coexistence).

## Prompt Context

All active interview states are included in the PersonaAction prompt:

```
### ACTIVE INTERVIEWS

You are currently managing 2 active interview(s):

1. **SignupInterviewAction** (State: ACTIVE)
   Current instruction: Ask for email address

2. **ProfileUpdateInterview** (State: REVIEW)
   Current instruction: Confirm collected information for ProfileUpdateInterview
```

This allows the agent to respond appropriately to multiple ongoing conversations.

## Conversation Helpers

```python
# Add active interview
conversation.add_active_interview(interview_type, session_id)

# Remove active interview
conversation.remove_active_interview(interview_type)

# Check if interview is active
if conversation.is_interview_active("SignupInterviewAction"):
    ...

# Get session ID for active interview
session_id = conversation.get_active_interview_session_id("SignupInterviewAction")

# Get all active interview types
active_types = conversation.get_all_active_interview_types()
```

## Example: Coexisting Interviews

```yaml
# agent.yaml
actions:
  - entity: InterviewAwareRouter
    label: router
    weight: -100
  
  # Account signup interview
  - entity: SignupInterviewAction
    label: signup
    activation_conditions:
      - "user wants to sign up"
    exclusive: false
    anchors:
      - "User wants to sign up"
      - "User provides signup info"
  
  # Profile update interview
  - entity: ProfileUpdateInterview
    label: profile_update
    activation_conditions:
      - "user wants to update profile"
    exclusive: false
    anchors:
      - "User updates profile"
  
  # Emergency support (exclusive)
  - entity: EmergencySupportInterview
    label: emergency
    activation_conditions:
      - "user reports urgent problem"
      - "user needs immediate help"
    exclusive: true  # Pauses other interviews
    anchors:
      - "User reports emergency"
```

## Typical Flow

1. User: "I want to sign up"
   - InterviewAwareRouter evaluates activation_conditions
   - SignupInterviewAction matches → session created → added to active_interviews
   - Interview asks first question

2. User: "Actually, can I also update my profile?"
   - ProfileUpdateInterview activation conditions match
   - New session created → added to active_interviews
   - Now 2 interviews active simultaneously

3. User: "What's my signup email again?"
   - InterviewAwareRouter delegates to SignupInterviewAction (active)
   - Response uses both interview contexts in prompt

4. User completes signup: "Yes, confirm"
   - SignupInterviewAction transitions to COMPLETED
   - Removed from active_interviews
   - ProfileUpdateInterview continues

## Best Practices

1. **Clear activation conditions**: Make conditions distinct to avoid accidental activation
2. **Use exclusive sparingly**: Most interviews should coexist gracefully
3. **Interview-scoped parameters**: Use `interview_scope` to avoid parameter conflicts
4. **State management**: Ensure completion/cancellation removes from active_interviews

## Migration from Single Interview

Existing interviews work unchanged:
- No activation_conditions → manual activation only (current behavior)
- Single interview per conversation (current behavior)
- Activation conditions are optional enhancement

To enable multi-interview:
1. Add `activation_conditions` to interview actions
2. Use `InterviewAwareRouter` instead of `InteractRouter`
3. Test with overlapping user intents
