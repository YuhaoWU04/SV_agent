# Changelog

## 1.2.0 — 2026-10-13

- Add `sv-fst-screen`: scikit-allel Hudson Fst, population-label permutations,
  BH-FDR, Fst-first eligible top-k selection, candidate JSON and runner manifests.
- Explain statistical methods and candidate ranks through English statistical
  context; retain population call rates as input observations rather than
  mechanically generated artifact-risk findings.
- Add ENCODE cCRE, GeneHancer, regional GTEx eQTL/sQTL context and reference
  mappability to the fixed evidence baseline. Preserve query scope and limitations.
- Expand dbVar detail retrieval without inferring numeric copy numbers from SV type.
  Fetch available PubMed abstracts and retain explicit partial/error states.
- Keep the full evidence store and provide bounded, deterministic verifier lookup
  and search. Bind both text and structured-tool verdicts to original synthesis claims.
- Require verifier approval for published evidence gaps and limitations. Retain
  qualified low-confidence hypotheses without promoting them to established facts.
- Record model and statistical context in reports. Mark failed, partial or
  explicitly truncated retrieval incomplete while preserving supported findings.
- Preserve VCF INFO descriptions and add deterministic fallback dictionaries.
  Provide synthesis/verifier with read-only, ambiguity-triggered INFO lookup.
- Add optional LiteLLM/local-model configuration and resume checks for backend/server.
  The default Gemini model is `gemini-3.5-flash`.
- Consolidate source metrics and repetitive collection/assembly logic; add malformed
  input, API-response, metadata and offline agent-flow regression tests.

Existing saved inputs and reports are not rewritten by this release. The v1.1.1
reference run remains a historical example. Default report and runner versions now
follow the package version; explicitly versioned older reports remain readable.

## 1.1.1

Previous package version at commit `aa70304` (MIT license update).
