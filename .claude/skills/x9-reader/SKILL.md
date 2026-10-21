---
name: x9-reader
description: >-
  Build, update, and deploy the X9 Reader — a WebView document reader for the
  X9-CALL watch. Use whenever adding or updating a document shown on the watch,
  changing the reader's look (fonts, theme, table of contents, layout for the
  320x385 rounded screen), changing input/scroll handling (touch, rotary crown,
  volume keys), or rebuilding and installing the APK. Covers the full
  docx -> HTML -> signed APK pipeline built with Android SDK tools only (no
  Android Studio, no Gradle).
---

# X9 Reader

Document reader for the X9-CALL watch (Android 8.1, screen 320x385, rounded
rectangle, Unisoc). A full-screen `WebView` renders HTML converted from the source
document, with large fonts, dark theme, an inline table of contents and font-size
controls — readable where Word is not.

## Pipeline

`.docx` --(`docx2html.py`)--> self-contained HTML --(baked into `assets/`)-->
`build_apk.py` --> signed `X9Reader.apk` --(FTP)--> watch.

## Files

- `reader/tools/docx2html.py` — converts a document to the reader HTML page.
  Keeps headings (-> TOC), paragraphs, lists, tables, bold/italic, and the
  `<sub>`/`<sup>` runs that carry the math. Emits one standalone `.html`
  (CSS + JS embedded) that both previews in a browser and loads in the app.
- `reader/app/` — the Android app: `AndroidManifest.xml`,
  `src/com/x9/reader/MainActivity.java`, `assets/doc.html` (the baked document).
- `reader/tools/build_apk.py` — manual build: aapt2 link -> javac (`--release 8`)
  -> d8 -> inject `classes.dex` -> zipalign -> apksigner (debug key).
- `reader/tools/inspect_docx.py` — prints styles / sub-sup counts / tables to
  understand a new document before converting.

## Update a document

```bash
python reader/tools/docx2html.py path/to.docx reader/app/assets/doc.html "Title"
python reader/tools/build_apk.py
python ftp_put.py reader/build/X9Reader.apk /device/Download
```

Then on the watch: CX File Explorer -> `Download` -> `X9Reader.apk` -> install.
The APK is signed with the project debug key, so reinstalling updates in place.

## Verify look before building

Open the generated HTML in a browser at the watch size (320x385, dark) and check
the math (`<sub>`/`<sup>`), tables (horizontally scrollable), and headings. The
HTML is the single source of the reading experience; tune CSS in
`docx2html.py`'s `PAGE` template, not in the app.

## Toolchain (already present on this machine)

- JDK 17 at `JAVA_HOME`; Android SDK at `D:\Android\Sdk`.
- `build_apk.py` hardcodes `build-tools/36.0.0` and `platforms/android-34`
  (compileSdk 34, targetSdk 26, minSdk 21). Update those constants if the SDK
  layout changes.

## Known open point: the rotary crown

The crown did not scroll in the first build. Its event is unknown on this
hardware, so `MainActivity` has a diagnostics strip: tap the bottom-left corner
to toggle it, turn the crown, and read the key code / motion axis values. Bind
the reported event in `dispatchKeyEvent` / `dispatchGenericMotionEvent`. Touch
scroll always works; volume/d-pad/page keys are already handled.

See also: [[x9-watch-access]] for reaching the watch over Wi-Fi/FTP.
