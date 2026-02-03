const fs = require("fs");
const u = process.env.VITE_API_URL || "";
const escaped = u.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
fs.writeFileSync("config.js", `window.__API_BASE__ = "${escaped}";\n`);
