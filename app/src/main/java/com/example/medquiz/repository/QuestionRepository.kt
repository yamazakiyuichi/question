package com.example.medquiz.repository

import com.example.medquiz.data.*
import kotlinx.coroutines.flow.Flow

class QuestionRepository(
    private val questionDao: QuestionDao,
    private val studyRecordDao: StudyRecordDao
) {

    fun getAllQuestions(): Flow<List<Question>> = questionDao.getAllQuestions()
    fun getQuestionsByYear(year: String) = questionDao.getQuestionsByYear(year)
    fun getQuestionsByCategory(category: String) = questionDao.getQuestionsByCategory(category)
    fun getAllYears(): Flow<List<String>> = questionDao.getAllYears()
    fun getAllCategories(): Flow<List<String>> = questionDao.getAllCategories()
    fun getTotalCount(): Flow<Int> = questionDao.getTotalCount()
    fun getWrongQuestions(): Flow<List<Question>> = questionDao.getWrongQuestions()
    fun getFilteredQuestions(year: String, category: String) =
        questionDao.getFilteredQuestions(year, category)

    suspend fun getUnansweredOrWrong(limit: Int = 20): List<Question> =
        questionDao.getUnansweredOrWrong(limit)

    suspend fun insertQuestions(questions: List<Question>) =
        questionDao.insertAll(questions)

    suspend fun recordAnswer(questionId: Long, selected: Int, correct: Boolean) {
        studyRecordDao.insert(
            StudyRecord(
                questionId = questionId,
                selectedAnswer = selected,
                isCorrect = correct
            )
        )
    }

    fun getAllStats(): Flow<List<QuestionStats>> = studyRecordDao.getAllStats()
    fun getCorrectQuestionCount(): Flow<Int> = studyRecordDao.getCorrectQuestionCount()
    fun getTotalAttempts(): Flow<Int> = studyRecordDao.getTotalAttempts()
    fun getStudiedQuestionCount(): Flow<Int> = studyRecordDao.getStudiedQuestionCount()
    suspend fun getLastResult(questionId: Long): Boolean? = studyRecordDao.getLastResult(questionId)

    suspend fun resetProgress() {
        studyRecordDao.deleteAll()
    }

    suspend fun deleteAllQuestions() {
        questionDao.deleteAll()
    }
}
