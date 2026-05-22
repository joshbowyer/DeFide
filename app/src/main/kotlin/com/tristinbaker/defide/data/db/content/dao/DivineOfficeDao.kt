package com.tristinbaker.defide.data.db.content.dao

import android.database.sqlite.SQLiteDatabase
import com.tristinbaker.defide.data.db.content.firstOrNull
import com.tristinbaker.defide.data.db.content.mapRows
import com.tristinbaker.defide.data.db.content.toDivineOffice
import com.tristinbaker.defide.data.db.content.toDivineOfficeCalendar
import com.tristinbaker.defide.data.db.content.toDivineOfficePsalm
import com.tristinbaker.defide.data.model.DivineOffice
import com.tristinbaker.defide.data.model.DivineOfficeCalendar
import com.tristinbaker.defide.data.model.DivineOfficePsalm
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DivineOfficeDao @Inject constructor(private val db: SQLiteDatabase) {

    /**
     * Returns the calendar entry for a date + language.
     * First tries exact key (e.g. "05-18"), then falls back to the n-suffix variant
     * (e.g. "05-21n") if no exact entry exists — this handles optional memorials that
     * use the "n" suffix when there's no base entry.
     */
    fun getCalendarEntry(mmDd: String, language: String): DivineOfficeCalendar? {
        // 1. Try exact key
        var result = db.rawQuery(
            "SELECT * FROM divine_office_calendar WHERE key = ? AND language = ? LIMIT 1",
            arrayOf(mmDd, language),
        ).firstOrNull { toDivineOfficeCalendar() }
        if (result != null) return result

        // 2. Fall back: try any n-suffix / letter-suffix variant (e.g. "05-21n", "05-21o")
        result = db.rawQuery(
            "SELECT * FROM divine_office_calendar WHERE key LIKE ? AND language = ? LIMIT 1",
            arrayOf("$mmDd%", language),
        ).firstOrNull { toDivineOfficeCalendar() }
        return result
    }

    fun getAllCalendarEntries(language: String): List<DivineOfficeCalendar> =
        db.rawQuery(
            "SELECT * FROM divine_office_calendar WHERE language = ? ORDER BY key",
            arrayOf(language),
        ).mapRows { toDivineOfficeCalendar() }

    fun getOfficeByFileAndType(file: String, officeType: String, language: String): DivineOffice? =
        db.rawQuery(
            "SELECT * FROM divine_office WHERE file = ? AND office_type = ? AND language = ? LIMIT 1",
            arrayOf(file, officeType, language),
        ).firstOrNull { toDivineOffice() }

    fun getOfficesByFile(file: String, language: String): List<DivineOffice> =
        db.rawQuery(
            "SELECT * FROM divine_office WHERE file = ? AND language = ? ORDER BY office_type",
            arrayOf(file, language),
        ).mapRows { toDivineOffice() }

    /** Returns all office sections for a list of files, in display order. */
    fun getOfficesByFiles(files: List<String>, language: String): List<DivineOffice> {
        if (files.isEmpty()) return emptyList()
        val placeholders = files.joinToString(",") { "?" }
        return db.rawQuery(
            "SELECT * FROM divine_office WHERE file IN ($placeholders) AND language = ? ORDER BY file, office_type",
            files.toTypedArray() + language,
        ).mapRows { toDivineOffice() }
    }

    fun getPsalmsForDayAndType(day: Int, officeType: String, language: String): List<DivineOfficePsalm> =
        db.rawQuery(
            "SELECT * FROM divine_office_psalms WHERE day = ? AND office_type = ? AND language = ? ORDER BY id",
            arrayOf(day.toString(), officeType, language),
        ).mapRows { toDivineOfficePsalm() }

    /** Get ferial psalms by day-of-week (0=Sun…6=Sat) and office type. */
    fun getFerialPsalms(dayOfWeek: Int, officeType: String, language: String): List<DivineOfficePsalm> =
        db.rawQuery(
            "SELECT * FROM divine_office_psalms WHERE day = ? AND office_type = ? AND language = ? ORDER BY id",
            arrayOf(dayOfWeek.toString(), officeType, language),
        ).mapRows { toDivineOfficePsalm() }

    /**
     * Get all offices for a given day-of-week: sancti/tempora/commune offices PLUS
     * the ferial offices (antiphons from the Psalterium) for that weekday.
     * Ferial offices are only included when no sancti/tempora entry exists for that
     * office type, so feast days show feast Laudes/Vespers and ferial days show ferial.
     * Antiphons from ferial psalm rows are merged into the returned office objects.
     */
    fun getAllOfficesForDay(dayOfWeek: Int, sanctiFiles: List<String>, language: String): List<DivineOffice> {
        val ferialMap: MutableMap<String, DivineOffice> = mutableMapOf()
        // Load all ferial offices for this day-of-week
        val ferialOffices = db.rawQuery(
            "SELECT * FROM divine_office WHERE file = ? AND language = ? ORDER BY office_type",
            arrayOf("ferial/$dayOfWeek", language),
        ).mapRows { toDivineOffice() }

        for (ferial in ferialOffices) {
            // Normalize "Completorium" → "Compline" so the key matches the psalm table's
            // office_type values (psalm rows use "Compline", not "Completorium").
            val ot = (ferial.officeType ?: "Laudes").let { if (it == "Completorium") "Compline" else it }
            ferialMap[ot] = ferial
        }

        // Load ferial antiphons from psalm_text JSON
        val ferialPsalmRows = db.rawQuery(
            "SELECT * FROM divine_office_psalms WHERE day = ? AND language = ? ORDER BY office_type",
            arrayOf(dayOfWeek.toString(), language),
        ).mapRows { toDivineOfficePsalm() }
        for (row in ferialPsalmRows) {
            val ot = row.officeType
            if (ot.isBlank()) continue
            // The psalms table uses "Compline" for Completorium ferial antiphons.
            // Try exact key first, then fall back to "Compline" → "Completorium" swap.
            val ferial = ferialMap[ot]
                ?: (if (ot == "Compline") ferialMap["Completorium"] else null)
                ?: (if (ot == "Completorium") ferialMap["Compline"] else null)
                ?: continue
            val blocks = row.parseBlocks()
            val antiphons = blocks.antiphons
            if (antiphons.isNotEmpty()) {
                ferialMap[ot] = ferial.copy(ferialAntiphons = antiphons)
            }
        }

        // Load sancti/tempora/commune offices
        val allOffices = mutableListOf<DivineOffice>()
        if (sanctiFiles.isNotEmpty()) {
            val placeholders = sanctiFiles.joinToString(",") { "?" }
            allOffices.addAll(
                db.rawQuery(
                    "SELECT * FROM divine_office WHERE file IN ($placeholders) AND language = ? ORDER BY file, office_type",
                    sanctiFiles.toTypedArray() + language,
                ).mapRows { toDivineOffice() }
            )
        }

        // For each sancti office with empty ant1-ant9, merge antiphons from the
        // corresponding ferial office (keyed by office type).
        val enrichedOffices = allOffices.map { office ->
            // Normalize "Completorium" → "Compline" so the key matches the psalm table's
            // office_type values (the ferial map is keyed by normalized office type).
            val ot = (office.officeType ?: return@map office).let {
                if (it == "Completorium") "Compline" else it
            }
            val ferial = ferialMap[ot] ?: return@map office
            val sanctiAnts = listOfNotNull(
                office.ant1, office.ant2, office.ant3,
                office.ant4, office.ant5, office.ant6,
                office.ant7, office.ant8, office.ant9,
            )
            // Only attach ferial antiphons as a fallback when sancti has ZERO antiphons.
            // Never attach when sancti already has its own ant1-ant9 to avoid duplication.
            if (sanctiAnts.isEmpty() && ferial.ferialAntiphons.isNotEmpty()) {
                office.copy(ferialAntiphons = ferial.ferialAntiphons)
            } else {
                office
            }
        }

        // Add ferial offices that don't overlap with sancti/tempora/commune entries.
        // Check against enrichedOffices (sancti with ferial antiphons merged in) so we
        // don't double-count when a sancti row already has ferial antiphons attached.
        val ferialToAdd = ferialMap.values.filter { ferial ->
            enrichedOffices.none { it.officeType == ferial.officeType }
        }
        return enrichedOffices + ferialToAdd
    }

    fun getOfficeCount(): Int {
        db.rawQuery("SELECT COUNT(*) FROM divine_office", null).use { c ->
            c.moveToFirst()
            return c.getInt(0)
        }
    }

    fun getCalendarCount(): Int {
        db.rawQuery("SELECT COUNT(*) FROM divine_office_calendar", null).use { c ->
            c.moveToFirst()
            return c.getInt(0)
        }
    }
}
