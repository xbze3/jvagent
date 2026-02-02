# Multi-Interview Architecture

This document describes the architecture of the parameter matching and multi-interview system.

## High-Level Architecture

```mermaid
graph TB
    User[User Message] --> Walker[InteractWalker]
    Walker --> Router[InterviewAwareRouter]
    
    Router --> PM[ParameterMatcher]
    Router --> AC[Activation Conditions Evaluator]
    
    PM --> Interaction[Interaction.matched_parameters]
    AC --> Conv[Conversation.active_interviews]
    
    Router --> IA[InterviewInteractActions]
    IA --> Session[InterviewSession]
    IA --> Directives[Interaction.directives]
    
    Walker --> Persona[PersonaAction]
    Persona --> MP[Get matched_parameters]
    Persona --> AS[Get active interview states]
    Persona --> Prompt[Build Context-Managed Prompt]
    
    Prompt --> Model[ModelAction]
    Model --> Response[Response]
    Response --> Bus[ResponseBus]
```

## Component Interaction

### 1. Request Entry

```mermaid
sequenceDiagram
    participant User
    participant Walker as InteractWalker
    participant Conv as Conversation
    participant Int as Interaction

    User->>Walker: utterance
    Walker->>Conv: get_session()
    Walker->>Int: create Interaction
    Walker->>Walker: visit(Agent) → visit(Actions)
```

### 2. Interview-Aware Routing (Optional)

```mermaid
sequenceDiagram
    participant Router as InterviewAwareRouter
    participant PM as ParameterMatcher
    participant Conv as Conversation
    participant Int as Interaction

    Router->>Router: Base routing (intent, anchors)
    Router->>Conv: get_all_active_interview_types()
    Router->>Router: Evaluate activation_conditions
    
    alt New interview activates
        Router->>Conv: add_active_interview(type, session_id)
        Router->>Int: Add to anchors (routing)
    end
    
    alt Parameter matching enabled
        Router->>PM: match_parameters()
        PM->>Int: Store matched_parameters
    end
```

### 3. Interview Execution

```mermaid
sequenceDiagram
    participant Walker as InteractWalker
    participant Interview as InterviewInteractAction
    participant Session as InterviewSession
    participant Conv as Conversation
    participant Int as Interaction

    Walker->>Interview: execute()
    Interview->>Conv: get_active_interview_session_id()
    
    alt No session exists
        Interview->>Session: create()
        Interview->>Conv: add_active_interview()
    end
    
    Interview->>Session: classify_and_extract()
    Interview->>Session: generate_directive()
    Interview->>Int: add_directive()
    
    alt State = COMPLETED or CANCELLED
        Interview->>Conv: remove_active_interview()
    end
```

### 4. Context-Managed Response

```mermaid
sequenceDiagram
    participant Persona as PersonaAction
    participant Int as Interaction
    participant Conv as Conversation
    participant Model as ModelAction
    
    Persona->>Int: get_matched_parameters()
    
    alt Matched parameters available
        Persona->>Persona: Use matched (context-managed)
    else No matching
        Persona->>Int: get_unexecuted_parameters()
        Persona->>Persona: Use all (legacy)
    end
    
    Persona->>Conv: get_all_active_interview_types()
    Persona->>Persona: Collect interview states
    Persona->>Int: get_tool_results()
    
    Persona->>Persona: Build prompt (matched context only)
    Persona->>Model: generate()
    Model-->>Persona: response
```

## Data Flow

### Parameter Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Defined: Configure in agent.yaml
    Defined --> Pushed: match_mode="always"
    Defined --> Evaluated: match_mode="matched"
    
    Evaluated --> Matched: Condition holds
    Evaluated --> Filtered: Condition doesn't hold
    
    Pushed --> InPrompt: All parameters
    Matched --> InPrompt: Selected parameters
    Filtered --> [*]: Not in prompt
    
    InPrompt --> Applied: LLM generates response
    Applied --> Executed: Mark executed=true
    Executed --> [*]
```

### Interview Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Inactive: Interview exists
    Inactive --> Activating: Activation conditions match
    Activating --> Active: Create session
    
    Active --> Active: Question answering
    Active --> Review: All questions answered
    Review --> Active: User requests changes
    Review --> Completed: User confirms
    Active --> Cancelled: User cancels
    
    state Active {
        [*] --> AskQuestion
        AskQuestion --> CollectResponse
        CollectResponse --> Validate
        Validate --> NextQuestion: Valid
        Validate --> AskAgain: Invalid
        AskAgain --> CollectResponse
        NextQuestion --> AskQuestion: More questions
        NextQuestion --> [*]: All answered
    }
    
    Completed --> [*]: Remove from active_interviews
    Cancelled --> [*]: Remove from active_interviews
```

## Storage Schema

### Interaction

```python
{
    # Existing fields...
    "utterance": str,
    "directives": List[Dict],
    "parameters": List[Dict],
    "response": str,
    
    # New fields
    "matched_parameters": List[Dict],  # Subset of parameters that matched
    "tool_results": List[Dict],        # Results from parameter-bound tools
}
```

### Conversation

```python
{
    # Existing fields...
    "session_id": str,
    "user_id": str,
    "context": Dict,
    
    # New field
    "active_interviews": Dict[str, str],  # interview_type → session_id
}
```

### Parameter Schema

```python
{
    # Existing
    "condition": str,
    "response": str,
    "action_name": str,
    "executed": bool,
    
    # New optional
    "match_mode": "always" | "matched",
    "tools": List[str],
    "reevaluate_after": List[str],
    "interview_scope": str,
    
    # Added by matcher
    "_match_score": float,
    "_match_rationale": str,
}
```

## Extensibility

### Custom Matching Strategies

Implement custom parameter matching:

```python
from jvagent.action.parameter.matcher import ParameterMatcher

class CustomMatcher(ParameterMatcher):
    async def _match_rule_based(self, parameters, interaction, conversation):
        # Your custom logic
        return results
```

### Custom Interview Activation

Implement custom activation logic:

```python
from jvagent.action.router.interview_aware_router import InterviewAwareRouter

class CustomInterviewRouter(InterviewAwareRouter):
    async def _should_activate_interview(self, interview, interaction, conversation):
        # Your custom logic
        return True/False
```

## Performance Considerations

### Parameter Matching

- Rule-based: O(n) where n = number of parameters with match_mode="matched"
- LLM-based (future): Single LLM call per turn, batches all parameters
- Hybrid (future): Quick rule filter + LLM for ambiguous cases

### Multi-Interview Tracking

- O(1) lookup: `conversation.active_interviews` is a dict
- O(k) state collection where k = number of active interviews
- Typical: 1-3 active interviews per conversation

### Prompt Size

Before (all parameters):
```
Parameters: 20 total → 20 in prompt (always)
```

After (matched parameters):
```
Parameters: 20 total → 3-5 matched → 3-5 in prompt (context-managed)
```

Reduction: 60-75% fewer parameters per prompt, lower cost and better attention.

## Integration Points

### With InteractRouter

```python
# Standard router (unchanged)
InteractRouter → classify intent → select actions

# Interview-aware router (extends)
InterviewAwareRouter → base routing → check interviews → match parameters
```

### With PersonaAction

```python
# Before
PersonaAction → get_unexecuted_parameters() → all in prompt

# After (when matching used)
PersonaAction → get_matched_parameters() → only relevant in prompt
PersonaAction → collect active interview states → include in prompt
PersonaAction → get_tool_results() → include in prompt
```

### With Interview System

```python
# Before
Single InterviewSession per action type

# After
Multiple InterviewSessions per Conversation
Tracked in conversation.active_interviews
Each contributes state to prompt
```

## Testing Strategy

1. **Unit tests**: ParameterMatcher logic, filtering, scope checking
2. **Integration tests**: Router + matcher + persona flow
3. **System tests**: Full multi-interview scenarios
4. **Backward compatibility tests**: Ensure legacy behavior preserved

## Future Enhancements

### Phase 6: Parameter-Bound Tool Execution

- Execute tools attached to matched parameters
- Re-run ParameterMatcher after tool execution (if reevaluate_after)
- Preparation loop: match → tools → re-match → respond
- Max iterations cap to prevent infinite loops

### LLM-Based Matching

- Single LLM call to evaluate all parameter conditions
- Return match scores and rationales
- More sophisticated condition evaluation

### Event Log

- Add event timeline to Conversation (like Parlant's sessions)
- Support multi-message batching
- Trace IDs for linking messages to tool calls

### Advanced Interview State

- Rich state summaries for prompt context
- Interview progress indicators
- Cross-interview dependency tracking
