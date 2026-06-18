package com.tristinbaker.defide.data.db.user.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.tristinbaker.defide.data.db.user.entity.ConfessionNoteEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ConfessionNoteDao {
    @Query("SELECT * FROM confession_notes ORDER BY created_at DESC")
    fun getAllFlow(): Flow<List<ConfessionNoteEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(note: ConfessionNoteEntity)

    @Delete
    suspend fun delete(note: ConfessionNoteEntity)

    @Query("DELETE FROM confession_notes")
    suspend fun deleteAll()
}
