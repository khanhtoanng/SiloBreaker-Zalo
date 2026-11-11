# Scorer status: PROXY — official parity UNKNOWN

The local organizer archive has a schema validator but no scorer. The evaluator
implements the participant-reported outline in the handoff with explicit choices:

1. Empty gold scores one only when prediction is empty. Hash match is still
   reported, but this special-case proxy score does not gate on it.
2. Nonempty gold scores zero on a differing gold-replay final SDK hash.
3. Otherwise, maximum bipartite one-to-one matching gives call F1. Duplicate calls
   retain multiplicity; matching ignores position. Execution remains ordered.
4. Calls match names and equal argument key sets. Values compare recursively;
   x-match:fuzzy strings use NFC, lowercase, whitespace-token multiset F1 >0.6.
   No punctuation removal or undocumented optional-field equivalence is inferred.
5. Missing, duplicate, extra or reordered prediction rows fail integrity checks.
   They are never turned into empty predictions.

Fixtures cover zero matches, both empty, nonempty/wrong hash, duplicate
multiplicity, extra reads, unordered calls, argument-key mismatch, differing text
with equal state hash, fuzzy threshold equality and a matching graph where greedy
matching would fail. ASK uses ordinary call matching. Gold reference hashes come
from separate authorized train replay and require the same manifest fingerprint.

**OBSERVED:** A label-derived identity fixture over 1,545 rows returned 100.0
PROXY and 1.0 hash match, as expected by construction. This verifies consistency
only. It is not an inference run, baseline accuracy, leaderboard result or parity
test. No model quality number is available yet.
