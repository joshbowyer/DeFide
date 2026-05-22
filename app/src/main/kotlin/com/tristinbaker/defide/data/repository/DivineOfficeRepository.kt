package com.tristinbaker.defide.data.repository

import com.tristinbaker.defide.data.db.content.dao.DivineOfficeDao
import com.tristinbaker.defide.data.model.DivineOffice
import com.tristinbaker.defide.data.model.DivineOfficeCalendar
import com.tristinbaker.defide.data.model.DivineOfficePsalm
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DivineOfficeRepository @Inject constructor(
    private val dao: DivineOfficeDao,
) {
    suspend fun getCalendarEntry(mmDd: String, language: String): DivineOfficeCalendar? =
        withContext(Dispatchers.IO) { dao.getCalendarEntry(mmDd, language) }

    suspend fun getAllCalendarEntries(language: String): List<DivineOfficeCalendar> =
        withContext(Dispatchers.IO) { dao.getAllCalendarEntries(language) }

    suspend fun getOfficeByFileAndType(file: String, officeType: String, language: String): DivineOffice? =
        withContext(Dispatchers.IO) { dao.getOfficeByFileAndType(file, officeType, language) }

    suspend fun getOfficesByFile(file: String, language: String): List<DivineOffice> =
        withContext(Dispatchers.IO) { dao.getOfficesByFile(file, language) }

    suspend fun getPsalmsForDayAndType(day: Int, officeType: String, language: String): List<DivineOfficePsalm> =
        withContext(Dispatchers.IO) { dao.getPsalmsForDayAndType(day, officeType, language) }

    suspend fun getOfficeCount(): Int =
        withContext(Dispatchers.IO) { dao.getOfficeCount() }

    suspend fun getCalendarCount(): Int =
        withContext(Dispatchers.IO) { dao.getCalendarCount() }

    /**
     * Returns all offices for a date + language: sancti/tempora/commune files, with ferial
     * offices and antiphons merged in automatically by the DAO.
     */
    suspend fun getAllOfficesForDate(date: LocalDate, language: String): List<DivineOffice> =
        withContext(Dispatchers.IO) {
            val mmDd = "%02d-%02d".format(date.monthValue, date.dayOfMonth)
            val cal = dao.getCalendarEntry(mmDd, language)
            // Day-of-week 0=Sun...6=Sat (Java convention)
            val dayOfWeek = date.dayOfWeek.value % 7
            val files = listOfNotNull(cal?.temporaFile, cal?.sanctiFile, cal?.communeFile)
            dao.getAllOfficesForDay(dayOfWeek, files, language)
        }

    /** Returns psalms for a given day-of-week and office type. */
    suspend fun getPsalmsForDayAndOffice(day: Int, officeType: String, language: String): List<DivineOfficePsalm> =
        withContext(Dispatchers.IO) { dao.getPsalmsForDayAndType(day, officeType, language) }

    /**
     * Returns ferial (Psalterium) psalms for a given day-of-week (0=Sun…6=Sat) and
     * office type ("Laudes" or "Vespers"). These always exist for every day since
     * fix_psalms.py inserts them as a complete fallback set.
     */
    suspend fun getFerialPsalms(dayOfWeek: Int, officeType: String, language: String): List<DivineOfficePsalm> =
        withContext(Dispatchers.IO) { dao.getFerialPsalms(dayOfWeek, officeType, language) }

    /**
     * Returns the ferial (weekday) tempora files for a given day-of-week.
     * Tempora keys are like "091-1" = Sunday after Sept 1st week, ferial day 1.
     * We pick the ferial entry (the -1, -2, ... suffix) whose day-of-week matches.
     *
     * The ferial cycle is stored in tempora files named "MMDD-F" where F is the
     * day-of-week position within that week (0=first day, 1=second, etc).
     * Since we don't have the liturgical week mapping, we use the raw calendar day
     * modulo 7 as an approximation, and look for the matching ferial tempora.
     *
     * A better approach: look up the tempora ferial by finding the closest
     * Sunday tempora file for the current liturgical season, then step to the right day.
     */
    suspend fun getFerialFiles(dayOfWeek: Int, language: String): List<String> =
        withContext(Dispatchers.IO) {
            // Try the ferial tempora entries directly
            // Files like "091-1" where 1 = ferial day of that week
            // We look for tempora files with a numeric suffix matching dayOfWeek
            val cur = dao.getAllCalendarEntries(language)
            val ferial = cur.filter {
                it.temporaFile != null &&
                it.temporaFile!!.matches(Regex("tempora/[0-9]{3}-[0-9]"))
            }
            // Return the tempora file for this day-of-week if available
            ferial.filter {
                val suffix = it.temporaFile!!.substringAfterLast("-")
                suffix.toIntOrNull() == dayOfWeek
            }.map { it.temporaFile!! }.take(1)
        }

    /**
     * Synchronous version of getOfficesByFiles for use on the IO dispatcher.
     */
    fun getOfficesByFilesSync(files: List<String>, language: String): List<DivineOffice> =
        dao.getOfficesByFiles(files, language)
}
