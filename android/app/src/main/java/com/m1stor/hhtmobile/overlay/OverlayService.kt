package com.m1stor.hhtmobile.overlay

import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.m1stor.hhtmobile.AppActions

class OverlayService : Service() {
    private lateinit var windowManager: WindowManager
    private var overlayView: View? = null
    private var expanded = false
    private var receiverRegistered = false
    private var capturePaused = false
    private var windowParams: WindowManager.LayoutParams? = null
    private var metricsView: TextView? = null
    private var statusView: TextView? = null
    private var pauseButton: Button? = null

    private val resultReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action != AppActions.ACTION_OCR_RESULT) return
            val value = intent.getStringExtra(AppActions.EXTRA_OCR_TEXT) ?: "Счётчики не найдены"
            metricsView?.text = value
            statusView?.text = "Последний OCR-кадр обработан"
        }
    }

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager

        val filter = IntentFilter(AppActions.ACTION_OCR_RESULT)
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(resultReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(resultReceiver, filter)
        }
        receiverRegistered = true
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!Settings.canDrawOverlays(this)) {
            stopSelf()
            return START_NOT_STICKY
        }
        if (overlayView == null) showBubble()
        return START_STICKY
    }

    private fun showBubble() {
        val bubble = TextView(this).apply {
            text = "H"
            textSize = 20f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            background = rounded(Color.rgb(31, 190, 185), 28f)
            elevation = dp(8).toFloat()
        }

        val params = WindowManager.LayoutParams(
            dp(56),
            dp(56),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = dp(18)
            y = dp(180)
        }
        windowParams = params
        bubble.setOnTouchListener(makeDragListener())
        overlayView = bubble
        expanded = false
        windowManager.addView(bubble, params)
    }

    private fun showPanel() {
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(14), dp(16), dp(14))
            background = rounded(Color.rgb(20, 30, 44), 20f)
            elevation = dp(10).toFloat()
        }

        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val title = TextView(this).apply {
            text = "HOBI  ·  HHT"
            textSize = 15f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
        }
        header.addView(title, LinearLayout.LayoutParams(0, dp(34), 1f))
        header.addView(smallButton("—") { collapse() })
        panel.addView(header)

        val caption = makeText("РАСПОЗНАННЫЕ СЧЁТЧИКИ", 10f, Color.rgb(133, 156, 178), true)
        caption.setPadding(0, dp(12), 0, dp(6))
        panel.addView(caption)

        metricsView = makeText("Ожидаю первый OCR-кадр…", 15f, Color.WHITE, true)
        metricsView?.setPadding(0, 0, 0, dp(8))
        panel.addView(metricsView)

        statusView = makeText("Захват пока не запущен", 11f, Color.rgb(166, 183, 199), false)
        statusView?.setPadding(0, 0, 0, dp(12))
        panel.addView(statusView)

        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        controls.addView(smallButton("Скан") {
            sendCaptureCommand(AppActions.ACTION_SCAN_NOW)
            statusView?.text = "Запрошен свежий кадр…"
        }, equalButtonParams())
        pauseButton = smallButton("Пауза") {
            capturePaused = !capturePaused
            val action = if (capturePaused) AppActions.ACTION_PAUSE_CAPTURE else AppActions.ACTION_RESUME_CAPTURE
            sendCaptureCommand(action)
            pauseButton?.text = if (capturePaused) "Продолжить" else "Пауза"
            statusView?.text = if (capturePaused) "OCR приостановлен" else "OCR возобновлён"
        }
        controls.addView(pauseButton, equalButtonParams())
        controls.addView(smallButton("Стоп") {
            sendCaptureCommand(AppActions.ACTION_STOP_CAPTURE)
            statusView?.text = "Отправлена команда остановки захвата"
        }, equalButtonParams())
        panel.addView(controls)

        val hint = makeText("Только OCR · без игровых нажатий", 10f, Color.rgb(133, 156, 178), false)
        hint.setPadding(0, dp(10), 0, 0)
        panel.addView(hint)

        val params = windowParams ?: WindowManager.LayoutParams(
            dp(56), dp(56),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply { gravity = Gravity.TOP or Gravity.START }
        params.width = dp(292)
        params.height = WindowManager.LayoutParams.WRAP_CONTENT

        overlayView?.let { windowManager.removeView(it) }
        overlayView = panel
        expanded = true
        windowManager.addView(panel, params)
        windowParams = params
    }

    private fun collapse() {
        overlayView?.let { windowManager.removeView(it) }
        metricsView = null
        statusView = null
        pauseButton = null
        showBubble()
    }

    private fun makeDragListener(): View.OnTouchListener {
        var downX = 0f
        var downY = 0f
        var startX = 0
        var startY = 0
        var moved = false

        return View.OnTouchListener { _, event ->
            val params = windowParams ?: return@OnTouchListener false
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX
                    downY = event.rawY
                    startX = params.x
                    startY = params.y
                    moved = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - downX).toInt()
                    val dy = (event.rawY - downY).toInt()
                    if (kotlin.math.abs(dx) + kotlin.math.abs(dy) > dp(5)) moved = true
                    params.x = (startX + dx).coerceAtLeast(0)
                    params.y = (startY + dy).coerceAtLeast(0)
                    overlayView?.let { windowManager.updateViewLayout(it, params) }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (!moved) showPanel()
                    true
                }
                else -> false
            }
        }
    }

    private fun sendCaptureCommand(action: String) {
        sendBroadcast(Intent(action).setPackage(packageName))
    }

    private fun smallButton(label: String, action: () -> Unit): Button =
        Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 11f
            minHeight = dp(38)
            minimumHeight = dp(38)
            setPadding(dp(4), 0, dp(4), 0)
            setTextColor(Color.WHITE)
            background = rounded(Color.rgb(43, 64, 83), 10f)
            setOnClickListener { action() }
        }

    private fun equalButtonParams() = LinearLayout.LayoutParams(
        0, dp(40), 1f
    ).apply {
        marginEnd = dp(5)
    }

    private fun makeText(value: String, size: Float, color: Int, bold: Boolean): TextView =
        TextView(this).apply {
            text = value
            textSize = size
            setTextColor(color)
            if (bold) typeface = Typeface.DEFAULT_BOLD
        }

    private fun rounded(color: Int, radius: Float): GradientDrawable =
        GradientDrawable().apply {
            setColor(color)
            cornerRadius = dp(radius.toInt()).toFloat()
        }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        overlayView?.let {
            try { windowManager.removeView(it) } catch (_: Exception) { }
        }
        overlayView = null
        if (receiverRegistered) {
            try { unregisterReceiver(resultReceiver) } catch (_: Exception) { }
        }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
