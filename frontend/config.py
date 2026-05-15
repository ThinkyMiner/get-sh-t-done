from __future__ import annotations

import copy
import os

API_URL = os.getenv("FLOW2API_API_URL", "http://localhost:8000")
STEP_TYPES = [
    "navigate",
    "fill",
    "click",
    "select",
    "wait",
    "extract_text",
    "extract_table",
    "download_file",
]
SELECTOR_TYPES = ["label", "role", "text", "test_id", "css", "placeholder"]
FIELD_TYPES = ["string", "number", "boolean"]

MOCK_WORKFLOW = {
    "workflow_name": "check_supplier_status",
    "slug": "check-supplier-status",
    "description": "Search for a supplier by ID and read the verification status",
    "inputs": [{"name": "supplier_id", "type": "string", "required": True}],
    "steps": [
        {
            "id": "step_1",
            "type": "navigate",
            "url": "http://localhost:5500/dashboard",
            "description": "Open supplier dashboard",
            "confidence": "high",
        },
        {
            "id": "step_2",
            "type": "fill",
            "selector_type": "label",
            "selector_value": "Supplier ID",
            "value": "{{supplier_id}}",
            "description": "Enter supplier ID",
            "confidence": "high",
        },
        {
            "id": "step_3",
            "type": "click",
            "selector_type": "role",
            "selector_value": "Search",
            "description": "Click search",
            "confidence": "high",
        },
        {
            "id": "step_4",
            "type": "wait",
            "duration_ms": 1500,
            "description": "Wait for results",
            "confidence": "medium",
        },
        {
            "id": "step_5",
            "type": "extract_text",
            "selector_type": "test_id",
            "selector_value": "verification-status",
            "output_key": "verification_status",
            "description": "Read status",
            "confidence": "high",
        },
    ],
    "outputs": [{"name": "verification_status", "type": "string"}],
}

DEMO_WORKFLOWS = [
    {
        "id": "demo1",
        "name": "Check Supplier Status",
        "slug": "check-supplier-status",
        "description": "Look up supplier verification",
        "created_at": "2026-05-15",
    },
    {
        "id": "demo2",
        "name": "Check API Score",
        "slug": "check-api-doc-score",
        "description": "Check API documentation score",
        "created_at": "2026-05-15",
    },
]

MOCK_LOGS = [
    {
        "step_id": "step_1",
        "step_type": "navigate",
        "status": "success",
        "message": "Navigated to dashboard",
        "screenshot_path": None,
        "duration_ms": 800,
    },
    {
        "step_id": "step_2",
        "step_type": "fill",
        "status": "success",
        "message": "Filled Supplier ID field",
        "screenshot_path": None,
        "duration_ms": 200,
    },
    {
        "step_id": "step_3",
        "step_type": "click",
        "status": "success",
        "message": "Clicked Search button",
        "screenshot_path": None,
        "duration_ms": 150,
    },
    {
        "step_id": "step_4",
        "step_type": "wait",
        "status": "success",
        "message": "Waited 1500ms",
        "screenshot_path": None,
        "duration_ms": 1500,
    },
    {
        "step_id": "step_5",
        "step_type": "extract_text",
        "status": "success",
        "message": "Extracted: Verified",
        "screenshot_path": None,
        "duration_ms": 100,
    },
]


def clone_mock_workflow() -> dict:
    return copy.deepcopy(MOCK_WORKFLOW)
