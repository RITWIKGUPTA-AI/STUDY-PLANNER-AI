# App screenshots — done

The 4 screenshots referenced in `manifest.json` are in this folder,
captured from the real running app (not the marketing mockups):

- `01-dashboard.png` — stats cards (Subjects/Tasks/Notes/Goals)
- `02-mock-test.png` — AI CBT Exam Simulator exam list
- `03-ai-tutor.png` — AI Personal Tutor chat
- `04-planner.png` — Study Planner with a filled plan table

All 4 are 1080×1920 PNG, matching the manifest entries and Play Store's
recommended portrait ratio.

**Before you submit to the Play Store:** these were captured from a demo
account with sample data (Physics/Chemistry/Maths/Biology, a few tasks
and plans) so the screens don't look empty. If you'd rather show your
own real data, or want different screens, just retake them the same way
described below and drop the new PNGs in here with the same filenames.

## Retaking a screenshot (2 minutes)

1. Run the app locally or open your deployed URL.
2. Open Chrome DevTools (F12) → toggle Device Toolbar (Ctrl/Cmd+Shift+M).
3. Pick a phone preset, or set a custom size — **1080x1920** matches the
   manifest entries and Play Store's recommended portrait ratio.
4. Log in, navigate to the screen, then DevTools → ⋮ menu →
   "Capture screenshot" (captures the exact viewport, no browser chrome).
5. Overwrite the matching PNG in this folder.

## Play Store also needs (separate from the manifest)

- **Phone screenshots:** 2–8 images, JPG/PNG, 16:9 to 9:16 ratio,
  320px–3840px per side. The 4 above satisfy the minimum of 2.
- **Feature graphic:** 1024×500 PNG/JPG, no transparency — a banner
  shown at the top of your store listing. Not in this repo yet; a good
  one uses your icon + app name on the brand navy (#2F4B7C) background.
- **App icon (Play Console upload):** 512×512 — use
  `store-assets/android/launchericon-512x512.png`.
