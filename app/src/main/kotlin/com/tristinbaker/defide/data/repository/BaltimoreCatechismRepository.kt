package com.tristinbaker.defide.data.repository

import com.tristinbaker.defide.data.db.content.dao.BaltimoreCatechismDao
import com.tristinbaker.defide.data.model.BaltimoreCatechism
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BaltimoreCatechismRepository @Inject constructor(
    private val dao: BaltimoreCatechismDao,
) {
    suspend fun getAll(): List<BaltimoreCatechism> =
        withContext(Dispatchers.IO) { dao.getAll() }

    suspend fun getByLesson(lesson: Int): List<BaltimoreCatechism> =
        withContext(Dispatchers.IO) { dao.getByLesson(lesson) }

    suspend fun getById(id: Int): BaltimoreCatechism? =
        withContext(Dispatchers.IO) { dao.getById(id) }

    suspend fun getDistinctLessons(): List<Int> =
        withContext(Dispatchers.IO) { dao.getDistinctLessons() }

    suspend fun getLessonTitle(lesson: Int): String =
        withContext(Dispatchers.IO) { dao.getLessonTitle(lesson) }
}
