---
name: savvyhrms-attendance
description: Use for SavvyHRMS login and attendance-marking workflows.
detection_terms:
  - savvyhrms
  - hrms
  - login with google
  - mark present
  - attendance
---

# SavvyHRMS Attendance

Use this skill when the workflow belongs to SavvyHRMS and the goal is to log in and mark attendance or capture the attendance confirmation.

Load `references/timeline-guidance.md` while building the timeline interpretation.

Load `references/workflow-guidance.md` while building the workflow JSON.

Load `references/failure-patterns.md` when the generic model output overfits to account chooser details or misses the post-login attendance confirmation.

Use `assets/workflow-template.json` as the canonical fallback when the generic model output is too person-specific or weak on the final attendance confirmation.
