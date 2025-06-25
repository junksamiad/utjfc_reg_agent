flowchart TD
    A[User Message] --> B{Has routine_number?}
    B -->|Yes| C[New Registration Agent]
    B -->|No| D{Has last_agent?}
    D -->|re_registration| E[Re-Registration Agent]
    D -->|new_registration| F[New Registration Agent]
    D -->|No| G{Valid registration code?}
    G -->|Yes| H[Route to Registration Flow]
    G -->|No| I[**Universal Agent**]
    I --> J[Database Operations]
    I --> K[General Club Info]
    I --> L[Business Logic Handling]