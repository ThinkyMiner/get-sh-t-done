APP SKILL: IndiaMART WebERP company verification

- Prefer reusable variable names like {{search_query}} and {{login_otp}}.
- Treat Google sign-in as a popup-capable authentication step.
- After the company result is chosen, the company detail view may be frame-based rather than top-level navigation.
- Known WebERP frame patterns:
  - company detail shell: IframeSTS
  - summary header: TopBar1_topbarIframe
  - expanded summary card: viewmoreIframe
  - KYC analytics tab: TabCtrl_Ifram
- If the flow is about verification, prefer extracting direct business statuses such as GST Verified, CIN Verified, and Address status from the summary frame.
- Avoid brittle selectors tied to employee names, emails, or full private account labels.
- Prefer root-frame scoped selectors for WebERP secondary frames because the visible host page may not be the current execution scope.
- Prefer extracting short status labels rather than the entire body text when the business value is a verification decision.
- If KYC content is already loaded in a dedicated frame, do not force a new popup step unless the video clearly shows a popup or new page.
