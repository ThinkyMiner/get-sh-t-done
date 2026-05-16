# 10x Productivity Hackathon Demo Script

## Title
Flow2API: Turn Repetitive Internal Workflows into Instant APIs

## Team
- Kaushlendra - Assistant Product Manager
- Kartik - Engineer
- Vijay - Engineer

## Demo Length
4 to 5 minutes

## Core Story
One internal workflow that normally requires a person to log in, search a company, open its detail view, and verify compliance signals can now be triggered as an API call. Instead of asking an ops user to repeat the same clicks again and again, we convert the workflow into reusable infrastructure.

## Demo Structure
1. Problem - 35 to 45 seconds
2. Why now - 20 to 30 seconds
3. Live demo - 2.5 to 3.5 minutes
4. Impact - 25 to 35 seconds

---

## 1. Problem

### Speaker: Kaushlendra
"Hi, we are Team Flow2API."

"Inside fast-moving companies like IndiaMART, a lot of important work is still trapped inside internal dashboards. A person logs in, searches a record, opens detail screens, checks statuses, and then passes that information to another team or tool."

"That sounds small, but it adds up fast. The same verification workflow gets repeated again and again by different people, across different requests, across different teams."

"And that is exactly the kind of problem that blocks 10x productivity. The knowledge exists. The data exists. The workflow exists. But it is still locked behind manual clicks."

"Our idea is simple: if a human can do a repeatable workflow on screen, that workflow should become an API."

---

## 2. Why Now

### Speaker: Kartik
"This becomes possible now because vision models are finally good enough to understand workflows from UI recordings, and browser automation is mature enough to replay those workflows in a controlled, logged, auditable way."

"So instead of building a custom integration for every single internal process, we can watch the process once, structure it, and expose it as an API."

"That is the shift: from manual operations to reusable workflow infrastructure."

---

## 3. Live Demo

### Speaker: Vijay
"We will show one real workflow from WebERP."

"The task is simple but common: verify a company record and extract business-critical status signals."

"In the manual workflow, a user logs in, searches by GLID, opens the company record, expands the summary, and reads verification fields."

"We took that workflow and converted it into an API."

### Action
- Show the recorded workflow briefly for 10 to 15 seconds.
- Pause on the key business state: company detail plus verification summary.

### Speaker: Vijay
"This is the original manual flow."

"Now we run the same thing through Flow2API."

### Action
- Show the product flow:
  - workflow definition
  - API call
  - live run
  - returned JSON

### Speaker: Kartik
"Under the hood, the system handles the real execution complexity."

"It manages authentication boundaries, browser context, frame navigation, and structured extraction from internal application screens."

"For this workflow, the system logs in, searches the target company by GLID, opens the correct company context, expands the summary, and extracts the verification outputs."

### Action
- Show the API request on screen.
- Use the working example:

```json
{
  "login_otp": "4403",
  "search_query": "28985416"
}
```

### Speaker: Vijay
"Now instead of a human doing repeated clicks, any internal tool can just call this endpoint."

### Action
- Show the API response:

```json
{
  "gst_status": "GST Verified",
  "cin_status": "CIN Verified",
  "address_status": "Address not Verified"
}
```

### Speaker: Vijay
"This is the key transformation."

"The output is no longer buried inside a dashboard. It is now machine-readable, reusable, and instantly available to any downstream system."

### Action
- Show execution logs and screenshots briefly.
- Show that the run is traceable step by step.

### Speaker: Kartik
"This is important because enterprise automation is not just about getting a result once."

"It has to be observable. It has to be debuggable. And it has to work on real internal systems, not just clean public websites."

"That is why our system keeps structured workflow steps, execution logs, screenshots, and extracted outputs."

### Speaker: Kaushlendra
"From a product point of view, this means teams do not have to wait for a custom backend integration every time they want one workflow automated."

"If the workflow is repeatable, we can productize it much faster."

---

## 4. Impact

### Speaker: Kaushlendra
"The impact is straightforward."

"A workflow that normally takes a person multiple clicks, context switching, and repeated verification can now be triggered in seconds."

"That means faster operations, fewer repetitive tasks, and fewer requests bouncing between teams just to fetch status from an internal tool."

"And more importantly, this is not limited to one use case."

"Today we showed company verification in WebERP."

"Tomorrow the same approach can turn many internal workflows into APIs: verification checks, catalog checks, seller operations, support operations, and other repetitive internal tasks."

"That is our 10x productivity bet: convert repeatable human dashboard work into reusable APIs."

"Thank you."

---

## Suggested On-Screen Flow

1. Team intro slide with one-line problem statement
2. Short visual of the manual WebERP workflow
3. Product UI showing the workflow/API setup
4. Live API trigger
5. Returned JSON
6. Logs/screenshots view
7. Final impact slide

---

## Recording Notes

- Keep the pace sharp. Do not exceed 5 minutes.
- Do not spend too long on architecture.
- Show the API doing the work, not just slides describing it.
- Keep the WebERP result visible when showing the returned JSON.
- If asked about reliability, say:
  "We built around real enterprise constraints like authentication, frames, and execution logging."
- If asked about scale, say:
  "The point is not one hardcoded workflow. The point is turning repeatable internal workflows into reusable programmable interfaces."

---

## Shorter Backup Version

### Kaushlendra
"A lot of internal productivity is still blocked by repeated dashboard work. Humans click through the same screens every day just to retrieve structured information."

### Kartik
"We built Flow2API to convert those repeatable UI workflows into APIs using vision understanding plus browser execution."

### Vijay
"Here is a real WebERP workflow. We log in, search a company by GLID, open the detail flow, and extract verification statuses."

### Kaushlendra
"The output is now reusable JSON instead of manual effort. That is the 10x productivity unlock."
