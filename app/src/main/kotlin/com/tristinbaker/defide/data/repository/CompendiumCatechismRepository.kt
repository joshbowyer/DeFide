package com.tristinbaker.defide.data.repository

import com.tristinbaker.defide.data.db.content.dao.CompendiumCatechismDao
import com.tristinbaker.defide.data.model.CompendiumCatechism
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CompendiumCatechismRepository @Inject constructor(
    private val compendiumDao: CompendiumCatechismDao,
) {
    suspend fun getAll(): List<CompendiumCatechism> =
        withContext(Dispatchers.IO) { compendiumDao.getAll() }

    suspend fun getByGroup(groupName: String): List<CompendiumCatechism> =
        withContext(Dispatchers.IO) { compendiumDao.getByGroup(groupName) }

    suspend fun getById(id: Int): CompendiumCatechism? =
        withContext(Dispatchers.IO) { compendiumDao.getById(id) }

    suspend fun getDistinctGroups(): List<String> =
        withContext(Dispatchers.IO) { compendiumDao.getDistinctGroups() }
}
