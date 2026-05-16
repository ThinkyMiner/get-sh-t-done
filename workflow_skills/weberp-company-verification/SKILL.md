---
name: weberp-company-verification
description: Use for IndiaMART WebERP company verification, GLID search, View More summary extraction, and GST/CIN/address status workflows.
detection_terms:
  - weberp
  - weberp.intermesh.net
  - glid
  - company search
  - view more
  - know your customer
  - gst verified
  - cin verified
  - address not verified
---

# WebERP Company Verification

Use this skill when the workflow belongs to IndiaMART WebERP and the goal is to search a company record, open the company detail flow, and extract verification statuses.

Load `references/timeline-guidance.md` while building the timeline interpretation.

Load `references/workflow-guidance.md` and `references/runtime-guidance.md` while building the workflow JSON.

Load `references/failure-patterns.md` when the model output is directionally correct but historically weak on WebERP-specific auth, iframe, or result-activation behavior.

Use `assets/workflow-template.json` as the canonical fallback when the generic model output is structurally valid but weak on WebERP-specific frames, auth boundaries, or extraction targets.
