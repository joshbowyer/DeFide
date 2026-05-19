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
     * Returns the calendar entry for a date.
     * First tries exact key (e.g. "05-18"), then falls back to the n-suffix variant
     * (e.g. "05-21n") if no exact entry exists — this handles optional memorials that
     * use the "n" suffix when there's no base entry.
     */
    fun getCalendarEntry(mmDd: String): DivineOfficeCalendar? {
        // 1. Try exact key
        var result = db.rawQuery(
            "SELECT * FROM divine_office_calendar WHERE key = ? LIMIT 1",
            arrayOf(mmDd),
        ).firstOrNull { toDivineOfficeCalendar() }
        if (result != null) return result

        // 2. Fall back: try any n-suffix / letter-suffix variant (e.g. "05-21n", "05-21o")
        result = db.rawQuery(
            "SELECT * FROM divine_office_calendar WHERE key LIKE ? LIMIT 1",
            arrayOf("$mmDd%"),
        ).firstOrNull { toDivineOfficeCalendar() }
        return result
    }

    fun getAllCalendarEntries(): List<DivineOfficeCalendar> =
        db.rawQuery(
            "SELECT * FROM divine_office_calendar ORDER BY key",
            null,
        ).mapRows { toDivineOfficeCalendar() }

    fun getOfficeByFileAndType(file: String, officeType: String): DivineOffice? =
        db.rawQuery(
            "SELECT * FROM divine_office WHERE file = ? AND office_type = ? LIMIT 1",
            arrayOf(file, officeType),
        ).firstOrNull { toDivineOffice() }

    fun getOfficesByFile(file: String): List<DivineOffice> =
        db.rawQuery(
            "SELECT * FROM divine_office WHERE file = ? ORDER BY office_type",
            arrayOf(file),
        ).mapRows { toDivineOffice() }

    /** Returns all office sections for a list of files, in display order. */
    fun getOfficesByFiles(files: List<String>): List<DivineOffice> {
        if (files.isEmpty()) return emptyList()
        val placeholders = files.joinToString(",") { "?" }
        return db.rawQuery(
            "SELECT * FROM divine_office WHERE file IN ($placeholders) ORDER BY file, office_type",
            files.toTypedArray(),
        ).mapRows { toDivineOffice() }
    }

    fun getPsalmsForDayAndType(day: Int, officeType: String): List<DivineOfficePsalm> =
        db.rawQuery(
            "SELECT * FROM divine_office_psalms WHERE day = ? AND office_type = ? ORDER BY id",
            arrayOf(day.toString(), officeType),
        ).mapRows { toDivineOfficePsalm() }

    /** Get ferial psalms by day-of-week (0=Sun…6=Sat) and office type. */
    fun getFerialPsalms(dayOfWeek: Int, officeType: String): List<DivineOfficePsalm> =
        db.rawQuery(
            "SELECT * FROM divine_office_psalms WHERE day = ? AND office_type = ? ORDER BY id",
            arrayOf(dayOfWeek.toString(), officeType),
        ).mapRows { toDivineOfficePsalm() }

    /**
     * Get all offices for a given day-of-week: sancti/tempora/commune offices PLUS
     * the ferial offices (antiphons from the Psalterium) for that weekday.
     * Ferial offices are only included when no sancti/tempora entry exists for that
     * office type, so feast days show feast Laudes/Vespers and ferial days show ferial.
     * Antiphons from ferial psalm rows are merged into the returned office objects.
     */
    fun getAllOfficesForDay(dayOfWeek: Int, sanctiFiles: List<String>): List<DivineOffice> {
        val ferialMap: MutableMap<String, DivineOffice> = mutableMapOf()
        // Load all ferial offices for this day-of-week
        val ferialOffices = db.rawQuery(
            "SELECT * FROM divine_office WHERE file = ? ORDER BY office_type",
            arrayOf("ferial/$dayOfWeek"),
        ).mapRows { toDivineOffice() }

        for (ferial in ferialOffices) {
            val ot = ferial.officeType ?: "Laudes"
            ferialMap[ot] = ferial
        }

        // Load ferial antiphons from psalm_text JSON
        val ferialPsalmRows = db.rawQuery(
            "SELECT * FROM divine_office_psalms WHERE day = ? ORDER BY office_type",
            arrayOf(dayOfWeek.toString()),
        ).mapRows { toDivineOfficePsalm() }
        for (row in ferialPsalmRows) {
            val ot = row.officeType
            if (ot.isBlank()) continue
            val ferial = ferialMap[ot] ?: continue
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
                    "SELECT * FROM divine_office WHERE file IN ($placeholders) ORDER BY file, office_type",
                    sanctiFiles.toTypedArray(),
                ).mapRows { toDivineOffice() }
            )
        }

        // For each sancti office with empty ant1-ant9, merge antiphons from the
        // corresponding ferial office (keyed by office type).
        val enrichedOffices = allOffices.map { office ->
            val ot = office.officeType ?: return@map office
            val ferial = ferialMap[ot] ?: return@map office
            val hasEmptyAnts = listOf(
                office.ant1, office.ant2, office.ant3,
                office.ant4, office.ant5, office.ant6,
                office.ant7, office.ant8, office.ant9,
            ).all { it.isNullOrBlank() }
            if (hasEmptyAnts && ferial.ferialAntiphons.isNotEmpty()) {
                office.copy(ferialAntiphons = ferial.ferialAntiphons)
            } else if (ferial.ferialAntiphons.isNotEmpty()) {
                // Also attach even if we have some antiphons, in case we need more
                val existing = listOfNotNull(
                    office.ant1, office.ant2, office.ant3,
                    office.ant4, office.ant5, office.ant6,
                    office.ant7, office.ant8, office.ant9,
                )
                office.copy(ferialAntiphons = ferial.ferialAntiphons)
            } else {
                office
            }
        }

        // Add any ferial offices that don't overlap with sancti
        for ((ot, ferial) in ferialMap) {
            val hasSancti = allOffices.any { it.officeType == ot }
            if (!hasSancti) {
                allOffices.add(ferial)
            }
        }

        return enrichedOffices + allOffices.filter { it.file.startsWith("ferial/") }
            .filter { ferial -> enrichedOffices.none { it.officeType == ferial.officeType } }
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
