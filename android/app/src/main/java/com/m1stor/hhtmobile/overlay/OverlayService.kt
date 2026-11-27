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
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import com.m1stor.hhtmobile.AppActions
import com.m1stor.hhtmobile.capture.ScreenCaptureService
import com.m1stor.hhtmobile.taps.TapAccessibilityService
import com.m1stor.hhtmobile.taps.TapPoint
import com.m1stor.hhtmobile.taps.TapPointStore
import kotlin.math.abs
import kotlin.math.roundToInt

class OverlayService : Service() {
    private lateinit var wm: WindowManager
    private var view: View? = null
    private var pointEditorView: FrameLayout? = null
    private var pointEditorParams: WindowManager.LayoutParams? = null
    private var registered = false
    private var paused = false
    private var params: WindowManager.LayoutParams? = null
    private var metrics: TextView? = null
    private var status: TextView? = null
    private var pauseBtn: Button? = null
    private var scanButton: Button? = null
    private var pointsButton: Button? = null
    private var runTapsButton: Button? = null
    private var stopTapsButton: Button? = null
    private var tapStatus: TextView? = null

    private val prefs by lazy { getSharedPreferences("hht_mobile", MODE_PRIVATE) }
    private val ru get() = prefs.getString("lang", "en") == "ru"
    private fun t(en: String, rus: String) = if (ru) rus else en
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                AppActions.ACTION_OCR_RESULT -> {
                    val value = intent.getStringExtra(AppActions.EXTRA_OCR_TEXT)
                        ?: t("Income not found", "Доход не найден")
                    prefs.edit().putString("last_ocr_readout", value).apply()
                    metrics?.text = value
                    status?.text = t("Income row scanned", "Строка дохода распознана")
                }
                AppActions.ACTION_CAPTURE_STATE -> updateCaptureControls()
                AppActions.ACTION_TAP_SEQUENCE_STATE -> {
                    val running = intent.getBooleanExtra(AppActions.EXTRA_TAP_RUNNING, false)
                    val message = intent.getStringExtra(AppActions.EXTRA_TAP_STATUS)
                        ?: t("Tap status unavailable", "Статус нажатий недоступен")
                    prefs.edit()
                        .putBoolean("tap_sequence_running", running)
                        .putString("tap_sequence_status", message)
                        .apply()
                    updateTapControls()
                }
                AppActions.ACTION_QUIT_OVERLAY -> quitAssistant()
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        paused = prefs.getBoolean("capture_paused", false)
        val filter = IntentFilter().apply {
            addAction(AppActions.ACTION_OCR_RESULT)
            addAction(AppActions.ACTION_CAPTURE_STATE)
            addAction(AppActions.ACTION_TAP_SEQUENCE_STATE)
            addAction(AppActions.ACTION_QUIT_OVERLAY)
        }
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(receiver, filter)
        }
        registered = true
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!Settings.canDrawOverlays(this)) {
            stopSelf()
            return START_NOT_STICKY
        }
        if (view == null && pointEditorView == null) bubble()
        return START_STICKY
    }

    private fun bubble() {
        val bubble = TextView(this).apply {
            text = "HHT"
            textSize = 13f
            typeface = Typeface.create("sans-serif-black", 0)
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            background = shape(Color.rgb(28, 166, 164), dp(30))
            elevation = dp(5).toFloat()
        }
        val layout = WindowManager.LayoutParams(
            dp(54),
            dp(54),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = params?.x ?: dp(14)
            y = params?.y ?: dp(180)
        }
        params = layout
        bubble.setOnTouchListener(drag())
        view = bubble
        wm.addView(bubble, layout)
        clampWindowPosition(bubble)
    }

    private fun panel() {
        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(15), dp(13), dp(15), dp(13))
            background = shape(Color.rgb(15, 22, 32), dp(20))
            elevation = dp(7).toFloat()
        }

        val header = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
        header.addView(
            TextView(this).apply {
                text = "HHT"
                textSize = 15f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.WHITE)
            },
            LinearLayout.LayoutParams(0, dp(32), 1f)
        )
        header.addView(btn("⌄") { collapse() })
        card.addView(header)

        label(card, t("INCOME OCR", "РАСПОЗНАВАНИЕ ДОХОДА"), 10, "#6F879D", top = 9, bold = true)
        val savedReadout = prefs.getString("last_ocr_readout", null)
        metrics = label(
            card,
            savedReadout ?: t("Waiting for income…", "Ожидаю доход…"),
            15,
            "#F3F7FA",
            top = 5,
            bold = true
        )

        val captureActive = prefs.getBoolean("capture_active", false)
        status = label(
            card,
            if (captureActive) t("Capture active", "Захват активен")
            else t("Capture stopped · last reading kept", "Захват остановлен · последние данные сохранены"),
            11,
            "#9EADBF",
            top = 9
        )

        val captureRow = LinearLayout(this).apply { gravity = Gravity.CENTER }
        scanButton = btn(if (captureActive) t("Scan", "Скан") else t("Start", "Старт")) {
            if (prefs.getBoolean("capture_active", false)) {
                sendCapture(AppActions.ACTION_SCAN_NOW)
                status?.text = t("Scan requested", "Запрошен скан")
            } else {
                requestCaptureFromOverlay()
            }
        }
        captureRow.addView(scanButton, weight())
        paused = prefs.getBoolean("capture_paused", false)
        pauseBtn = btn(if (paused) t("Resume", "Продолжить") else t("Pause", "Пауза")) {
            paused = !paused
            prefs.edit().putBoolean("capture_paused", paused).apply()
            sendCapture(if (paused) AppActions.ACTION_PAUSE_CAPTURE else AppActions.ACTION_RESUME_CAPTURE)
            pauseBtn?.text = if (paused) t("Resume", "Продолжить") else t("Pause", "Пауза")
            status?.text = if (paused) t("OCR paused", "OCR на паузе") else t("OCR resumed", "OCR продолжен")
        }
        pauseBtn?.isEnabled = captureActive
        captureRow.addView(pauseBtn, weight())
        captureRow.addView(
            btn(t("Stop", "Стоп")) {
                paused = false
                prefs.edit().putBoolean("capture_active", false).putBoolean("capture_paused", false).apply()
                sendCapture(AppActions.ACTION_STOP_CAPTURE)
                scanButton?.text = t("Start", "Старт")
                pauseBtn?.text = t("Pause", "Пауза")
                pauseBtn?.isEnabled = false
                status?.text = t(
                    "Capture stopped · last reading kept",
                    "Захват остановлен · последние данные сохранены"
                )
            },
            weight()
        )
        card.addView(captureRow)

        val savedPoints = TapPointStore.load(this)
        label(
            card,
            t("TAP POINTS · ${savedPoints.size}", "ТОЧКИ НАЖАТИЙ · ${savedPoints.size}"),
            10,
            "#6F879D",
            top = 12,
            bold = true
        )
        tapStatus = label(card, initialTapStatus(savedPoints.size), 11, "#9EADBF", top = 5)

        val tapRow = LinearLayout(this).apply { gravity = Gravity.CENTER }
        pointsButton = btn(t("Edit points", "Точки")) { openPointEditor() }
        tapRow.addView(pointsButton, weight())
        runTapsButton = btn(t("Run once", "Пуск")) { runTapPoints() }
        tapRow.addView(runTapsButton, weight())
        stopTapsButton = btn(t("Stop taps", "Стоп")) { stopTapPoints() }
        tapRow.addView(stopTapsButton, weight())
        card.addView(tapRow)
        updateTapControls()

        label(
            card,
            t("OCR + SAVED TAPS ONLY", "OCR + СОХРАНЁННЫЕ ТОЧКИ"),
            10,
            "#6F879D",
            top = 10
        )
        card.addView(
            btn(t("Quit HHT", "Выйти из HHT")) { quitAssistant() },
            LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(8) }
        )

        val layout = params ?: WindowManager.LayoutParams(
            dp(54),
            dp(54),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        )
        layout.width = dp(310)
        layout.height = -2
        view?.let { try { wm.removeView(it) } catch (_: Exception) { } }
        view = card
        wm.addView(card, layout)
        params = layout
        clampWindowPosition(card)
    }

    private fun initialTapStatus(pointCount: Int): String {
        if (TapAccessibilityService.isRunning()) return t("Running saved taps…", "Выполняю точки…")
        if (!TapAccessibilityService.isEnabled(this)) {
            return t("Tap access is not enabled", "Доступ для нажатий не включён")
        }
        if (pointCount == 0) return t("Add points, then run them once", "Добавь точки, затем запусти их")
        return prefs.getString("tap_sequence_status", null)
            ?: t("Ready · runs once in saved order", "Готово · один проход по порядку")
    }

    private fun updateTapControls() {
        val count = TapPointStore.load(this).size
        pointsButton?.text = t("Edit points ($count)", "Точки ($count)")
        val running = TapAccessibilityService.isRunning() ||
            prefs.getBoolean("tap_sequence_running", false)
        runTapsButton?.isEnabled = count > 0 && !running
        stopTapsButton?.isEnabled = running
        tapStatus?.text = if (running) {
            t("Running saved taps…", "Выполняю точки…")
        } else {
            initialTapStatus(count)
        }
    }

    private fun openPointEditor() {
        if (pointEditorView != null) return

        val display = DisplayMetrics()
        @Suppress("DEPRECATION")
        wm.defaultDisplay.getRealMetrics(display)
        val screenWidth = display.widthPixels.coerceAtLeast(1)
        val screenHeight = display.heightPixels.coerceAtLeast(1)
        val aspectRatio = screenWidth.toFloat() / screenHeight.toFloat()
        val points = TapPointStore.load(this).toMutableList()

        val root = FrameLayout(this).apply {
            setBackgroundColor(0x22000000)
            isClickable = true
        }
        val markerLayer = FrameLayout(this).apply {
            isClickable = false
            isFocusable = false
        }
        root.addView(
            markerLayer,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        )

        val instruction = TextView(this).apply {
            text = t(
                "Tap where HHT should press. Calibration taps are not sent to the game.",
                "Нажимай места, куда HHT должен нажимать. Калибровочные касания в игру не отправляются."
            )
            textSize = 12f
            setTextColor(Color.WHITE)
        }
        val countText = TextView(this).apply {
            textSize = 11f
            setTextColor(Color.rgb(108, 216, 213))
            typeface = Typeface.DEFAULT_BOLD
        }

        val toolbar = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(12), dp(10), dp(12), dp(10))
            background = shape(Color.rgb(15, 22, 32), dp(16))
            elevation = dp(8).toFloat()
        }
        toolbar.addView(instruction)
        toolbar.addView(countText, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = dp(5)
        })

        val toolbarButtons = LinearLayout(this).apply { gravity = Gravity.CENTER }
        val undoButton = btn(t("Undo", "Назад")) {
            if (points.isNotEmpty()) points.removeAt(points.lastIndex)
            TapPointStore.save(this@OverlayService, points)
            redrawPointMarkers(markerLayer, root, points, screenWidth, screenHeight)
            updateEditorCount(countText, points.size)
        }
        val clearButton = btn(t("Clear", "Очистить")) {
            points.clear()
            TapPointStore.save(this@OverlayService, points)
            redrawPointMarkers(markerLayer, root, points, screenWidth, screenHeight)
            updateEditorCount(countText, points.size)
        }
        val doneButton = btn(t("Done", "Готово")) { finishPointEditor() }
        toolbarButtons.addView(undoButton, weight())
        toolbarButtons.addView(clearButton, weight())
        toolbarButtons.addView(doneButton, weight())
        toolbar.addView(toolbarButtons, LinearLayout.LayoutParams(-1, dp(40)).apply {
            topMargin = dp(8)
        })

        val toolbarWidth = (screenWidth - dp(24)).coerceAtLeast(dp(240)).coerceAtMost(dp(380))
        val toolbarLayout = FrameLayout.LayoutParams(toolbarWidth, -2).apply {
            gravity = Gravity.TOP or Gravity.START
            leftMargin = dp(12)
            topMargin = statusBarInset() + dp(8)
        }
        root.addView(toolbar, toolbarLayout)

        root.setOnTouchListener { _, event ->
            if (event.action == MotionEvent.ACTION_UP) {
                if (points.size >= TapPointStore.MAX_POINTS) {
                    instruction.text = t(
                        "Point limit reached. Undo or clear a point.",
                        "Достигнут лимит точек. Удали или очисти точки."
                    )
                } else {
                    val x = event.rawX.coerceIn(0f, (screenWidth - 1).toFloat())
                    val y = event.rawY.coerceIn(0f, (screenHeight - 1).toFloat())
                    val minY = (statusBarInset() + dp(4)).toFloat()
                    val maxY = (screenHeight - navigationBarInset() - dp(4)).toFloat()
                    if (y in minY..maxY) {
                        points.add(
                            TapPoint(
                                xRatio = x / screenWidth,
                                yRatio = y / screenHeight,
                                aspectRatio = aspectRatio
                            )
                        )
                        TapPointStore.save(this@OverlayService, points)
                        instruction.text = t(
                            "Tap where HHT should press. Calibration taps are not sent to the game.",
                            "Нажимай места, куда HHT должен нажимать. Калибровочные касания в игру не отправляются."
                        )
                        redrawPointMarkers(markerLayer, root, points, screenWidth, screenHeight)
                        updateEditorCount(countText, points.size)
                    }
                }
            }
            true
        }

        updateEditorCount(countText, points.size)
        val layout = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
        }
        pointEditorView = root
        pointEditorParams = layout
        wm.addView(root, layout)
        redrawPointMarkers(markerLayer, root, points, screenWidth, screenHeight)
    }

    private fun updateEditorCount(view: TextView, count: Int) {
        view.text = t(
            "Saved points: $count / ${TapPointStore.MAX_POINTS}",
            "Сохранено точек: $count / ${TapPointStore.MAX_POINTS}"
        )
    }

    private fun redrawPointMarkers(
        layer: FrameLayout,
        root: FrameLayout,
        points: List<TapPoint>,
        screenWidth: Int,
        screenHeight: Int
    ) {
        layer.removeAllViews()
        val location = IntArray(2)
        root.getLocationOnScreen(location)
        points.forEachIndexed { index, point ->
            val markerSize = dp(34)
            val marker = TextView(this).apply {
                text = (index + 1).toString()
                textSize = 13f
                typeface = Typeface.DEFAULT_BOLD
                gravity = Gravity.CENTER
                setTextColor(Color.WHITE)
                background = shape(Color.rgb(28, 166, 164), markerSize)
                elevation = dp(4).toFloat()
            }
            val layout = FrameLayout.LayoutParams(markerSize, markerSize).apply {
                leftMargin = (point.xRatio * screenWidth).roundToInt() - location[0] - markerSize / 2
                topMargin = (point.yRatio * screenHeight).roundToInt() - location[1] - markerSize / 2
            }
            layer.addView(marker, layout)
        }
    }

    private fun finishPointEditor() {
        pointEditorView?.let {
            try { wm.removeView(it) } catch (_: Exception) { }
        }
        pointEditorView = null
        pointEditorParams = null
        panel()
    }

    private fun runTapPoints() {
        val points = TapPointStore.load(this)
        if (points.isEmpty()) {
            tapStatus?.text = t("Add at least one point first", "Сначала добавь хотя бы одну точку")
            return
        }

        if (!TapAccessibilityService.isEnabled(this)) {
            tapStatus?.text = t(
                "Enable HHT Tap Control in Accessibility settings",
                "Включи HHT Tap Control в настройках специальных возможностей"
            )
            try {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            } catch (_: Exception) { }
            return
        }
        if (!TapAccessibilityService.isConnected()) {
            tapStatus?.text = t(
                "HHT Tap Control is enabled but not connected. Reopen HHT or re-enable the service.",
                "HHT Tap Control включён, но не подключён. Перезапусти HHT или повторно включи службу."
            )
            return
        }

        val display = DisplayMetrics()
        @Suppress("DEPRECATION")
        wm.defaultDisplay.getRealMetrics(display)
        val currentAspect = display.widthPixels.toFloat() / display.heightPixels.toFloat()
        if (points.any { abs(it.aspectRatio - currentAspect) > 0.12f }) {
            tapStatus?.text = t(
                "Screen orientation changed. Re-add the points in the current layout.",
                "Ориентация экрана изменилась. Добавь точки заново в текущей ориентации."
            )
            return
        }

        // Remove the large panel and move the bubble away before injecting
        // the first gesture, otherwise the overlay itself could receive a tap.
        collapse()
        moveBubbleAwayFrom(points)

        val started = TapAccessibilityService.runPoints(
            points,
            display.widthPixels,
            display.heightPixels
        ) { success, _ ->
            val finalStatus = if (success) {
                t("Completed: ${points.size} taps", "Выполнено нажатий: ${points.size}")
            } else {
                t("Tap sequence stopped", "Последовательность остановлена")
            }
            publishTapState(false, finalStatus)
        }

        if (!started) {
            panel()
            tapStatus?.text = t(
                "HHT Tap Control could not start the tap sequence.",
                "Не удалось запустить последовательность HHT Tap Control."
            )
            return
        }

        publishTapState(true, t("Running saved taps…", "Выполняю сохранённые точки…"))
    }

    private fun moveBubbleAwayFrom(points: List<TapPoint>) {
        val bubble = view ?: return
        val currentParams = params ?: return
        val display = DisplayMetrics()
        @Suppress("DEPRECATION")
        wm.defaultDisplay.getRealMetrics(display)

        val bubbleWidth = dp(54)
        val bubbleHeight = dp(54)
        val minX = dp(8)
        val maxX = (display.widthPixels - bubbleWidth - dp(8)).coerceAtLeast(minX)
        val minY = statusBarInset() + dp(8)
        val maxY = (display.heightPixels - navigationBarInset() - bubbleHeight - dp(8))
            .coerceAtLeast(minY)

        val candidates = listOf(
            minX to minY,
            maxX to minY,
            minX to maxY,
            maxX to maxY
        )
        val safest = candidates.maxByOrNull { (candidateX, candidateY) ->
            points.minOf { point ->
                val pointX = point.xRatio * display.widthPixels
                val pointY = point.yRatio * display.heightPixels
                val dx = pointX - (candidateX + bubbleWidth / 2f)
                val dy = pointY - (candidateY + bubbleHeight / 2f)
                dx * dx + dy * dy
            }
        } ?: (minX to minY)

        currentParams.x = safest.first
        currentParams.y = safest.second
        try { wm.updateViewLayout(bubble, currentParams) } catch (_: Exception) { }
    }

    private fun stopTapPoints() {
        if (!TapAccessibilityService.stopPoints()) {
            tapStatus?.text = t("No tap sequence is running", "Нет выполняемой последовательности")
        }
    }

    private fun publishTapState(running: Boolean, message: String) {
        prefs.edit()
            .putBoolean("tap_sequence_running", running)
            .putString("tap_sequence_status", message)
            .apply()
        sendBroadcast(
            Intent(AppActions.ACTION_TAP_SEQUENCE_STATE)
                .setPackage(packageName)
                .putExtra(AppActions.EXTRA_TAP_RUNNING, running)
                .putExtra(AppActions.EXTRA_TAP_STATUS, message)
        )
    }

    private fun finishPointEditorIfOpen() {
        pointEditorView?.let {
            try { wm.removeView(it) } catch (_: Exception) { }
        }
        pointEditorView = null
        pointEditorParams = null
    }

    private fun collapse() {
        view?.let { try { wm.removeView(it) } catch (_: Exception) { } }
        view = null
        metrics = null
        status = null
        pauseBtn = null
        scanButton = null
        pointsButton = null
        runTapsButton = null
        stopTapsButton = null
        tapStatus = null
        bubble()
    }

    private fun drag(): View.OnTouchListener {
        var downX = 0f
        var downY = 0f
        var startX = 0
        var startY = 0
        var moved = false

        return View.OnTouchListener { _, event ->
            val currentParams = params
            if (currentParams == null) {
                false
            } else {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        downX = event.rawX
                        downY = event.rawY
                        startX = currentParams.x
                        startY = currentParams.y
                        moved = false
                        true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = (event.rawX - downX).toInt()
                        val dy = (event.rawY - downY).toInt()
                        if (abs(dx) + abs(dy) > dp(5)) moved = true
                        val display = DisplayMetrics()
                        @Suppress("DEPRECATION")
                        wm.defaultDisplay.getRealMetrics(display)
                        val target = view
                        val targetWidth = target?.width?.takeIf { it > 0 } ?: dp(54)
                        val targetHeight = target?.height?.takeIf { it > 0 } ?: dp(54)
                        val minY = statusBarInset() + dp(8)
                        val maxX = (display.widthPixels - targetWidth - dp(8)).coerceAtLeast(dp(8))
                        val maxY = (display.heightPixels - navigationBarInset() - targetHeight - dp(8))
                            .coerceAtLeast(minY)
                        currentParams.x = (startX + dx).coerceIn(dp(8), maxX)
                        currentParams.y = (startY + dy).coerceIn(minY, maxY)
                        target?.let { wm.updateViewLayout(it, currentParams) }
                        true
                    }
                    MotionEvent.ACTION_UP -> {
                        if (!moved) panel()
                        true
                    }
                    else -> false
                }
            }
        }
    }

    private fun statusBarInset(): Int {
        val id = resources.getIdentifier("status_bar_height", "dimen", "android")
        return if (id > 0) resources.getDimensionPixelSize(id) else dp(24)
    }

    private fun navigationBarInset(): Int {
        val id = resources.getIdentifier("navigation_bar_height", "dimen", "android")
        return if (id > 0) resources.getDimensionPixelSize(id) else dp(24)
    }

    private fun clampWindowPosition(target: View) {
        target.post {
            val p = params ?: return@post
            val display = DisplayMetrics()
            @Suppress("DEPRECATION")
            wm.defaultDisplay.getRealMetrics(display)
            val minY = statusBarInset() + dp(8)
            val maxX = (display.widthPixels - target.width - dp(8)).coerceAtLeast(dp(8))
            val maxY = (display.heightPixels - navigationBarInset() - target.height - dp(8))
                .coerceAtLeast(minY)
            p.x = p.x.coerceIn(dp(8), maxX)
            p.y = p.y.coerceIn(minY, maxY)
            try { wm.updateViewLayout(target, p) } catch (_: Exception) { }
        }
    }

    private fun requestCaptureFromOverlay() {
        val launch = Intent(this, com.m1stor.hhtmobile.MainActivity::class.java).apply {
            action = AppActions.ACTION_REQUEST_CAPTURE
            addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_CLEAR_TOP or
                    Intent.FLAG_ACTIVITY_SINGLE_TOP
            )
        }
        try {
            startActivity(launch)
        } catch (_: Exception) {
            status?.text = t("Open HHT to start screen capture", "Открой HHT для запуска захвата экрана")
        }
    }

    private fun updateCaptureControls() {
        val active = prefs.getBoolean("capture_active", false)
        scanButton?.text = if (active) t("Scan", "Скан") else t("Start", "Старт")
        val isPaused = prefs.getBoolean("capture_paused", false)
        paused = isPaused
        pauseBtn?.text = if (isPaused) t("Resume", "Продолжить") else t("Pause", "Пауза")
        pauseBtn?.isEnabled = active
        status?.text = when {
            !active -> t("Capture stopped · last reading kept", "Захват остановлен · последние данные сохранены")
            isPaused -> t("OCR paused", "OCR на паузе")
            else -> t("Capture active", "Захват активен")
        }
    }

    private fun btn(text: String, action: () -> Unit) = Button(this).apply {
        this.text = text
        isAllCaps = false
        textSize = 11f
        minHeight = dp(38)
        minimumHeight = dp(38)
        setTextColor(Color.WHITE)
        background = shape(Color.rgb(34, 48, 64), dp(10))
        setOnClickListener { action() }
    }

    private fun weight() = LinearLayout.LayoutParams(0, dp(40), 1f).apply {
        marginEnd = dp(5)
    }

    private fun label(
        parent: LinearLayout,
        text: String,
        size: Int,
        color: String,
        top: Int = 0,
        bold: Boolean = false
    ): TextView = TextView(this).apply {
        this.text = text
        textSize = size.toFloat()
        setTextColor(Color.parseColor(color))
        if (bold) typeface = Typeface.DEFAULT_BOLD
        parent.addView(this, LinearLayout.LayoutParams(-1, -2).apply {
            if (top > 0) topMargin = dp(top)
        })
    }

    private fun shape(color: Int, radius: Int) = GradientDrawable().apply {
        setColor(color)
        cornerRadius = radius.toFloat()
    }

    private fun quitAssistant() {
        TapAccessibilityService.stopPoints()
        prefs.edit()
            .putBoolean("assistant_enabled", false)
            .putBoolean("capture_active", false)
            .putBoolean("capture_paused", false)
            .apply()
        sendCapture(AppActions.ACTION_STOP_CAPTURE)
        stopService(Intent(this, ScreenCaptureService::class.java))
        stopSelf()
    }

    private fun sendCapture(action: String) {
        sendBroadcast(Intent(action).setPackage(packageName))
    }

    override fun onDestroy() {
        finishPointEditorIfOpen()
        view?.let { try { wm.removeView(it) } catch (_: Exception) { } }
        view = null
        if (registered) try { unregisterReceiver(receiver) } catch (_: Exception) { }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
