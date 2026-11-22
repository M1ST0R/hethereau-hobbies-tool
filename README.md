# Hethereau Owner's Selection Tool

[English](README.md) | [Русский](README.ru.md)

A Windows desktop tool that automates the **Owner's Selection** event in **Hethereau**. It attaches to the game window (`HTGame.exe`), reads the event income and energy counters with OCR, completes the challenge, claims the reward, and repeats while enough energy remains.

> This is an unofficial, community-made automation tool. It is not affiliated with or endorsed by the game's developers.

## Features

- Finds and attaches to the `HTGame.exe` window.
- Uses the game window's client area for screenshots and mouse coordinates.
- Opens the event shop and repeatedly clicks the hammer.
- Detects the target income **automatically from the current level**. The target is read from the denominator of the live income counter (for example, `1100` or `1900`); it is not hard-coded to one difficulty.
- Waits for the target to be reached and confirmed by a second OCR reading.
- Exits the challenge, claims the reward, checks energy, and starts another cycle when possible.
- Provides a dark desktop GUI with cycle, energy, and income indicators, status display, and activity log.
- Global hotkeys: `F6` to start/pause/resume and `F7` to stop.
- Supports English and Russian. Use the `RU` / `EN` button in the top-right corner. The selected language is saved locally.

## Automatic level detection

The tool reads the income counter as `current / target` and uses the target shown by the game for the selected challenge level. It does not maintain a hard-coded list of difficulty levels.

To avoid acting on incomplete OCR results (for example, reading `70/1` while the real value is `1270/1900`), the app:

- runs several OCR passes with different image channels, scales, and segmentation;
- requires the target denominator to appear consistently in at least two passes;
- rejects incomplete values that do not form a valid `current / target` ratio;
- uses the detected target for the current run and confirms completion with two consecutive readings.

The minimum denominator sanity check is only a guard against tiny OCR fragments; the actual target value is taken from the game screen.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` (or available through `PATH`).
- The game running in a visible, non-minimized window.

Python dependencies are listed in `requirements.txt` and are installed by `start.bat`.

## Run

1. Download and extract the project ZIP, or clone this repository.
2. Install Tesseract OCR.
3. Run `start.bat`.
4. Open the **Owner's Selection** event in the game.
5. Check that the app has found `HTGame.exe`.
6. Press **Start** or `F6`.

## Controls

| Action | Control |
|---|---|
| Start / pause / resume | `F6` |
| Stop automation | `F7` |
| Emergency stop | Move the mouse cursor to the top-left corner of the screen |
| Change application language | `RU` / `EN` button in the app header |

## OCR diagnostics

Use **Test OCR** in the app. The latest captured regions are saved beside the script:

- `debug_energy_capture.png` — energy counter region;
- `debug_income_capture.png` — income counter region.

If OCR fails, inspect these images and include them when reporting a problem.

## Notes and limitations

- The game window must remain visible and must not be covered by another window while OCR is running.
- Click positions are scaled from a 1600×900 reference client area. Other client sizes are proportionally scaled, but should be tested before unattended use.
- The automation has not been verified against every game level, resolution, or display-scaling configuration. Supervise the first run.
- The selected application language is stored in `app_config.json`; this local preference file is ignored by Git.

## License

MIT. See [LICENSE](LICENSE).
