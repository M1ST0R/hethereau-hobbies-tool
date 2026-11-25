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
    private val prefs by lazy{getSharedPreferences("hht_mobile",MODE_PRIVATE)}
    private val ru get()=prefs.getString("lang","en")=="ru"
    private fun t(en:String,rus:String)=if(ru)rus else en
    private fun dp(v:Int)=(v*resources.displayMetrics.density).toInt()

    private val receiver=object:BroadcastReceiver(){override fun onReceive(context:Context?,intent:Intent?){when(intent?.action){
        AppActions.ACTION_OCR_RESULT->{metrics?.text=intent.getStringExtra(AppActions.EXTRA_OCR_TEXT)?:t("No counters detected","Счётчики не найдены");status?.text=t("Frame scanned","Кадр обработан")}
        AppActions.ACTION_QUIT_OVERLAY->{sendCapture(AppActions.ACTION_STOP_CAPTURE);stopSelf()}
    }}}
    override fun onCreate(){super.onCreate();wm=getSystemService(WINDOW_SERVICE) as WindowManager;val f=IntentFilter().apply{addAction(AppActions.ACTION_OCR_RESULT);addAction(AppActions.ACTION_QUIT_OVERLAY)};if(Build.VERSION.SDK_INT>=33)registerReceiver(receiver,f,Context.RECEIVER_NOT_EXPORTED)else @Suppress("DEPRECATION") registerReceiver(receiver,f);registered=true}
    override fun onStartCommand(intent:Intent?,flags:Int,startId:Int):Int{if(!Settings.canDrawOverlays(this)){stopSelf();return START_NOT_STICKY};if(view==null)bubble();return START_STICKY}
    private fun bubble(){val v=TextView(this).apply{text="H";textSize=21f;typeface=Typeface.create("sans-serif-black",0);gravity=Gravity.CENTER;setTextColor(Color.WHITE);background=shape(Color.rgb(28,166,164),dp(30));elevation=dp(5).toFloat()};val p=WindowManager.LayoutParams(dp(54),dp(54),WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,PixelFormat.TRANSLUCENT).apply{gravity=Gravity.TOP or Gravity.START;x=dp(14);y=dp(180)};params=p;v.setOnTouchListener(drag());view=v;expanded=false;wm.addView(v,p)}
    private fun panel(){val card=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(15),dp(13),dp(15),dp(13));background=shape(Color.rgb(15,22,32),dp(20));elevation=dp(7).toFloat()};val head=LinearLayout(this).apply{gravity=Gravity.CENTER_VERTICAL};head.addView(TextView(this).apply{text="HHT  /  HOBI";textSize=15f;typeface=Typeface.DEFAULT_BOLD;setTextColor(Color.WHITE)},LinearLayout.LayoutParams(0,dp(32),1f));head.addView(btn("—"){collapse()});card.addView(head);label(card,t("OCR READOUT","ПОКАЗАНИЯ OCR"),10,"#6F879D",top=9,bold=true);metrics=label(card,t("Waiting for scan…","Ожидаю скан…"),15,"#F3F7FA",top=5,bold=true);status=label(card,t("Capture not started","Захват не запущен"),11,"#9EADBF",top=9);val row=LinearLayout(this).apply{gravity=Gravity.CENTER};row.addView(btn(t("Scan","Скан")){sendCapture(AppActions.ACTION_SCAN_NOW);status?.text=t("Scan requested","Запрошен скан")},weight());pauseBtn=btn(t("Pause","Пауза")){paused=!paused;sendCapture(if(paused)AppActions.ACTION_PAUSE_CAPTURE else AppActions.ACTION_RESUME_CAPTURE);pauseBtn?.text=if(paused)t("Resume","Продолжить")else t("Pause","Пауза");status?.text=if(paused)t("OCR paused","OCR на паузе")else t("OCR resumed","OCR продолжен")};row.addView(pauseBtn,weight());row.addView(btn(t("Stop","Стоп")){sendCapture(AppActions.ACTION_STOP_CAPTURE);status?.text=t("Capture stopped","Захват остановлен")},weight());card.addView(row);label(card,t("READ-ONLY · NO GAME INPUT","ТОЛЬКО OCR · БЕЗ НАЖАТИЙ"),10,"#6F879D",top=10);card.addView(btn(t("Quit floating assistant","Завершить помощник")){sendCapture(AppActions.ACTION_STOP_CAPTURE);stopSelf()},LinearLayout.LayoutParams(-1,dp(40)).apply{topMargin=dp(8)});val p=params?:WindowManager.LayoutParams(dp(54),dp(54),WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,PixelFormat.TRANSLUCENT);p.width=dp(300);p.height=-2;view?.let{wm.removeView(it)};view=card;expanded=true;wm.addView(card,p);params=p}
    private fun collapse(){view?.let{wm.removeView(it)};metrics=null;status=null;pauseBtn=null;bubble()}
    private fun drag():View.OnTouchListener{var dx=0f;var dy=0f;var sx=0;var sy=0;var moved=false;return View.OnTouchListener{_,e->val p=params?:return@OnTouchListener false;when(e.action){MotionEvent.ACTION_DOWN->{dx=e.rawX;dy=e.rawY;sx=p.x;sy=p.y;moved=false;true};MotionEvent.ACTION_MOVE->{val x=(e.rawX-dx).toInt();val y=(e.rawY-dy).toInt();if(kotlin.math.abs(x)+kotlin.math.abs(y)>dp(5))moved=true;p.x=(sx+x).coerceAtLeast(0);p.y=(sy+y).coerceAtLeast(0);view?.let{wm.updateViewLayout(it,p)};true};MotionEvent.ACTION_UP->{if(!moved)panel();true};else false}}}
    private fun btn(text:String,action:()->Unit)=Button(this).apply{text=text;isAllCaps=false;textSize=11f;minHeight=dp(38);minimumHeight=dp(38);setTextColor(Color.WHITE);background=shape(Color.rgb(34,48,64),dp(10));setOnClickListener{action()}}
    private fun weight()=LinearLayout.LayoutParams(0,dp(40),1f).apply{marginEnd=dp(5)}
    private fun label(parent:LinearLayout,text:String,size:Int,color:String,top:Int=0,bold:Boolean=false):TextView=TextView(this).apply{this.text=text;textSize=size.toFloat();setTextColor(Color.parseColor(color));if(bold)typeface=Typeface.DEFAULT_BOLD;parent.addView(this,LinearLayout.LayoutParams(-1,-2).apply{if(top>0)topMargin=dp(top)})}
    private fun shape(color:Int,r:Int)=GradientDrawable().apply{setColor(color);cornerRadius=r.toFloat()}
    private fun sendCapture(action:String){sendBroadcast(Intent(action).setPackage(packageName))}
    override fun onDestroy(){view?.let{try{wm.removeView(it)}catch(_:Exception){}};view=null;if(registered)try{unregisterReceiver(receiver)}catch(_:Exception){};super.onDestroy()}
    override fun onBind(intent:Intent?):IBinder?=null
}