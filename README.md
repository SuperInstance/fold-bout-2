# fold-bout-2

> Bout 2: head-to-head implementation of the §6 retraction doctrine. The first bout (fold-bout#1) was about implementing the deterministic fold. This bout is about implementing the *retraction* half: how a fold port surfaces tamper, what it returns, and how it is scored against the SANITY-CHECK.

## What is the §6 doctrine?

The §6 doctrine (formalized in `quilt-research-canons/research/retraction-doctrine-2026-10-15/DOCTRINE.md`) answers the question: when the closure root at a record does not match the pinned closure root, what does the fold port return?

**Option II (recommended)**: The port returns `{ verdict: "MISMATCH", state, conflicts, root: <computed>, pinned: <expected> }`. The captain signs the settlement. The port does *not* mutate the state, does *not* attempt to "fix" the discrepancy, and does *not* lie about the divergence.

This bout is a fold-port-vs-fold-port competition on how well a port implements Option II. The SANITY-CHECK in the doctrine document provides four scenarios that probe the doctrine's load-bearing rules.

## The four scenarios (from SANITY-CHECK.md)

1. **VERIFIED**: closure root matches the pinned value exactly. Port returns `verdict: "VERIFIED"`. State is the live state.
2. **STATE-ONLY**: closure root matches, but the requested state subset (e.g. `state.config.timeout`) matches. Port returns `verdict: "STATE-ONLY"` (the state is the same but the root isn't; the captain can see both).
3. **MISMATCH**: closure root differs. Port returns `verdict: "MISMATCH"`, includes both roots, and *does not* attempt to repair.
4. **missing-root**: the closure root cannot be computed (incomplete closure). Port returns `verdict: "MISMATCH"`, `root: null`, and explains the closure is incomplete.

## Scoring

Each port is judged by a single number: the number of scenarios it returns the correct verdict for. A port that returns the wrong verdict on any scenario is "off"; a port that mutates state is "broken"; a port that lies is "fired."

The four scenarios are not unit tests in the traditional sense — they are *scenarios* that exercise the doctrine's load-bearing rules. The exact behavior of the port (the shape of the returned object, the names of the verdict strings) is up to the port author; the scoring is on whether the *intent* of the doctrine is preserved.

## The four ports (so far)

| Port | Lang | Author | Status |
|------|------|--------|--------|
| `git.pp-ng` (referee) | TypeScript | Casey | reference |
| `gitpp-beam` | Elixir | Casey | implemented |
| `git.pp-ng/referee/` | Python | Casey | implemented |
| `gitpp-js` | JavaScript | Mavis (this session) | implemented |

## How to compete

1. Fork this repo.
2. Implement the `fold_bout_2.py` (or `.ts`, `.exs`, `.js`) function: takes a record set and a pinned root, returns `{ verdict, state, conflicts, root, pinned }`.
3. Add a `score.py` (or equivalent) that runs your port against the four scenarios and prints the score.
4. Open a PR; the CI runs the canonical four scenarios and posts a comment with the score.

The first port to score 4/4 against the four scenarios is the winner. The winner's name is added to `WINNERS.md`.
