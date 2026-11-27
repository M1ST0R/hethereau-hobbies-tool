package com.m1stor.hhtmobile.taps

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.ComponentName
import android.content.Context
import android.graphics.Path
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.accessibility.AccessibilityEvent
import kotlin.math.abs
import kotlin.math.roundToInt

class TapAccessibilityService : AccessibilityService() {
    companion object {
        private const val TAP_DURATION_MS = 70L
        private const val INTER_TAP_DELAY_MS = 450L
        private const val MAX_ASPECT_DELTA = 0.12f

        @Volatile
        private var activeService: TapAccessibilityService? = null

        fun isEnabled(context: Context): Boolean {
            val expected = ComponentName(context, TapAccessibilityService::class.java)
                .flattenToString()
            val enabled = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            ).orEmpty()
            return enabled.split(':').any { it.equals(expected, ignoreCase = true) }
        }

        fun isConnected(): Boolean = activeService != null

        fun isRunning(): Boolean = activeService?.sequenceRunning == true

        fun runPoints(
            points: List<TapPoint>,
            screenWidth: Int,
            screenHeight: Int,
            onFinished: (success: Boolean, message: String) -> Unit
        ): Boolean {
            val service = activeService ?: return false
            return service.startSequence(points, screenWidth, screenHeight, onFinished)
        }

        fun stopPoints(): Boolean {
            val service = activeService ?: return false
            if (!service.sequenceRunning) return false
            service.finishSequence(false, "Stopped by user")
            return true
        }
    }

    private val handler = Handler(Looper.getMainLooper())

    @Volatile
    private var sequenceRunning = false

    private var sequencePoints: List<TapPoint> = emptyList()
    private var sequenceIndex = 0
    private var screenWidth = 0
    private var screenHeight = 0
    private var sequenceToken = 0
    private var completion: ((Boolean, String) -> Unit)? = null

    override fun onServiceConnected() {
        super.onServiceConnected()
        activeService = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // HHT does not inspect other apps' UI or accessibility node contents.
    }

    override fun onInterrupt() {
        if (sequenceRunning) finishSequence(false, "Interrupted by Android")
    }

    override fun onDestroy() {
        if (activeService === this) activeService = null
        if (sequenceRunning) finishSequence(false, "Accessibility service stopped")
        super.onDestroy()
    }

    private fun startSequence(
        points: List<TapPoint>,
        width: Int,
        height: Int,
        onFinished: (success: Boolean, message: String) -> Unit
    ): Boolean {
        if (sequenceRunning || points.isEmpty() || width <= 0 || height <= 0) return false

        val currentAspect = width.toFloat() / height.toFloat()
        if (points.any { abs(it.aspectRatio - currentAspect) > MAX_ASPECT_DELTA }) {
            handler.post { onFinished(false, "Screen orientation changed. Re-add the points.") }
            return true
        }

        sequencePoints = points.toList()
        sequenceIndex = 0
        screenWidth = width
        screenHeight = height
        completion = onFinished
        sequenceRunning = true
        sequenceToken += 1
        dispatchNext(sequenceToken)
        return true
    }

    private fun dispatchNext(token: Int) {
        if (!sequenceRunning || token != sequenceToken) return

        if (sequenceIndex >= sequencePoints.size) {
            finishSequence(true, "Completed ${sequencePoints.size} taps")
            return
        }

        val point = sequencePoints[sequenceIndex]
        val x = (point.xRatio * screenWidth).roundToInt().coerceIn(1, screenWidth - 2)
        val y = (point.yRatio * screenHeight).roundToInt().coerceIn(1, screenHeight - 2)
        val path = Path().apply { moveTo(x.toFloat(), y.toFloat()) }
        val stroke = GestureDescription.StrokeDescription(path, 0, TAP_DURATION_MS)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()

        val accepted = dispatchGesture(
            gesture,
            object : GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    if (!sequenceRunning || token != sequenceToken) return
                    sequenceIndex += 1
                    handler.postDelayed({ dispatchNext(token) }, INTER_TAP_DELAY_MS)
                }

                override fun onCancelled(gestureDescription: GestureDescription?) {
                    if (sequenceRunning && token == sequenceToken) {
                        finishSequence(false, "Tap ${sequenceIndex + 1} was cancelled")
                    }
                }
            },
            handler
        )

        if (!accepted && sequenceRunning && token == sequenceToken) {
            finishSequence(false, "Android rejected tap ${sequenceIndex + 1}")
        }
    }

    private fun finishSequence(success: Boolean, message: String) {
        if (!sequenceRunning && completion == null) return
        sequenceRunning = false
        sequenceToken += 1
        sequencePoints = emptyList()
        sequenceIndex = 0
        val callback = completion
        completion = null
        handler.post { callback?.invoke(success, message) }
    }
}
