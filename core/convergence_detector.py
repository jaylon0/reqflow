"""ConvergenceDetector -- checks if a multi-round debate has converged.

Provides dual convergence detection: round counter + text similarity.
Includes anti-sycophancy check to prevent premature agreement.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConvergenceDetector:
    """Detects whether debate rounds have converged.

    Args:
        min_rounds: Minimum number of rounds before convergence can be declared.
        max_rounds: Maximum number of rounds (hard stop).
        similarity_threshold: Text similarity above this means converged.
        sycophancy_threshold: If all agents agree above this, flag sycophancy.
    """

    min_rounds: int = 2
    max_rounds: int = 5
    similarity_threshold: float = 0.85
    sycophancy_threshold: float = 0.95

    def check(self, rounds: list[dict]) -> dict:
        """Check convergence status of debate rounds.

        Args:
            rounds: List of round dicts, each with 'round_num' and 'opinions' list.
                     Each opinion has 'conclusion' and 'cross_commentary'.

        Returns:
            Dict with 'converged' (bool), 'reason' (str), 'score' (float).
        """
        if not rounds:
            return {"converged": False, "reason": "no_rounds", "score": 0.0}

        round_count = len(rounds)

        # Hard stop at max rounds
        if round_count >= self.max_rounds:
            return {
                "converged": True,
                "reason": f"max_rounds_reached ({self.max_rounds})",
                "score": 1.0,
            }

        # Need minimum rounds
        if round_count < self.min_rounds:
            return {
                "converged": False,
                "reason": f"below_min_rounds ({round_count}/{self.min_rounds})",
                "score": 0.0,
            }

        # Calculate text similarity across rounds
        similarity = self._calculate_similarity(rounds)

        # Anti-sycophancy check
        if similarity > self.sycophancy_threshold:
            return {
                "converged": False,
                "reason": "sycophancy_detected",
                "score": similarity,
            }

        # Check if similarity exceeds threshold
        if similarity >= self.similarity_threshold:
            return {
                "converged": True,
                "reason": "convergence_achieved",
                "score": similarity,
            }

        return {
            "converged": False,
            "reason": "not_converged",
            "score": similarity,
        }

    def _calculate_similarity(self, rounds: list[dict]) -> float:
        """Calculate average text similarity between consecutive rounds.

        Uses a simple token-overlap (Jaccard) approach for conclusions
        and cross-commentary.
        """
        if len(rounds) < 2:
            return 0.0

        similarities: list[float] = []
        for i in range(1, len(rounds)):
            prev_opinions = rounds[i - 1].get("opinions", [])
            curr_opinions = rounds[i].get("opinions", [])

            if not prev_opinions or not curr_opinions:
                continue

            # Compare conclusions between same-role agents
            prev_texts = {o.get("role", ""): o.get("conclusion", "") for o in prev_opinions}
            curr_texts = {o.get("role", ""): o.get("conclusion", "") for o in curr_opinions}

            common_roles = set(prev_texts.keys()) & set(curr_texts.keys())
            if not common_roles:
                continue

            role_similarities = []
            for role in common_roles:
                sim = self._jaccard_similarity(prev_texts[role], curr_texts[role])
                role_similarities.append(sim)

            if role_similarities:
                similarities.append(sum(role_similarities) / len(role_similarities))

        return sum(similarities) / len(similarities) if similarities else 0.0

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        """Calculate Jaccard similarity between two texts based on character n-grams."""
        if not text_a or not text_b:
            return 0.0

        # Use bigrams for better granularity
        def bigrams(text: str) -> set[str]:
            return {text[i:i + 2] for i in range(len(text) - 1)} if len(text) >= 2 else {text}

        a_bigrams = bigrams(text_a)
        b_bigrams = bigrams(text_b)

        intersection = a_bigrams & b_bigrams
        union = a_bigrams | b_bigrams

        return len(intersection) / len(union) if union else 0.0
