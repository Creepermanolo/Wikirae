#!/usr/bin/env node
/**
 * md2wiki.js — convertit un fichier Markdown en page Wikirae (même structure
 * HTML que Kingdom_erel.html : en-tête + recherche, encadré .info, corps).
 *
 * Usage :
 *   node md2wiki.js page.md                 -> fichier "output:" du front matter,
 *                                              sinon page.html (à côté du .md)
 *   node md2wiki.js page.md sortie.html     -> fichier précis (prioritaire)
 *   node md2wiki.js dossier_md/ [dossier_html/]   -> convertit tous les .md
 */
const fs = require('fs');
const path = require('path');

const DEFAULT_ICON =
  'https://static.vecteezy.com/system/resources/thumbnails/068/811/399/small_2x/golden-sun-emblem-with-radiant-rays-and-shiny-center-design-png.png';
const DEFAULT_FOOTER = '© 2026 Aetas Irae. Tous droits réservés.';

/* ---------- utilitaires ---------- */

const esc = (s) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Markdown "en ligne" : liens, images, gras, italique, code
function inline(text) {
  let s = esc(text.trim());
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, '<img src="$2" alt="$1">');
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*\w])\*([^*]+)\*/g, '$1<em>$2</em>');
  s = s.replace(/(^|[^_\w])_([^_]+)_(?!\w)/g, '$1<em>$2</em>');
  return s;
}

// Ligne contenant uniquement une image Markdown : ![alt](url)
const IMG_LINE = /^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$/;
const imgTag = (m, indent) =>
  `${indent}<img src="${esc(m[2])}"${m[1] ? ` alt="${esc(m[1])}"` : ''}>`;

// Commentaires de fin de ligne : " #texte" ou " # texte" sont ignorés.
// Pas touchés : les titres (lignes commençant par #), le HTML brut (lignes
// commençant par <) et les "\#" (écrire \# pour obtenir un # littéral).
function stripComments(src) {
  return src
    .split('\n')
    .map((l) =>
      /^\s*[#<]/.test(l) ? l.replace(/\\#/g, '#') : l.replace(/\s+#.*$/, '').replace(/\\#/g, '#')
    )
    .join('\n');
}

// Front matter YAML très simple (clé: valeur)
function parseFrontMatter(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!m) return { meta: {}, body: src };
  const meta = {};
  for (const line of m[1].split(/\r?\n/)) {
    const k = line.match(/^([\w-]+):\s*(.*)$/);
    if (k) meta[k[1]] = k[2].replace(/^["'](.*)["']$/, '$1');
  }
  return { meta, body: src.slice(m[0].length) };
}

/* ---------- blocs ::: infobox / ::: nav ---------- */

// Lignes "Clé | valeur" ; "Clé |" suivi de lignes indentées "- item" => liste
function parseRows(lines) {
  const rows = [];
  for (const raw of lines) {
    if (!raw.trim()) continue;
    const item = raw.match(/^\s+[-*]\s+(.*)$/);
    if (item && rows.length) {
      rows[rows.length - 1].items.push(item[1]);
      continue;
    }
    // "Clé | valeur" (l'ancien "Clé: valeur" reste accepté si la ligne n'a pas de |)
    const kv = raw.match(/^([^|]+)\|\s*(.*)$/) || (!raw.includes('|') && raw.match(/^([^:]+):\s*(.*)$/));
    if (kv) rows.push({ key: kv[1].trim(), value: kv[2].trim(), items: [] });
  }
  return rows;
}

function cell(row) {
  if (row.items.length) {
    return (
      '<ul>' + row.items.map((i) => `<li>${inline(i)}</li>`).join('') + '</ul>'
    );
  }
  return inline(row.value);
}

// Encadré :
//   ( ... )          -> contenu de <div class="inftit"> (### = h3, texte = p)
//   ![](url)         -> <img>          (avant le premier "## ")
//   ligne de texte   -> <p>            (avant le premier "## ")
//   ## Titre + lignes "Clé: valeur" -> <h2> + <table>
function renderInfobox(lines, title, headClass) {
  const I = '            ';
  const sections = [];
  const intro = []; // html des éléments avant le premier "## "
  let paren = null; // lignes du bloc ( ... ) en cours
  let inftit = []; // éléments du bloc inftit [{ tag, text }]
  let cur = null;
  for (const l of lines) {
    if (!cur && paren === null && /^\s*\(\s*$/.test(l)) { paren = []; continue; }
    if (paren !== null && /^\s*\)\s*$/.test(l)) {
      for (const p of paren) {
        if (!p.trim()) continue;
        const h = p.match(/^(#{2,6})\s+(.*)$/);
        inftit.push(h ? { tag: 'h' + h[1].length, text: h[2] } : { tag: 'p', text: p });
      }
      paren = null;
      continue;
    }
    if (paren !== null) { paren.push(l); continue; }
    const h = l.match(/^##\s+(.*)$/);
    if (h) {
      cur = { title: h[1].trim(), lines: [] };
      sections.push(cur);
    } else if (cur) cur.lines.push(l);
    else if (IMG_LINE.test(l)) intro.push(imgTag(l.match(IMG_LINE), I));
    else if (l.trim()) intro.push(`${I}<p>${inline(l)}</p>`);
  }
  if (!inftit.some((e) => e.tag === 'h2')) inftit.unshift({ tag: 'h2', text: title });
  const inftitHtml =
    `${I}<div class="inftit${headClass ? ' ' + esc(headClass) : ''}">\n` +
    inftit.map((e) => `${I}    <${e.tag}>${inline(e.text)}</${e.tag}>`).join('\n') +
    `\n${I}</div>`;
  const introHtml = [inftitHtml, ...intro];
  const sectionsHtml = sections.map((sec) => {
    const rows = parseRows(sec.lines)
      .map(
        (r) =>
          `                <tr>\n                    <th>${inline(r.key)}</th>\n                    <td>${cell(r)}</td>\n                </tr>`
      )
      .join('\n');
    return `            <h2>${inline(sec.title)}</h2>\n            <table>\n${rows}\n            </table>`;
  });
  return [...introHtml, ...sectionsHtml].join('\n');
}

function renderNav(lines) {
  const rows = parseRows(lines);
  if (!rows.length) return '';
  const ths = rows.map((r) => `                    <th>${inline(r.key)}</th>`).join('\n');
  const tds = rows.map((r) => `                    <td>${cell(r)}</td>`).join('\n');
  return `            <table class="chr">\n                <tr>\n${ths}\n                </tr>\n                <tr>\n${tds}\n                </tr>\n            </table>`;
}

/* ---------- corps Markdown ---------- */

function renderBody(lines) {
  const out = [];
  let para = [];
  let list = null; // { type: 'ul'|'ol', items: [] }
  let quote = [];

  const flushPara = () => {
    if (para.length) out.push(`        <p>${inline(para.join(' '))}</p>`);
    para = [];
  };
  const flushList = () => {
    if (list) {
      out.push(
        `        <${list.type}>\n` +
          list.items.map((i) => `            <li>${inline(i)}</li>`).join('\n') +
          `\n        </${list.type}>`
      );
    }
    list = null;
  };
  const flushQuote = () => {
    if (quote.length) out.push(`        <blockquote>${inline(quote.join(' '))}</blockquote>`);
    quote = [];
  };
  const flushAll = () => {
    flushPara();
    flushList();
    flushQuote();
  };

  for (const line of lines) {
    let m;
    if (!line.trim()) {
      flushAll();
    } else if ((m = line.match(/^(#{2,6})\s+(.*)$/))) {
      flushAll();
      out.push(`        <h${m[1].length}>${inline(m[2])}</h${m[1].length}>`);
    } else if ((m = line.match(/^q\[([^\]]*)\]\((.*)\)\s*$/))) {
      // q[classe](citation | traduction | auteur)
      flushAll();
      const cls = m[1].trim() || 'quote';
      const parts = m[2].split('|').map((s) => s.trim());
      const names = ['mainquote', 'transquote', 'authorquote'];
      out.push(
        `        <div class="${esc(cls)}">\n` +
          parts
            .slice(0, 3)
            .map((p, i) =>
              p
                ? `            <div class="${names[i]}">\n                ${inline(p)}\n            </div>`
                : ''
            )
            .filter(Boolean)
            .join('\n') +
          `\n        </div>`
      );
    } else if ((m = line.match(IMG_LINE))) {
      flushAll();
      out.push(imgTag(m, '        '));
    } else if (/^(-{3,}|\*{3,})\s*$/.test(line)) {
      flushAll();
      out.push('        <hr>');
    } else if ((m = line.match(/^\s*[-*+]\s+(.*)$/))) {
      flushPara();
      flushQuote();
      if (!list || list.type !== 'ul') { flushList(); list = { type: 'ul', items: [] }; }
      list.items.push(m[1]);
    } else if ((m = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
      flushPara();
      flushQuote();
      if (!list || list.type !== 'ol') { flushList(); list = { type: 'ol', items: [] }; }
      list.items.push(m[1]);
    } else if ((m = line.match(/^>\s?(.*)$/))) {
      flushPara();
      flushList();
      quote.push(m[1]);
    } else if (/^</.test(line.trim())) {
      flushAll();
      out.push('        ' + line.trim()); // HTML brut conservé tel quel
    } else {
      flushList();
      flushQuote();
      para.push(line.trim());
    }
  }
  flushAll();
  return out.join('\n');
}

/* ---------- page complète ---------- */

function convert(src) {
  const { meta, body } = parseFrontMatter(stripComments(src.replace(/\r\n/g, '\n')));

  // Sépare les blocs ::: ... ::: du reste
  const bodyLines = [];
  const blocks = []; // { type, lines }
  let cur = null;
  for (const line of body.split('\n')) {
    const open = line.match(/^:::\s*(\w+)\s*$/);
    if (!cur && open) { cur = { type: open[1], lines: [] }; continue; }
    if (cur && /^:::\s*$/.test(line)) { blocks.push(cur); cur = null; continue; }
    (cur ? cur.lines : bodyLines).push(line);
  }

  const title = meta.title || meta.titre || 'Sans titre';
  const lang = meta.lang || 'fr';
  const icon = meta.icon || DEFAULT_ICON;
  const footer = meta.footer || DEFAULT_FOOTER;
  const css = meta.css || 'style.css';

  // Encadré latéral (le bloc inftit est toujours généré, titre = title)
  const info = [];
  const headClass = meta['heading-class'] || meta.classe || '';
  const boxes = blocks.filter((b) => b.type === 'infobox');
  if (!boxes.length) boxes.push({ type: 'infobox', lines: [] });
  for (const b of boxes) info.push(renderInfobox(b.lines, title, headClass));
  for (const b of blocks) {
    if (b.type === 'nav') info.push(renderNav(b.lines));
  }

  const html = `<!DOCTYPE html>
<html lang="${lang}">


<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${esc(title)}</title>
    <link rel="stylesheet" href="${esc(css)}">
    <link rel="icon"
        href="${esc(icon)}">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+SC:wght@300;400;500;600;700&display=swap');
    </style>


</head>


<body>


    <div class="head">
        <h1>${inline(title)}</h1>
        <form id="searchForm" autocomplete="off">
            <div class="search-line">
                
                <div class="search-box">
                    <span class="search-icon">⌕</span>


                    <input type="search" id="search" placeholder="Rechercher sur Wikirae" aria-autocomplete="list"
                        aria-controls="suggestions" required>


                    <ul id="suggestions" role="listbox"></ul>
                </div>
                <button type="submit">Rechercher</button>
            </div>
        </form>


        <script src="recherche.js"></script>
    </div>
    <div class="main">
        <div class="info">
${info.join('\n')}
        </div>
${renderBody(bodyLines)}
        <p class="footerp">${esc(footer)}</p>
    </div>
</body>


</html>
`;
  return { html, meta };
}

/* ---------- CLI ---------- */

function main() {
  const [input, output] = process.argv.slice(2);
  if (!input) {
    console.error('Usage : node md2wiki.js <fichier.md|dossier> [sortie.html|dossier]');
    process.exit(1);
  }
  if (fs.statSync(input).isDirectory()) {
    const outDir = output || input;
    fs.mkdirSync(outDir, { recursive: true });
    for (const f of fs.readdirSync(input).filter((f) => f.endsWith('.md'))) {
      const { html, meta } = convert(fs.readFileSync(path.join(input, f), 'utf8'));
      const dest = path.join(outDir, meta.output || f.replace(/\.md$/, '.html'));
      fs.writeFileSync(dest, html);
      console.log('✔', dest);
    }
  } else {
    const { html, meta } = convert(fs.readFileSync(input, 'utf8'));
    // priorité : argument CLI > "output" du front matter > nom du .md
    const dest =
      output ||
      (meta.output
        ? path.join(path.dirname(input), meta.output)
        : input.replace(/\.md$/i, '.html'));
    fs.writeFileSync(dest, html);
    console.log('✔', dest);
  }
}

if (require.main === module) main();
module.exports = { convert };
