"""OCR evaluation: CER/WER vs baseline."""

from __future__ import annotations


def character_error_rate(reference: str, hypothesis: str) -> float:
    ref, hyp = reference.strip(), hypothesis.strip()
    if not ref:
        return 0.0 if not hyp else 1.0
    d = _edit_distance(list(ref), list(hyp))
    return d / len(ref)


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    d = _edit_distance(ref_words, hyp_words)
    return d / len(ref_words)


def _edit_distance(a: list, b: list) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]


if __name__ == "__main__":
    ref = "Theft reported at Colombo 07"
    hyp = "Theft reported at Colombo 07"
    print(f"CER: {character_error_rate(ref, hyp):.4f}")
    print(f"WER: {word_error_rate(ref, hyp):.4f}")
