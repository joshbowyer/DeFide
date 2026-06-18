package com.tristinbaker.defide.data.db.user.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "confession_notes")
data class ConfessionNoteEntity(
    @PrimaryKey val id: String,
    val text: String,
    @ColumnInfo(name = "created_at") val createdAt: Long,
)
