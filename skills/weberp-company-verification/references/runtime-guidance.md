RUNTIME GUIDANCE: IndiaMART WebERP company verification

- Google sign-in can open in a popup page. The popup may also auto-close immediately if the Google session is already cached. After auth-related actions, the runner should be ready to fall back to the root WebERP page.
- OTP entry, when required, happens on the Google/WebERP auth popup, not on the root dashboard page.
- The company-result anchor may expose a valid href and target attribute but still fail to populate the company frame on a plain click. If `IframeSTS` remains `about:blank`, hydrate the frame from the clicked href inside the authenticated host page.
- Direct top-level navigation to `/company/comptab.aspx?...` can be rejected as unauthorized. Prefer frame hydration from inside the authenticated app shell.
- `View More` does not create a new page. It loads `viewmoreIframe`.
- The KYC analytics content is commonly loaded in `TabCtrl_Ifram`, while company summary statuses are loaded in `viewmoreIframe`.
- For this workflow family, `viewmoreIframe` is the preferred source for compact verification outputs.
