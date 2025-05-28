# Prompt Organization with FormatPrompt

The prompt system in our framework centers around the `FormatPrompt` class, which provides a powerful templating mechanism for dynamic prompt generation. This system enables flexible, context-aware prompts that can adapt to different situations while maintaining a consistent structure.

## Core Components

### FormatPrompt

FormatPrompt is a powerful class for handling prompt templating with features like:

- Variable substitution using simple `{variable}` syntax
- Expression evaluation with `${expression}` syntax
- System prompt integration
- Binding to objects and methods
- Automatic async detection and handling
- Dialog format conversion

## Supported Formatting Styles

FormatPrompt supports two primary formats for including dynamic content:

1. **Simple Variable Substitution** - `{variable}`
   - Direct substitution of variable values
   - Example: `"Hello, {name}!"`

2. **Expression Evaluation** - `${expression}`
   - Evaluates Python expressions
   - Can access bound objects
   - Supports async functions (automatically awaited)
   - Example: `"Today's weather: ${environment.get_weather()}"`

## Basic Usage

The simplest way to use FormatPrompt is with direct key-value pairs:

```python
from agentsociety.agent.prompt import FormatPrompt

# Create a template
template = FormatPrompt("Hello, my name is {name} and I am {age} years old.")

# Format with key-value pairs
await template.format(name="Alice", age=30)

# Get the formatted string
formatted_text = template.formatted_string
print(formatted_text)  # "Hello, my name is Alice and I am 30 years old."

# Convert to dialog format (for LLM interactions)
dialog = template.to_dialog()  # Returns a list of message objects
```

## System Prompts

FormatPrompt supports system prompts for LLM interactions:

```python
# Create template with system prompt
template = FormatPrompt(
    "Please analyze this data: {data}",
    system_prompt="You are a data analyst AI. Provide concise insights."
)

# Generate dialog format for LLM
dialog = template.to_dialog()
```

## Binding Environment Variables

You can bind objects to the FormatPrompt at initialization or later using the `bind()` method:

```python
# Binding at initialization
env = Environment()
template = FormatPrompt(
    "The current temperature is ${weather.temperature}°C.", 
    **{"weather": env.weather_service}
)

# Or binding later
database = Database()
template.bind(db=database)

# Now expressions can access these objects
await template.format()  # "The current temperature is 22°C."
```

## Formatting with Agent or Block Context

FormatPrompt can use agent or block contexts to resolve variables:

```python
# Create a template that uses agent properties
agent_template = FormatPrompt(
    "Agent {name} is at location {location} with {energy} energy remaining."
)

# Format using an agent
await agent_template.format(agent=my_agent)
```

The `format()` method will look for variables in this order of precedence:
1. Explicitly provided kwargs
2. Method arguments (if associated with a method)
3. Agent attributes or memory
4. Block attributes
5. Bound objects

## Advanced Usage

Combining binding and explicit formatting provides maximum flexibility:

```python
DEFAULT_PROMPT = """
My name is {name}, hello {target_name}!
"""

class ExampleClass:
    def __init__(self, agent: Agent, tool: Any, environment: Any, prompt: str = DEFAULT_PROMPT):
        self.agent = agent
        self.tool = tool
        self.environment = environment
        self.format_prompt = FormatPrompt(
            prompt,
            tool=tool, # bind objects into format prompt
            environment=environment,
        )

    def get_name(self, name: str, target_name: str):
        self.format_prompt.format(
            agent=self.agent,  # import agent as the format context
            method_args={"name": name, "target_name": target_name},  # pass method arguments into the context
        )
        return self.format_prompt.formatted_string
```

By doing so, even if users initailize the ExampleClass with a different prompt, the format prompt will still be able to access the agent and tool objects. For example:

```python
prompt_to_use = """
===========================
My name is {name}
My age is {age}
===========================

Hello {target_name}! Today is ${environment.get_date()}, I want to tell you that ${tool.get_message()}
"""

example = ExampleClass(agent, tool, environment, prompt_to_use)
print(example.get_name("Alice"))
```

In the upper example, the `age` will extract from the `agent` object, and the `target_name` will extract from the `method_args`; while `${environment.get_date()}` and `${tool.get_message()}` will extract from the `environment` and `tool` objects respectively. This is quite powerful when you want to share you work with other people.

## Expression Evaluation Considerations

When using the `${expression}` syntax:

1. **Safety**: Expressions are checked for safety to prevent code injection
2. **Async Support**: Async functions are automatically awaited
3. **Bound Objects**: All bound objects are available in the expression context
4. **Limitations**: Import statements, exec(), eval(), and other potentially unsafe operations are blocked
5. **Error Handling**: If expression evaluation fails, the original expression text is preserved

This architecture allows for flexible, context-aware prompt templates that can be reused across different agents and scenarios while maintaining consistent structure.
