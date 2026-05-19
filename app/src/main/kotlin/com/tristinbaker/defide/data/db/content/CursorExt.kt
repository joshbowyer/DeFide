package com.tristinbaker.defide.data.db.content

import android.database.Cursor
import com.tristinbaker.defide.data.model.Book
import com.tristinbaker.defide.data.model.MysteryBead
import com.tristinbaker.defide.data.model.Mystery
import com.tristinbaker.defide.data.model.Novena
import com.tristinbaker.defide.data.model.NovenaDay
import com.tristinbaker.defide.data.model.Prayer
import com.tristinbaker.defide.data.model.Saint
import com.tristinbaker.defide.data.model.Translation
import com.tristinbaker.defide.data.model.Verse
import com.tristinbaker.defide.data.model.BaltimoreCatechism
import com.tristinbaker.defide.data.model.DivineOffice
import com.tristinbaker.defide.data.model.DivineOfficeCalendar
import com.tristinbaker.defide.data.model.DivineOfficePsalm

fun Cursor.toTranslation() = Translation(
    id = getString(getColumnIndexOrThrow("id")),
    name = getString(getColumnIndexOrThrow("name")),
    language = getString(getColumnIndexOrThrow("language")),
    license = getString(getColumnIndexOrThrow("license")),
)

fun Cursor.toBook() = Book(
    id = getInt(getColumnIndexOrThrow("id")),
    translationId = getString(getColumnIndexOrThrow("translation_id")),
    bookNumber = getInt(getColumnIndexOrThrow("book_number")),
    testament = getString(getColumnIndexOrThrow("testament")),
    shortName = getString(getColumnIndexOrThrow("short_name")),
    fullName = getString(getColumnIndexOrThrow("full_name")),
    drName = getString(getColumnIndexOrThrow("dr_name")),
)

fun Cursor.toVerse() = Verse(
    id = getInt(getColumnIndexOrThrow("id")),
    bookId = getInt(getColumnIndexOrThrow("book_id")),
    chapter = getInt(getColumnIndexOrThrow("chapter")),
    verse = getInt(getColumnIndexOrThrow("verse")),
    text = getString(getColumnIndexOrThrow("text")),
)

fun Cursor.toPrayer() = Prayer(
    id = getString(getColumnIndexOrThrow("id")),
    title = getString(getColumnIndexOrThrow("title")),
    body = getString(getColumnIndexOrThrow("body")),
    source = getStringOrNull("source"),
    category = getString(getColumnIndexOrThrow("category")),
)

fun Cursor.toNovena() = Novena(
    id = getString(getColumnIndexOrThrow("id")),
    title = getString(getColumnIndexOrThrow("title")),
    description = getStringOrNull("description"),
    totalDays = getInt(getColumnIndexOrThrow("total_days")),
    feastDay = getStringOrNull("feast_day"),
)

fun Cursor.toNovenaDay() = NovenaDay(
    id = getInt(getColumnIndexOrThrow("id")),
    novenaId = getString(getColumnIndexOrThrow("novena_id")),
    dayNumber = getInt(getColumnIndexOrThrow("day_number")),
    title = getStringOrNull("title"),
    body = getString(getColumnIndexOrThrow("body")),
)

fun Cursor.toMystery() = Mystery(
    id = getString(getColumnIndexOrThrow("id")),
    name = getString(getColumnIndexOrThrow("name")),
    traditionalDays = getStringOrNull("traditional_days"),
)

fun Cursor.toMysteryBead() = MysteryBead(
    id = getInt(getColumnIndexOrThrow("id")),
    mysteryId = getString(getColumnIndexOrThrow("mystery_id")),
    position = getInt(getColumnIndexOrThrow("position")),
    prayerId = getStringOrNull("prayer_id"),
    mysteryNumber = getIntOrNull("mystery_number"),
    mysteryTitle = getStringOrNull("mystery_title"),
    mysteryScripture = getStringOrNull("mystery_scripture"),
    mysteryMeditation = getStringOrNull("mystery_meditation"),
)

fun Cursor.toSaint() = Saint(
    id = getString(getColumnIndexOrThrow("id")),
    name = getString(getColumnIndexOrThrow("name")),
    feastDate = getStringOrNull("feast_date"),
    shortBio = getString(getColumnIndexOrThrow("short_bio")),
    fullBio = getString(getColumnIndexOrThrow("full_bio")),
    patronage = getStringOrNull("patronage"),
    category = getString(getColumnIndexOrThrow("category")),
)

fun Cursor.toBaltimoreCatechism() = BaltimoreCatechism(
    id = getInt(getColumnIndexOrThrow("id")),
    number = getInt(getColumnIndexOrThrow("number")),
    lesson = getInt(getColumnIndexOrThrow("lesson")),
    question = getString(getColumnIndexOrThrow("question")),
    answer = getString(getColumnIndexOrThrow("answer")),
)

fun Cursor.toDivineOffice() = DivineOffice(
    id = getInt(getColumnIndexOrThrow("id")),
    file = getString(getColumnIndexOrThrow("file")),
    fileType = getString(getColumnIndexOrThrow("file_type")),
    title = getString(getColumnIndexOrThrow("title")),
    officeType = getStringOrNull("office_type"),
    invitatorium = getStringOrNull("invitatorium"),
    ant1 = getStringOrNull("antiphon_1"), ant2 = getStringOrNull("antiphon_2"), ant3 = getStringOrNull("antiphon_3"),
    ant4 = getStringOrNull("antiphon_4"), ant5 = getStringOrNull("antiphon_5"), ant6 = getStringOrNull("antiphon_6"),
    ant7 = getStringOrNull("antiphon_7"), ant8 = getStringOrNull("antiphon_8"), ant9 = getStringOrNull("antiphon_9"),
    antVespera1 = getStringOrNull("antiphon_vespera_1"), antVespera2 = getStringOrNull("antiphon_vespera_2"), antVespera3 = getStringOrNull("antiphon_vespera_3"),
    antVespera4 = getStringOrNull("antiphon_vespera_4"), antVespera5 = getStringOrNull("antiphon_vespera_5"), antVespera6 = getStringOrNull("antiphon_vespera_6"),
    antVespera7 = getStringOrNull("antiphon_vespera_7"), antVespera8 = getStringOrNull("antiphon_vespera_8"), antVespera9 = getStringOrNull("antiphon_vespera_9"),
    antVespera10 = getStringOrNull("antiphon_vespera_10"), antVespera11 = getStringOrNull("antiphon_vespera_11"), antVespera12 = getStringOrNull("antiphon_vespera_12"),
    hymn = getStringOrNull("hymn"),
    lectio1 = getStringOrNull("lectio_1"), lectio2 = getStringOrNull("lectio_2"), lectio3 = getStringOrNull("lectio_3"),
    responsory1 = getStringOrNull("responsory_1"), responsory2 = getStringOrNull("responsory_2"), responsory3 = getStringOrNull("responsory_3"),
    versus = getStringOrNull("versus"),
    preces = getStringOrNull("preces"),
    capitulum = getStringOrNull("capitulum"),
    oratio = getStringOrNull("oratio"),
    conclusio = getStringOrNull("conclusio"),
    matinsAntiphon = getStringOrNull("matins_antiphon"),
)

fun Cursor.toDivineOfficeCalendar() = DivineOfficeCalendar(
    key = getString(getColumnIndexOrThrow("key")),
    title = getString(getColumnIndexOrThrow("title")),
    rank = getStringOrNull("rank"),
    grade = getInt(getColumnIndexOrThrow("grade")),
    temporaFile = getStringOrNull("tempora_file"),
    sanctiFile = getStringOrNull("sancti_file"),
    communeFile = getStringOrNull("commune_file"),
)

fun Cursor.toDivineOfficePsalm() = DivineOfficePsalm(
    id = getInt(getColumnIndexOrThrow("id")),
    day = getInt(getColumnIndexOrThrow("day")),
    officeType = getString(getColumnIndexOrThrow("office_type")),
    antiphon = getStringOrNull("antiphon"),
    psalms = getString(getColumnIndexOrThrow("psalms")),
    psalmTextJson = getStringOrNull("psalm_text"),
)

private fun Cursor.getStringOrNull(column: String): String? {
    val idx = getColumnIndexOrThrow(column)
    return if (isNull(idx)) null else getString(idx)
}

private fun Cursor.getIntOrNull(column: String): Int? {
    val idx = getColumnIndexOrThrow(column)
    return if (isNull(idx)) null else getInt(idx)
}

/** Iterates all rows, applying [transform] to each, then closes the cursor. */
inline fun <T> Cursor.mapRows(transform: Cursor.() -> T): List<T> = use {
    val result = mutableListOf<T>()
    while (moveToNext()) result.add(transform())
    result
}

/** Returns the first row or null, then closes the cursor. */
inline fun <T> Cursor.firstOrNull(transform: Cursor.() -> T): T? = use {
    if (moveToFirst()) transform() else null
}
