# Hethereau Owner's Selection Tool (HOST)

[English](README.md) | [Русский](README.ru.md)

Desktop automation for the **Owner's Selection** event in **Hethereau**.

HOST attaches to the game window (HTGame.exe), reads income and energy counters with OCR, completes the challenge, claims the reward, and repeats while enough energy remains.

> Unofficial community project. HOST is not affiliated with, endorsed by, or supported by the game's developers.

## Downloads

Prebuilt packages are published in [GitHub Releases](https://github.com/M1ST0R/hethereau-owners-selection-tool/releases).

| Platform | Package | Notes |
|---|---|---|
| Windows 10/11 x64 | Hethereau-HOST-Windows-x64.exe | Portable single-file executable; includes Tesseract OCR |
| Linux x86_64 | hethereau-host_<version>_amd64.deb | Debian/Ubuntu package for X11 sessions |
| Linux x86_64 | Hethereau-HOST-Linux-x86_64.tar.gz | Portable PyInstaller folder; Tesseract must be installed separately |

The latest workflow build is also available under the repository's **Actions → Build packages** run artifacts. A GitHub Release is created automatically when a tag starting with v is pushed (for example, v0.3.0).

## Features

- Finds and attaches to the HTGame.exe game window.
- Uses the game's client area for screenshots and click coordinates.
- Opens the event shop and repeatedly clicks the hammer.
- Detects the target income automatically from the live counter denominator (for example, 1100 or 1900); the target is not hard-coded to one difficulty.
- Requires OCR consensus for the target and confirms completion with a second reading.
- Exits the challenge, claims the reward, checks energy, and starts another cycle when possible.
- Dark desktop GUI with cycle, energy, and income indicators, status display, and activity log.
- Global hotkeys: F6 to start/pause/resume and F7 to stop.
- English and Russian UI. Use the RU / EN button in the app header; the choice is saved locally.

## Installation

### Windows

1. Download Hethereau-HOST-Windows-x64.exe from [Releases](https://github.com/M1ST0R/hethereau-owners-selection-tool/releases).
2. Run the executable. Tesseract OCR and its bundled language data are included.
3. Open the Owner's Selection event in the game.
4. Confirm that HOST has found HTGame.exe, then press Start or F6.

For running from source, install Python 3.10+, install Tesseract OCR, then run start.bat. The starter requests administrator privileges before installing dependencies.

### Linux (Debian / Ubuntu, X11)

Install the .deb package:

~~~bash
sudo apt install ./hethereau-host_*_amd64.deb
~~~

Then launch Hethereau Owner's Selection Tool from the application menu or run:

~~~bash
hethereau-host
~~~

The package installs the required X11 utilities and Tesseract language data through package dependencies.

On Windows, HOST always requests administrator privileges through UAC before starting. The packaged EXE carries a `requireAdministrator` manifest, and source runs elevate themselves. This is needed when HOST must send input to applications that run with elevated privileges. Review the UAC prompt before approving.

**Linux limitations:**
- X11 is required. Wayland-only sessions are not supported because global input hooks, window activation, and screen capture rely on X11.
- The game must be visible and not covered by another window.
- If running the Windows game through Wine/Proton, Linux support is experimental. The game window must expose the _NET_WM_PID property and the associated process must be identifiable as HTGame.exe.
- The Linux build is provided for x86_64.

To run from source on Linux, install Python 3.10+, Tk support, Tesseract OCR with English data, and X11 utilities (scrot, wmctrl), then run:

~~~bash
chmod +x start.sh
./start.sh
~~~

### Linux portable archive

Extract Hethereau-HOST-Linux-x86_64.tar.gz, install Tesseract OCR and X11 utilities, then run ./run.sh from the extracted folder.

## Controls

| Action | Control |
|---|---|
| Start / pause / resume | F6 |
| Stop automation | F7 |
| Emergency stop | Move the mouse cursor to the top-left corner of the screen |
| Change application language | RU / EN in the app header |

## Automatic level detection

HOST reads the income counter as current / target and uses the target shown by the game for the selected challenge level. It does not maintain a hard-coded list of level limits.

To avoid acting on incomplete OCR results (for example, 70/1 instead of 1270/1900), the app:
- runs several OCR passes with different image channels, scales, and segmentation;
- requires the target denominator to appear consistently in multiple passes;
- rejects incomplete or invalid ratios;
- confirms that the target has been reached with two consecutive readings.

The first run on a new level or display resolution should be supervised.

## OCR diagnostics

Use Test OCR in the app. Captured regions are saved beside the application:

- debug_energy_capture.png — energy counter;
- debug_income_capture.png — income counter.

Attach these images to bug reports if OCR fails.

## Building packages locally

GitHub Actions builds both platforms. To build manually, install the platform-specific dependencies and PyInstaller, then use the commands in .github/workflows/build.yml.

## Icon attribution

The UI symbols are adapted from **Material Symbols Rounded** by Google and are licensed under Apache License 2.0. The required license text is included in [LICENSE-MATERIAL-SYMBOLS.txt](LICENSE-MATERIAL-SYMBOLS.txt). The HOST launcher icon is an original project asset.

## License

HOST source code: MIT. See [LICENSE](LICENSE).
