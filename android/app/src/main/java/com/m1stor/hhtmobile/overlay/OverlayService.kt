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
import android.util.DisplayMetrics
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import com.m1stor.hhtmobile.AppActions

class OverlayService:Service(){
    private lateinit var wm:WindowManager
    private var view:View?=null
    private var expanded=false
    private var registered=false
    private var paused=false
    private var params:WindowManager.LayoutParams?=null
    private var metrics:TextView?=null
    private var status:TextView?=null
    private var pauseBtn:Button?=null
    private var scanButton:Button?=null
    private val prefs by lazy{getSharedPreferences("hht_mobile",MODE_PRIVATE)}
    private val ru get()=prefs.getString("lang","en")=="ru"
    private fun t(en:String,rus:String)=if(ru)rus else en
    private fun dp(v:Int)=(v*resources.displayMetrics.density).toInt()

    private val receiver=object:BroadcastReceiver(){override fun onReceive(context:Context?,intent:Intent?){when(intent?.action){
        AppActions.ACTION_OCR_RESULT->{
            val value=intent.getStringExtra(AppActions.EXTRA_OCR_TEXT)?:t("No counters detected","Счётчики не найдены")
            prefs.edit().putString("last_ocr_readout",value).apply()
            metrics?.text=value
            status?.text=t("Frame scanned","Кадр обработан")
        }
        AppActions.ACTION_CAPTURE_STATE->{updateCaptureControls()}
        AppActions.ACTION_QUIT_OVERLAY->{quitAssistant()}
    }}}
    override fun onCreate(){super.onCreate();wm=getSystemService(WINDOW_SERVICE) as WindowManager;paused=prefs.getBoolean("capture_paused",false);val f=IntentFilter().apply{addAction(AppActions.ACTION_OCR_RESULT);addAction(AppActions.ACTION_CAPTURE_STATE);addAction(AppActions.ACTION_QUIT_OVERLAY)};if(Build.VERSION.SDK_INT>=33)registerReceiver(receiver,f,Context.RECEIVER_NOT_EXPORTED)else @Suppress("DEPRECATION") registerReceiver(receiver,f);registered=true}
    override fun onStartCommand(intent:Intent?,flags:Int,startId:Int):Int{if(!Settings.canDrawOverlays(this)){stopSelf();return START_NOT_STICKY};if(view==null)bubble();return START_STICKY}
    private fun bubble(){val v=TextView(this).apply{text="HHT";textSize=13f;typeface=Typeface.create("sans-serif-black",0);gravity=Gravity.CENTER;setTextColor(Color.WHITE);background=shape(Color.rgb(28,166,164),dp(30));elevation=dp(5).toFloat()};val p=WindowManager.LayoutParams(dp(54),dp(54),WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,PixelFormat.TRANSLUCENT).apply{gravity=Gravity.TOP or Gravity.START;x=dp(14);y=dp(180)};params=p;v.setOnTouchListener(drag());view=v;expanded=false;wm.addView(v,p);clampWindowPosition(v)}
    private fun panel(){
        val card=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(15),dp(13),dp(15),dp(13))
            background=shape(Color.rgb(15,22,32),dp(20))
            elevation=dp(7).toFloat()
        }
        val head=LinearLayout(this).apply{gravity=Gravity.CENTER_VERTICAL}
        head.addView(TextView(this).apply{
            text="HHT"
            textSize=15f
            typeface=Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
        },LinearLayout.LayoutParams(0,dp(32),1f))
        head.addView(btn("⌄"){collapse()})
        card.addView(head)

        label(card,t("OCR READOUT","ПОКАЗАНИЯ OCR"),10,"#6F879D",top=9,bold=true)
        val savedReadout=prefs.getString("last_ocr_readout",null)
        metrics=label(card,savedReadout?:t("Waiting for scan…","Ожидаю скан…"),15,"#F3F7FA",top=5,bold=true)

        val active=prefs.getBoolean("capture_active",false)
        status=label(
            card,
            if(active)t("Capture active","Захват активен") else t("Capture stopped · last reading kept","Захват остановлен · последние данные сохранены"),
            11,
            "#9EADBF",
            top=9
        )

        val row=LinearLayout(this).apply{gravity=Gravity.CENTER}
        scanButton=btn(if(active)t("Scan","Скан") else t("Start","Старт")){
            if(prefs.getBoolean("capture_active",false)){
                sendCapture(AppActions.ACTION_SCAN_NOW)
                status?.text=t("Scan requested","Запрошен скан")
            }else{
                requestCaptureFromOverlay()
            }
        }
        row.addView(scanButton,weight())

        paused=prefs.getBoolean("capture_paused",false)
        pauseBtn=btn(if(paused)t("Resume","Продолжить") else t("Pause","Пауза")){
            paused=!paused
            prefs.edit().putBoolean("capture_paused",paused).apply()
            sendCapture(if(paused)AppActions.ACTION_PAUSE_CAPTURE else AppActions.ACTION_RESUME_CAPTURE)
            pauseBtn?.text=if(paused)t("Resume","Продолжить")else t("Pause","Пауза")
            status?.text=if(paused)t("OCR paused","OCR на паузе")else t("OCR resumed","OCR продолжен")
        }
        pauseBtn?.isEnabled=active
        row.addView(pauseBtn,weight())

        row.addView(btn(t("Stop","Стоп")){
            paused=false
            prefs.edit().putBoolean("capture_active",false).putBoolean("capture_paused",false).apply()
            sendCapture(AppActions.ACTION_STOP_CAPTURE)
            scanButton?.text=t("Start","Старт")
            pauseBtn?.text=t("Pause","Пауза")
            pauseBtn?.isEnabled=false
            status?.text=t("Capture stopped · last reading kept","Захват остановлен · последние данные сохранены")
        },weight())
        card.addView(row)

        label(card,t("READ-ONLY · NO GAME INPUT","ТОЛЬКО OCR · БЕЗ НАЖАТИЙ"),10,"#6F879D",top=10)
        card.addView(
            btn(t("Quit HHT","Выйти из HHT")){quitAssistant()},
            LinearLayout.LayoutParams(-1,dp(40)).apply{topMargin=dp(8)}
        )

        val p=params?:WindowManager.LayoutParams(
            dp(54),dp(54),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        )
        p.width=dp(300)
        p.height=-2
        view?.let{wm.removeView(it)}
        view=card
        expanded=true
        wm.addView(card,p)
        params=p
        clampWindowPosition(card)
    }

    private fun collapse(){view?.let{wm.removeView(it)};metrics=null;status=null;pauseBtn=null;scanButton=null;bubble()}
    private fun drag(): View.OnTouchListener {
        var downX=0f
        var downY=0f
        var startX=0
        var startY=0
        var moved=false
        return View.OnTouchListener { _,event ->
            val currentParams=params
            if(currentParams==null){
                false
            }else{
                when(event.action){
                    MotionEvent.ACTION_DOWN->{
                        downX=event.rawX
                        downY=event.rawY
                        startX=currentParams.x
                        startY=currentParams.y
                        moved=false
                        true
                    }
                    MotionEvent.ACTION_MOVE->{
                        val dx=(event.rawX-downX).toInt()
                        val dy=(event.rawY-downY).toInt()
                        if(kotlin.math.abs(dx)+kotlin.math.abs(dy)>dp(5))moved=true
                        val display=DisplayMetrics()
                        @Suppress("DEPRECATION")
                        wm.defaultDisplay.getRealMetrics(display)
                        val target=view
                        val targetWidth=target?.width?.takeIf{it>0}?:dp(54)
                        val targetHeight=target?.height?.takeIf{it>0}?:dp(54)
                        val minY=statusBarInset()+dp(8)
                        val maxX=(display.widthPixels-targetWidth-dp(8)).coerceAtLeast(dp(8))
                        val maxY=(display.heightPixels-navigationBarInset()-targetHeight-dp(8)).coerceAtLeast(minY)
                        currentParams.x=(startX+dx).coerceIn(dp(8),maxX)
                        currentParams.y=(startY+dy).coerceIn(minY,maxY)
                        target?.let{wm.updateViewLayout(it,currentParams)}
                        true
                    }
                    MotionEvent.ACTION_UP->{
                        if(!moved)panel()
                        true
                    }
                    else->false
                }
            }
        }
    }

    private fun statusBarInset():Int{
        val id=resources.getIdentifier("status_bar_height","dimen","android")
        return if(id>0)resources.getDimensionPixelSize(id) else dp(24)
    }

    private fun navigationBarInset():Int{
        val id=resources.getIdentifier("navigation_bar_height","dimen","android")
        return if(id>0)resources.getDimensionPixelSize(id) else dp(24)
    }

    private fun clampWindowPosition(target:View){
        target.post{
            val p=params?:return@post
            val display=DisplayMetrics()
            @Suppress("DEPRECATION")
            wm.defaultDisplay.getRealMetrics(display)
            val minY=statusBarInset()+dp(8)
            val maxX=(display.widthPixels-target.width-dp(8)).coerceAtLeast(dp(8))
            val maxY=(display.heightPixels-navigationBarInset()-target.height-dp(8)).coerceAtLeast(minY)
            p.x=p.x.coerceIn(dp(8),maxX)
            p.y=p.y.coerceIn(minY,maxY)
            try{wm.updateViewLayout(target,p)}catch(_:Exception){}
        }
    }

    private fun requestCaptureFromOverlay(){
        val launch=Intent(this,com.m1stor.hhtmobile.MainActivity::class.java).apply{
            action=AppActions.ACTION_REQUEST_CAPTURE
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
        }
        try{
            startActivity(launch)
        }catch(_:Exception){
            status?.text=t("Open HHT to start screen capture","Открой HHT для запуска захвата экрана")
        }
    }

    private fun updateCaptureControls(){
        val active=prefs.getBoolean("capture_active",false)
        scanButton?.text=if(active)t("Scan","Скан")else t("Start","Старт")
        val isPaused=prefs.getBoolean("capture_paused",false)
        paused=isPaused
        pauseBtn?.text=if(isPaused)t("Resume","Продолжить")else t("Pause","Пауза")
        pauseBtn?.isEnabled=active
        status?.text=when {
            !active -> t("Capture stopped · last reading kept","Захват остановлен · последние данные сохранены")
            isPaused -> t("OCR paused","OCR на паузе")
            else -> t("Capture active","Захват активен")
        }
    }

    private fun btn(text:String,action:()->Unit)=Button(this).apply{this.text=text;isAllCaps=false;textSize=11f;minHeight=dp(38);minimumHeight=dp(38);setTextColor(Color.WHITE);background=shape(Color.rgb(34,48,64),dp(10));setOnClickListener{action()}}
    private fun weight()=LinearLayout.LayoutParams(0,dp(40),1f).apply{marginEnd=dp(5)}
    private fun label(parent:LinearLayout,text:String,size:Int,color:String,top:Int=0,bold:Boolean=false):TextView=TextView(this).apply{this.text=text;textSize=size.toFloat();setTextColor(Color.parseColor(color));if(bold)typeface=Typeface.DEFAULT_BOLD;parent.addView(this,LinearLayout.LayoutParams(-1,-2).apply{if(top>0)topMargin=dp(top)})}
    private fun shape(color:Int,r:Int)=GradientDrawable().apply{setColor(color);cornerRadius=r.toFloat()}
    private fun quitAssistant(){
        prefs.edit().putBoolean("assistant_enabled",false).putBoolean("capture_active",false).putBoolean("capture_paused",false).apply()
        sendCapture(AppActions.ACTION_STOP_CAPTURE)
        stopService(Intent(this,com.m1stor.hhtmobile.capture.ScreenCaptureService::class.java))
        stopSelf()
    }
    private fun sendCapture(action:String){sendBroadcast(Intent(action).setPackage(packageName))}
    override fun onDestroy(){view?.let{try{wm.removeView(it)}catch(_:Exception){}};view=null;if(registered)try{unregisterReceiver(receiver)}catch(_:Exception){};super.onDestroy()}
    override fun onBind(intent:Intent?):IBinder?=null
}