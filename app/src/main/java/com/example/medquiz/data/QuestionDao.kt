package com.example.medquiz.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface QuestionDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(questions: List<Question>)

    @Query("SELECT * FROM questions ORDER BY year DESC, questionNumber ASC")
    fun getAllQuestions(): Flow<List<Question>>

    @Query("SELECT * FROM questions WHERE id = :id")
    suspend fun getQuestionById(id: Long): Question?

    @Query("SELECT * FROM questions WHERE year = :year ORDER BY questionNumber ASC")
    fun getQuestionsByYear(year: String): Flow<List<Question>>

    @Query("SELECT * FROM questions WHERE category = :category ORDER BY year DESC, questionNumber ASC")
    fun getQuestionsByCategory(category: String): Flow<List<Question>>

    @Query("SELECT DISTINCT year FROM questions ORDER BY year DESC")
    fun getAllYears(): Flow<List<String>>

    @Query("SELECT DISTINCT category FROM questions ORDER BY category ASC")
    fun getAllCategories(): Flow<List<String>>

    @Query("SELECT COUNT(*) FROM questions")
    fun getTotalCount(): Flow<Int>

    @Query("""
        SELECT q.* FROM questions q
        WHERE q.id NOT IN (
            SELECT DISTINCT sr.questionId FROM study_records sr WHERE sr.isCorrect = 1
        )
        ORDER BY RANDOM()
        LIMIT :limit
    """)
    suspend fun getUnansweredOrWrong(limit: Int): List<Question>

    @Query("""
        SELECT q.* FROM questions q
        INNER JOIN study_records sr ON q.id = sr.questionId
        WHERE sr.isCorrect = 0
        GROUP BY q.id
        ORDER BY MAX(sr.answeredAt) DESC
    """)
    fun getWrongQuestions(): Flow<List<Question>>

    @Query("""
        SELECT q.* FROM questions q
        WHERE (:year = '' OR q.year = :year)
        AND (:category = '' OR q.category = :category)
        ORDER BY q.year DESC, q.questionNumber ASC
    """)
    fun getFilteredQuestions(year: String, category: String): Flow<List<Question>>

    @Query("DELETE FROM questions")
    suspend fun deleteAll()
}
