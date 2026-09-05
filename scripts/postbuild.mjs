import { copyFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

/**
 * Η εφαρμογή έχει διαδρομές που δεν αντιστοιχούν σε αρχεία, οπότε σε στατικό
 * hosting χωρίς rewrite (Plesk, Apache χωρίς AllowOverride) ένα refresh στη
 * /diadikasia δίνει 404. Γράφουμε το index.html και σε πραγματικό αρχείο ανά
 * διαδρομή, ώστε ο server να το βρίσκει χωρίς καμία ρύθμιση.
 */
const routes = ["diadikasia"];
const dist = "dist";
const source = join(dist, "index.html");

for (const route of routes) {
  mkdirSync(join(dist, route), { recursive: true });
  copyFileSync(source, join(dist, route, "index.html"));
}

// Fallback για ό,τι άλλο ζητηθεί, όπου ο server το υποστηρίζει.
copyFileSync(source, join(dist, "404.html"));

console.log(`postbuild: ${routes.length + 1} αρχεία διαδρομών`);
