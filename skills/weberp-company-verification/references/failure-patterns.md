OBSERVED FAILURE PATTERNS: IndiaMART WebERP company verification

- Failure: the workflow assumed normal top-level page navigation after clicking the company result.
  Correction: the app uses named frames, so selectors after the search step must be frame-aware.

- Failure: the workflow assumed `View More` or `Know Your Customer` would be visible in `IframeSTS`.
  Correction: company summary controls are exposed in `TopBar1_topbarIframe`; expanded status cards appear in `viewmoreIframe`; KYC analytics appear in `TabCtrl_Ifram`.

- Failure: the workflow assumed `View More` created a popup.
  Correction: `View More` mutates frame state inside the same app shell and loads `viewmoreIframe`.

- Failure: the workflow treated any auth-step failure as skippable.
  Correction: auth steps should only be skipped when a real post-auth state is visible, not when the WebERP login page or OTP fields are still on screen.

- Failure: the workflow overfit to person-specific Google account selectors.
  Correction: prefer generic authentication labels and popup behavior; do not rely on private account text.

- Failure: direct navigation to internal company-detail URLs returned unauthorized responses.
  Correction: use the authenticated host page and frame hydration strategy instead of raw top-level navigation.
