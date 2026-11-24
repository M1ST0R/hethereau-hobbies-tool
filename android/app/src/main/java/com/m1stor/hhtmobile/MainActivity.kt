package com.m1stor.hhtmobile

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.m1stor.hhtmobile.capture.ScreenCaptureService
import com.m1stor.hhtmobile.overlay.OverlayService

class MainActivity : Activity() {
    private lateinit var statusView: TextView

    companion object {
        private const val REQUEST_OVERLAY_PERMISSION = 4101
        private const val REQUEST_SCREEN_CAPTURE = 4102
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(24), dp(32), dp(24), dp(24))
            setBackgroundColor(Color.rgb(16, 23, 34))
        }

        val title = TextView(this).apply {
            text = "HHT Mobile"
            textSize = 28f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
        }
        root.addView(title, matchWrap())

        val subtitle = TextView(this).apply {
            text = "Плавающий игровой помощник · prototype"
            textSize = 14f
            setTextColor(Color.rgb(166, 183, 199))
            setPadding(0, dp(8), 0, dp(28))
        }
        root.addView(subtitle, matchWrap())

        root.addView(actionButton("Разрешить и показать Hobi") {
            showOverlay()
        }, matchWrap())

        root.addView(actionButton("Запустить захват экрана и OCR") {
            requestScreenCapture()
        }, matchWrap().apply { topMargin = dp(12) })

        root.addView(actionButton("Остановить захват") {
            sendCaptureCommand(AppActions.ACTION_STOP_CAPTURE)
            setStatus("Отправлена команда остановки захвата")
        }, matchWrap().apply { topMargin = dp(12) })

        statusView = TextView(this).apply {
            text = "Сначала разреши плавающее окно, затем запусти захват."
            textSize = 13f
            setTextColor(Color.rgb(166, 183, 199))
            setPadding(0, dp(24), 0, 0)
        }
        root.addView(statusView, matchWrap())

        val note = TextView(this).apply {
            text = "Сейчас это read-only прототип: он показывает распознанные счётчики, но не нажимает кнопки в игре."
            textSize = 12f
            setTextColor(Color.rgb(133, 150, 168))
            setPadding(0, dp(28), 0, 0)
        }
        root.addView(note, matchWrap())

        setContentView(root)
    }

    private fun showOverlay() {
        if (!Settings.canDrawOverlays(this)) {
            val permissionIntent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")
            )
            startActivityForResult(permissionIntent, REQUEST_OVERLAY_PERMISSION)
            setStatus("Разреши HHT Mobile отображаться поверх других приложений.")
            return
        }

        startService(Intent(this, OverlayService::class.java))
        setStatus("Плавающее окно Hobi запущено.")
    }

    private fun requestScreenCapture() {
        val manager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        startActivityForResult(manager.createScreenCaptureIntent(), REQUEST_SCREEN_CAPTURE)
    }

    @Deprecated("Using the platform result callback keeps this prototype dependency-light.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        when (requestCode) {
            REQUEST_OVERLAY_PERMISSION -> {
                if (Settings.canDrawOverlays(this)) {
                    startService(Intent(this, OverlayService::class.java))
                    setStatus("Плавающее окно Hobi запущено.")
                } else {
                    setStatus("Разрешение на отображение поверх приложений не выдано.")
                }
            }

            REQUEST_SCREEN_CAPTURE -> {
                if (resultCode == RESULT_OK && data != null) {
                    val serviceIntent = Intent(this, ScreenCaptureService::class.java).apply {
                        action = AppActions.ACTION_START_CAPTURE
                        putExtra(AppActions.EXTRA_RESULT_CODE, resultCode)
                        putExtra(AppActions.EXTRA_RESULT_DATA, data)
                    }

                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        startForegroundService(serviceIntent)
                    } else {
                        startService(serviceIntent)
                    }
                    setStatus("Захват экрана запускается. Подтверди системный индикатор записи.")
                } else {
                    setStatus("Захват экрана отменён.")
                }
            }
        }
    }

    private fun sendCaptureCommand(action: String) {
        sendBroadcast(Intent(action).setPackage(packageName))
    }

    private fun setStatus(message: String) {
        if (::statusView.isInitialized) statusView.text = message
    }

    private fun actionButton(label: String, action: () -> Unit): Button =
        Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 14f
            setTextColor(Color.WHITE)
            setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(38, 57, 76)))
            setOnClickListener { action() }
        }

    private fun matchWrap() = LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT,
        LinearLayout.LayoutParams.WRAP_CONTENT
    )

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
