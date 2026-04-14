package com.example.medquiz.ui.result

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.example.medquiz.R
import com.example.medquiz.databinding.FragmentResultBinding

class ResultFragment : Fragment() {

    private var _binding: FragmentResultBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentResultBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val correct = arguments?.getInt("correct") ?: 0
        val total = arguments?.getInt("total") ?: 1
        val percent = if (total > 0) correct * 100 / total else 0

        binding.textScore.text = "$correct / $total 問正解"
        binding.textPercent.text = "正答率: $percent%"
        binding.progressResult.max = total
        binding.progressResult.progress = correct

        val message = when {
            percent >= 90 -> "素晴らしい！完璧に近いです！"
            percent >= 70 -> "よくできました！引き続き頑張りましょう。"
            percent >= 50 -> "もう少しです。苦手問題を復習しましょう。"
            else -> "基礎から復習しましょう。"
        }
        binding.textMessage.text = message

        binding.btnReturnHome.setOnClickListener {
            findNavController().navigate(R.id.homeFragment)
        }

        binding.btnRetryWrong.setOnClickListener {
            findNavController().navigate(
                R.id.action_resultFragment_to_quizFragment,
                Bundle().apply {
                    putString("year", "")
                    putString("category", "")
                    putString("mode", "wrong")
                }
            )
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
