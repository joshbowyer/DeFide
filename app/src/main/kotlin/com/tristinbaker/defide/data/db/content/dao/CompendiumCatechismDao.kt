package com.tristinbaker.defide.data.db.content.dao

import android.database.sqlite.SQLiteDatabase
import com.tristinbaker.defide.data.db.content.firstOrNull
import com.tristinbaker.defide.data.db.content.mapRows
import com.tristinbaker.defide.data.db.content.toCompendiumCatechism
import com.tristinbaker.defide.data.model.CompendiumCatechism
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CompendiumCatechismDao @Inject constructor(private val db: SQLiteDatabase) {

    fun getAll(): List<CompendiumCatechism> =
        db.rawQuery(
            "SELECT * FROM compendium_catechism ORDER BY id",
            null,
        ).mapRows { toCompendiumCatechism() }

    fun getByGroup(groupName: String): List<CompendiumCatechism> =
        db.rawQuery(
            "SELECT * FROM compendium_catechism WHERE group_name = ? ORDER BY id",
            arrayOf(groupName),
        ).mapRows { toCompendiumCatechism() }

    fun getById(id: Int): CompendiumCatechism? =
        db.rawQuery(
            "SELECT * FROM compendium_catechism WHERE id = ?",
            arrayOf(id.toString()),
        ).firstOrNull { toCompendiumCatechism() }

    fun getDistinctGroups(): List<String> {
        val groups = mutableListOf<String>()
        db.rawQuery(
            "SELECT DISTINCT group_name FROM compendium_catechism ORDER BY id",
            null,
        ).use { cursor ->
            while (cursor.moveToNext()) {
                groups.add(cursor.getString(0))
            }
        }
        return groups
    }
}
