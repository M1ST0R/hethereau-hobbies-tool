# HHT Mobile — Android prototype

> Experimental branch: `android/mobile-overlay-prototype`. This is a read-only MVP scaffold, not a release APK.

HHT Mobile is a separate Android companion for the Hethereau Hobbies Tool. The first milestone is deliberately limited to a floating Hobi panel, explicit screen-capture consent, and on-device OCR.

## Included in this prototype

- Draggable floating bubble and compact expanded panel.
- Screen capture through Android MediaProjection.
- ML Kit Text Recognition with the model bundled in the APK, so the recognizer does not need to download its model at first launch.
- Extraction of visible `current/maximum` number pairs from OCR text.
- Pause, resume, request-an-extra-scan, and stop controls.
- Frame throttling and a single in-flight OCR task. Stale frames are discarded rather than queued.

## Not implemented yet

- Automated game taps or gestures.
- Separate classification of energy vs. income.
- Mobile-game counter coordinates and resolution calibration.
- Level profiles, reward claiming, or the Windows HHT automation engine.

The NTE mobile layout may differ from the desktop layout. The prototype therefore reports generic ratios instead of guessing which number is energy or income. The next implementation step is to collect a few real mobile screenshots, calibrate two small OCR regions, and validate the readings on-device.

## Permissions and Android behavior

- Minimum Android version: Android 8.0 (API 26), required for `TYPE_APPLICATION_OVERLAY`.
- The user must explicitly allow HHT Mobile to display over other apps.
- The user must approve each screen-capture session through the Android system prompt. The app does not retain or reuse a MediaProjection token.
- Screen capture runs in a foreground service with the `mediaProjection` service type.
- The service registers `MediaProjection.Callback` and releases its virtual display and image reader when capture stops.
- For cleaner OCR, choose the game app/window in the Android screen-capture prompt when that option is offered. If the user selects the entire display, the overlay may also appear in the captured image.

The current prototype does not request Accessibility access and does not simulate taps. That permission can be considered later, after the OCR regions and game-state logic are validated.

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

## Suggested next milestones

1. Validate overlay permissions and projection lifecycle on a physical Android device.
2. Capture screenshots from the actual mobile game and calibrate the income/energy regions.
3. Measure OCR latency on the target phone and tune the frame interval.
4. Add an explicit, user-enabled AccessibilityService only if real automation is still needed.
5. Add profiles, settings, logs, and a proper Hobi visual asset after the capture/OCR loop is reliable.
