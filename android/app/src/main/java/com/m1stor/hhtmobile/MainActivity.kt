package com.m1stor.hhtmobile

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import android.Manifest
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import com.m1stor.hhtmobile.capture.ScreenCaptureService
import com.m1stor.hhtmobile.overlay.OverlayService

class MainActivity : Activity() {
    private var lang = "en"
    private val prefs by lazy { getSharedPreferences("hht_mobile", MODE_PRIVATE) }
    private lateinit var root: LinearLayout
    private companion object { const val REQUEST_CAPTURE = 4102; const val REQUEST_NOTIFICATIONS = 4103 }

    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); lang=prefs.getString("lang","en") ?: "en"; renderSetup() }
    private fun s(en:String,ru:String)=if(lang=="ru")ru else en
    private fun dp(v:Int)=(v*resources.displayMetrics.density).toInt()

    private fun renderSetup() {
        root=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(20),dp(18),dp(20),dp(24)); setBackgroundColor(Color.rgb(12,17,26)) }
        header(root,s("SETUP","НАСТРОЙКА"))
        text(root,s("Prepare Android permissions once. You can revisit this screen anytime.","Настрой разрешения Android. Этот экран можно открыть повторно."),13,"#B8C5D3",8)
        permissionCard(root,s("Display over other apps","Поверх других приложений"),s("Required for the floating Hobi panel.","Нужно для плавающего окна Hobi."),Settings.canDrawOverlays(this),s("Open settings","Открыть настройки")) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:$packageName")))
        }
        val pm=getSystemService(POWER_SERVICE) as PowerManager
        val batteryOk=if(Build.VERSION.SDK_INT>=23)pm.isIgnoringBatteryOptimizations(packageName) else true
        permissionCard(root,s("Battery restrictions","Оптимизация батареи"),s("Allow unrestricted background operation for more reliable capture.","Разреши работу без ограничений батареи для стабильного захвата."),batteryOk,s("Open settings","Открыть настройки")) {
            if(Build.VERSION.SDK_INT>=23) try { startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,Uri.parse("package:$packageName"))) } catch(_:Exception){startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))}
        }
        permissionCard(root,s("Notifications","Уведомления"),s("Show the ongoing capture status. Recommended on Android 13+.","Показывать состояние захвата. Рекомендуется на Android 13+."),Build.VERSION.SDK_INT < 33 || checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED,s("Allow notifications","Разрешить уведомления")) {
            if(Build.VERSION.SDK_INT >= 33) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQUEST_NOTIFICATIONS)
        }
        permissionCard(root,s("Screen capture","Захват экрана"),s("Android asks for consent each time a session starts.","Android запрашивает разрешение при каждом запуске захвата."),false,s("Requested on start","Запрашивается при запуске")) { requestCapture() }
        permissionCard(root,s("Accessibility service","Специальные возможности"),s("Not needed for read-only OCR. No game taps are automated.","Для OCR не требуется. Автоматические нажатия пока не реализованы."),true,s("Not required","Не требуется")) {}
        text(root,s("Play Protect may scan sideloaded APKs. Install only builds from this repository and review warnings. Do not disable device protection globally.","Play Protect может проверять APK из сторонних источников. Устанавливай только сборки из репозитория и проверяй предупреждения. Не отключай защиту устройства целиком."),11,"#8E9BAA",18)
        root.addView(button(s("Continue to HHT","Перейти в HHT"),true){renderHome()},LinearLayout.LayoutParams(-1,dp(52)).apply{topMargin=dp(18)})
        setContentView(ScrollView(this).apply{addView(root)})
    }

    private fun renderHome() {
        root=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(20),dp(18),dp(20),dp(24));setBackgroundColor(Color.rgb(12,17,26))}
        header(root,s("ASSISTANT","ПОМОЩНИК"))
        text(root,s("Floating controls and OCR status","Плавающее управление и статус OCR"),13,"#9EADBF",6)
        text(root,s("MODULES","МОДУЛИ"),11,"#58D6CF",24,true)
        moduleCard(root,s("Owner's Selection","Подборка владельца"),s("Counter OCR · Read-only","OCR счётчиков · только чтение"),s("Available · calibration needed","Доступен · нужна калибровка"))
        text(root,s("CONTROL","УПРАВЛЕНИЕ"),11,"#58D6CF",22,true)
        root.addView(button(s("START HOBI + SCREEN SCAN","ЗАПУСТИТЬ HOBI И СКАН"),true){startAssistant()},LinearLayout.LayoutParams(-1,dp(54)).apply{topMargin=dp(10)})
        root.addView(button(s("Stop screen scan","Остановить сканирование"),false){sendCaptureCommand(AppActions.ACTION_STOP_CAPTURE)},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        root.addView(button(s("Close floating panel","Завершить плавающее окно"),false){sendBroadcast(Intent(AppActions.ACTION_QUIT_OVERLAY).setPackage(packageName))},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        text(root,s("SETTINGS","НАСТРОЙКИ"),11,"#58D6CF",22,true)
        root.addView(button(s("Permissions & setup","Разрешения и настройка"),false){renderSetup()},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        text(root,s("Read-only OCR only. Automated game interaction is not implemented.","Только OCR. Автоматическое управление игрой пока не реализовано."),11,"#8E9BAA",14)
        setContentView(ScrollView(this).apply{addView(root)})
    }

    private fun startAssistant() {
        if(!Settings.canDrawOverlays(this)){Toast.makeText(this,s("Enable overlay permission first","Сначала разреши отображение поверх приложений"),Toast.LENGTH_LONG).show();renderSetup();return}
        startService(Intent(this,OverlayService::class.java));requestCapture()
    }
    private fun requestCapture(){val mgr=getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager;startActivityForResult(mgr.createScreenCaptureIntent(),REQUEST_CAPTURE)}
    @Deprecated("MediaProjection result")
    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?){super.onActivityResult(requestCode,resultCode,data);if(requestCode==REQUEST_CAPTURE){if(resultCode==RESULT_OK&&data!=null){val intent=Intent(this,ScreenCaptureService::class.java).apply{action=AppActions.ACTION_START_CAPTURE;putExtra(AppActions.EXTRA_RESULT_CODE,resultCode);putExtra(AppActions.EXTRA_RESULT_DATA,data)};if(Build.VERSION.SDK_INT>=26)startForegroundService(intent)else startService(intent);Toast.makeText(this,s("Screen scan started","Сканирование запущено"),Toast.LENGTH_SHORT).show();renderHome()}else Toast.makeText(this,s("Screen capture permission cancelled","Разрешение на захват отменено"),Toast.LENGTH_SHORT).show()}}
    private fun permissionCard(parent:LinearLayout,title:String,desc:String,ok:Boolean,actionText:String,action:()->Unit){
        val card=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(14),dp(13),dp(14),dp(13));background=surface()}
        val row=LinearLayout(this).apply{gravity=Gravity.CENTER_VERTICAL}
        row.addView(TextView(this@MainActivity).apply{text=title;textSize=15f;setTextColor(Color.WHITE)},LinearLayout.LayoutParams(0,-2,1f))
        row.addView(TextView(this@MainActivity).apply{text=if(ok)"✓" else "○";textSize=18f;setTextColor(if(ok)Color.rgb(82,214,177)else Color.rgb(255,176,90))})
        card.addView(row);text(card,desc,12,"#9EADBF",5)
        card.addView(button(actionText,false,action),LinearLayout.LayoutParams(-1,dp(40)).apply{topMargin=dp(9)})
        parent.addView(card,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(10)})
    }
    private fun moduleCard(parent:LinearLayout,title:String,desc:String,status:String){val card=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(16),dp(14),dp(16),dp(14));background=surface()};text(card,title,16,"#FFFFFF",0,true);text(card,desc,12,"#9EADBF",6);text(card,status,11,"#58D6CF",10,true);parent.addView(card,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(10)})}
    private fun header(parent:LinearLayout,label:String){val row=LinearLayout(this).apply{gravity=Gravity.CENTER_VERTICAL};row.addView(TextView(this@MainActivity).apply{text="HHT MOBILE";textSize=23f;setTextColor(Color.WHITE);typeface=android.graphics.Typeface.create("sans-serif-black",0)},LinearLayout.LayoutParams(0,-2,1f));row.addView(button(if(lang=="en")"RU" else "EN",false){lang=if(lang=="en")"ru" else "en";prefs.edit().putString("lang",lang).apply();renderSetup()});parent.addView(row);text(parent,label,11,"#58D6CF",12,true)}
    private fun text(parent:LinearLayout,value:String,size:Int,color:String,top:Int=0,bold:Boolean=false){parent.addView(TextView(this).apply{text=value;textSize=size.toFloat();setTextColor(Color.parseColor(color));if(bold)typeface=android.graphics.Typeface.DEFAULT_BOLD},LinearLayout.LayoutParams(-1,-2).apply{if(top>0)topMargin=dp(top)})}
    private fun surface()=android.graphics.drawable.GradientDrawable().apply{setColor(Color.rgb(21,29,41));cornerRadius=dp(16).toFloat();setStroke(dp(1),Color.rgb(39,51,67))}
    private fun button(label:String,primary:Boolean,action:()->Unit)=Button(this).apply{text=label;isAllCaps=false;textSize=13f;setTextColor(Color.WHITE);background=android.graphics.drawable.GradientDrawable().apply{setColor(if(primary)Color.rgb(26,154,151)else Color.rgb(35,47,63));cornerRadius=dp(12).toFloat()};setOnClickListener{action()}}
    private fun sendCaptureCommand(action:String){sendBroadcast(Intent(action).setPackage(packageName))}
}
