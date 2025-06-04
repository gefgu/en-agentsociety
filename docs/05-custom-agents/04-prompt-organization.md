# Prompt Organization with FormatPrompt

The FormatPrompt class is the core of the prompt system in our framework, providing a powerful templating mechanism for dynamic prompt generation. This system supports flexible, context-aware prompts that can adapt to different situations while maintaining a consistent structure.

## Core Components

### FormatPrompt

FormatPrompt is a powerful class for handling prompt templating with features like:

- Simple variable substitution using `{variable}` syntax
- Expression evaluation with `${expression}` syntax for memory and context access
- System prompt integration
- Memory integration for profile and status access
- Safety checks for expression evaluation
- Dialog format conversion for LLM interactions

## Supported Formatting Styles

FormatPrompt supports two main formats for dynamic content:

1. **Simple Variable Substitution** - `{variable}`
   - Direct substitution of variable values passed as kwargs
   - Used for customizable prompts where values are provided at runtime
   - Example: `"Hello, {name}!"`

2. **Expression Evaluation** - `${expression}`
   - Evaluates safe expressions to access memory and context
   - Supports three main patterns:
     - `${profile.xxx}` - Access agent profile data from memory
     - `${status.xxx}` - Access agent status data from memory  
     - `${context.xxx}` - Access values from the provided context dictionary
   - Supports nested access with square brackets: `${profile.user["preferences"]}`
   - Example: `"Current status: ${status.energy_level}"`

**Important Note**: It is strongly discouraged to mix `{}` and `${}` syntax. Choose one format and maintain consistency throughout the entire template.

## Usage Scenarios

### Scenario 1: Static Prompts with Runtime Variables

Scenario 1 is suitable for prompts that don't need modification, directly defining variables through `{}` and passing key-value pairs for replacement during usage.

This approach is suitable for:
- Fixed prompt templates
- Variables that need specific values provided at runtime
- Scenarios that don't require access to agent internal state

```python
from agentsociety.agent.prompt import FormatPrompt

# Create a template with simple variable placeholders
template = FormatPrompt("Hello, my name is {name} and I am {age} years old.")

# Format with key-value pairs
await template.format(name="Alice", age=30)

# Get the formatted string
formatted_text = template.formatted_string
print(formatted_text)  # "Hello, my name is Alice and I am 30 years old."

# Convert to dialog format for LLM interactions
dialog = template.to_dialog()
```

### Scenario 2: Shareable Agent/Block Designs

Scenario 2 is suitable when you want to share your agent/block design and allow users to customize prompts. For such prompts, you need to use `${}` to define variables, which allows access to the agent's internal state.

This approach is suitable for:
- Need to access agent's profile and status data
- Shareable agent designs
- Scenarios requiring dynamic access to context information

```python
from agentsociety.agent.prompt import FormatPrompt

# Template that accesses agent's internal state
template = FormatPrompt(
    """
    Agent Status Report:
    - Name: ${profile.name}
    - Current Energy: ${status.energy_level}
    - Location: ${status.current_location}
    - Mission: ${context.current_mission}
    """,
    memory=agent_memory
)

# Format with context (no need to pass individual variables)
await template.format(context={"current_mission": "Explore the forest"})

formatted_text = template.formatted_string
```

## Basic Implementation Examples

### Simple Variable Substitution Usage

```python
# For prompts that need runtime values
user_prompt = FormatPrompt(
    "Please analyze the {data_type} data for {customer_name}. "
    "Focus on {analysis_focus} and provide insights."
)

await user_prompt.format(
    data_type="sales",
    customer_name="TechCorp",
    analysis_focus="quarterly trends"
)
```

### Expression Evaluation Usage

```python
# For prompts that access agent state
agent_prompt = FormatPrompt(
    """
    Current agent state:
    - Energy: ${status.energy}/100
    - Mood: ${profile.personality["mood"]}
    - Task: ${context.active_task}
    
    Based on my current state, I will proceed with the mission.
    """,
    memory=agent.memory
)

await agent_prompt.format(context={"active_task": "data collection"})
```

## Advanced Expression Features

### Nested Access Patterns

FormatPrompt supports nested access patterns, including dictionary keys and array indices:

```python
# Accessing nested dictionary values
template = FormatPrompt(
    "User preference: ${profile.settings['ui_theme']} theme",
    memory=memory
)

# Accessing array elements
template = FormatPrompt(
    "Latest log entry: ${status.logs[0]}",
    memory=memory
)
```

### Safety and Error Handling

Expression evaluation includes safety check mechanisms:

- Only allows access to `profile`, `status`, and `context` objects
- Supports attribute access with dot notation
- Supports dictionary/array access with square brackets
- Prevents execution of arbitrary code
- Returns "Don't know" for failed evaluations

```python
# Safe expressions
"${profile.name}"                    # ✓ Attribute access
"${status.energy_level}"            # ✓ Attribute access  
"${profile.settings['theme']}"      # ✓ Dictionary access
"${context.data[0]}"                # ✓ Array access

# Unsafe expressions (will be rejected)
"${import os}"                      # ✗ Import statements
"${exec('malicious code')}"         # ✗ Code execution
```

## System Prompts and Dialog Conversion

FormatPrompt supports system prompts for LLM interactions:

```python
# Create template with system prompt
template = FormatPrompt(
    "Current status: ${status.energy_level}. What should I do next?",
    system_prompt="You are a helpful AI agent. Provide clear guidance.",
    memory=agent_memory
)

# Generate dialog format for LLM
await template.format()
dialog = template.to_dialog()
# Returns: [
#   {"role": "system", "content": "You are a helpful AI agent..."},
#   {"role": "user", "content": "Current status: 85. What should I do next?"}
# ]
```

## Best Practices

1. **Choose One Format**: Choose either `{}` or `${}` format and maintain consistency throughout the entire template
2. **Scenario-Based Selection**: 
   - Use `{}` for runtime variable substitution
   - Use `${}` for accessing agent state and creating shareable designs
3. **Error Handling**: Always handle potential evaluation errors gracefully
4. **Safety First**: Only use trusted expressions in `${}` syntax
5. **Memory Integration**: Ensure proper memory setup when using `${}` expressions

This architecture provides flexible, safe prompt templating that can be adapted for both simple variable substitution and complex agent state access scenarios.
