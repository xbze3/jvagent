# Multi-Interview Example Agent

This example demonstrates an agent that can handle multiple coexisting interviews simultaneously using the new parameter matching and multi-interview features.

## Features Demonstrated

1. **Multiple Coexisting Interviews**: User can start signup and profile update simultaneously
2. **Interview Activation Conditions**: Interviews start automatically based on user intent
3. **Interview-Scoped Parameters**: Parameters apply only within specific interviews
4. **Context-Managed Prompting**: Only matched parameters included in prompt
5. **InterviewAwareRouter**: Handles activation and delegation

## Agent Structure

```
MultiInterviewAgent/
├── InterviewAwareRouter (automatic routing + parameter matching)
├── SignupInterviewAction (can coexist)
│   └── Questions: email, password, name
├── ProfileUpdateInterview (can coexist)
│   └── Questions: name, bio, preferences
├── EmergencyResetInterview (exclusive - pauses others)
│   └── Questions: confirmation, reason
└── PersonaAction (responds with multi-interview context)
```

## Usage Examples

### Example 1: Single Interview

```
User: I want to sign up
Agent: Great! Let's get you started. What email address would you like to use?
User: test@example.com
Agent: Perfect! Now please create a password...
```

### Example 2: Coexisting Interviews

```
User: I want to sign up
Agent: Great! Let's get you started. What email address would you like to use?

User: Actually, can I also update my profile?
Agent: Of course! I can help with both. For signup: what email would you like?
      And for your profile: what would you like to update?

User: My signup email is test@example.com and I want to change my bio
Agent: Excellent! I've recorded your signup email. For your profile bio, 
       what would you like it to say?
```

### Example 3: Exclusive Interview

```
User: I need to reset everything urgently
Agent: I understand this is urgent. Starting emergency reset will pause your other 
       activities. Are you sure you want to proceed?
User: Yes
Agent: [SignupInterview and ProfileUpdate are now paused]
       OK, please confirm you want to reset by typing "CONFIRM RESET"
```

## Configuration

See `multi_interview_agent.yaml` for the complete configuration.

Key settings:
- `InterviewAwareRouter.enable_parameter_matching: true`
- Interview `activation_conditions` for automatic start
- Interview `exclusive: false` for coexistence
- Parameters with `match_mode: "matched"` for context-managed prompting

## Running

```bash
# Start the agent
jvagent run --config examples/multi_interview_example/multi_interview_agent.yaml

# Or programmatically
python examples/multi_interview_example/run_example.py
```

## Testing

Test scenarios:
1. Start signup alone
2. Start profile update alone
3. Start both simultaneously
4. Complete one while other continues
5. Trigger exclusive interview (resets)
6. Verify parameters match correctly
7. Check active_interviews tracking

## Implementation Notes

- SignupInterviewAction and ProfileUpdateInterview are standard InterviewInteractActions
- activation_conditions use simple phrases users might say
- exclusive=true on EmergencyResetInterview deactivates others
- PersonaAction prompt includes all active interview states
- Parameters scoped to interviews avoid cross-contamination
