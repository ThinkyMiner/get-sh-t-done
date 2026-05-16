---
name: weberp-company-verification
description: Use when a workflow video or execution target is IndiaMART WebERP and the goal is to authenticate, search a company by GLID or company identifier, open company details, expand the summary view, and extract verification statuses.
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

Use this skill for WebERP company verification flows. The purpose of the skill is to convert a noisy screen recording or partially-correct workflow draft into a stable company-verification automation.

## Use this skill when
- the app is `weberp.intermesh.net`
- the video shows Google sign-in, OTP, GLID/company search, `View More`, or verification labels
- the target output is structured verification data such as GST, CIN, or address status

## Core workflow expectations
1. Recognize login and OTP as an auth boundary, not the business output.
2. Find the post-login company search flow.
3. Treat result activation as frame-oriented navigation, not simple top-level navigation.
4. Reach the summary/detail view and extract normalized verification outputs.

## Read these references as needed
- Load `references/timeline-guidance.md` when turning frames into an ordered timeline.
- Load `references/workflow-guidance.md` when generating or repairing workflow JSON.
- Load `references/runtime-guidance.md` when selector scope, frames, popup behavior, or execution sequencing is unstable.
- Load `references/failure-patterns.md` when the workflow is close but fails on auth, frame switching, `View More`, or extraction state.

## Fallback
Use `assets/workflow-template.json` only when the generated workflow is structurally valid but operationally weak on WebERP-specific behavior.
