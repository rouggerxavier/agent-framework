---
name: frontend-a11y
description: Use to build or review frontend accessibility (semantic HTML, ARIA, form labels, keyboard, focus, screen readers) in React, Next.js, or plain HTML.
---

# Frontend A11y

## Objective
Make the interface work for keyboard and screen reader users, using semantic
HTML first and ARIA only when HTML is not enough.

## When to use
- Building or reviewing a form, menu, modal, dropdown, tabs, table, or interactive component.
- Auditing a page before release.
- Triggers: "accessibility", "a11y", "screen reader", "keyboard navigation".

## When not to use
- Motion without accessibility components: use `animation-performance` or
  `review-animations`. Respect `prefers-reduced-motion` there.
- Broad UI audit (hierarchy, copy, layout): use `ui-ux-pro-max-audit`.
- Native mobile apps (iOS/Android): out of scope; use the platform skill.

## Expected inputs
- Code snippet, component, or URL/page to review.

## Workflow
1. Use native elements before any ARIA: `button`, `a`, `label`, `input`,
   `select`, `dialog`, `nav`, `main`, `h1`-`h6` in logical order.
2. Forms: every field has an associated `label` (`htmlFor`/`id` or wrapping).
   Link errors to fields with `aria-describedby`; set `aria-invalid` when invalid.
   Do not use placeholder as the only label.
3. Keyboard: everything reachable with Tab, focus order matches visual order,
   Enter and Space activate buttons, Esc closes overlays. Never use positive `tabIndex`.
4. Focus: keep it visible (do not remove `outline` without a replacement). In a
   modal, trap focus inside and return it to the trigger on close.
5. ARIA: only when native cannot express it (e.g. `role="tablist"` with `aria-selected`).
   Do not add redundant `role`. Icon without text: `aria-label`; decorative:
   `aria-hidden="true"`.
6. Dynamic content: status messages in `role="status"` or `aria-live="polite"`.
7. Text and control contrast meets WCAG AA (text 4.5:1, large text and UI
   components 3:1). Do not convey information by color alone.
8. Images: descriptive `alt`; decorative images get `alt=""`.
9. React/Next: prefer `next/link` and real `button` elements; avoid `div onClick`
   without role, keyboard, and focus.
10. Verify: navigate with keyboard only; if possible, run a screen reader or
    axe/Lighthouse on the component.

## Required output
- Issue list in the form `file:line: <severity>: <problem>. <fix>.`
  (severity: blocker, high, medium, low), or the diff of applied fixes.

## Acceptance criteria
- Every interactive control works by keyboard and has an accessible name.
- Every form field has a label and linked errors.
- Focus is visible and focus order is correct.
- Contrast meets AA on changed text and controls.
- No redundant `role`/`aria-*`, or ARIA used where native HTML suffices.

## Usage examples
- "review this confirmation modal" -> checks `dialog` or focus trap, Esc,
  focus return to trigger, and `aria-labelledby` on the title.
- "a11y of the signup form" -> labels, `aria-describedby` on errors,
  `aria-live` on the error summary.

Standards reference: WCAG 2.2 AA and WAI-ARIA Authoring Practices.
Origin: concepts adapted from `affaan-m/ecc` (`frontend-a11y`, MIT license).
