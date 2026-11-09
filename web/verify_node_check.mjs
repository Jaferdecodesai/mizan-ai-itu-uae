import { readFileSync } from "node:fs";
import { webcrypto } from "node:crypto";
import { verifyChain } from "./assets/chain.js";
const lines = readFileSync(process.argv[2], "utf8").split("\n").filter(Boolean);
const r = await verifyChain(lines, webcrypto.subtle);
console.log(r.ok ? `OK ${r.records}` : `FAIL ${JSON.stringify(r)}`);
