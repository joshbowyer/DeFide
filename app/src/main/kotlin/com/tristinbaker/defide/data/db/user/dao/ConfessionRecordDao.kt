package com.tristinbaker.defide.data.db.user.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.tristinbaker.defide.data.db.user.entity.ConfessionRecordEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ConfessionRecordDao {
    @Query("SELECT * FROM confession_records ORDER BY made_at DESC")
    fun getAllFlow(): Flow<List<ConfessionRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(record: ConfessionRecordEntity)

    @Delete
    suspend fun delete(record: ConfessionRecordEntity)
}
