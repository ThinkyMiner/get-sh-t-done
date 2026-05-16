TIMELINE_SYSTEM_PROMPT = """You are an expert at understanding web-app workflows from ordered screenshots.

You receive screenshots from a screen recording in chronological order. Your first job is to reconstruct what happened over time.

RULES:
1. Output ONLY valid JSON. No markdown, no explanation, no backticks.
2. Respect screenshot order and timestamps.
3. Focus on user-visible actions and state changes.
4. Prefer generic, reusable descriptions over user-specific secrets.
5. Infer candidate API inputs only when the value is likely to vary between runs.
6. Infer candidate outputs only when the final screen visibly exposes a result or confirmation.
"""

WORKFLOW_SYSTEM_PROMPT = """You are an expert at converting UI workflow timelines into reusable automation workflows.

You receive an ordered screenshot sequence plus a structured timeline describing what likely happened.

RULES:
1. Output ONLY valid JSON. No markdown, no explanation, no backticks.
2. Follow the exact workflow schema.
3. Prefer readable selectors: use "label" for form inputs, "text" for visible links/buttons, "placeholder" for obvious placeholders, and "role" only when the visible label is ambiguous.
4. Avoid overfitting to private or person-specific values such as emails, employee IDs, or full account chooser aria-labels.
5. For user inputs that vary per execution, use {{variable_name}} syntax and add the variable to the "inputs" array.
6. Include a "confidence" field per step: "high", "medium", or "low".
7. Include a "description" field per step in plain English.
8. Add "wait" steps after actions that trigger navigation or async updates.
9. If the final screen shows a confirmation or extracted result, include an output step when it can be expressed with the supported schema.
"""

WORKFLOW_SCHEMA_DEFINITION = """
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

TIMELINE_SCHEMA_DEFINITION = """
TIMELINE JSON SCHEMA:
{
  "workflow_goal": "One-sentence summary of what the user accomplished",
  "start_url": "URL if visible, else empty string",
  "likely_app_name": "App or site name if visible",
  "candidate_inputs": [
    {
      "name": "variable_name",
      "type": "string"|"number"|"boolean",
      "reason": "Why this value should be parameterized"
    }
  ],
  "candidate_outputs": [
    {
      "name": "output_name",
      "type": "string"|"number"|"boolean",
      "source_text": "Visible text or state being captured"
    }
  ],
  "actions": [
    {
      "timestamp": "HH:MM:SS or HH:MM:SS.mmm",
      "frame_index": 0,
      "screen_state": "What is visible on screen",
      "user_action": "What the user likely did between the previous frame and this frame",
      "target_text": "Visible label/button/text involved, if any",
      "result": "What changed after the action"
    }
  ]
}
"""

TIMELINE_EXAMPLE = """
EXAMPLE:
{
  "workflow_goal": "Log into the HR portal and mark attendance",
  "start_url": "https://portal.example.com/login",
  "likely_app_name": "Example HR Portal",
  "candidate_inputs": [],
  "candidate_outputs": [
    {
      "name": "attendance_status",
      "type": "string",
      "source_text": "Attendance Marked Successfully"
    }
  ],
  "actions": [
    {
      "timestamp": "00:00:00",
      "frame_index": 0,
      "screen_state": "Login page with a Login With Google button",
      "user_action": "Opened the login page",
      "target_text": "Login With Google",
      "result": "Ready to start authentication"
    },
    {
      "timestamp": "00:00:05",
      "frame_index": 1,
      "screen_state": "Google account chooser",
      "user_action": "Clicked Login With Google",
      "target_text": "Login With Google",
      "result": "Account chooser is displayed"
    },
    {
      "timestamp": "00:00:12",
      "frame_index": 2,
      "screen_state": "Dashboard with a Mark Present button and a success banner",
      "user_action": "Selected an account, landed on the dashboard, and marked attendance",
      "target_text": "Mark Present",
      "result": "A success confirmation is visible"
    }
  ]
}
"""

WORKFLOW_EXAMPLE = """
EXAMPLE WORKFLOW:
{
  "workflow_name": "mark_attendance",
  "slug": "mark-attendance",
  "description": "Log into the employee dashboard and mark attendance",
  "inputs": [],
  "steps": [
    {
      "id": "step_1",
      "type": "navigate",
      "url": "https://portal.example.com/login",
      "description": "Open the employee login page",
      "confidence": "high"
    },
    {
      "id": "step_2",
      "type": "click",
      "selector_type": "text",
      "selector_value": "Login With Google",
      "description": "Start Google-based login",
      "confidence": "high"
    },
    {
      "id": "step_3",
      "type": "wait",
      "duration_ms": 1500,
      "description": "Wait for account selection to appear",
      "confidence": "medium"
    },
    {
      "id": "step_4",
      "type": "click",
      "selector_type": "text",
      "selector_value": "Work Account",
      "description": "Choose the saved work account",
      "confidence": "medium"
    },
    {
      "id": "step_5",
      "type": "wait",
      "duration_ms": 1500,
      "description": "Wait for the dashboard to load",
      "confidence": "medium"
    },
    {
      "id": "step_6",
      "type": "click",
      "selector_type": "text",
      "selector_value": "Mark Present",
      "description": "Click the Mark Present button",
      "confidence": "high"
    },
    {
      "id": "step_7",
      "type": "wait",
      "duration_ms": 1500,
      "description": "Wait for the attendance confirmation to appear",
      "confidence": "medium"
    }
  ],
  "outputs": [
    { "name": "attendance_status", "type": "string" }
  ]
}
"""


def build_timeline_prompt(user_context: str = "", skill_context: str = "") -> str:
    context_section = ""
    if user_context:
        context_section = f"\nADDITIONAL CONTEXT FROM USER:\n{user_context}\n"
    skill_section = ""
    if skill_context:
        skill_section = f"\nAPP SKILL CONTEXT:\n{skill_context}\n"

    return (
        f"{TIMELINE_SCHEMA_DEFINITION}\n\n"
        f"{TIMELINE_EXAMPLE}\n"
        f"{skill_section}"
        f"{context_section}"
        "Analyze the screenshots as a time-ordered sequence and output the timeline JSON only."
    )


def build_workflow_prompt_from_timeline(
    timeline: dict,
    user_context: str = "",
    skill_context: str = "",
) -> str:
    context_section = ""
    if user_context:
        context_section = f"\nADDITIONAL CONTEXT FROM USER:\n{user_context}\n"
    skill_section = ""
    if skill_context:
        skill_section = f"\nAPP SKILL CONTEXT:\n{skill_context}\n"

    return (
        f"{WORKFLOW_SCHEMA_DEFINITION}\n\n"
        f"{WORKFLOW_EXAMPLE}\n\n"
        f"TIMELINE JSON:\n{timeline}\n"
        f"{skill_section}"
        f"{context_section}"
        "Convert the timeline into the workflow JSON only."
    )
