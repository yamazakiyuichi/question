package com.example.medquiz.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

data class QuestionStats(
    val questionId: Long,
    val totalAttempts: Int,
    val correctCount: Int
)

@Dao
interface StudyRecordDao {

    @Insert
    suspend fun insert(record: StudyRecord)

    @Query("""
        SELECT questionId, COUNT(*) as totalAttempts, SUM(CASE WHEN isCorrect = 1 THEN 1 ELSE 0 END) as correctCount
        FROM study_records
        GROUP BY questionId
    """)
    fun getAllStats(): Flow<List<QuestionStats>>

    @Query("""
        SELECT COUNT(DISTINCT questionId) FROM study_records WHERE isCorrect = 1
    """)
    fun getCorrectQuestionCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM study_records")
    fun getTotalAttempts(): Flow<Int>

    @Query("""
        SELECT COUNT(DISTINCT questionId) FROM study_records
    """)
    fun getStudiedQuestionCount(): Flow<Int>

    @Query("""
        SELECT isCorrect FROM study_records
        WHERE questionId = :questionId
        ORDER BY answeredAt DESC
        LIMIT 1
    """)
    suspend fun getLastResult(questionId: Long): Boolean?

    @Query("DELETE FROM study_records")
    suspend fun deleteAll()
}
