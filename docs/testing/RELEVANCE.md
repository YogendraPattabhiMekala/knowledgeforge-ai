# Answer relevance safeguard

## Root cause

`rag.retrieve` produces candidates, not evidence of answerability. PostgreSQL first uses AND-style `plainto_tsquery`, then falls back to OR-style normalized keywords if empty. Any common match could qualify. Reciprocal-rank fusion orders lexical/pgvector candidates but has no absolute sufficiency meaning; even its highest result can be unrelated. SQLite similarly accepted any positive keyword overlap. The previous graph only abstained when retrieval returned an empty list. It also appended the last user question to every question of seven or fewer words, which could contaminate topic changes.

A separate citation issue listed up to six extractive citations while displaying only three truncated passages. A matching detail after the 650-character cutoff could be omitted from the answer.

## Implementation

The existing PostgreSQL full-text/pgvector and SQLite candidate retrieval, SQL tenant/visibility checks, HTTP routes and storage are preserved. No dependency, schema or migration is added.

The LangGraph flow is now **retrieve → relevance → generate**:

1. Retrieve up to 30 authorized candidates so that a relevant lower-ranked passage can survive the gate. Search remains candidate discovery; its raw scores/results are not assertions of answerability.
2. Normalize English query/passage tokens with small plural/verb/adverb inflection rules. Generic question and company/policy boilerplate words do not establish a topic.
3. For each passage independently, compute `matched unique query terms / unique query terms`. Require coverage **≥ 0.8**, at least **min(2, query term count)** matches, and at least one matched alphabetic topic. Coverage is not a probability.
4. Require every literal numeric qualifier and every double-quoted phrase from the evidence question in that same passage. This rejects unsupported dates, quantities and exact phrases even when many broad terms match. Evidence from unrelated partial passages is not pooled.
5. A specific new question stands on its own. A brief, underspecified follow-up (fewer than two alphabetic topical terms) also uses the last user question as context for both retrieval and gating. This preserves e.g. “How many days?” after a remote-work question without accepting an unrelated starter-checklist passage mentioning days.
6. Keep at most six admitted passages. With none, return “I couldn’t find enough evidence … No sufficiently relevant information was found …” and `citations: []`, before any chat-generation call.
7. Extractive mode displays at most three complete admitted passages and cites exactly those three or fewer, retaining original document/chunk IDs, text, page and ordinal. It never synthesizes an answer.
8. Provider mode receives only admitted evidence. Existing numeric reference validation and server-side post-generation access rechecks remain in place. High vector similarity alone cannot bypass the textual gate.

Settings, also shown in `.env.example`:

```dotenv
RELEVANCE_MIN_COVERAGE=0.8
RELEVANCE_MIN_MATCHES=2
```

Settings validate coverage in `[0,1]` and match count in `[1,20]`. Lowering thresholds increases false-positive risk; calibrate with a representative domain-specific evaluation set, not a single example. There is no topic-name or planet-specific branch.

## Executed verification

From `apps/api` with locked dependencies:

```sh
.venv/bin/python -m pytest -q
# 63 passed, 2 skipped

TEST_DATABASE_URL=postgresql+asyncpg://forge:disposable-test-only@127.0.0.1:55432/knowledgeforge_test \
  .venv/bin/python -m pytest -q
# 64 passed, 1 skipped
```

PostgreSQL was a fresh disposable `pgvector/pgvector:0.8.2-pg17` container, not a mocked database. Its database name ends `_test`; the existing destructive-test guard remains enabled. SQLite skips PostgreSQL semantics and the combined external-service smoke test. PostgreSQL skips only the combined Redis/S3/Celery smoke test (`INTEGRATION_SERVICES` not enabled). **The entire Compose stack was not rerun for this patch.**

Twenty-two new tests cover positive, unmatched, irrelevant and partial evidence; numeric/quoted qualifiers; configurable thresholds; exact citations and untruncated text; no cross-passage pooling; current-question versus history handling; numeric-only ambiguity; no-key and mocked-provider abstention; provider context filtering; and authenticated tenant/private-document boundaries. API tests upload all five actual synthetic seed sources and check remote work, security incidents, release deployment, incident response, learning budgets and time off. PostgreSQL exercises the real FTS OR fallback and pgvector query. The vector test explicitly proves that a perfect deterministic vector match can remain searchable while still being rejected as insufficient answer evidence.

The no-key live preview was also tested with the exact Mars/2035 question and an unrelated-location variant: both returned abstention and zero citations. Remote-work and release-deployment questions returned the correct source. Playwright's existing document/chat/source, mobile, and new-account/upload/access/search flows were run against the refreshed preview; **3 passed** against the refreshed no-key production preview (no frontend source changes). No real LLM calls or charges were incurred; provider HTTP behavior uses deterministic MockTransport.

Initial new regression runs exposed a `requires`/`required` inflection mismatch; normalization/question boilerplate handling was corrected before the passing runs above. Failed intermediate tests were not counted as passes.

## Limitations

- This is a conservative English lexical gate, not semantic entailment, answer-accuracy certification or a benchmark-calibrated confidence score.
- Synonyms, translations, complex inflections, cross-passage reasoning and paraphrases may cause false abstention, including genuine semantic-only vector matches. Search still exposes authorized candidates for inspection.
- Literal numeric and phrase matching can reject alternate formats or spelled-out equivalents. Conversely, coincidental term/number overlap can still pass without proving a relationship, negation, completeness or an authoritative/current policy.
- Brief follow-up resolution is heuristic. Users may need to restate the topic explicitly.
- Candidate pools remain bounded; relevant evidence outside those bounds may be missed. Historical saved answers are not retroactively regraded.
- A real model may still make an unsupported claim with a syntactically valid citation. The gate and existing reference validation reduce risk but do not establish semantic truth. Real paid-provider verification was not performed.
