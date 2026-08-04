# Store assets

Generated icon sets for packaging the PWA as a native app on each store.
These are **not served by the Flask app** (nothing in `app.py` references
this folder) — they're inputs you upload during packaging.

## android/
Adaptive launcher icons (48–512px). This is what you need for:
- **PWABuilder → Android package** (paste your live HTTPS URL at
  pwabuilder.com → Android → it can pull `launchericon-512x512.png`
  automatically, or you can upload it manually if asked).
- **Play Console → App icon**: upload `launchericon-512x512-playstore.png`
  — Play Console rejects any icon with transparency, so this is a
  flattened (opaque, brand-navy background) version of the 512 icon
  made specifically for that upload. Don't use `launchericon-512x512.png`
  directly there; it has real alpha transparency.

## ios/
Full iOS icon size set (16px–1024px), for PWABuilder's iOS packaging
step if you ever submit to the Apple App Store via a WKWebView wrapper.
Not needed for the Play Store.

## windows/
Windows Store tile assets (if you ever package for the Microsoft Store
via PWABuilder). Not needed for the Play Store.

---

The web app itself only uses `static/icons/` (copied from `android/` +
`ios/1024.png`), referenced from `static/manifest.json`. This folder is
just the full source set so you don't have to regenerate everything if
you add another store later.
