package com.tristinbaker.defide.data.db.user.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "confession_records")
data class ConfessionRecordEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "made_at") val madeAt: Long,
)
