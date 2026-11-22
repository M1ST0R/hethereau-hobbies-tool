# Hethereau Hobbies Tool (HHT)

[English](README.md) | [Русский](README.ru.md)

**Hethereau Hobbies Tool (HHT)** is a growing desktop toolkit for automating hobbies and side activities in **Neverness to Everness (NTE)**.

The first available automation module is **Owner's Selection**. The project is designed to add more independent activity modules later, including fishing and other NTE hobbies.

> Unofficial community project. HHT is not affiliated with, endorsed by, or supported by the game's developers.

## Downloads

Prebuilt packages are published in [GitHub Releases](https://github.com/M1ST0R/hethereau-hobbies-tool/releases).

| Platform | Package | Notes |
|---|---|---|
| Windows 10/11 x64 | Hethereau-HHT-Windows-x64.exe | Portable single-file executable; includes Tesseract OCR |
| Linux x86_64 | hethereau-hobbies-tool_VERSION_amd64.deb | Debian/Ubuntu package for X11 sessions |
| Linux x86_64 | Hethereau-HHT-Linux-x86_64.tar.gz | Portable PyInstaller folder; Tesseract must be installed separately |

Build artifacts are also available under **Actions → Build HHT packages**. A GitHub Release is created automatically when a tag starting with v is pushed (for example, v0.4.0).

## Features

- Attaches to the HTGame.exe game window and uses its client area for screenshots and clicks.
- Automates the Owner's Selection event: opens the event shop, clicks the hammer, reads income, claims the reward, checks energy, and repeats while possible.
- Detects target income from the live counter, so different challenge levels can use different target values.
- Uses OCR consensus and confirmation reads to avoid reacting to incomplete or animated numbers.
- Desktop dashboard with cycles, energy, income, current status, and global hotkeys.
- Separate **View logs** and **About** windows.
- Language dropdown with English and Russian; the language registry is structured to add more translations.
- Explicit **Light / Dark** theme switch; the choice is saved locally.
- Actual Google **Material Symbols Outlined** SVG glyphs are bundled and rendered locally. No web font or network connection is needed at runtime.
- Windows build requests Administrator privileges through UAC, allowing HHT to send input to elevated NTE processes.
- Global hotkeys: F6 to start/pause/resume and F7 to stop.

## Installation

### Windows

1. Download Hethereau-HHT-Windows-x64.exe from [Releases](https://github.com/M1ST0R/hethereau-hobbies-tool/releases).
2. Run the EXE and approve the Windows UAC prompt.
3. Open the Owner's Selection event in NTE.
4. Confirm that HHT has found HTGame.exe, then press Start / Pause or F6.

The EXE contains a requireAdministrator manifest. Running start.bat from source also requests elevation before installing dependencies and launching HHT.

### Linux (Debian / Ubuntu, X11)

Install the DEB package:

    sudo apt install ./hethereau-hobbies-tool_*_amd64.deb

Then launch Hethereau Hobbies Tool from the application menu or run:

    hht

The package installs required X11 utilities, Cairo runtime libraries, and Tesseract language data through package dependencies. HHT runs as the current desktop user; do not launch it with sudo.

**Linux limitations:**
- X11 is required. Wayland-only sessions are not supported because global input hooks, window activation, and screen capture rely on X11.
- The game must be visible and not covered by another window.
- If the Windows game is running through Wine/Proton, support is experimental. The game window must expose _NET_WM_PID, and the associated process must be identifiable as HTGame.exe.
- The Linux build targets x86_64.

To run from source on Linux, install Python 3.10+, Tk support, Tesseract OCR with English data, X11 utilities (scrot, wmctrl), and Cairo development libraries, then run:

    chmod +x start.sh
    ./start.sh

### Linux portable archive

Extract Hethereau-HHT-Linux-x86_64.tar.gz, install Tesseract OCR and X11 utilities, then run ./run.sh from the extracted folder.

## Controls

| Action | Control |
|---|---|
| Start / pause / resume | F6 |
| Stop automation | F7 |
| Emergency stop | Move the mouse cursor to the top-left corner of the screen |
| Change language | Language dropdown in the header |
| Change theme | Light / Dark switch in the header |
| Open logs | View logs button |
| About HHT | About button |

## Adding another language

The language selector is data-driven. To add a language:
1. Add its language code and display label to SUPPORTED_LANGUAGES.
2. Add a matching dictionary to LANGUAGE_TRANSLATIONS.
3. Translate the interface strings and test layouts with longer labels.

English remains the fallback for strings that have not yet been translated.

## Current and planned hobby modules

- **Available:** Owner's Selection.
- **Planned:** fishing and other NTE hobby activities.

Each activity should be implemented as a separate module so it can have its own game-window logic, OCR regions, controls, and status reporting.

## OCR diagnostics

Use Test OCR in the app. Captured regions are saved beside the application:

- debug_energy_capture.png — energy counter;
- debug_income_capture.png — income counter.

Attach these images to bug reports if OCR fails.

## Building packages locally

GitHub Actions builds Windows and Linux packages. The main workflow is .github/workflows/build.yml.

## Icon attribution

The UI icons are Google's **Material Symbols Outlined**, distributed under Apache License 2.0. The license text is included in LICENSE-MATERIAL-SYMBOLS.txt. The HHT app launcher icon/mascot is a separate branding asset and will be added after the final visual direction is chosen.

## License

HHT source code: MIT. See LICENSE.
