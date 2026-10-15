// reference-js.mjs — a reference implementation of fold_bout_2 in JS
// (using the SuperInstance/gitpp-js port as the base)
//
// Usage:
//   import { fold_bout_2 } from './reference-js.mjs';
//   const result = await fold_bout_2(records, "task-c", pinnedRoot);
//
// Or directly:
//   node reference-js.mjs <records-file-or-url> <at> <pinnedRoot>

import { derive, closureRoot } from "/tmp/gitpp-js-clone/src/gitpp.js";

export async function fold_bout_2(records, at, pinned) {
  // 1. Compute the closure and root
  const root = await closureRoot(records, at);
  
  // 2. Compute the state
  const d = derive(records);
  
  // 3. Decide the verdict
  let verdict;
  let reason;
  if (root === null) {
    // Missing root: closure was incomplete
    verdict = "MISMATCH";
    reason = "closure incomplete";
  } else if (root === pinned) {
    // Root matches pinned
    verdict = "VERIFIED";
  } else {
    // Root differs from pinned
    verdict = "MISMATCH";
    reason = "root differs from pinned";
  }
  
  return {
    verdict,
    state: d.state,
    conflicts: d.conflicts,
    root,
    pinned,
    reason,
  };
}

// CLI mode
if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , recordsArg, at, pinned] = process.argv;
  let records;
  if (recordsArg.startsWith("https://")) {
    const r = await fetch(recordsArg);
    const j = await r.json();
    records = j.records;
  } else {
    const { readFile } = await import("node:fs/promises");
    records = JSON.parse(await readFile(recordsArg, "utf8"));
  }
  const result = await fold_bout_2(records, at, pinned);
  console.log(JSON.stringify(result, null, 2));
}
