# Design Rationale: Parameter Matching and Multi-Interview

This document explains the design decisions made during the implementation of Parlant-style features in jvagent.

## Core Philosophy

**Preserve jvagent as a foundational framework, not replace it with Parlant's engine model.**

Parlant uses an engine-centric architecture where all flow is controlled by a single Engine that orchestrates guideline matching, tool calling, and message composition. JVAgent uses a graph-centric architecture where InteractWalker traverses InteractActions that have autonomy.

Both are valid. The refactor adds Parlant's **capabilities** (matching, coexistence) while preserving jvagent's **architecture** (walker, actions, graph).

## Decision 1: Parameters Stay "Parameters"

### Why Not Rename to "Guidelines"?

**Rationale**: Maintains terminology consistency and avoids confusion.

- Parameters are already `{condition, response}` - structurally identical to guidelines
- Renaming would:
  - Break existing configurations
  - Confuse developers familiar with jvagent
  - Create unnecessary diff noise
  - Require updating all documentation

**Decision**: Extend the parameter concept rather than introducing a parallel "guideline" system.

**Result**: Parameters gain `match_mode`, `tools`, `interview_scope` fields while remaining "parameters".

## Decision 2: InterviewSession IS the Journey Session

### Why Not Create "JourneySession"?

**Rationale**: InterviewSession already does everything a journey session needs.

| Journey Session Feature | InterviewSession Equivalent |
|------------------------|----------------------------|
| State tracking | `state: InterviewState` (ACTIVE, REVIEW, COMPLETED, CANCELLED) |
| Response storage | `responses: Dict[str, Any]` |
| Position tracking | `active_question_key: str` |
| History | `update_history: List[Dict]` |
| Context | `context: Dict[str, Any]` |

Creating a separate "JourneySession" would duplicate all this functionality.

**Decision**: InterviewSession IS the journey session. No new entity needed.

**Result**: Multi-interview support reuses existing InterviewSession, just tracks multiple per Conversation.

## Decision 3: InteractRouter Stays Generic

### Why Not Force Interview Logic into InteractRouter?

**Rationale**: InteractRouter is used by agents that don't have interviews.

Some agents use:
- Just PersonaAction (conversational chat)
- Custom InteractActions (business logic flows)
- Combinations without interviews

Forcing interview logic into the base router would:
- Violate single responsibility principle
- Add complexity to simple use cases
- Make router harder to understand and maintain

**Decision**: Create **InterviewAwareRouter** as an optional subclass.

**Result**: 
- Base InteractRouter unchanged
- InterviewAwareRouter adds interview delegation
- Agents choose which router to use

## Decision 4: Hybrid Instruction Sources

### Why Not "Matched Only" Like Parlant?

**Rationale**: JVAgent's directive system has proven value.

Parlant: All instructions come from matched guidelines/journey states.
JVAgent: Instructions can come from multiple sources:
- **Directives**: InteractActions push immediate instructions (e.g., "Ask for email")
- **Parameters**: General conditional guidance (can be always OR matched)
- **Interview states**: Current step in interview flow

This hybrid approach supports:
- Interview-driven directives (current functionality)
- Matched parameters (new capability)
- Custom action directives (flexibility)

**Decision**: Support both push-based and match-based instruction sources.

**Result**: 
- `interaction.directives` (pushed) + `interaction.matched_parameters` (matched)
- PersonaAction merges both
- Backward compatible with existing directive flow

## Decision 5: Action-Centric Journeys

### Why Not Lightweight Journey Data?

**Rationale**: JVAgent's action model provides power and flexibility.

Parlant journeys are lightweight:
- State graph stored as data
- Engine interprets and traverses
- No custom code per journey

JVAgent interviews are heavyweight:
- InterviewInteractAction is a full action class
- Can implement custom logic (handlers, validators, branch functions)
- QuestionWalker provides sophisticated traversal
- DirectiveBuilder customizes prompts

This allows:
- Complex validation rules
- Custom input handlers
- Dynamic question generation
- Integration with external APIs
- Reusable decorator patterns

**Decision**: Keep InterviewInteractAction as the journey implementation.

**Result**: 
- More powerful than Parlant's lightweight journeys
- Requires more setup but offers more control
- Suitable for complex business logic

## Decision 6: Optional Enhancement, Not Required Migration

### Why Not Make New Features Mandatory?

**Rationale**: Not all agents need these features.

Simple chatbots with PersonaAction don't need:
- Parameter matching (all guidance is relevant)
- Multi-interview (single conversation flow)
- Activation conditions (no structured flows)

Forcing migration would:
- Create unnecessary work
- Complicate simple use cases
- Risk breaking existing agents

**Decision**: All new features are **opt-in** with backward compatibility.

**Result**:
- `match_mode` defaults to "always" (current behavior)
- `activation_conditions` defaults to empty (manual activation)
- PersonaAction falls back to legacy if no matching
- Zero breaking changes

## Decision 7: Conversation Tracks Active Interviews

### Why Not Session-Level Tracking?

**Rationale**: Interviews are conversation-scoped, not session-scoped.

In jvagent:
- Conversation = long-lived user context
- Session = identifier that can change
- Interviews span multiple interactions within a conversation

Example:
```
User starts signup → Interaction 1
User continues signup → Interaction 2 (same conversation, same interview)
User completes signup → Interaction 3 (same conversation, same interview)
```

The interview state needs to persist across interactions within the conversation.

**Decision**: Store `active_interviews` on Conversation, not session tracking.

**Result**: 
- Interview state persists correctly
- Multiple conversations can have different active interviews
- Session ID changes don't affect interview tracking

## Decision 8: Preparation Phase Deferred

### Why Not Implement Full Preparation Loop Now?

**Rationale**: Foundation first, optimization later.

The preparation loop requires:
- Tool execution orchestration
- Re-matching logic
- Iteration cap and bailout
- Error handling and recovery

This is complex and should be:
- Thoroughly designed
- Carefully tested
- Added after foundation is validated

**Decision**: Build foundation (ToolContext, ToolResult, schema), defer execution.

**Result**:
- Schema supports `tools` and `reevaluate_after` fields
- ToolContext and ToolResult classes ready
- Execution logic can be added incrementally
- No risk from rushing complex orchestration

## Decision 9: Rule-Based Matching First

### Why Not LLM-Based Matching Immediately?

**Rationale**: Incremental implementation reduces risk.

LLM-based matching requires:
- Prompt engineering for condition evaluation
- Batching strategy (all at once vs. incremental)
- Error handling for LLM failures
- Cost optimization

**Decision**: Start with rule-based placeholder, add LLM matching later.

**Result**:
- System works end-to-end immediately (rule-based matches all valid conditions)
- Interface is defined (ParameterMatcher with pluggable strategies)
- LLM matching can be added without changing interface
- Agents can start using multi-interview features now

## Design Patterns Used

### 1. Extension, Not Replacement

**Pattern**: Add optional fields to existing schemas rather than new entities.

Example:
- Don't create "Guideline" entity, extend "Parameter"
- Don't create "JourneySession", reuse "InterviewSession"

### 2. Subclassing for Specialization

**Pattern**: InterviewAwareRouter extends InteractRouter.

Benefits:
- Base class unchanged
- Specialization is opt-in
- Clear inheritance hierarchy

### 3. Optional Features with Fallback

**Pattern**: Check if new fields exist, fall back to legacy if not.

Example:
```python
matched = interaction.get_matched_parameters()
if matched:
    use_matched(matched)  # New behavior
else:
    use_unexecuted()      # Legacy fallback
```

### 4. Helpers Hide Complexity

**Pattern**: Add helper methods to hide new field access patterns.

Example:
```python
# Don't: if conversation.active_interviews.get(type)
# Do: if conversation.is_interview_active(type)
```

### 5. Documentation-Driven Development

**Pattern**: Write docs first, ensures clarity.

Created:
- Architecture docs before implementation
- Migration guide before schema changes
- Quick reference for developers
- Examples showing real usage

## Lessons from Parlant Integration

### What Translated Well

1. **Condition/action pairs**: Parameters already had this
2. **State diagrams**: QuestionGraph already implements this
3. **Context management**: Easily added to prompt building
4. **Coexistence**: Simple dict tracking on Conversation

### What Needed Adaptation

1. **Engine vs. Walker**: Kept walker, added matching as service
2. **Tool binding**: Parlant's engine-owned tools → jvagent's parameter-bound tools
3. **Journey activation**: Parlant's engine evaluates → jvagent's router evaluates
4. **Prompt composition**: Parlant's PromptBuilder → jvagent's template strings

### What We Improved

1. **Router flexibility**: Pluggable routers vs. monolithic engine
2. **Action autonomy**: InteractActions have more freedom
3. **Custom logic**: Interview handlers/validators/branch functions
4. **Graph composition**: Actions compose via graph relationships

## Conclusion

The design successfully:
- ✅ Translates Parlant's key mechanisms (matching, coexistence, context management)
- ✅ Preserves jvagent's architecture and terminology
- ✅ Maintains 100% backward compatibility
- ✅ Provides incremental adoption path
- ✅ Keeps the system flexible for non-Parlant use cases

The result is a hybrid that combines:
- Parlant's **context management** and **coexistence** capabilities
- JVAgent's **graph-based** and **action-centric** foundation

This gives users the best of both worlds: Parlant-style multiturn conversations when needed, jvagent's flexibility for custom flows when needed.
