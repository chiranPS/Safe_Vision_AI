# NLP Classification: Model Comparison Results

This report benchmarks classical Machine Learning models on the synthetic Sri Lanka Police Complaint Dataset for the task of classifying complaint categories from English narrative text.

## Evaluation Metrics (Macro-Averaged)

| Model | F1-Score | Precision | Recall |
|-------|----------|-----------|--------|
| Naive Bayes | 0.9158 | 0.9165 | 0.9167 |
| Random Forest | 0.9076 | 0.9181 | 0.8989 |
| XGBoost | 0.9572 | 0.9599 | 0.9545 |
| DistilBERT (DL) | 0.9526 | 0.9570 | 0.9494 |

## Technical Justification

1. **XGBoost vs. Baseline Models:** The **TF-IDF + XGBoost** model (F1-score: **0.9572**) significantly outperforms the baseline Naive Bayes (**0.9158**) and Random Forest (**0.9076**). While Naive Bayes struggles with overlapping features, XGBoost's gradient-boosting decision trees effectively capture complex non-linear combinations of character n-grams.
2. **Deep Learning (DistilBERT) vs. XGBoost:** **DistilBERT** achieved a macro F1-score of **0.9526** after 3 epochs of fine-tuning on Colab. Although DistilBERT offers deep semantic understanding of sentences, the character n-gram representation with XGBoost yields comparable accuracy (0.9572) by capturing local typos and Singlish code-mixed terms at the sub-word level.
3. **Deployment Trade-Off (Thesis Highlight):** In resource-constrained environments like local police stations (which lack dedicated GPUs), the **XGBoost** model is the ideal choice for production deployment. It runs CPU-inference in milliseconds with a tiny memory footprint, delivering deep-learning-level performance without the massive VRAM overhead of transformer models. DistilBERT serves as a high-fidelity reference ceiling for verification.

## Confusion Matrix Analysis

The confusion matrix for the XGBoost model has been generated and saved as `xgboost_confusion_matrix.png`. Reviewing this matrix helps identify systematic misclassifications, such as confusing 'Social Conflict' with 'Assault' due to shared aggressive vocabulary.
