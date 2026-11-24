package com.m1stor.hhtmobile.capture

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.SystemClock
import android.util.DisplayMetrics
import android.view.WindowManager
import android.content.pm.ServiceInfo
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.TextRecognizer
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.m1stor.hhtmobile.AppActions
import java.util.concurrent.atomic.AtomicBoolean

class ScreenCaptureService : Service() {
    companion object {
        private const val CHANNEL_ID = "hht_screen_capture"
        private const val NOTIFICATION_ID = 7401
        private const val MIN_FRAME_INTERVAL_MS = 320L
    }

    private var projection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var projectionCallback: MediaProjection.Callback? = null
    private var receiverRegistered = false

    private lateinit var imageThread: HandlerThread
    private lateinit var imageHandler: Handler
    private val ocrInFlight = AtomicBoolean(false)
    private val recognizer: TextRecognizer by lazy {
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    }

    @Volatile private var paused = false
    @Volatile private var forceNextFrame = true
    @Volatile private var lastOcrAt = 0L

    private val controlReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                AppActions.ACTION_SCAN_NOW -> forceNextFrame = true
                AppActions.ACTION_PAUSE_CAPTURE -> paused = true
                AppActions.ACTION_RESUME_CAPTURE -> {
                    paused = false
                    forceNextFrame = true
                }
                AppActions.ACTION_STOP_CAPTURE -> stopCapture()
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        imageThread = HandlerThread("HHT-Mobile-Capture").apply { start() }
        imageHandler = Handler(imageThread.looper)

        val filter = IntentFilter().apply {
            addAction(AppActions.ACTION_SCAN_NOW)
            addAction(AppActions.ACTION_PAUSE_CAPTURE)
            addAction(AppActions.ACTION_RESUME_CAPTURE)
            addAction(AppActions.ACTION_STOP_CAPTURE)
        }
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(controlReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(controlReceiver, filter)
        }
        receiverRegistered = true
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action != AppActions.ACTION_START_CAPTURE || projection != null) {
            return START_NOT_STICKY
        }

        val resultCode = intent.getIntExtra(AppActions.EXTRA_RESULT_CODE, Activity.RESULT_CANCELED)
        val resultData = if (Build.VERSION.SDK_INT >= 33) {
            intent.getParcelableExtra(AppActions.EXTRA_RESULT_DATA, Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra(AppActions.EXTRA_RESULT_DATA)
        }

        if (resultCode != Activity.RESULT_OK || resultData == null) {
            stopSelf()
            return START_NOT_STICKY
        }

        try {
            startAsForegroundService()
            val manager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            val activeProjection = manager.getMediaProjection(resultCode, resultData)
            projection = activeProjection

            val callback = object : MediaProjection.Callback() {
                override fun onStop() {
                    projection = null
                    releaseDisplayResources()
                    stopForeground(STOP_FOREGROUND_REMOVE)
                    stopSelf()
                }
            }
            projectionCallback = callback
            activeProjection.registerCallback(callback, imageHandler)
            createVirtualDisplay(activeProjection)
        } catch (error: Exception) {
            publishOcr("Не удалось запустить захват: ${error.javaClass.simpleName}")
            stopCapture()
        }

        return START_NOT_STICKY
    }

    private fun createVirtualDisplay(activeProjection: MediaProjection) {
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        (getSystemService(WINDOW_SERVICE) as WindowManager).defaultDisplay.getRealMetrics(metrics)

        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi

        val reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
        imageReader = reader
        reader.setOnImageAvailableListener({ source -> processLatestFrame(source) }, imageHandler)

        // Android 14+ permits one VirtualDisplay creation per projection token.
        // A fresh system consent is requested by MainActivity for every new run.
        virtualDisplay = activeProjection.createVirtualDisplay(
            "HHT Mobile screen capture",
            width,
            height,
            density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader.surface,
            null,
            imageHandler
        )
        publishOcr("Захват активен · ожидаю кадры…")
    }

    private fun processLatestFrame(source: ImageReader) {
        val image = try {
            source.acquireLatestImage()
        } catch (_: Exception) {
            null
        } ?: return

        val now = SystemClock.elapsedRealtime()
        if (paused || (!forceNextFrame && now - lastOcrAt < MIN_FRAME_INTERVAL_MS)) {
            image.close()
            return
        }
        if (!ocrInFlight.compareAndSet(false, true)) {
            // Never queue stale frames: the next callback will acquireLatestImage().
            image.close()
            return
        }

        forceNextFrame = false
        lastOcrAt = now
        val bitmap = try {
            imageToBitmap(image)
        } catch (error: Exception) {
            publishOcr("Ошибка кадра: ${error.javaClass.simpleName}")
            null
        } finally {
            image.close()
        }

        if (bitmap == null) {
            ocrInFlight.set(false)
            return
        }

        recognizer.process(InputImage.fromBitmap(bitmap, 0))
            .addOnSuccessListener { result ->
                val readout = CounterOcr.formatReadout(result.text)
                publishOcr(readout)
            }
            .addOnFailureListener { error ->
                publishOcr("Ошибка OCR: ${error.javaClass.simpleName}")
            }
            .addOnCompleteListener {
                bitmap.recycle()
                ocrInFlight.set(false)
            }
    }

    private fun imageToBitmap(image: Image): Bitmap {
        val plane = image.planes.first()
        val buffer = plane.buffer
        val pixelStride = plane.pixelStride
        val rowStride = plane.rowStride
        val rowPadding = rowStride - pixelStride * image.width
        val paddedWidth = image.width + rowPadding / pixelStride

        val padded = Bitmap.createBitmap(
            paddedWidth,
            image.height,
            Bitmap.Config.ARGB_8888
        )
        buffer.rewind()
        padded.copyPixelsFromBuffer(buffer)

        val output = Bitmap.createBitmap(padded, 0, 0, image.width, image.height)
        if (output !== padded) padded.recycle()
        return output
    }

    private fun publishOcr(value: String) {
        sendBroadcast(
            Intent(AppActions.ACTION_OCR_RESULT)
                .setPackage(packageName)
                .putExtra(AppActions.EXTRA_OCR_TEXT, value)
        )
    }

    private fun startAsForegroundService() {
        val notification = Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setContentTitle("HHT Mobile")
            .setContentText("Захват экрана и распознавание счётчиков активно")
            .setOngoing(true)
            .build()

        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "HHT screen capture",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Уведомление о захвате экрана для OCR"
        }
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
            .createNotificationChannel(channel)
    }

    private fun releaseDisplayResources() {
        try { virtualDisplay?.release() } catch (_: Exception) { }
        virtualDisplay = null
        try { imageReader?.setOnImageAvailableListener(null, null) } catch (_: Exception) { }
        try { imageReader?.close() } catch (_: Exception) { }
        imageReader = null
    }

    private fun stopCapture() {
        val currentProjection = projection
        projection = null
        if (currentProjection != null) {
            try {
                projectionCallback?.let { currentProjection.unregisterCallback(it) }
                currentProjection.stop()
            } catch (_: Exception) { }
        }
        projectionCallback = null
        releaseDisplayResources()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        stopCapture()
        if (receiverRegistered) {
            try { unregisterReceiver(controlReceiver) } catch (_: Exception) { }
        }
        if (::imageThread.isInitialized) imageThread.quitSafely()
        try { recognizer.close() } catch (_: Exception) { }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
