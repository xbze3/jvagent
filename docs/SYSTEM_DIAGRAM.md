# System Diagram: Multi-Interview Architecture

## Complete System Overview

```mermaid
graph TB
    subgraph User Layer
        User[User Message]
    end
    
    subgraph Entry Point
        API[API/Endpoint]
        Walker[InteractWalker]
    end
    
    subgraph Memory Layer
        Conv[Conversation]
        Int[Interaction]
        ISession[InterviewSession]
    end
    
    subgraph Routing Layer
        Router[InterviewAwareRouter]
        PM[ParameterMatcher]
    end
    
    subgraph Execution Layer
        IA1[InterviewInteractAction 1]
        IA2[InterviewInteractAction 2]
        Custom[Custom InteractActions]
    end
    
    subgraph Response Layer
        Persona[PersonaAction]
        Model[ModelAction]
        Bus[ResponseBus]
    end
    
    User --> API
    API --> Walker
    Walker --> Conv
    Walker --> Int
    
    Walker --> Router
    Router --> PM
    PM --> Int
    Router --> Conv
    
    Walker --> IA1
    Walker --> IA2
    Walker --> Custom
    
    IA1 --> ISession
    IA2 --> ISession
    IA1 --> Int
    IA2 --> Int
    
    Walker --> Persona
    Persona --> Int
    Persona --> Conv
    Persona --> Model
    Model --> Bus
    
    style Router fill:#e1f5ff
    style PM fill:#e1f5ff
    style IA1 fill:#fff4e1
    style IA2 fill:#fff4e1
    style Persona fill:#e8f5e9
```

## Request Flow Detail

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant W as InteractWalker
    participant R as InterviewAwareRouter
    participant PM as ParameterMatcher
    participant C as Conversation
    participant I as Interaction
    participant IA as InterviewInteractAction
    participant IS as InterviewSession
    participant P as PersonaAction
    participant M as ModelAction
    participant B as ResponseBus

    U->>W: Send message
    W->>C: get_session()
    W->>I: create Interaction
    W->>W: visit(Agent) → visit(Actions)
    
    W->>R: execute()
    R->>R: Base routing (intent classification)
    
    opt Parameter Matching Enabled
        R->>PM: match_parameters()
        PM->>I: Store matched_parameters
    end
    
    R->>C: get_all_active_interview_types()
    
    loop For each interview
        R->>R: Check activation_conditions
        alt Conditions match & not active
            R->>C: add_active_interview()
            R->>I: Add to routing (anchors)
        end
    end
    
    W->>IA: execute() [if routed]
    IA->>C: get_active_interview_session_id()
    
    alt No session
        IA->>IS: create InterviewSession
        IA->>C: add_active_interview()
    end
    
    IA->>IS: classify_and_extract()
    IA->>IS: update state
    IA->>I: add_directive()
    
    alt State = COMPLETED/CANCELLED
        IA->>C: remove_active_interview()
    end
    
    W->>P: execute()
    P->>I: get_matched_parameters() OR get_unexecuted_parameters()
    P->>C: get_all_active_interview_types()
    
    loop For each active interview
        P->>IS: Get current state
        P->>P: Build state directive
    end
    
    P->>I: get_tool_results()
    P->>P: Build context-managed prompt
    P->>M: generate(prompt, history)
    M-->>P: Response
    P->>B: publish(response)
    P->>I: Save response
    W->>B: finalize_interaction()
    B-->>U: Deliver response
```

## Data Flow

```mermaid
graph LR
    subgraph Configuration
        A[agent.yaml]
    end
    
    subgraph Runtime
        B[Parameters with match_mode]
        C[Interview with activation_conditions]
    end
    
    subgraph Per-Turn Processing
        D[ParameterMatcher]
        E[Activation Evaluator]
        F[Interview Executor]
    end
    
    subgraph Storage
        G[Interaction.matched_parameters]
        H[Conversation.active_interviews]
        I[InterviewSession]
    end
    
    subgraph Prompt Building
        J[Collect matched params]
        K[Collect interview states]
        L[Build context-managed prompt]
    end
    
    subgraph Response
        M[ModelAction]
        N[ResponseBus]
    end
    
    A --> B
    A --> C
    B --> D
    C --> E
    E --> F
    D --> G
    E --> H
    F --> I
    G --> J
    H --> K
    I --> K
    J --> L
    K --> L
    L --> M
    M --> N
```

## Interview Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Configured: Interview defined in agent.yaml
    
    Configured --> Evaluating: User message arrives
    
    Evaluating --> Inactive: Conditions don't match
    Evaluating --> Activating: Conditions match
    
    Activating --> Creating: Create InterviewSession
    Creating --> Registering: Add to active_interviews
    Registering --> Active: Start asking questions
    
    Active --> Active: User answers questions
    Active --> Review: All questions answered
    Review --> Active: User requests changes
    Review --> Completing: User confirms
    Active --> Cancelling: User cancels
    
    Completing --> Deregistering: Remove from active_interviews
    Cancelling --> Deregistering
    Deregistering --> Terminated: Session marked COMPLETED/CANCELLED
    Terminated --> [*]
    
    Inactive --> [*]: Not started
```

## Component Relationships

```mermaid
graph TB
    subgraph Agent Level
        Agent[Agent Node]
        Actions[Actions Node]
    end
    
    subgraph Action Level
        Router[InterviewAwareRouter]
        Interview1[SignupInterview]
        Interview2[ProfileInterview]
        Persona[PersonaAction]
    end
    
    subgraph Service Level
        Matcher[ParameterMatcher]
        Tools[Tool Registry]
    end
    
    subgraph Memory Level
        Conv[Conversation]
        Int[Interaction]
        Session1[InterviewSession 1]
        Session2[InterviewSession 2]
    end
    
    Agent --> Actions
    Actions --> Router
    Actions --> Interview1
    Actions --> Interview2
    Actions --> Persona
    
    Router --> Matcher
    Router --> Conv
    Router --> Int
    
    Interview1 --> Session1
    Interview2 --> Session2
    Interview1 --> Int
    Interview2 --> Int
    
    Session1 --> Conv
    Session2 --> Conv
    Int --> Conv
    
    Persona --> Int
    Persona --> Conv
    Persona --> Session1
    Persona --> Session2
    
    Matcher --> Int
    Tools --> Int
    
    style Router fill:#e1f5ff
    style Matcher fill:#e1f5ff
    style Interview1 fill:#fff4e1
    style Interview2 fill:#fff4e1
    style Persona fill:#e8f5e9
```

## Parameter Flow

```mermaid
graph LR
    subgraph Definition
        P1[Parameter: match_mode=always]
        P2[Parameter: match_mode=matched]
    end
    
    subgraph Evaluation
        E1[Push to prompt]
        E2[ParameterMatcher]
    end
    
    subgraph Results
        R1[All in prompt]
        R2[Matched subset]
    end
    
    subgraph Prompt
        Pr1[Full parameters section]
        Pr2[Matched parameters section]
    end
    
    P1 --> E1
    P2 --> E2
    E1 --> R1
    E2 --> R2
    R1 --> Pr1
    R2 --> Pr2
    Pr1 --> Model[ModelAction]
    Pr2 --> Model
    
    style E2 fill:#e1f5ff
    style R2 fill:#e1f5ff
    style Pr2 fill:#e8f5e9
```

## Multi-Interview State

```mermaid
graph TB
    subgraph Conversation
        AI[active_interviews]
    end
    
    subgraph Interview Sessions
        S1[SignupInterview Session]
        S2[ProfileInterview Session]
        S3[FAQInterview Session]
    end
    
    subgraph States
        ST1[State: ACTIVE<br/>Question: email]
        ST2[State: REVIEW<br/>Confirming info]
        ST3[State: COMPLETED<br/>Done]
    end
    
    subgraph Prompt
        PR[PersonaAction Prompt]
    end
    
    AI -->|"SignupInterview" → id1| S1
    AI -->|"ProfileInterview" → id2| S2
    
    S1 --> ST1
    S2 --> ST2
    S3 --> ST3
    
    ST1 -->|Active: Include| PR
    ST2 -->|Active: Include| PR
    ST3 -->|Completed: Exclude| PR
    
    style AI fill:#fff4e1
    style PR fill:#e8f5e9
```

## Comparison: Before vs After

### Before (Single Interview, All Parameters)

```mermaid
graph LR
    U[User] --> W[Walker]
    W --> R[Router]
    R --> I1[Interview 1]
    I1 --> P[PersonaAction]
    
    subgraph Prompt
        D[Directives from I1]
        Params[All 20 parameters]
    end
    
    P --> D
    P --> Params
    P --> M[Model]
    
    style Params fill:#ffcccc
```

### After (Multi-Interview, Matched Parameters)

```mermaid
graph LR
    U[User] --> W[Walker]
    W --> R[InterviewAwareRouter]
    R --> PM[ParameterMatcher]
    PM --> I1[Interview 1]
    PM --> I2[Interview 2]
    I1 --> P[PersonaAction]
    I2 --> P
    
    subgraph Prompt
        D1[Directive: I1 state]
        D2[Directive: I2 state]
        MP[Matched 3/20 parameters]
    end
    
    P --> D1
    P --> D2
    P --> MP
    P --> M[Model]
    
    style R fill:#e1f5ff
    style PM fill:#e1f5ff
    style MP fill:#ccffcc
```

The prompt is **smaller** and **more focused**, leading to better responses.

## Integration Points

```mermaid
graph TB
    subgraph External
        Client[Frontend Client]
        API[REST API]
    end
    
    subgraph JVAgent Core
        Walker[InteractWalker]
        Actions[InteractActions]
        Persona[PersonaAction]
    end
    
    subgraph New Layer
        Router[InterviewAwareRouter]
        Matcher[ParameterMatcher]
    end
    
    subgraph Memory
        Conv[Conversation]
        Int[Interaction]
    end
    
    Client --> API
    API --> Walker
    Walker --> Router
    Router --> Matcher
    Matcher --> Int
    Router --> Conv
    Walker --> Actions
    Actions --> Persona
    Persona --> Int
    Persona --> Conv
    
    style Router fill:#e1f5ff
    style Matcher fill:#e1f5ff
```

The new layer integrates seamlessly with existing components without requiring changes to the core walker, actions, or response pipeline.
