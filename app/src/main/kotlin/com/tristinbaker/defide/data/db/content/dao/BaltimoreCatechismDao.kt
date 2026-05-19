package com.tristinbaker.defide.data.db.content.dao

import android.database.sqlite.SQLiteDatabase
import com.tristinbaker.defide.data.db.content.firstOrNull
import com.tristinbaker.defide.data.db.content.mapRows
import com.tristinbaker.defide.data.db.content.toBaltimoreCatechism
import com.tristinbaker.defide.data.model.BaltimoreCatechism
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BaltimoreCatechismDao @Inject constructor(private val db: SQLiteDatabase) {

    fun getAll(): List<BaltimoreCatechism> =
        db.rawQuery(
            "SELECT * FROM baltimore_catechism ORDER BY id",
            null,
        ).mapRows { toBaltimoreCatechism() }

    fun getByLesson(lesson: Int): List<BaltimoreCatechism> =
        db.rawQuery(
            "SELECT * FROM baltimore_catechism WHERE lesson = ? ORDER BY number",
            arrayOf(lesson.toString()),
        ).mapRows { toBaltimoreCatechism() }

    fun getById(id: Int): BaltimoreCatechism? =
        db.rawQuery(
            "SELECT * FROM baltimore_catechism WHERE id = ?",
            arrayOf(id.toString()),
        ).firstOrNull { toBaltimoreCatechism() }

    fun getDistinctLessons(): List<Int> {
        val lessons = mutableListOf<Int>()
        db.rawQuery(
            "SELECT DISTINCT lesson FROM baltimore_catechism ORDER BY lesson",
            null,
        ).use { cursor ->
            while (cursor.moveToNext()) {
                lessons.add(cursor.getInt(0))
            }
        }
        return lessons
    }

    fun getLessonTitle(lesson: Int): String = "Lesson $lesson"
}
