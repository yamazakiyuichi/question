package com.example.medquiz.ui.review

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.medquiz.data.Question
import com.example.medquiz.databinding.ItemReviewBinding

class ReviewAdapter : ListAdapter<Question, ReviewAdapter.ViewHolder>(DiffCallback()) {

    class ViewHolder(private val binding: ItemReviewBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(q: Question) {
            binding.textYear.text = "${q.year}年 第${q.questionNumber}問"
            binding.textCategory.text = q.category
            binding.textQuestion.text = q.questionText
            val correctText = when (q.correctAnswer) {
                1 -> q.choice1
                2 -> q.choice2
                3 -> q.choice3
                4 -> q.choice4
                5 -> q.choice5
                else -> ""
            }
            binding.textCorrectAnswer.text = "正解: ${q.correctAnswer}. $correctText"
            if (q.explanation.isNotBlank()) {
                binding.textExplanation.text = q.explanation
                binding.textExplanation.visibility = android.view.View.VISIBLE
            } else {
                binding.textExplanation.visibility = android.view.View.GONE
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemReviewBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class DiffCallback : DiffUtil.ItemCallback<Question>() {
        override fun areItemsTheSame(oldItem: Question, newItem: Question) = oldItem.id == newItem.id
        override fun areContentsTheSame(oldItem: Question, newItem: Question) = oldItem == newItem
    }
}
