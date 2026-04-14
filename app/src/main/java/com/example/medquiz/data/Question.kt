package com.example.medquiz.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "questions")
data class Question(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val year: String,           // 例: "2023"
    val category: String,       // 例: "医療情報基礎知識"
    val questionNumber: Int,    // 問題番号
    val questionText: String,   // 問題文
    val choice1: String,
    val choice2: String,
    val choice3: String,
    val choice4: String,
    val choice5: String = "",   // 5択の場合
    val correctAnswer: Int,     // 1〜4 (または5)
    val explanation: String = ""// 解説
)
