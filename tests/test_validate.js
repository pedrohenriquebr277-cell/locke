const assert = require("assert");
const V = require("../web/js/validate.js");

const dom = (s) => V.normalizeDomain(s);
assert.strictEqual(dom("https://www.YouTube.com/watch?v=1").value, "youtube.com");
assert.strictEqual(dom("  http://user:pw@reddit.com:8080/r/x ").value, "reddit.com");
assert.strictEqual(dom("x.com").value, "x.com");
assert.strictEqual(dom("news.ycombinator.com/").value, "news.ycombinator.com");
["", "abc", "-a.com", "a..com", "exa mple.com", "a.c", "http://"].forEach((s) => assert.strictEqual(dom(s).ok, false, s));

const exe = (s) => V.normalizeExe(s);
assert.strictEqual(exe("C:\\Program Files\\Discord\\Discord.exe").value, "discord.exe");
assert.strictEqual(exe('"steam"').value, "steam.exe");
assert.strictEqual(exe("a.txt").ok, false);
assert.strictEqual(exe("").ok, false);

assert.strictEqual(V.checkDuration(8 * 3600).ok, true);
assert.strictEqual(V.checkDuration(8 * 3600 + 1).ok, false);
assert.strictEqual(V.checkDuration(0).ok, false);
assert.strictEqual(V.customSeconds("1", "30"), 5400);
assert.strictEqual(V.customSeconds("", "25"), 1500);
assert.strictEqual(V.formatClock(3725), "01:02:05");
assert.strictEqual(V.formatClock(-4), "00:00:00");
assert.strictEqual(V.formatDuration(5400), "1 h 30 min");
assert.strictEqual(V.hasItem(["a.com"], "A.com"), true);

console.log("validate.js ok");
