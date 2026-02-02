# Changelog

All notable changes to jvagent will be documented in this file.

## [Unreleased]

### Added - Parameter Matching and Multi-Interview Support

#### Core Features

- **Parameter Matching System** (`jvagent/action/parameter/`)
  - `ParameterMatcher` service for selecting applicable parameters per turn
  - `match_mode` field on parameters: "always" (default) | "matched"
  - `interview_scope` field to scope parameters to specific interviews
  - Support for `tools`, `reevaluate_after` fields (foundation for Phase 6)
  - Rule-based matching strategy (LLM and hybrid strategies planned)

- **Multi-Interview Coexistence** 
  - `Conversation.active_interviews: Dict[str, str]` tracks active interview sessions
  - Multiple InterviewSessions can be active simultaneously
  - Conversation helpers: `add_active_interview()`, `remove_active_interview()`, `is_interview_active()`
  - Interview lifecycle management: activate on start, deactivate on completion/cancellation

- **Interview Activation Conditions**
  - `activation_conditions: List[str]` on InterviewInteractAction
  - `exclusive: bool` flag (if True, deactivates other interviews when activated)
  - Automatic activation when conditions match (with InterviewAwareRouter)

- **InterviewAwareRouter** (`jvagent/action/router/interview_aware_router.py`)
  - Extends InteractRouter with interview-aware routing
  - Evaluates activation conditions and delegates to active interviews
  - Optional parameter matching integration (`enable_parameter_matching`)
  - Keeps base InteractRouter generic and unchanged

- **Context-Managed Prompting**
  - PersonaAction uses `interaction.matched_parameters` when available
  - Falls back to `get_unexecuted_parameters()` if no matching performed
  - New prompt sections: active_interviews, matched_parameters, tool_results
  - Updated SYSTEM_PROMPT_TEMPLATE with new sections

- **Parameter-Bound Tools** (foundation)
  - `ToolContext` class for tool execution context
  - `ToolResult` class for tool results with data, metadata, control
  - `Interaction.tool_results` field for storing tool execution results
  - Helpers: `add_tool_result()`, `get_tool_results()`

#### Memory Schema Extensions

- **Interaction**:
  - `matched_parameters: List[Dict]` - Parameters matched by ParameterMatcher
  - `tool_results: List[Dict]` - Results from parameter-bound tools
  - `add_matched_parameter()`, `add_matched_parameters()` helpers
  - `add_tool_result()`, `get_tool_results()` helpers

- **Conversation**:
  - `active_interviews: Dict[str, str]` - Active interview tracking
  - `add_active_interview()`, `remove_active_interview()` helpers
  - `get_active_interview_session_id()`, `is_interview_active()` helpers
  - `get_all_active_interview_types()` helper

#### Documentation

- `docs/parameter_matching.md` - Parameter matching system overview
- `docs/multi_interview.md` - Multi-interview coexistence guide
- `docs/MIGRATION_MULTI_INTERVIEW.md` - Migration guide for existing agents
- `jvagent/action/parameter/README.md` - ParameterMatcher module documentation
- `examples/multi_interview_agent_example.yaml` - Example configuration
- `examples/multi_interview_example/README.md` - Complete example with usage patterns

### Changed

- **PersonaAction**:
  - `respond()` now uses matched_parameters when available
  - `_compose_prompt()` accepts optional visitor parameter
  - `_build_active_interviews_section()` collects state from active interviews
  - `_build_tool_results_section()` formats tool results for prompt
  - Backward compatible: falls back to legacy behavior when new features not used

- **InterviewInteractAction**:
  - Registers/unregisters with `Conversation.active_interviews` on create/complete/cancel
  - `_deactivate_interview()` helper removes from active_interviews
  - Added activation_conditions and exclusive attributes

- **Prompts** (`jvagent/action/persona/prompts.py`):
  - Updated SYSTEM_PROMPT_TEMPLATE with active_interviews_section and tool_results_section
  - Added MATCHED_PARAMETERS_SECTION_PROMPT
  - Added ACTIVE_INTERVIEWS_SECTION_PROMPT
  - Added TOOL_RESULTS_SECTION_PROMPT
  - Added helper functions: `format_matched_parameters_section()`, `format_active_interviews_section()`, `format_tool_results_section()`

### Backward Compatibility

All changes are backward compatible:
- Existing parameters default to `match_mode: "always"`
- Existing interviews work without activation_conditions
- PersonaAction falls back to legacy behavior
- InteractRouter unchanged (InterviewAwareRouter is optional subclass)
- No breaking changes to core InteractWalker, ResponseBus, or ModelAction

### Implementation Status

Completed:
- ✅ Phase 1: Extended parameter schema
- ✅ Phase 2: ParameterMatcher service (rule-based)
- ✅ Phase 3: InterviewAwareRouter and activation conditions
- ✅ Phase 4: Multi-interview coexistence tracking
- ✅ Phase 5: Context-managed prompting in PersonaAction

Remaining:
- ⏳ Phase 6: Parameter-bound tool execution and preparation loop
- 🔮 Future: LLM-based parameter matching
- 🔮 Future: Hybrid matching strategy
- 🔮 Future: Event log and multi-message batching

## Notes

This release implements the foundation for Parlant-style multiturn conversations while preserving jvagent's interact pipeline as the core framework. The design maintains backward compatibility and allows gradual adoption of new features.
