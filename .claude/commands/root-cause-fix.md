---
description: Root-cause-first TDD loop for a bug or data fix.
---

Fix the reported problem at its root, not at its symptom.

1. Write a failing reproduction test FIRST, before touching any production code.
   Run it and paste the failure.
2. Find the root cause. State it in one sentence.
3. Grep for every sibling case sharing that same root cause - other callers,
   other modes, duplicate code paths. Cite file and line for each. A narrow
   first fix that misses siblings is the normal failure mode here.
4. Add a test covering each sibling.
5. Write the minimal fix.
6. Run the tier-appropriate suite and report the exact counts.
7. Check for already-corrupted data. A fix that only prevents future occurrences
   leaves existing bad rows wrong. Plan and run the backfill in this same
   change, and verify the historical rows are corrected.
