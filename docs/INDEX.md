# Documentation Index: Multi-Interview and Parameter Matching

## Start Here

**New to the system?** → [README_MULTI_INTERVIEW.md](README_MULTI_INTERVIEW.md)  
**Implementing?** → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)  
**Migrating existing agent?** → [MIGRATION_MULTI_INTERVIEW.md](MIGRATION_MULTI_INTERVIEW.md)

---

## Documentation by Purpose

### Getting Started

1. **[README_MULTI_INTERVIEW.md](README_MULTI_INTERVIEW.md)**
   - Overview of all features
   - Quick start guide
   - Links to detailed docs
   - Performance metrics
   - Status and roadmap

2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
   - Parameter schema
   - API reference
   - Configuration examples
   - Helper functions
   - Common patterns
   - Debugging checklist

### Feature Guides

3. **[parameter_matching.md](parameter_matching.md)**
   - Parameter matching system
   - Match modes (always, matched)
   - ParameterMatcher strategies
   - Interview-scoped parameters
   - Integration with PersonaAction
   - Usage examples

4. **[multi_interview.md](multi_interview.md)**
   - Multi-interview coexistence
   - Interview lifecycle
   - Activation conditions
   - Exclusive mode
   - Conversation helpers
   - Typical flows
   - Best practices

### Migration and Deployment

5. **[MIGRATION_MULTI_INTERVIEW.md](MIGRATION_MULTI_INTERVIEW.md)**
   - Schema changes explained
   - Migration paths (3 options)
   - Testing checklist
   - Rollback instructions
   - Common patterns
   - Progressive enhancement approach

### Architecture and Design

6. **[architecture_multi_interview.md](architecture_multi_interview.md)**
   - High-level architecture
   - Component interaction
   - Data flow diagrams
   - Storage schema
   - Extensibility points
   - Performance considerations

7. **[comparison_parlant_jvagent.md](comparison_parlant_jvagent.md)**
   - Terminology mapping
   - Architecture comparison
   - Feature parity matrix
   - Prompt structure comparison
   - Key differences explained
   - When to use which approach

8. **[DESIGN_RATIONALE.md](DESIGN_RATIONALE.md)**
   - Why parameters stay "parameters"
   - Why InterviewSession IS journey session
   - Why router stays generic
   - Hybrid instruction sources
   - Action-centric journeys
   - Optional enhancement philosophy
   - Design patterns used

9. **[SYSTEM_DIAGRAM.md](SYSTEM_DIAGRAM.md)**
   - Complete system overview (Mermaid)
   - Request flow detail
   - Data flow visualization
   - Interview lifecycle diagram
   - Component relationships
   - Before/after comparison

### Implementation Details

10. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**
    - What was implemented (phase by phase)
    - Files created/modified
    - What remains
    - File inventory
    - Usage patterns
    - Performance impact

11. **[../REFACTOR_REPORT.md](../REFACTOR_REPORT.md)**
    - Implementation metrics
    - Architecture changes
    - Key features
    - Benefits breakdown
    - Testing status
    - Recommendations

12. **[../IMPLEMENTATION_COMPLETE.md](../IMPLEMENTATION_COMPLETE.md)**
    - Status summary
    - What was delivered
    - Validation results
    - Usage examples
    - Success criteria
    - Next actions

---

## Documentation by Role

### I'm a Developer Implementing This

Start: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)  
Then: [parameter_matching.md](parameter_matching.md) + [multi_interview.md](multi_interview.md)  
Reference: Module READMEs (`jvagent/action/parameter/README.md`)

### I'm Migrating an Existing Agent

Start: [MIGRATION_MULTI_INTERVIEW.md](MIGRATION_MULTI_INTERVIEW.md)  
Then: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)  
Reference: [README_MULTI_INTERVIEW.md](README_MULTI_INTERVIEW.md)

### I'm an Architect Reviewing This

Start: [architecture_multi_interview.md](architecture_multi_interview.md)  
Then: [DESIGN_RATIONALE.md](DESIGN_RATIONALE.md)  
Compare: [comparison_parlant_jvagent.md](comparison_parlant_jvagent.md)

### I'm Coming from Parlant

Start: [comparison_parlant_jvagent.md](comparison_parlant_jvagent.md)  
Then: [README_MULTI_INTERVIEW.md](README_MULTI_INTERVIEW.md)  
Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### I Want to Understand the Design

Start: [DESIGN_RATIONALE.md](DESIGN_RATIONALE.md)  
Then: [architecture_multi_interview.md](architecture_multi_interview.md)  
Visual: [SYSTEM_DIAGRAM.md](SYSTEM_DIAGRAM.md)

---

## Key Documents by Topic

### Parameter Matching

- [parameter_matching.md](parameter_matching.md) - Feature guide
- [jvagent/action/parameter/README.md](../jvagent/action/parameter/README.md) - Module docs
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Syntax reference

### Multi-Interview

- [multi_interview.md](multi_interview.md) - Feature guide
- [MIGRATION_MULTI_INTERVIEW.md](MIGRATION_MULTI_INTERVIEW.md) - Migration steps
- [examples/multi_interview_example/README.md](../examples/multi_interview_example/README.md) - Working example

### Architecture

- [architecture_multi_interview.md](architecture_multi_interview.md) - Technical details
- [SYSTEM_DIAGRAM.md](SYSTEM_DIAGRAM.md) - Visual diagrams
- [comparison_parlant_jvagent.md](comparison_parlant_jvagent.md) - Cross-framework

### Implementation

- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was built
- [../REFACTOR_REPORT.md](../REFACTOR_REPORT.md) - Detailed report
- [../IMPLEMENTATION_COMPLETE.md](../IMPLEMENTATION_COMPLETE.md) - Status

---

## Quick Navigation

**Need help choosing?** Use this decision tree:

```
START
  ├─ Want overview? → README_MULTI_INTERVIEW.md
  ├─ Want to implement? → QUICK_REFERENCE.md
  ├─ Want to migrate? → MIGRATION_MULTI_INTERVIEW.md
  ├─ Want to understand design? → DESIGN_RATIONALE.md
  ├─ Want technical details? → architecture_multi_interview.md
  ├─ Coming from Parlant? → comparison_parlant_jvagent.md
  └─ Want examples? → examples/multi_interview_example/
```

---

## Examples and Tutorials

### Configuration Examples

- [examples/multi_interview_agent_example.yaml](../examples/multi_interview_agent_example.yaml)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Multiple configuration patterns

### Complete Working Example

- [examples/multi_interview_example/README.md](../examples/multi_interview_example/README.md)

### Code Examples

Throughout the docs:
- Parameter matching examples
- Multi-interview flows
- Activation condition patterns
- Interview-scoped parameters
- Context-managed prompting

---

## Testing and Validation

### Test Files

- `tests/action/parameter/test_matcher.py` - ParameterMatcher tests

### Validation

See [IMPLEMENTATION_COMPLETE.md](../IMPLEMENTATION_COMPLETE.md):
- ✅ Compilation successful
- ✅ Syntax validation passed
- ⏳ Unit tests require environment

### Manual Testing

See [MIGRATION_MULTI_INTERVIEW.md](MIGRATION_MULTI_INTERVIEW.md):
- Testing checklist
- Common scenarios
- Debugging guide

---

## Support and Troubleshooting

### Common Issues

See [MIGRATION_MULTI_INTERVIEW.md](MIGRATION_MULTI_INTERVIEW.md) - Debugging section

### Logging

```python
import logging
logging.getLogger("jvagent.action.parameter").setLevel(logging.DEBUG)
logging.getLogger("jvagent.action.router").setLevel(logging.DEBUG)
logging.getLogger("jvagent.action.interview").setLevel(logging.DEBUG)
```

### Log Messages to Watch

```
INFO  SignupInterview: Registered as active interview
INFO  InterviewAwareRouter: Matched 3 parameters
DEBUG PersonaAction.respond: Using 3 matched parameters
INFO  SignupInterview: Removed from active interviews (state: COMPLETED)
```

---

## Contributing

### Adding Features

1. Review [DESIGN_RATIONALE.md](DESIGN_RATIONALE.md) for design philosophy
2. Follow existing patterns (extension, not replacement)
3. Maintain backward compatibility
4. Update relevant documentation
5. Add tests

### Extending Matching

See `jvagent/action/parameter/matcher.py`:
- Implement `_match_llm_based()` for LLM strategy
- Implement `_match_hybrid()` for hybrid approach
- Add strategy to ParameterMatcher.__init__()

### Adding New Router Modes

Extend InterviewAwareRouter or create new subclass:
```python
class CustomRouter(InterviewAwareRouter):
    async def _handle_interview_delegation(self, ...):
        # Your custom logic
```

---

## Change Log

See [../CHANGELOG.md](../CHANGELOG.md) for complete change history.

---

## Summary

This documentation suite provides everything needed to:
- ✅ Understand the new system
- ✅ Implement features in agents
- ✅ Migrate existing agents
- ✅ Extend the system
- ✅ Troubleshoot issues
- ✅ Compare with Parlant

**Start with README_MULTI_INTERVIEW.md, then use this index to find specific topics.**
