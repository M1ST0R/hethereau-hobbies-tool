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

    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); lang=prefs.getString("lang","en") ?: "en"; if(prefs.getBoolean("setup_seen",false)) renderHome() else renderSetup() }
    override fun onResume() { super.onResume(); if(::root.isInitialized && !isFinishing) { if(prefs.getBoolean("setup_seen",false)) renderHome() else renderSetup() } }
    private fun s(en:String,ru:String)=if(lang=="ru")ru else en
    private fun dp(v:Int)=(v*resources.displayMetrics.density).toInt()

    private fun renderSetup() {
        root=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(20),dp(18),dp(20),dp(24)); setBackgroundColor(Color.rgb(12,17,26)) }
        header(root,s("SETUP","НАСТРОЙКА"))
        text(root,s("Set up the permissions HHT needs. You can revisit this page from the dashboard.","Настрой необходимые разрешения. Этот экран можно повторно открыть из меню."),13,"#B8C5D3",8)
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
        permissionCard(root,s("Accessibility access (optional)","Специальные возможности (необязательно)"),s("Not used by this read-only prototype. No game taps or automation are performed.","Для OCR не требуется. Автоматические нажатия пока не реализованы."),true,s("Not required","Не требуется")) {}
        text(root,s("Android may verify sideloaded APKs. Review the system warning and install only a build you trust; keep Play Protect enabled.","Android может проверять APK из сторонних источников. Проверяй предупреждения и устанавливай только доверенную сборку; Play Protect отключать не нужно."),11,"#8E9BAA",18)
        root.addView(button(s("Open dashboard","Открыть меню"),true){
            if(!Settings.canDrawOverlays(this)){Toast.makeText(this,s("Overlay permission is required.","Нужно разрешить отображение поверх приложений."),Toast.LENGTH_LONG).show();return@button}
            prefs.edit().putBoolean("setup_seen",true).apply();renderHome()
        },LinearLayout.LayoutParams(-1,dp(52)).apply{topMargin=dp(18)})
        setContentView(ScrollView(this).apply{addView(root)})
    }

    private fun renderHome() {
        root=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(20),dp(18),dp(20),dp(24));setBackgroundColor(Color.rgb(12,17,26))}
        header(root,s("ASSISTANT","ПОМОЩНИК"))
        text(root,s("Floating controls and OCR status","Плавающее управление и статус OCR"),13,"#9EADBF",6)
        text(root,s("MODULES","МОДУЛИ"),11,"#58D6CF",24,true)
        val ownerModuleEnabled=prefs.getBoolean("owner_module_enabled",true)
        moduleCard(root,s("Owner Selection","Подборка владельца"),s("Counter OCR · Read-only","OCR счётчиков · только чтение"),s(if(ownerModuleEnabled)"Module enabled · calibration needed" else "Module disabled",if(ownerModuleEnabled)"Модуль включён · нужна калибровка" else "Модуль выключен"))
        root.addView(button(s(if(ownerModuleEnabled)"Disable Owner Selection" else "Enable Owner Selection",if(ownerModuleEnabled)"Выключить модуль" else "Включить модуль"),false){prefs.edit().putBoolean("owner_module_enabled",!ownerModuleEnabled).apply();renderHome()},LinearLayout.LayoutParams(-1,dp(42)).apply{topMargin=dp(8)})
        text(root,s("CONTROL","УПРАВЛЕНИЕ"),11,"#58D6CF",22,true)
        val assistantEnabled=prefs.getBoolean("assistant_enabled",false)
        root.addView(button(s(if(assistantEnabled)"DISABLE HOBI ASSISTANT" else "ENABLE HOBI ASSISTANT",if(assistantEnabled)"ВЫКЛЮЧИТЬ HOBI" else "ВКЛЮЧИТЬ HOBI"),true){
            if(assistantEnabled) stopAssistant() else startAssistant()
        },LinearLayout.LayoutParams(-1,dp(54)).apply{topMargin=dp(10)})
        root.addView(button(s("Scan once","Сканировать один раз"),false){sendCaptureCommand(AppActions.ACTION_SCAN_NOW)},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        root.addView(button(s("Stop capture","Остановить захват"),false){sendCaptureCommand(AppActions.ACTION_STOP_CAPTURE);prefs.edit().putBoolean("assistant_enabled",false).apply();renderHome()},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        root.addView(button(s("Exit HHT","Выйти из HHT"),false){exitApp()},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        text(root,s("SETTINGS","НАСТРОЙКИ"),11,"#58D6CF",22,true)
        root.addView(button(s("Permissions & setup","Разрешения и настройка"),false){prefs.edit().putBoolean("setup_seen",false).apply();renderSetup()},LinearLayout.LayoutParams(-1,dp(48)).apply{topMargin=dp(10)})
        text(root,s("Read-only OCR only. Automated game interaction is not implemented.","Только OCR. Автоматическое управление игрой пока не реализовано."),11,"#8E9BAA",14)
        setContentView(ScrollView(this).apply{addView(root)})
    }

    private fun startAssistant() {
        if(!prefs.getBoolean("owner_module_enabled",true)){Toast.makeText(this,s("Enable the module first.","Сначала включи модуль."),Toast.LENGTH_SHORT).show();return}
        if(!Settings.canDrawOverlays(this)){Toast.makeText(this,s("Enable overlay permission first","Сначала разреши отображение поверх приложений"),Toast.LENGTH_LONG).show();renderSetup();return}
        startService(Intent(this,OverlayService::class.java));requestCapture()
    }
    private fun stopAssistant(){
        sendCaptureCommand(AppActions.ACTION_STOP_CAPTURE)
        sendBroadcast(Intent(AppActions.ACTION_QUIT_OVERLAY).setPackage(packageName))
        stopService(Intent(this,ScreenCaptureService::class.java))
        stopService(Intent(this,OverlayService::class.java))
        prefs.edit().putBoolean("assistant_enabled",false).apply()
        renderHome()
    }
    private fun exitApp(){
        stopAssistant()
        finishAndRemoveTask()
    }
    private fun requestCapture(){val mgr=getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager;startActivityForResult(mgr.createScreenCaptureIntent(),REQUEST_CAPTURE)}
    @Deprecated("MediaProjection result")
    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?){
        super.onActivityResult(requestCode,resultCode,data)
        if(requestCode!=REQUEST_CAPTURE) return
        if(resultCode==RESULT_OK && data!=null){
            prefs.edit().putBoolean("assistant_enabled",true).apply()
            val intent=Intent(this,ScreenCaptureService::class.java).apply{
                action=AppActions.ACTION_START_CAPTURE
                putExtra(AppActions.EXTRA_RESULT_CODE,resultCode)
                putExtra(AppActions.EXTRA_RESULT_DATA,data)
            }
            if(Build.VERSION.SDK_INT>=26) startForegroundService(intent) else startService(intent)
            Toast.makeText(this,s("Screen scan started","Сканирование запущено"),Toast.LENGTH_SHORT).show()
        }else{
            prefs.edit().putBoolean("assistant_enabled",false).apply()
            stopService(Intent(this,OverlayService::class.java))
            Toast.makeText(this,s("Screen capture permission was not granted","Разрешение на захват экрана не предоставлено"),Toast.LENGTH_SHORT).show()
        }
        renderHome()
    }
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
