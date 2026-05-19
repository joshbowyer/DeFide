package com.tristinbaker.defide.data.model

import androidx.compose.runtime.Immutable

@Immutable
data class DivineOfficeCalendar(
    val key: String,        // "MM-DD"
    val title: String,
    val rank: String?,
    val grade: Int,
    val temporaFile: String?,
    val sanctiFile: String?,
    val communeFile: String?,
)

@Immutable
data class DivineOffice(
    val id: Int,
    val file: String,
    val fileType: String,
    val title: String,
    val officeType: String?,
    val invitatorium: String?,
    val ant1: String?, val ant2: String?, val ant3: String?,
    val ant4: String?, val ant5: String?, val ant6: String?,
    val ant7: String?, val ant8: String?, val ant9: String?,
    val antVespera1: String?, val antVespera2: String?, val antVespera3: String?,
    val antVespera4: String?, val antVespera5: String?, val antVespera6: String?,
    val antVespera7: String?, val antVespera8: String?, val antVespera9: String?,
    val antVespera10: String?, val antVespera11: String?, val antVespera12: String?,
    val hymn: String?,
    val lectio1: String?, val lectio2: String?, val lectio3: String?,
    val responsory1: String?, val responsory2: String?, val responsory3: String?,
    val versus: String?,
    val preces: String?,
    val oratio: String?,
    val conclusio: String?,
    /** Matins antiphon loaded from matutinum.txt, used when office_type is Matins. */
    val matinsAntiphon: String? = null,
    /**
     * Antiphons populated at runtime from ferial psalm rows (keyed by day-of-week).
     * Used for feast days where sancti offices have empty antiphon columns.
     * Stored as list of strings, indexed by position (0=first antiphon, etc.).
     */
    val ferialAntiphons: List<String> = emptyList(),
)

/**
 * A single antiphon + its accompanying psalm verses from the Psalmi txt files.
 */
@Immutable
data class PsalmBlock(
    val antiphon: String?,
    val verses: List<String>,  // list of "ps:vs:text" strings
)

/**
 * The raw JSON stored in divine_office_psalms.psalm_text, parsed for UI use.
 * Format: [{"antiphon": "Ant text", "verses": ["ps:vs:text", ...]}, ...]
 */
@Immutable
data class PsalmBlocks(
    val blocks: List<PsalmBlock>,
) {
    /** Antiphons for all blocks that have them (for Laudes/Vespers display). */
    val antiphons: List<String> get() = blocks.mapNotNull { it.antiphon }.filter { it.isNotBlank() }
    /** All verse texts concatenated, for the psalm reading section. */
    val versesText: String get() = blocks.joinToString("\n") { it.verses.joinToString("\n") }
}

@Immutable
data class DivineOfficePsalm(
    val id: Int,
    val day: Int,           // 0=Sunday … 6=Saturday
    val officeType: String,
    val antiphon: String?,  // short antiphon set at DB row level (rarely used)
    val psalms: String,     // comma-separated refs: "1,50,117,62,220"
    /** Pre-expanded antiphon + verse blocks from the Psalmi txt files. */
    val psalmTextJson: String?,
) {
    /** Parse the JSON into a PsalmBlocks value, or return empty if null/invalid. */
    fun parseBlocks(): PsalmBlocks {
        if (psalmTextJson.isNullOrBlank()) return PsalmBlocks(emptyList())
        return try {
            @Suppress("UNCHECKED_CAST")
            val list = org.json.JSONArray(psalmTextJson)
            val blocks = (0 until list.length()).map { i ->
                val obj = list.getJSONObject(i)
                PsalmBlock(
                    antiphon = obj.optString("antiphon", "").ifEmpty { null },
                    verses = buildList {
                        val verses = obj.optJSONArray("verses")
                        if (verses != null) {
                            for (j in 0 until verses.length()) {
                                verses.getString(j)?.let { add(it) }
                            }
                        }
                    },
                )
            }
            PsalmBlocks(blocks)
        } catch (_: Exception) {
            PsalmBlocks(emptyList())
        }
    }
}
