# HHT Mobile — Android prototype

> Experimental branch: `android/mobile-overlay-prototype`. The Android companion is a prototype and is not yet a release build.

HHT Mobile combines an on-screen HHT control panel, a dedicated income OCR crop, and manually configured tap points for Neverness to Everness.

## Included

- Bilingual (English/Russian) onboarding and control screens.
- Permission setup for overlay display, battery restrictions, notifications, screen capture, and optional tap automation.
- Floating HHT panel with Start/Scan, Pause/Resume, Stop, point editing, one-shot tap execution, and one Quit HHT action.
- Adaptive screen capture through Android MediaProjection.
- On-device ML Kit Text Recognition with the model bundled in the APK.
- Income OCR uses a dedicated crop around the `Доход` row in the upper-right game HUD. It no longer scans arbitrary number ratios from the entire screen.
- The income crop is based on the six supplied 2244×1008 screenshots and uses normalized screen coordinates, then enlarges the cropped row before recognition.
- Saved tap points are added from the floating panel. HHT shows numbered markers and stores normalized coordinates, with a maximum of 20 points.
- Tap points execute once, in the order they were added. There is a 450 ms pause between taps. The sequence can be stopped from the floating panel.
- Tap positions are normalized to the screen dimensions. HHT asks for points to be re-added if the screen aspect ratio changes substantially.
- The point editor intercepts calibration touches: those touches register coordinates and are **not** sent to the game.

## Tap automation and privacy

Tap execution requires the user to enable **HHT Tap Control** manually in Android Accessibility settings. Android does not allow HHT to enable this access silently.

The service uses Android's `AccessibilityService.dispatchGesture()` API to send taps at saved coordinates. Its service configuration sets `canPerformGestures=true` and `canRetrieveWindowContent=false`: it can perform the gestures requested by the user, but it does not inspect the game's accessibility tree or read other apps' UI text.

The point sequence is currently a manual, one-shot action. It does not loop, decide which game action to perform, or automatically react to OCR income. Those behaviours should only be added after the saved coordinates and tap timing are validated in the game.

## OCR calibration notes

The supplied screenshots show the income row at approximately 74.0–93.6% of screen width and 8.9–17.4% of screen height. The crop is calibrated for that HUD layout. If the game changes its interface, aspect ratio, or HUD placement, the crop may need recalibration.

OCR reads only the cropped row and returns the first valid `current / target` pair. If it cannot find a valid pair, the overlay reports the recognized text from that crop rather than mixing ratios from other parts of the screen.

## Permissions and Android behaviour

- Minimum Android version: Android 8.0 (API 26), required for `TYPE_APPLICATION_OVERLAY`.
- The user must explicitly allow HHT to display over other apps.
- The user must approve each screen-capture session through the Android system prompt. HHT does not retain or reuse a MediaProjection token.
- Screen capture runs in a foreground service with the `mediaProjection` service type.
- The service registers `MediaProjection.Callback` and releases its virtual display and image reader when capture stops.
- The user must separately enable HHT Tap Control in Accessibility settings before taps can be sent.
- The floating HHT panel and point editor reserve the status/navigation-bar safe area where their controls are placed.
- If the user selects the entire display in the Android capture prompt, the overlay may also appear in the captured image. Select the game app/window when Android offers that option.
- Play Protect or other Android installation verification is controlled by the operating system; HHT does not attempt to bypass it.

## Build

Requirements:

- JDK 17
- Android SDK Platform 36
- Android SDK Build Tools 36.0.0
- Gradle 9.6.0
- Android Gradle Plugin 9.5.0

Open the `android/` folder in Android Studio or run:

```bash
gradle --no-daemon :app:assembleDebug
```

Debug APK output:

```
app/build/outputs/apk/debug/app-debug.apk
```

The branch includes an Android GitHub Actions workflow that builds this debug APK and uploads it as an artifact. This repository snapshot does not yet include a Gradle wrapper.
