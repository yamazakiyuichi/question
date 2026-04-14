package com.example.medquiz.ui.quiz

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.navigation.fragment.findNavController
import com.example.medquiz.MedQuizApp
import com.example.medquiz.R
import com.example.medquiz.databinding.FragmentQuizBinding
import com.google.android.material.button.MaterialButton

class QuizFragment : Fragment() {

    private var _binding: FragmentQuizBinding? = null
    private val binding get() = _binding!!

    private val viewModel: QuizViewModel by viewModels {
        QuizViewModelFactory((requireActivity().application as MedQuizApp).repository)
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentQuizBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val year = arguments?.getString("year") ?: ""
        val category = arguments?.getString("category") ?: ""
        val mode = arguments?.getString("mode") ?: "all"

        viewModel.loadQuestions(year, category, mode)

        val choiceButtons = listOf(
            binding.btnChoice1,
            binding.btnChoice2,
            binding.btnChoice3,
            binding.btnChoice4,
            binding.btnChoice5
        )

        viewModel.state.observe(viewLifecycleOwner) { state ->
            if (state == null) {
                binding.textQuestion.text = "問題がありません。\nまず問題データをインポートしてください。"
                choiceButtons.forEach { it.visibility = View.GONE }
                binding.btnNext.visibility = View.GONE
                binding.textExplanation.visibility = View.GONE
                return@observe
            }

            val q = state.question
            binding.textProgress.text = "${state.index + 1} / ${state.total}"
            binding.progressBar.max = state.total
            binding.progressBar.progress = state.index + 1
            binding.textQuestion.text = q.questionText
            binding.textExplanation.visibility = View.GONE
            binding.btnNext.visibility = View.GONE

            val choices = listOf(q.choice1, q.choice2, q.choice3, q.choice4, q.choice5)
            choiceButtons.forEachIndexed { i, btn ->
                val text = choices.getOrElse(i) { "" }
                if (text.isBlank()) {
                    btn.visibility = View.GONE
                } else {
                    btn.visibility = View.VISIBLE
                    btn.text = "${i + 1}. $text"
                    btn.isEnabled = !state.isAnswered
                    btn.strokeWidth = 0

                    // 回答後の色付け
                    if (state.isAnswered) {
                        when {
                            i + 1 == q.correctAnswer -> {
                                btn.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.correct_green))
                                btn.setTextColor(ContextCompat.getColor(requireContext(), android.R.color.white))
                            }
                            i + 1 == state.selectedAnswer -> {
                                btn.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.wrong_red))
                                btn.setTextColor(ContextCompat.getColor(requireContext(), android.R.color.white))
                            }
                            else -> {
                                btn.setBackgroundColor(ContextCompat.getColor(requireContext(), android.R.color.transparent))
                                btn.setTextColor(ContextCompat.getColor(requireContext(), R.color.text_primary))
                            }
                        }
                    } else {
                        btn.setBackgroundColor(ContextCompat.getColor(requireContext(), android.R.color.transparent))
                        btn.setTextColor(ContextCompat.getColor(requireContext(), R.color.text_primary))
                    }
                }
            }

            if (state.isAnswered) {
                if (q.explanation.isNotBlank()) {
                    binding.textExplanation.visibility = View.VISIBLE
                    binding.textExplanation.text = "【解説】\n${q.explanation}"
                }
                binding.btnNext.visibility = View.VISIBLE
                val isCorrect = state.selectedAnswer == q.correctAnswer
                binding.textResult.visibility = View.VISIBLE
                binding.textResult.text = if (isCorrect) "正解！" else "不正解"
                binding.textResult.setTextColor(
                    ContextCompat.getColor(requireContext(),
                        if (isCorrect) R.color.correct_green else R.color.wrong_red)
                )
            } else {
                binding.textResult.visibility = View.GONE
            }
        }

        choiceButtons.forEachIndexed { i, btn ->
            btn.setOnClickListener { viewModel.selectAnswer(i + 1) }
        }

        binding.btnNext.setOnClickListener { viewModel.next() }

        viewModel.quizFinished.observe(viewLifecycleOwner) { result ->
            result ?: return@observe
            findNavController().navigate(
                R.id.action_quizFragment_to_resultFragment,
                bundleOf("correct" to result.first, "total" to result.second)
            )
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
