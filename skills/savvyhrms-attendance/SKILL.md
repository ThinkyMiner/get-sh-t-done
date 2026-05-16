---
name: savvyhrms-attendance
description: Use when a workflow video or execution target is SavvyHRMS and the goal is to authenticate, reach the attendance dashboard, mark attendance, and capture the visible confirmation.
detection_terms:
  - savvyhrms
  - hrms
  - login with google
  - mark present
  - attendance
---

# SavvyHRMS Attendance

Use this skill for SavvyHRMS attendance flows. The purpose of the skill is to keep the workflow focused on the repeatable attendance action instead of overfitting to personal account-picker details.

## Use this skill when
- the app is SavvyHRMS
- the video shows `Login With Google`, attendance buttons, or attendance confirmation text
- the target output is attendance state or confirmation text

## Core workflow expectations
1. Treat Google login as an auth boundary.
2. Prefer stable post-login attendance actions over person-specific account selectors.
3. Capture the visible success confirmation as structured output.

## Read these references as needed
- Load `references/timeline-guidance.md` when turning frames into an ordered timeline.
- Load `references/workflow-guidance.md` when generating or repairing workflow JSON.
- Load `references/failure-patterns.md` when the output overfits to account-selection details or misses the final confirmation state.

## Fallback
Use `assets/workflow-template.json` only when the generated workflow is directionally correct but too person-specific or too weak on final extraction.
