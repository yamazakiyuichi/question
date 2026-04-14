package com.example.medquiz.util

import com.example.medquiz.data.Question
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import com.google.gson.reflect.TypeToken

/**
 * JSONファイルからQuestion一覧を読み込むユーティリティ
 *
 * 想定JSONフォーマット:
 * [
 *   {
 *     "year": "2023",
 *     "category": "医療情報基礎知識",
 *     "question_number": 1,
 *     "question_text": "問題文...",
 *     "choice1": "選択肢1",
 *     "choice2": "選択肢2",
 *     "choice3": "選択肢3",
 *     "choice4": "選択肢4",
 *     "choice5": "",
 *     "correct_answer": 2,
 *     "explanation": "解説..."
 *   },
 *   ...
 * ]
 */
object JsonImporter {

    private val gson = Gson()

    data class QuestionJson(
        @SerializedName("year") val year: String,
        @SerializedName("category") val category: String,
        @SerializedName("question_number") val questionNumber: Int,
        @SerializedName("question_text") val questionText: String,
        @SerializedName("choice1") val choice1: String,
        @SerializedName("choice2") val choice2: String,
        @SerializedName("choice3") val choice3: String,
        @SerializedName("choice4") val choice4: String,
        @SerializedName("choice5") val choice5: String = "",
        @SerializedName("correct_answer") val correctAnswer: Int,
        @SerializedName("explanation") val explanation: String = ""
    )

    fun parseJson(jsonString: String): List<Question> {
        val type = object : TypeToken<List<QuestionJson>>() {}.type
        val jsonList: List<QuestionJson> = gson.fromJson(jsonString, type)
        return jsonList.map { it.toQuestion() }
    }

    private fun QuestionJson.toQuestion() = Question(
        year = year,
        category = category,
        questionNumber = questionNumber,
        questionText = questionText,
        choice1 = choice1,
        choice2 = choice2,
        choice3 = choice3,
        choice4 = choice4,
        choice5 = choice5,
        correctAnswer = correctAnswer,
        explanation = explanation
    )
}
