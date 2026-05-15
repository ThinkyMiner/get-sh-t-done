SYSTEM_PROMPT = """You are an expert at analyzing user interface workflows from screenshots.

You receive a sequence of screenshots from a screen recording showing someone performing a repetitive task in a web application. Your job is to understand what the user did and produce a structured workflow JSON that can automate that same task.

RULES:
1. Output ONLY valid JSON. No markdown, no explanation, no backticks.
2. Follow the exact schema provided below.
3. For user inputs that vary per execution, use {{variable_name}} syntax and add the variable to the "inputs" array.
4. Prefer readable selectors: use "label" for form inputs, "role" for buttons, "text" for links. Only use "css" as a last resort.
5. Include a "confidence" field per step: "high", "medium", or "low".
6. Include a "description" field per step in plain English.
7. Add "wait" steps after actions that trigger navigation or async updates.
"""

SCHEMA_DEFINITION = """
WORKFLOW JSON SCHEMA:
{
  "workflow_name": "snake_case_name",
  "slug": "kebab-case-slug",
  "description": "What this workflow does in one sentence",
  "inputs": [
    { "name": "variable_name", "type": "string"|"number"|"boolean", "required": true|false }
  ],
  "steps": [
    {
      "id": "step_1",
      "type": "navigate"|"fill"|"click"|"select"|"wait"|"extract_text"|"extract_table"|"download_file",
      "url": "(for navigate only)",
      "selector_type": "label"|"role"|"text"|"test_id"|"css"|"placeholder",
      "selector_value": "the selector string",
      "value": "value to fill or {{variable_name}}",
      "option_value": "(for select only)",
      "output_key": "(for extract_text/extract_table only)",
      "duration_ms": 1500,
      "description": "Human-readable step description",
      "confidence": "high"|"medium"|"low"
    }
  ],
  "outputs": [
    { "name": "output_variable_name", "type": "string"|"number"|"boolean" }
  ]
}
"""

FEW_SHOT_EXAMPLE = """
EXAMPLE:
Given screenshots showing someone opening a supplier dashboard, typing "SUP001" into a search box labeled "Supplier ID", clicking a "Search" button, and reading a "Verified" status from the results:

{
  "workflow_name": "check_supplier_status",
  "slug": "check-supplier-status",
  "description": "Check supplier verification status from the internal dashboard",
  "inputs": [
    { "name": "supplier_id", "type": "string", "required": true }
  ],
  "steps": [
    {
      "id": "step_1",
      "type": "navigate",
      "url": "http://localhost:5500/dashboard",
      "description": "Open the supplier dashboard",
      "confidence": "high"
    },
    {
      "id": "step_2",
      "type": "fill",
      "selector_type": "label",
      "selector_value": "Supplier ID",
      "value": "{{supplier_id}}",
      "description": "Enter the supplier ID into the search field",
      "confidence": "high"
    },
    {
      "id": "step_3",
      "type": "click",
      "selector_type": "role",
      "selector_value": "Search",
      "description": "Click the search button to look up the supplier",
      "confidence": "high"
    },
    {
      "id": "step_4",
      "type": "wait",
      "duration_ms": 1500,
      "description": "Wait for search results to load",
      "confidence": "medium"
    },
    {
      "id": "step_5",
      "type": "extract_text",
      "selector_type": "test_id",
      "selector_value": "verification-status",
      "output_key": "verification_status",
      "description": "Read the verification status from the results",
      "confidence": "high"
    }
  ],
  "outputs": [
    { "name": "verification_status", "type": "string" }
  ]
}
"""


def build_analysis_prompt(user_context: str = "") -> str:
    context_section = ""
    if user_context:
        context_section = f"\nADDITIONAL CONTEXT FROM USER:\n{user_context}\n"

    return (
        f"{SCHEMA_DEFINITION}\n\n"
        f"{FEW_SHOT_EXAMPLE}\n"
        f"{context_section}"
        "Now analyze the provided screenshots and output the workflow JSON. "
        "Remember: output ONLY valid JSON, nothing else."
    )
