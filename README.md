<p align="center">
  <img src="assets/readme-banner.svg" alt="Hethereau Hobbies Tool" width="100%">
</p>

<p align="center">
  <img src="assets/app_icon.png" alt="HHT app icon" width="112">
</p>

<p align="center">
  <a href="https://github.com/M1ST0R/hethereau-hobbies-tool/actions/workflows/build.yml"><img src="https://github.com/M1ST0R/hethereau-hobbies-tool/actions/workflows/build.yml/badge.svg" alt="Build packages"></a>
  <a href="https://github.com/M1ST0R/hethereau-hobbies-tool/releases"><img src="https://img.shields.io/github/v/release/M1ST0R/hethereau-hobbies-tool?label=latest%20release&color=ff648d" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-7c8fff.svg" alt="MIT license"></a>
  <a href="LICENSE-MATERIAL-SYMBOLS.txt"><img src="https://img.shields.io/badge/icons-Material%20Symbols-59cfe0.svg" alt="Material Symbols"></a>
</p>

<p align="center">
  <a href="https://github.com/zzstar101/awesome-nte"><img src="https://raw.githubusercontent.com/zzstar101/awesome-nte/main/assets/badge-listed.svg" alt="Listed in Awesome NTE"></a>
</p>

<h3 align="center">One toolkit. Many hobbies. Less repetitive work.</h3>

<p align="center">
  <strong>Hethereau Hobbies Tool (HHT)</strong> is a growing desktop toolkit for automating hobbies and side activities in <strong>Neverness to Everness (NTE)</strong>.
  <br>
  Start with Owner's Selection today. Add fishing and more activities as separate modules tomorrow.
</p>

<p align="center">
  <a href="https://github.com/M1ST0R/hethereau-hobbies-tool/releases"><strong>Download</strong></a>
  ·
  <a href="#features"><strong>Features</strong></a>
  ·
  <a href="#quick-start"><strong>Quick start</strong></a>
</p>

<h1 align="center">
  <a href="README.md">🇬🇧</a>
  <a href="README.ru.md">🇷🇺</a>
</h1>

> [!NOTE]
> HHT is an unofficial community project. It is not affiliated with, endorsed by, or supported by the developers of Neverness to Everness.

## ✦ At a glance

| **Thing** | **Desc** |
|---|---|
| **Current module** | Owner's Selection |
| **Game process** | `HTGame.exe` |
| **Platforms** | Windows 10/11 x64 · Linux x86_64 (X11) |
| **Interface** | English · Русский |
| **Themes** | Light · Dark |
| **Automation** | OCR + window-bound input |
| **Hotkeys** | Capture any key or modifier combination (defaults: INS / DEL) |

## Interface technology

The desktop interface uses **PySide6 + Qt Quick (QML)**. The automation and OCR remain in Python and are exposed to QML through Qt signals and slots. The interface uses the Qt for Python Essentials distribution, which includes QtQml, QtQuick and QtQuick Controls.

## Features

- **Game-aware automation** — attaches to the `HTGame.exe` window and calculates clicks relative to its client area.
- **Owner's Selection module** — opens the event shop, taps the hammer, tracks income, claims the challenge reward, checks energy, and repeats while possible.
- **Adaptive income target** — reads the target shown by the current level; no hard-coded 1100 / 1900 level table.
- **OCR validation** — separates the changing yellow income from the static white target and confirms readings before acting.
- **State resynchronization** — confirms energy twice on the event start menu, reads income during the challenge, and rescans the visible counter after resuming from a pause. Ambiguous readings block further clicks.
- **Live dashboard** — cycle count, energy, income, game connection and status, without repeated shortcut hints.
- **Control settings** — click a shortcut field and press the key or combination you want for start / pause and stop. Letters, digits, function/navigation keys and Ctrl / Alt / Shift / Win combinations are supported. Choices persist between sessions.
- **Integrated workspace** — a persistent sidebar switches between hobby modules, Settings, About and the activity log inside one window.
- **Custom window frame** — custom title bar, window controls, drag-to-move and edge resizing without the standard Windows frame.
- **Selectable logs** — copy a highlighted excerpt with `Ctrl+C`, use the right-click menu, or copy the full log.
- **Personalized interface** — language dropdown, Light / Dark switch, and saved preferences.
- **Material Symbols Outlined** — official SVG glyphs bundled locally and tinted for the active theme. No remote font requests.
- **UI font:** Montserrat Variable is bundled locally for consistent rendering on Windows and Linux. It is distributed under the SIL Open Font License 1.1; see [assets/fonts/OFL.txt](assets/fonts/OFL.txt).
- **Windows elevation** — the Windows build requests Administrator privileges through UAC so HHT can send input to an elevated game process.

## Downloads

Get the latest published version from **[GitHub Releases](https://github.com/M1ST0R/hethereau-hobbies-tool/releases)**.

| Platform | Package | Notes |
|---|---|---|
| **Windows 10/11 x64** | `Hethereau-HHT-Windows-x64-VERSION.exe` | Portable single-file app; Tesseract OCR is bundled |
| **Debian / Ubuntu x86_64** | `hethereau-hobbies-tool_VERSION_amd64.deb` | Installable package for X11 |
| **Linux x86_64** | `Hethereau-HHT-Linux-x86_64-VERSION.tar.gz` | Portable PyInstaller folder; install Tesseract separately |

No release yet? The latest CI packages can be downloaded from **[Actions → Build HHT packages](https://github.com/M1ST0R/hethereau-hobbies-tool/actions/workflows/build.yml)**. Open a successful run and download the latest `HHT-dev-windows-x64-*` or `HHT-dev-linux-x86_64-*` artifact.

## Quick start

### Windows

1. Download the versioned `Hethereau-HHT-Windows-x64-VERSION.exe` file from [Releases](https://github.com/M1ST0R/hethereau-hobbies-tool/releases).
2. Launch HHT and approve the Windows UAC prompt.
3. Open **Owner's Selection** in NTE.
4. Wait until HHT finds `HTGame.exe`.
5. Press **Start**. Change global shortcuts from the **Settings** section when needed.

The packaged EXE contains a `requireAdministrator` manifest. To run from source, use `start.bat`; it requests elevation before installing Python dependencies.

### Linux (Debian / Ubuntu, X11)

Install the package:

```bash
sudo apt install ./hethereau-hobbies-tool_*_amd64.deb
```

Then launch **Hethereau Hobbies Tool** from the application menu or run:

```bash
hht
```

HHT runs as the current desktop user. **Do not launch it with `sudo`** — elevated root GUI processes can lose access to the user's desktop session and input devices.

### Run from source

Requirements: Python 3.10+, PySide6 Essentials (installed from `requirements.txt`), Tesseract OCR. Linux additionally requires an X11 desktop session, `scrot`, and `wmctrl`.

**Windows:** run `start.bat`.

**Linux:**

```bash
chmod +x start.sh
./start.sh
```

## Controls

| Action | Control |
|---|---|
| Start / pause | Selected key in **Settings** |
| Stop automation | Selected key in **Settings** |
| Emergency stop | Move the cursor to the top-left screen corner |
| Change language | Language dropdown in the header |
| Change appearance | Light / Dark switch in the header |
| Workspace navigation | **Owner / About / Logs** tabs in the left sidebar |
| Copy selected log text | Select text, then `Ctrl+C` or right-click → Copy selection |
| Copy full activity history | **Copy all** on the Logs tab |

## How level detection works

The challenge target can differ between levels. HHT reads the current / target counter from the game instead of relying on a fixed list.

To reduce mistakes such as reading `1270/1900` as `70/1`, the Owner's Selection module:
1. Separates the yellow current-income digits from the white target digits.
2. Confirms the static target with independent OCR passes.
3. Reuses the confirmed target during the active challenge.
4. Prefers valid readings that preserve leading digits and preserves income values that overshoot the target, such as `2303/1900`.
5. Stops hammer input when the target is detected and performs a fresh paired confirmation before leaving the event.

Energy OCR is restricted to the event start menu (the screen with the **Start** button), because the same screen area displays a different value during gameplay. During the challenge HHT reads income only. Energy is accepted only when two independent screenshots agree; a single complete OCR ratio remains provisional until the second screenshot confirms it. Supervise the first run on a new resolution or level.

## Diagnostics

Use **Scan visible counter** in **Settings → Game window and diagnostics**. HHT scans the counter appropriate to the current screen: energy in the event start menu and income during the challenge. The selected counter is captured twice and only stable readings are accepted. Automation performs screen-specific checks when starting a cycle, after opening the event shop, and after resuming from pause. If the required counter cannot be confirmed, HHT does not continue clicking. Captured counter regions are saved in the HHT user configuration folder:

- `debug_income_capture.png` — income counter;
- `debug_energy_capture.png` — original energy area; `debug_energy_gray.png` and `debug_energy_threshold.png` — processed variants.
- `debug_income_current_mask.png`, `debug_income_current_relaxed.png`, `debug_income_current_fallback.png` — current-income OCR diagnostics.

`debug_hammer_target.png` — the active game screen with the expected hammer click point marked in red; `debug_reward_target.png` — the reward screen with the expected claim-button click point marked in red.

When reporting an OCR or click-position issue, attach the relevant images and copy the recent activity log.

## Project direction

HHT is intended to become a collection of small, independent activity modules rather than one script tied to a single event.

| Module | Status |
|---|---|
| Owner's Selection | <strong>Available</strong> |
| Fishing | Planned |
| More NTE hobbies | Planned |

Each module can have its own window logic, screen regions, OCR strategy, controls, and status reporting while sharing the same app shell.

## Building

GitHub Actions builds both platforms on pushes to `main`, pull requests, and manual dispatches.

- [Build workflow](.github/workflows/build.yml)
- Windows: one-file EXE with UAC manifest.
- Linux: Debian package and portable TAR.GZ.
- Push a version tag such as `v0.4.0` to create a GitHub Release automatically.

## Versioning and releases

HHT uses a simple SemVer-based two-channel workflow.

| Channel | Version example | How it is created | Where to get it |
|---|---|---|---|
| **DEV** | `0.3.0-dev.142+1a2b3c4` | Every push to `main` (also PR/manual CI runs) | GitHub Actions artifacts |
| **Release** | `0.3.0` | Run the workflow with a release version, or push a `v0.3.0` tag | GitHub Releases |
| **Prerelease** | `0.4.0-beta.1` | Run the workflow with a prerelease version, or push a `v0.4.0-beta.1` tag | GitHub Releases, marked as prerelease |

### Create a release from GitHub Actions

1. Open **Actions → Build HHT packages → Run workflow**.
2. Select the branch to release (normally `main`).
3. Enter a version in **Release version**, without the leading `v`:
   - `0.3.0` for a stable release;
   - `0.4.0-beta.1` for a prerelease.
4. Click **Run workflow**.

HHT builds Windows and Linux packages, creates the matching Git tag (`v0.3.0`), and publishes a GitHub Release with the generated files. The tag is created only after both platform builds succeed.

Leave **Release version** empty to create a DEV build only. No Git tag or Release is created.

### Version rules

- Use `MAJOR.MINOR.PATCH`, for example `0.3.0`.
- Increase **PATCH** for fixes, **MINOR** for backwards-compatible features, and **MAJOR** for breaking changes.
- Use suffixes such as `-alpha.1`, `-beta.1`, or `-rc.1` for prereleases.
- The app's **About** window shows the exact build version and whether it is DEV or Release.
- DEV builds have unique run numbers and a short commit SHA, so two Actions builds are easy to distinguish.

## App icon

The original HHT launcher artwork is stored in `assets/app_icon.png`. Windows packaging generates a multi-size `.ico` from this PNG; Linux packaging uses the PNG directly.

**Icon artwork location:** `assets/app_icon.png` (restored original artwork).

## Credits

- UI glyphs: [Google Material Symbols Outlined](https://github.com/google/material-design-icons), licensed under Apache License 2.0. See [LICENSE-MATERIAL-SYMBOLS.txt](LICENSE-MATERIAL-SYMBOLS.txt).
- HHT source code: MIT. See [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built for the little things you would rather not repeat.</sub>
</p>
