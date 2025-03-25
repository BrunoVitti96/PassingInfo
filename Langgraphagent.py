# Import standard libraries and typing helpers
from typing import TypedDict, Any
import operator

# Import LangGraph components
from langgraph.graph import StateGraph, START, END
# (The add_messages helper is often used to merge list-type state keys.)
from langgraph.graph.message import add_messages

# ------------------------------------------------------------------------------
# Define the state schema for our exchange processing workflow.
# This state holds:
#   - file_text: the raw text content extracted from a customer file.
#   - bank_channels_info: dictionary for bank channel, amount, currency, and beneficiaries.
#   - modality: the determined operation modality.
#   - additional_info: modality-specific extracted fields.
# ------------------------------------------------------------------------------
class ExchangeState(TypedDict):
    file_text: str
    bank_channels_info: Any  # will be a dict once extracted; initially None
    modality: str | None
    additional_info: Any  # modality‐specific info (dict) or None

# ------------------------------------------------------------------------------
# Node 1: (Optional) “Extract” file content.
# In a real scenario this might read a PDF, image, etc. Here we assume file_text is provided.
# ------------------------------------------------------------------------------
def extract_file_content(state: ExchangeState) -> ExchangeState:
    # In a production system, add OCR/PDF extraction here.
    # For this example we simply pass the file_text as is.
    return state

# ------------------------------------------------------------------------------
# Node 2: Extract bank channel information.
#
# Uses the “bank chanel extraction prompt” (a prompt we assume is defined elsewhere)
# to extract details such as bank channels, amount, currency, and beneficiaries.
# ------------------------------------------------------------------------------
def extract_bank_channels(state: ExchangeState) -> ExchangeState:
    # Construct a prompt using the available bank channel extraction prompt.
    # (In practice, you would call your LLM’s invoke method here.)
    prompt = (
        "bank chanel extraction prompt:\n"
        "Extract the bank channels, operation amount, currency, and, if applicable, "
        "split the payment among multiple beneficiaries from the following text:\n"
        f"{state['file_text']}"
    )
    # For this example, we simulate the LLM output:
    result = {
        "channels": "Online Banking, Wire Transfer",
        "amount": "10000",
        "currency": "USD",
        "beneficiaries": ["Beneficiary A", "Beneficiary B"],
    }
    state["bank_channels_info"] = result
    return state

# ------------------------------------------------------------------------------
# Node 3: Determine the operation modality.
#
# Uses the “modality prompt” to decide if the operation is, for example,
# "import already arrived", "import with advance payment", or "service".
# ------------------------------------------------------------------------------
def determine_modality(state: ExchangeState) -> ExchangeState:
    prompt = (
        "modality prompt:\n"
        "Based on the following file text and bank channels info, determine the modality "
        "of the operation (e.g., 'import already arrived', 'import with advance payment', or 'service').\n"
        f"Text: {state['file_text']}\n"
        f"Bank Channels: {state['bank_channels_info']}\n"
    )
    # Simulate an LLM response. For example, we assume the modality is "advance payment".
    modality = "advance payment"
    state["modality"] = modality
    return state

# ------------------------------------------------------------------------------
# Node 4a: If modality is "advance payment", extract additional info (e.g. expected shipment date).
#
# Uses the “advance payment prompt.”
# ------------------------------------------------------------------------------
def extract_advance_payment_info(state: ExchangeState) -> ExchangeState:
    prompt = (
        "advance payment prompt:\n"
        "From the following text, extract the expected shipment date for the import with advance payment:\n"
        f"{state['file_text']}"
    )
    # Simulate output:
    info = {"expected_shipment_date": "2025-04-15"}
    state["additional_info"] = info
    return state

# ------------------------------------------------------------------------------
# Node 4b: If modality is "import already arrived", extract declaration details.
#
# Uses the “declaration import prompt.”
# ------------------------------------------------------------------------------
def extract_declaration_import_info(state: ExchangeState) -> ExchangeState:
    prompt = (
        "declaration import prompt:\n"
        "From the following text, extract the declaration details including protocol and value:\n"
        f"{state['file_text']}"
    )
    # Simulate output:
    info = {"protocol": "ABC123", "declaration_value": "5000"}
    state["additional_info"] = info
    return state

# ------------------------------------------------------------------------------
# Node 4c: If modality is "service", extract service-related information.
#
# Uses the “services prompt.”
# ------------------------------------------------------------------------------
def extract_services_info(state: ExchangeState) -> ExchangeState:
    prompt = (
        "services prompt:\n"
        "From the following text, extract details relevant to the service operation:\n"
        f"{state['file_text']}"
    )
    # Simulate output:
    info = {"service_details": "Maintenance service contract details"}
    state["additional_info"] = info
    return state

# ------------------------------------------------------------------------------
# Define a conditional function that routes the workflow after modality determination.
#
# Returns a key that will select the next node:
#   - "advance_payment" if modality is "advance payment"
#   - "declaration_import" if modality is "import already arrived"
#   - "services" if modality is "service"
# ------------------------------------------------------------------------------
def modality_condition(state: ExchangeState) -> str:
    modality = state.get("modality", "").lower()
    if "advance payment" in modality:
        return "advance_payment"
    elif "import already arrived" in modality:
        return "declaration_import"
    elif "service" in modality:
        return "services"
    else:
        # Default fallback (could also raise an error or return END)
        return "unknown"

# ------------------------------------------------------------------------------
# Build the LangGraph state graph.
#
# The overall flow is:
#   START → extract_file_content → extract_bank_channels → determine_modality
#   → [conditional branch based on modality]:
#         if "advance payment": extract_advance_payment_info
#         if "import already arrived": extract_declaration_import_info
#         if "service": extract_services_info
#   → END
# ------------------------------------------------------------------------------
def build_exchange_graph() -> Any:
    # Initialize the state graph with our ExchangeState type.
    graph_builder = StateGraph(ExchangeState)

    # Add nodes for each step.
    graph_builder.add_node("extract_file_content", extract_file_content)
    graph_builder.add_node("extract_bank_channels", extract_bank_channels)
    graph_builder.add_node("determine_modality", determine_modality)
    graph_builder.add_node("extract_advance_payment_info", extract_advance_payment_info)
    graph_builder.add_node("extract_declaration_import_info", extract_declaration_import_info)
    graph_builder.add_node("extract_services_info", extract_services_info)

    # Set entry point.
    graph_builder.set_entry_point("extract_file_content")

    # Define the linear sequence.
    graph_builder.add_edge("extract_file_content", "extract_bank_channels")
    graph_builder.add_edge("extract_bank_channels", "determine_modality")

    # Add a conditional edge from 'determine_modality' based on modality_condition.
    graph_builder.add_conditional_edge(
        "determine_modality",
        modality_condition,
        {
            "advance_payment": "extract_advance_payment_info",
            "declaration_import": "extract_declaration_import_info",
            "services": "extract_services_info",
        },
    )

    # Connect each modality-specific extraction node to the END node.
    graph_builder.add_edge("extract_advance_payment_info", END)
    graph_builder.add_edge("extract_declaration_import_info", END)
    graph_builder.add_edge("extract_services_info", END)

    # Compile and return the runnable graph.
    return graph_builder.compile()

# ------------------------------------------------------------------------------
# Example usage:
# Create an initial state dictionary with the file text and empty placeholders.
# In a real system, file_text would be the extracted text from customer files.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Sample file text (this text should include details that allow extraction
    # of bank channel info and hints at the operation modality)
    sample_text = (
        "Customer File Content:\n"
        "The customer has provided a remittance file. The transaction was processed via Online Banking and Wire Transfer. "
        "The amount of USD 10,000 was remitted to Beneficiary A and Beneficiary B. "
        "The operation is an import with advance payment; the expected shipment date is 2025-04-15. "
    )

    initial_state: ExchangeState = {
        "file_text": sample_text,
        "bank_channels_info": None,
        "modality": None,
        "additional_info": None,
    }

    # Build and run the graph.
    graph = build_exchange_graph()
    final_state = graph.invoke(initial_state)

    # Print the final state.
    print("Final Exchange Processing State:")
    print(final_state)
