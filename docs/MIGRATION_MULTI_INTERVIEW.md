# Migration Guide: Multi-Interview and Parameter Matching

This guide helps you migrate existing agents to use the new parameter matching and multi-interview features.

## Schema Changes

### Interaction

New fields added (automatically available):
```python
matched_parameters: List[Dict[str, Any]]  # Matched parameters this turn
tool_results: List[Dict[str, Any]]        # Results from parameter-bound tools
```

### Conversation

New field added (automatically available):
```python
active_interviews: Dict[str, str]  # Maps interview_type → session_id
```

### InterviewInteractAction

New attributes added:
```python
activation_conditions: List[str]  # When interview should start
exclusive: bool                    # Whether to deactivate other interviews
```

## Migration Paths

### Path 1: No Changes Required (Backward Compatible)

Your existing agents work unchanged:
- Parameters without `match_mode` default to "always" (current behavior)
- Interviews without `activation_conditions` start when explicitly routed
- PersonaAction uses legacy parameter handling if no matching performed

**Action required**: None

### Path 2: Enable Parameter Matching

Add to your router or PersonaAction:

```yaml
# Option A: Via InterviewAwareRouter
- entity: InterviewAwareRouter
  label: router
  enable_parameter_matching: true
  parameter_matcher_strategy: "rule"

# Option B: Keep standard router, parameters still work
- entity: InteractRouter
  label: router
```

Mark parameters for matching:

```yaml
- entity: PersonaAction
  parameters:
    - condition: "User asks for help"
      response: "Offer assistance"
      match_mode: "matched"  # Only included when relevant
    
    - condition: "User asks about identity"
      response: "Introduce yourself"
      match_mode: "always"   # Always included (default)
```

### Path 3: Enable Multi-Interview

1. **Add activation conditions** to interviews:

```yaml
- entity: SignupInterviewAction
  activation_conditions:
    - "user wants to sign up"
    - "user creates account"
  exclusive: false
```

2. **Use InterviewAwareRouter** for automatic activation:

```yaml
- entity: InterviewAwareRouter
  label: router
  weight: -100
```

3. **Add interview-scoped parameters** (optional):

```yaml
- entity: SignupInterviewAction
  parameters:
    - condition: "User provides invalid email"
      response: "Explain email format"
      match_mode: "matched"
      interview_scope: "SignupInterviewAction"
```

## Testing Checklist

After migration:

- [ ] Test single interview flow (should work unchanged)
- [ ] Test multiple interviews simultaneously
- [ ] Test interview completion removes from active_interviews
- [ ] Test parameter matching (if enabled)
- [ ] Test interview-scoped parameters (if used)
- [ ] Test activation conditions trigger interviews
- [ ] Test exclusive mode deactivates other interviews
- [ ] Verify PersonaAction includes active interview states in prompt
- [ ] Check logs for "Registered as active interview" messages

## Rollback

To disable new features:

1. **Remove InterviewAwareRouter**, use InteractRouter
2. **Remove activation_conditions** from interviews
3. **Remove match_mode** from parameters (or set to "always")
4. System reverts to previous behavior

## Common Patterns

### Pattern 1: Main Flow + Side Tasks

```yaml
# Main interview (exclusive)
- entity: OnboardingInterview
  activation_conditions: ["user starts onboarding"]
  exclusive: true

# Side task (can coexist)
- entity: FAQInterview
  activation_conditions: ["user has question"]
  exclusive: false
```

### Pattern 2: Context-Dependent Parameters

```yaml
- entity: PersonaAction
  parameters:
    # General parameter (always applies)
    - condition: "User asks about capabilities"
      response: "List your capabilities"
      match_mode: "always"
    
    # Context-specific (only when matched)
    - condition: "User seems confused about multiple tasks"
      response: "Clarify active tasks and offer to focus"
      match_mode: "matched"
    
    # Interview-specific
    - condition: "User provides invalid data in signup"
      response: "Validate and explain format"
      match_mode: "matched"
      interview_scope: "SignupInterviewAction"
```

### Pattern 3: Progressive Enhancement

Start simple, add features gradually:

1. **Week 1**: Add activation_conditions to interviews
2. **Week 2**: Enable InterviewAwareRouter
3. **Week 3**: Add match_mode to select parameters
4. **Week 4**: Enable parameter_matching in router

## Debugging

### Check Active Interviews

```python
# In code or logs
active_types = conversation.get_all_active_interview_types()
print(f"Active interviews: {active_types}")
```

### Check Matched Parameters

```python
# On interaction
matched = interaction.get_matched_parameters()
print(f"Matched {len(matched)} parameters")
```

### Enable Debug Logging

```python
import logging
logging.getLogger("jvagent.action.router").setLevel(logging.DEBUG)
logging.getLogger("jvagent.action.parameter").setLevel(logging.DEBUG)
logging.getLogger("jvagent.action.interview").setLevel(logging.DEBUG)
```

Look for:
- "Registered as active interview"
- "Removed from active interviews"
- "Matched N parameters"
- "Using matched parameters" vs "Using unexecuted parameters"
