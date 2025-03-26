from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

# Define the state schema.
class State(TypedDict):
    messages: Annotated[list, add_messages]  # List of messages (each message is a simple dict)
    wants_joke: bool  # A flag to indicate if the user asked for a joke

# Create a graph builder using our state.
graph_builder = StateGraph(State)

def greet(state: State):
    # Append a greeting message.
    greeting = {"role": "assistant", "content": "Hello! I am your friendly assistant. How can I help you today?"}
    # Return an update: we add this greeting to the messages.
    return {"messages": state["messages"] + [greeting]}


def process_input(state: State):
    # Assume the last message in the conversation is from the user.
    last_message = state["messages"][-1]
    # Check for the keyword "joke" (case-insensitive).
    if "joke" in last_message["content"].lower():
        state["wants_joke"] = True
    else:
        state["wants_joke"] = False
    # Append a processing message.
    processing_msg = {"role": "assistant", "content": "Let me process your request..."}
    return {"messages": state["messages"] + [processing_msg], "wants_joke": state["wants_joke"]}

def tell_joke(state: State):
    joke = "Why did the scarecrow win an award? Because he was outstanding in his field!"
    joke_msg = {"role": "assistant", "content": joke}
    return {"messages": state["messages"] + [joke_msg]}

def ask_clarification(state: State):
    clarification = "I'm sorry, I didn't understand your request. Could you please clarify what you need?"
    clarify_msg = {"role": "assistant", "content": clarification}
    return {"messages": state["messages"] + [clarify_msg]}

def wants_joke_condition(state: State):
    # Return True if the user asked for a joke.
    return state.get("wants_joke", False)


# Add nodes to the graph.
graph_builder.add_node("greet", greet)
graph_builder.add_node("process", process_input)
graph_builder.add_node("tell_joke", tell_joke)
graph_builder.add_node("ask_clarification", ask_clarification)

# Set up the edges.
graph_builder.add_edge(START, "greet")         # The graph starts at the greeting node.
graph_builder.add_edge("greet", "process")       # After greeting, process the input.
graph_builder.add_conditional_edges("process", wants_joke_condition, {True: "tell_joke", False: "ask_clarification"})
graph_builder.add_edge("tell_joke", END)         # End the workflow after telling the joke.
graph_builder.add_edge("ask_clarification", END) # End after asking for clarification.


# Compile the graph.
graph = graph_builder.compile()

# Define the initial state with a user message.
initial_state = {
    "messages": [{"role": "user", "content": "Tell me a joke!"}],
    "wants_joke": False  # default value
}

# Invoke the graph with the initial state.
result = graph.invoke(initial_state)

# Print the final assistant message.
final_message = result["messages"][-1]
print("Final Output:", final_message["content"])
