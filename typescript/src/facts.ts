import {canonicalizeFacts} from "./facts-canonical.js";
import {
  extractRawFacts,
  extractReconstructedRawFacts,
} from "./facts-extract.js";
import type {ExtractFactsInput, ExtractFactsResult} from "./types.js";

export function extractFacts(input: ExtractFactsInput): ExtractFactsResult {
  const raw = extractRawFacts(input);
  return {
    raw,
    canonical: canonicalizeFacts(raw),
  };
}

export function extractReconstructedFacts(
  input: ExtractFactsInput,
): ExtractFactsResult {
  const raw = extractReconstructedRawFacts(input);
  return {
    raw,
    canonical: canonicalizeFacts(raw),
  };
}
