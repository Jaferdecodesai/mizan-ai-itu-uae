# KB retrieval evaluation (2026-11-09T15:41:57.060012+00:00)

30 hand-written queries, gold document per query, gold article/section for 19 of them. k=5. Embedding: fastembed:nomic-ai/nomic-embed-text-v1.5.

| method | doc hit@5 | section hit@5 | doc MRR@5 |
|---|---|---|---|
| bm25 | 30/30 (1.0) | 19/19 (1.0) | 0.9 |
| hybrid | 29/30 (0.967) | 19/19 (1.0) | 0.886 |
| vector | 28/30 (0.933) | 19/19 (1.0) | 0.883 |

Misses (hybrid):
- Guidance for government employees on risks of using generative AI chatbots with sensitive information → got ['nist-ai-600-1:p-22', 'nist-ai-600-1:p-11', 'sg-genai-mgf-2024:p-21-2']
