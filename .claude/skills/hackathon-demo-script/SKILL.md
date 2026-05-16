---
name: hackathon-demo-script
description: Use when asked to write or refine hackathon pitch scripts, demo intros, submission answers, or judge-facing storytelling for Get Shit Done / Flow2API. Best for 1-3 minute monologues, 1-line pitches, impact answers, and role-based scripts for Kartik, Vijay, and Kaushlendra.
disable-model-invocation: true
---

# Hackathon Demo Script

Use this skill when the task is to produce spoken or written submission material for the project.

## Goals
- Produce concise, high-conviction script output.
- Optimize for judges, not internal notes.
- Preserve technical honesty while still sounding ambitious.
- Keep the story centered on 10x productivity and reusable workflow automation.

## Workflow
1. Read `references/project-context.md` first.
2. Read `references/judging-rubric.md` if the user asks for submission copy, impact text, or prize-focused framing.
3. Read `references/voice-guidelines.md` if the user asks for a speech, monologue, or team dialogue.
4. If the output is time-boxed, keep speaking pace near 130-150 words per minute.
5. If needed, run `scripts/estimate_speaking_time.py` on the draft before finalizing.

## Writing Rules
- Start with the pain point or the leverage, not with greetings.
- Keep claims honest. Separate what is already demonstrated from future platform potential.
- Use the team name `Get Shit Done` as brand language, but do not overuse it.
- If multiple speakers are involved:
  - Kaushlendra handles business framing, impact, and close.
  - Kartik explains the technical architecture and system insight.
  - Vijay explains execution reliability and demo logic.
- Do not narrate screen-by-screen demo actions unless the user explicitly asks for a demo walkthrough.
- For IndiaMART-facing copy, frame the problem around repeatable software work inside internal tools, but keep the audience broad unless the user explicitly wants company-specific language.

## Default Structures

### 2-minute pitch
1. Problem
2. Why this matters now
3. What we built
4. Why it is a 10x productivity lever
5. Handoff to demo

### Submission answer
1. State the pain clearly
2. Explain the leverage or impact
3. Mention what is already working
4. Keep the answer compact and concrete

### One-line pitch
- One sentence
- No jargon pile-up
- Clear action + outcome

## Output Contracts
- 1-line pitch: under 280 characters
- 2-minute script: usually 220-300 words
- Submission answer: compact markdown, no filler
- Role-based script: each speaker should have a clear function, not random line splitting

## Project-specific reminders
- The core idea is: turn repeatable desktop workflows into reusable APIs.
- The strongest proven story is not “AI watched a video.” It is “manual UI work became programmable infrastructure.”
- The strongest technical credibility points are:
  - keyframe-based video understanding
  - timeline-to-workflow generation
  - skill-guided correction
  - browser execution with logs and screenshots

Use this skill to return the final script text directly, without extra meta commentary, unless the user asks for reasoning.
