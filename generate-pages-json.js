// generate-pages-json.js
const fs = require("fs");
const path = require("path");

// Mets "docs" à la place de "." si ton site GitHub Pages est dans /docs
const dir = ".";

const files = fs
  .readdirSync(dir)
  .filter(f => f.endsWith(".html") && f !== "recherche.html");

fs.writeFileSync(
  path.join(dir, "pages.json"),
  JSON.stringify(files, null, 2)
);

console.log("pages.json généré :", files);