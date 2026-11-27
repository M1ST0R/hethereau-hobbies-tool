package com.m1stor.hhtmobile.capture

/**
 * Extracts the income counter from a cropped game HUD region.
 *
 * The caller is responsible for cropping the screen to the income row first.
 * This prevents unrelated ratios elsewhere in the game from being considered.
 */
object CounterOcr {
    private val incomePattern = Regex(
        """(?<!\d)(\d[\d\s,.'’]{0,12}|\d)\s*/\s*(\d[\d\s,.'’]{0,12}|\d)(?!\d)"""
    )

    fun formatIncome(text: String, english: Boolean = false): String {
        val match = incomePattern.find(text)
        if (match == null) {
            val recognized = text.replace(Regex("""\s+"""), " ").trim().take(70)
            return if (recognized.isBlank()) {
                if (english) "Income not found" else "Доход не найден"
            } else {
                if (english) "Income not recognized: $recognized"
                else "Не удалось распознать доход: $recognized"
            }
        }

        val current = match.groupValues[1].filter(Char::isDigit).toLongOrNull()
        val target = match.groupValues[2].filter(Char::isDigit).toLongOrNull()
        if (current == null || target == null || target <= 0L) {
            return if (english) "Income not recognized" else "Доход не распознан"
        }

        return "$current/$target"
    }
}
