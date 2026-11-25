package com.m1stor.hhtmobile.capture

/**
 * Generic counter extraction for the prototype.
 *
 * The mobile game's counter positions are not calibrated yet, so we deliberately
 * return every ratio found on screen instead of guessing which one is energy
 * and which one is income.
 */
object CounterOcr {
    private val ratioPattern = Regex("""(?<!\d)(\d{1,6})\s*/\s*(\d{1,6})(?!\d)""")

    fun extractRatios(text: String): List<String> =
        ratioPattern.findAll(text)
            .map { match -> "${match.groupValues[1]}/${match.groupValues[2]}" }
            .distinct()
            .toList()

    fun formatReadout(text: String, english: Boolean = false): String {
        val ratios = extractRatios(text)
        return if (ratios.isEmpty()) {
            if (english) "No counters found. Text: ${text.take(90).ifBlank { "—"}}" else "Счётчики не найдены. Текст: ${text.take(90).ifBlank { "—"}}"
        } else {
            ratios.joinToString("  ·  ")
        }
    }
}
