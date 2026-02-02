# Parameter Matching System

The parameter matching system enables context-managed prompting where only relevant parameters are included in the LLM prompt each turn, reducing cognitive load and improving response quality.

## Motivation

Previously, all parameters were always included in prompts, regardless of relevance to the current interaction. This led to:
- Increased prompt size and cost
- Reduced LLM attention on relevant instructions
- Difficulty managing complex agents with many conditional behaviors

The new system allows parameters to be **matched** per turn based on their conditions, similar to Parlant's guideline matching.

## Parameter Schema

Parameters now support optional fields for matching:

```python
{
    # Existing fields
    "condition": str,           # When this applies
    "response": str,            # Instruction/action
    "action_name": str,         # Source action (set automatically)
    "executed": bool,           # Tracking (set automatically)
    
    # New optional fields
    "match_mode": str,          # "always" (default) | "matched"
    "tools": List[str],         # Tool IDs to call when matched
    "reevaluate_after": List[str],  # Tool IDs that trigger re-matching
    "interview_scope": str,     # Only apply when this interview is active
}
```

## Match Modes

### always (default)

Current behavior - parameter is always included in prompt:

```python
{
    "condition": "User asks about your identity",
    "response": "Refer to yourself by name only",
    # match_mode defaults to "always"
}
```

### matched

Parameter is evaluated by ParameterMatcher and only included if condition matches:

```python
{
    "condition": "User seems frustrated",
    "response": "Acknowledge their frustration and offer assistance",
    "match_mode": "matched",
}
```

## ParameterMatcher

The `ParameterMatcher` service evaluates parameter conditions against the current context.

### Strategies

#### rule (default)

Simple heuristic matching (currently matches all valid conditions as a placeholder):

```python
from jvagent.action.parameter import ParameterMatcher

matcher = ParameterMatcher(strategy="rule")
results = await matcher.match_parameters(
    parameters=parameters,
    interaction=interaction,
    conversation=conversation,
    active_interview_types=["SignupInterview"],
)
```

#### llm (future)

Uses language model to evaluate conditions against context (not yet implemented).

#### hybrid (future)

Combines rule-based quick filtering with LLM evaluation for ambiguous cases (not yet implemented).

## Interview-Scoped Parameters

Parameters can be scoped to specific interviews:

```python
{
    "condition": "User provides invalid email",
    "response": "Explain email format requirements",
    "match_mode": "matched",
    "interview_scope": "SignupInterviewAction",
}
```

This parameter only applies when SignupInterviewAction is in `conversation.active_interviews`.

## Integration with PersonaAction

PersonaAction automatically uses matched parameters when available:

```python
# In PersonaAction.respond():
matched_params = interaction.get_matched_parameters()
if matched_params:
    # Use matched parameters (context-managed)
    applicable_parameters = matched_params
else:
    # Fall back to all unexecuted parameters (legacy behavior)
    applicable_parameters = interaction.get_unexecuted_parameters()
```

## Integration with InterviewAwareRouter

Enable parameter matching in the router:

```yaml
- entity: InterviewAwareRouter
  label: router
  enable_parameter_matching: true
  parameter_matcher_strategy: "rule"
```

The router will:
1. Run its base routing logic (intent classification, anchor matching)
2. Evaluate interview activation conditions
3. Run ParameterMatcher if enabled
4. Store results on `interaction.matched_parameters`

## Usage Example

```yaml
# agent.yaml
actions:
  - entity: InterviewAwareRouter
    enable_parameter_matching: true
  
  - entity: SignupInterviewAction
    activation_conditions:
      - "user wants to sign up"
    parameters:
      - condition: "User provides invalid email"
        response: "Validate and explain email format"
        match_mode: "matched"
        interview_scope: "SignupInterviewAction"
  
  - entity: PersonaAction
    parameters:
      - condition: "User asks for help"
        response: "Offer assistance"
        match_mode: "matched"
      
      - condition: "User asks about your identity"
        response: "Introduce yourself by name"
        match_mode: "always"  # Always in prompt
```

## Backward Compatibility

- Parameters without `match_mode` default to "always"
- Agents without InterviewAwareRouter work unchanged
- PersonaAction falls back to legacy behavior if no matching performed
- Existing InteractActions continue to work

## Future Enhancements

- LLM-based parameter matching for sophisticated condition evaluation
- Parameter-bound tool execution with re-matching
- Advanced interview state summarization for prompt context
- Conflict resolution for overlapping parameters
