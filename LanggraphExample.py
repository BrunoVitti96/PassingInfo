# Step 1: Import necessary components.
# - StateGraph helps us build the graph.
# - START and END are special markers for where the graph begins and ends.
# - add_messages is a helper to tell LangGraph to add new messages to our list.
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# We also import an LLM client. In this example we use ChatOpenAI.
from langchain_openai import ChatOpenAI

# To define our state, we use TypedDict.
from typing_extensions import TypedDict
from typing import Annotated

# Step 2: Define the state.
# Here, our state is a dictionary with one key: "messages".
# The "Annotated" part tells LangGraph that when a new message comes in, it should be added (appended) to the list.
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

# Step 3: Create a graph with the state.
graph = StateGraph(ChatState)

# Step 4: Initialize your language model.
# Here we use ChatOpenAI with a specified model and set temperature=0 for deterministic output.
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Step 5: Define a node (a function that will be a step in our graph).
# This function takes the current state (our notebook of messages),
# calls the LLM with all the messages, and returns a new message to add.
def chatbot_node(state: ChatState):
    # state["messages"] is our list of conversation messages.
    response = llm.invoke(state["messages"])
    # Return a dictionary that updates the state.
    # Because we set up our state with "add_messages", this new message will be appended.
    return {"messages": [response]}

# Step 6: Add the node to the graph.
# We give the node a name ("chatbot") so we can refer to it.
graph.add_node("chatbot", chatbot_node)

# Step 7: Define where the graph should start.
# We set the entry point to our "chatbot" node.
graph.set_entry_point("chatbot")

# Step 8: Define the finish.
# In this simple example, we say that once the "chatbot" node runs, we are finished.
graph.add_edge("chatbot", END)

# Step 9: Compile the graph.
# Compilation checks the graph structure and makes it ready for running.
compiled_graph = graph.compile()

# Step 10: Create an initial state.
# We start the conversation by providing a user message.
from langchain_core.messages import HumanMessage
initial_state = {"messages": [HumanMessage(content="Hello, what is LangGraph?")]}

# Step 11: Run the graph (i.e. have the chatbot respond).
result = compiled_graph.invoke(initial_state)

# Step 12: Print the final response from the chatbot.
print(result["messages"][-1].content)
