package com.m1stor.hhtmobile

object AppActions {
    const val ACTION_START_CAPTURE = "com.m1stor.hhtmobile.START_CAPTURE"
    const val ACTION_OCR_RESULT = "com.m1stor.hhtmobile.OCR_RESULT"
    const val ACTION_SCAN_NOW = "com.m1stor.hhtmobile.SCAN_NOW"
    const val ACTION_PAUSE_CAPTURE = "com.m1stor.hhtmobile.PAUSE_CAPTURE"
    const val ACTION_RESUME_CAPTURE = "com.m1stor.hhtmobile.RESUME_CAPTURE"
    const val ACTION_STOP_CAPTURE = "com.m1stor.hhtmobile.STOP_CAPTURE"
    const val ACTION_QUIT_OVERLAY = "com.m1stor.hhtmobile.QUIT_OVERLAY"
    const val ACTION_CAPTURE_STATE = "com.m1stor.hhtmobile.CAPTURE_STATE"
    const val ACTION_REQUEST_CAPTURE = "com.m1stor.hhtmobile.REQUEST_CAPTURE"
    const val ACTION_TAP_SEQUENCE_STATE = "com.m1stor.hhtmobile.TAP_SEQUENCE_STATE"
    const val EXTRA_RESULT_CODE = "projection_result_code"
    const val EXTRA_RESULT_DATA = "projection_result_data"
    const val EXTRA_OCR_TEXT = "ocr_text"
    const val EXTRA_TAP_RUNNING = "tap_running"
    const val EXTRA_TAP_STATUS = "tap_status"
}