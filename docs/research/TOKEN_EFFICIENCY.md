# Input-token efficiency research

## Research objective

Reduce model input tokens and latency without reducing answer quality, permission safety, grounding, or citation correctness. Optimising only the bill is not a pass if relevant evidence disappears or unsupported claims increase.

## Current measured baseline

The reproduced multi-document recovery used:

- 35 evidence records;
- 26,226 total input tokens;
- 1,239 output tokens;
- 14 cited evidence records;
- 14.548 seconds frontend latency;
- a successful grounded answer with no `answer_failed` event.

This is the first research benchmark. The other four recovered questions used 10–15 evidence records and materially fewer input tokens.

## Evaluation contract

Every experiment must rerun the same fixed questions and record:

- retrieval recall against expected documents;
- answer correctness and groundedness;
- citation precision and citation coverage;
- evidence records and unique sources supplied to the model;
- input, output, cache-read, and cache-write tokens when available;
- latency and estimated model cost;
- recovery frequency and terminal failures.

Compare one change at a time against the baseline. Preserve raw measured results in `evals/`.

## Research order

1. **Measure repetition and usefulness.** Determine how many of the 35 records were near-duplicates, uncited, or from an overrepresented source.
2. **Deterministic duplicate removal.** Collapse identical/overlapping chunks while retaining the best provenance record.
3. **Per-source caps plus diversity selection.** Prevent one document from crowding out other relevant sources; evaluate maximal marginal relevance or an equivalent diversity rule.
4. **Rerank before generation.** Retrieve broadly for recall, then send a smaller high-quality set to Claude. Compare a deterministic/embedding reranker with a learned reranker only if the simpler option fails the acceptance gate.
5. **Contextual compression.** Extract only the directly relevant passages while preserving immutable source/page mapping. Treat model-generated compression as untrusted and test for omitted qualifiers.
6. **Query planning and bounded tool use.** Avoid repeated searches that express the same intent; retain the current strict search and retry budgets.
7. **Prompt caching where supported.** Cache only stable repeated prefixes such as system instructions and tool definitions. Measure cache hits and actual price impact; caching does not reduce the logical evidence volume or fix poor retrieval.
8. **Model routing only after quality evidence.** Consider a smaller model for routing/reranking and the stronger model for final synthesis only if the evaluation demonstrates equal or acceptable quality.

## Likely first implementation experiment

Add an evidence-selection stage between retrieval and finalization:

```text
broad retrieval
    -> exact/overlap deduplication
    -> per-source cap
    -> diversity-aware top-k
    -> final evidence context
    -> Claude answer with citations
```

Start with configuration-driven limits and no new managed service. This is explainable, cheap to test, and reversible. Do not add a reranking model until the deterministic experiment shows a measured gap.

## Current source notes

- Amazon Bedrock prompt caching can reduce cost and latency for supported models when a sufficiently long prompt prefix repeats; support, minimum tokens, cache fields, TTL, and pricing vary by model.
- Bedrock model invocation observability can expose invocation counts, token use, and errors. Full invocation logging can contain prompt/evidence content, so privacy and retention must be designed before enabling it.
- The application already records aggregate input/output token counts. Extend those privacy-conscious metrics before considering full prompt logging.

Official references checked 2026-09-20:

- https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/model-invocations.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html
