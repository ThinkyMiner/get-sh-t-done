from __future__ import annotations

import json

import streamlit as st


def render_api_docs(slug: str, workflow: dict, docs: dict) -> None:
    st.subheader("Endpoint")
    st.code(f"POST http://localhost:8000/api/generated/{slug}/run", language=None)

    st.subheader("Description")
    st.write(docs.get("description", "No description"))

    st.subheader("Request Body")
    st.json(docs.get("request_body", {}))

    st.subheader("Response Body")
    response_example = {
        "execution_id": "<string>",
        "status": "success",
        "outputs": docs.get("response_body", {}),
        "duration_ms": "<number>",
        "logs_url": "/api/executions/<execution_id>/logs",
    }
    st.json(response_example)

    st.subheader("Code Examples")
    tab1, tab2, tab3 = st.tabs(["cURL", "Python", "JavaScript"])

    with tab1:
        request_body = {inp["name"]: f"<{inp['type']}>" for inp in workflow.get("inputs", [])}
        curl = (
            f"curl -X POST http://localhost:8000/api/generated/{slug}/run \\\n"
            '  -H "Content-Type: application/json" \\\n'
            f"  -d '{json.dumps(request_body, indent=2)}'\n"
        )
        st.code(curl, language="bash")

    with tab2:
        fields = "\n".join(
            f'        "{inp["name"]}": "<{inp["type"]}>",' for inp in workflow.get("inputs", [])
        )
        python_code = (
            "import requests\n\n"
            "response = requests.post(\n"
            f'    "http://localhost:8000/api/generated/{slug}/run",\n'
            "    json={\n"
            f"{fields}\n"
            "    }\n"
            ")\n\n"
            "data = response.json()\n"
            'print(data["outputs"])\n'
        )
        st.code(python_code, language="python")

    with tab3:
        fields = "\n".join(
            f'    "{inp["name"]}": "<{inp["type"]}>",' for inp in workflow.get("inputs", [])
        )
        js_code = (
            f'const response = await fetch("http://localhost:8000/api/generated/{slug}/run", {{\n'
            '  method: "POST",\n'
            '  headers: { "Content-Type": "application/json" },\n'
            "  body: JSON.stringify({\n"
            f"{fields}\n"
            "  })\n"
            "});\n\n"
            "const data = await response.json();\n"
            "console.log(data.outputs);\n"
        )
        st.code(js_code, language="javascript")
