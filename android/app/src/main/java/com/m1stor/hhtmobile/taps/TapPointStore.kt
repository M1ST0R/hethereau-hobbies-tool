package com.m1stor.hhtmobile.taps

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

data class TapPoint(
    val xRatio: Float,
    val yRatio: Float,
    val aspectRatio: Float
)

object TapPointStore {
    private const val PREFS_NAME = "hht_mobile"
    private const val KEY_POINTS = "tap_points_json"
    const val MAX_POINTS = 20

    fun load(context: Context): List<TapPoint> {
        val raw = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getString(KEY_POINTS, null)
            ?: return emptyList()

        return try {
            val json = JSONArray(raw)
            buildList {
                for (index in 0 until json.length()) {
                    val item = json.optJSONObject(index) ?: continue
                    val x = item.optDouble("x", Double.NaN).toFloat()
                    val y = item.optDouble("y", Double.NaN).toFloat()
                    val aspect = item.optDouble("aspect", Double.NaN).toFloat()
                    if (x.isFinite() && y.isFinite() && aspect.isFinite() &&
                        x in 0f..1f && y in 0f..1f && aspect > 0f
                    ) {
                        add(TapPoint(x, y, aspect))
                    }
                }
            }.take(MAX_POINTS)
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun save(context: Context, points: List<TapPoint>) {
        val json = JSONArray()
        points.take(MAX_POINTS).forEach { point ->
            json.put(
                JSONObject()
                    .put("x", point.xRatio.toDouble())
                    .put("y", point.yRatio.toDouble())
                    .put("aspect", point.aspectRatio.toDouble())
            )
        }
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_POINTS, json.toString())
            .apply()
    }
}
