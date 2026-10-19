#!/usr/bin/env python3
"""
md2wiki.py — convertit un fichier Markdown en page Wikirae (même structure
HTML que Kingdom_erel.html : en-tête + recherche, encadré .info, corps).

Usage :
  python md2wiki.py page.md                  -> fichier "output:" du front matter,
                                               sinon page.html (à côté du .md)
  python md2wiki.py page.md sortie.html      -> fichier précis (prioritaire)
  python md2wiki.py dossier_md/ [dossier_html/]   -> convertit tous les .md
  python md2wiki.py .                        -> convertit les .md du dossier courant
"""

import re
import sys
from html import escape
from pathlib import Path

DEFAULT_ICON = (
    "https://static.vecteezy.com/system/resources/thumbnails/068/811/399/"
    "small_2x/golden-sun-emblem-with-radiant-rays-and-shiny-center-design-png.png"
)
DEFAULT_FOOTER = "© 2026 Aetas Irae. Tous droits réservés."

# \w limité à l'ASCII, comme en JavaScript
A = re.ASCII

# ---------- utilitaires ----------


def esc(s):
    return escape(s, quote=False)


def inline(text):
    """Markdown « en ligne » : code, images, liens, gras, italique."""
    s = esc(text.strip())
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(^|[^*\w])\*([^*]+)\*", r"\1<em>\2</em>", s, flags=A)
    s = re.sub(r"(^|[^_\w])_([^_]+)_(?!\w)", r"\1<em>\2</em>", s, flags=A)
    return s


# Ligne contenant uniquement une image Markdown : ![alt](url)
IMG_LINE = re.compile(r"^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$")


def img_tag(m, indent):
    alt = f' alt="{esc(m.group(1))}"' if m.group(1) else ""
    return f'{indent}<img src="{esc(m.group(2))}"{alt}>'


def strip_comments(src):
    """Ignore les commentaires de fin de ligne " #texte" ou " # texte".

    Pas touchés : les titres (lignes commençant par #) et le HTML brut
    (lignes commençant par <). Écrire \\# pour obtenir un # littéral.
    """
    out = []
    for line in src.split("\n"):
        if not re.match(r"^\s*[#<]", line):
            line = re.sub(r"\s+#.*$", "", line)
        out.append(line.replace("\\#", "#"))
    return "\n".join(out)


def parse_front_matter(src):
    """Front matter YAML très simple (clé: valeur)."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", src, re.S)
    if not m:
        return {}, src
    meta = {}
    for line in re.split(r"\r?\n", m.group(1)):
        k = re.match(r"^([\w-]+):\s*(.*)$", line, A)
        if k:
            meta[k.group(1)] = re.sub(r"^[\"'](.*)[\"']$", r"\1", k.group(2))
    return meta, src[m.end():]


# ---------- blocs ::: infobox / ::: nav ----------


def parse_items(lines):
    """Découpe des lignes en éléments, dans l'ordre :
    ("table", [lignes])  pour « Clé | valeur » (« Clé | » + lignes « - item » => liste)
    ("p", [lignes])      pour le texte sans | : lignes consécutives = un paragraphe
                         (reliées par <br>), une ligne vide commence un nouveau paragraphe
    """
    items = []
    gap = False  # ligne vide rencontrée depuis le dernier élément
    for raw in lines:
        if not raw.strip():
            gap = True
            continue
        prev_gap, gap = gap, False
        tab = items[-1][1] if items and items[-1][0] == "table" else None
        li = re.match(r"^\s+[-*]\s+(.*)$", raw)
        if li and tab:
            tab[-1]["items"].append(li.group(1))
            continue
        kv = re.match(r"^([^|]+)\|\s*(.*)$", raw)
        if kv:
            row = {"key": kv.group(1).strip(), "value": kv.group(2).strip(), "items": []}
            if tab is not None:
                tab.append(row)
            else:
                items.append(("table", [row]))
        elif items and items[-1][0] == "p" and not prev_gap:
            items[-1][1].append(raw.strip())
        else:
            items.append(("p", [raw.strip()]))
    return items


def cell(row):
    if row["items"]:
        return "<ul>" + "".join(f"<li>{inline(i)}</li>" for i in row["items"]) + "</ul>"
    return inline(row["value"])


def render_infobox(lines, title, head_class):
    """Encadré :
    ( ... )         -> contenu de <div class="inftit"> (### = h3, texte = p)
    ![](url)        -> <img>   (avant le premier "## ")
    ligne de texte  -> <p>     (avant le premier "## ")
    ## Titre + lignes « Clé | valeur » -> <h2> + <table> (texte sans | => <p>)
    """
    ind = " " * 12
    sections = []
    intro = []  # éléments avant le premier "## " : ("html", str) ou ("p", [lignes])
    gap = False
    paren = None  # lignes du bloc ( ... ) en cours
    inftit = []  # éléments du bloc inftit : (balise, texte)
    cur = None
    for l in lines:
        if cur is None and paren is None and re.match(r"^\s*\(\s*$", l):
            paren = []
            continue
        if paren is not None and re.match(r"^\s*\)\s*$", l):
            gap = False
            for p in paren:
                if not p.strip():
                    gap = True
                    continue
                h = re.match(r"^(#{2,6})\s+(.*)$", p)
                if h:
                    inftit.append(("h" + str(len(h.group(1))), [h.group(2)]))
                elif inftit and inftit[-1][0] == "p" and not gap:
                    inftit[-1][1].append(p.strip())
                else:
                    inftit.append(("p", [p.strip()]))
                gap = False
            paren = None
            continue
        if paren is not None:
            paren.append(l)
            continue
        h = re.match(r"^##\s+(.*)$", l)
        if h:
            cur = {"title": h.group(1).strip(), "lines": []}
            sections.append(cur)
        elif cur is not None:
            cur["lines"].append(l)
        elif IMG_LINE.match(l):
            intro.append(("html", img_tag(IMG_LINE.match(l), ind)))
            gap = False
        elif l.strip():
            if intro and intro[-1][0] == "p" and not gap:
                intro[-1][1].append(l.strip())
            else:
                intro.append(("p", [l.strip()]))
            gap = False
        else:
            gap = True

    if not any(tag == "h2" for tag, _ in inftit):
        inftit.insert(0, ("h2", [title]))
    cls = f" {esc(head_class)}" if head_class else ""
    inftit_html = (
        f'{ind}<div class="inftit{cls}">\n'
        + "\n".join(f"{ind}    <{t}>{'<br>'.join(inline(y) for y in x)}</{t}>" for t, x in inftit)
        + f"\n{ind}</div>"
    )

    parts = [inftit_html] + [
        data if kind == "html" else f"{ind}<p>{'<br>'.join(inline(x) for x in data)}</p>"
        for kind, data in intro
    ]
    for sec in sections:
        parts.append(f"            <h2>{inline(sec['title'])}</h2>")
        for kind, data in parse_items(sec["lines"]):
            if kind == "p":
                parts.append(f"            <p>{'<br>'.join(inline(x) for x in data)}</p>")
                continue
            rows = "\n".join(
                "                <tr>\n"
                f"                    <th>{inline(r['key'])}</th>\n"
                f"                    <td>{cell(r)}</td>\n"
                "                </tr>"
                for r in data
            )
            parts.append(f"            <table>\n{rows}\n            </table>")
    return "\n".join(parts)


def render_nav(lines):
    """::: nav ... ::: -> <div class="hor_tab"> avec une sous-div par groupe.

    Une sous-div commence à chaque ligne « Titre | texte » (titre en texte simple,
    ou en <hN> si la ligne commence par ###). Le texte après « | » et les lignes suivantes forment le
    contenu : liste « - item » => <ul>, autre ligne => <p>. Les lignes vides sont
    ignorées. Sans aucune ligne-titre, une ligne = une sous-div.
    """
    ind = " " * 12
    head = re.compile(r"^\s*(#{2,6})\s+(.*)$")
    bullet = re.compile(r"^\s*[-*+]\s+")
    lines = [l for l in lines if l.strip()]
    if not lines:
        return ""

    def title_of(l):
        """(niveau, titre, reste) si la ligne ouvre une sous-div, sinon None."""
        h = head.match(l)
        if h:
            t, _, rest = h.group(2).partition("|")
            return len(h.group(1)), t.strip(), rest.strip()
        if "|" in l and not bullet.match(l):
            t, _, rest = l.partition("|")
            return 0, t.strip(), rest.strip()  # niveau 0 = titre en texte simple
        return None

    if not any(title_of(l) for l in lines):
        cells = []
        for raw in lines:
            txt = bullet.sub("", raw).strip()  # puce Markdown éventuelle
            cells.append(f"{ind}    <div>\n{ind}        {inline(txt)}\n{ind}    </div>")
        return f'{ind}<div class="hor_tab">\n' + "\n".join(cells) + f"\n{ind}</div>"

    groups = []  # {"level", "title", "lines"}
    for l in lines:
        t = title_of(l)
        if t:
            groups.append({"level": t[0], "title": t[1], "lines": [t[2]] if t[2] else []})
        elif groups:
            groups[-1]["lines"].append(l)
        else:
            groups.append({"level": 0, "title": "", "lines": [l]})

    cells = []
    for g in groups:
        inner = []
        if g["title"]:
            if g["level"]:  # "### Titre" explicite => <hN>
                inner.append(f"{ind}        <h{g['level']}>{inline(g['title'])}</h{g['level']}>")
            else:  # "Titre | ..." => texte simple
                inner.append(f"{ind}        {inline(g['title'])}")
        body = render_body(g["lines"], per_line=True)
        if body:
            inner.append("\n".join(" " * 12 + x for x in body.split("\n")))
        cells.append(f"{ind}    <div>\n" + "\n".join(inner) + f"\n{ind}    </div>")
    return f'{ind}<div class="hor_tab">\n' + "\n".join(cells) + f"\n{ind}</div>"


# ---------- corps Markdown ----------


def render_body(lines, per_line=False):
    out = []
    para = []
    lst = None  # {"type": "ul"|"ol", "items": []}
    quote = []

    def flush_para():
        nonlocal para
        if para:
            out.append(f"        <p>{'<br>'.join(inline(x) for x in para)}</p>")
        para = []

    def flush_list():
        nonlocal lst
        if lst:
            items = "\n".join(f"            <li>{inline(i)}</li>" for i in lst["items"])
            out.append(f"        <{lst['type']}>\n{items}\n        </{lst['type']}>")
        lst = None

    def flush_quote():
        nonlocal quote
        if quote:
            out.append(f"        <blockquote>{inline(' '.join(quote))}</blockquote>")
        quote = []

    def flush_all():
        flush_para()
        flush_list()
        flush_quote()

    for line in lines:
        if not line.strip():
            flush_all()
        elif (m := re.match(r"^(#{2,6})\s+(.*)$", line)):
            flush_all()
            n = len(m.group(1))
            out.append(f"        <h{n}>{inline(m.group(2))}</h{n}>")
        elif (m := re.match(r"^q\[([^\]]*)\]\((.*)\)\s*$", line)):
            # q[classe](citation | traduction | auteur)
            flush_all()
            cls = m.group(1).strip() or "quote"
            parts = [s.strip() for s in m.group(2).split("|")]
            names = ["mainquote", "transquote", "authorquote"]
            inner = "\n".join(
                f'            <div class="{names[i]}">\n'
                f"                {inline(p)}\n"
                "            </div>"
                for i, p in enumerate(parts[:3])
                if p
            )
            out.append(f'        <div class="{esc(cls)}">\n{inner}\n        </div>')
        elif (m := IMG_LINE.match(line)):
            flush_all()
            out.append(img_tag(m, " " * 8))
        elif re.match(r"^(-{3,}|\*{3,})\s*$", line):
            flush_all()
            out.append("        <hr>")
        elif (m := re.match(r"^\s*[-*+]\s+(.*)$", line)):
            flush_para()
            flush_quote()
            if not lst or lst["type"] != "ul":
                flush_list()
                lst = {"type": "ul", "items": []}
            lst["items"].append(m.group(1))
        elif (m := re.match(r"^\s*\d+[.)]\s+(.*)$", line)):
            flush_para()
            flush_quote()
            if not lst or lst["type"] != "ol":
                flush_list()
                lst = {"type": "ol", "items": []}
            lst["items"].append(m.group(1))
        elif (m := re.match(r"^>\s?(.*)$", line)):
            flush_para()
            flush_list()
            quote.append(m.group(1))
        elif line.strip().startswith("<"):
            flush_all()
            out.append("        " + line.strip())  # HTML brut conservé tel quel
        else:
            flush_list()
            flush_quote()
            para.append(line.strip())
            if per_line:
                flush_para()  # une ligne = un élément
    flush_all()
    return "\n".join(out)


# ---------- page complète ----------


def convert(src):
    """Retourne (html, meta)."""
    meta, body = parse_front_matter(strip_comments(src.replace("\r\n", "\n")))

    # Sépare les blocs ::: nom ... ::: du reste (les blocs peuvent être imbriqués,
    # ex. un bloc nav dans un bloc infobox ; ":::" seul ferme le dernier ouvert)
    body_lines = []
    blocks = []  # (type, lignes)
    stack = []
    for line in body.split("\n"):
        opening = re.match(r"^:::\s*(\w+)\s*$", line, A)
        if opening:
            stack.append((opening.group(1), []))
        elif stack and re.match(r"^:::\s*$", line):
            blocks.append(stack.pop())
        else:
            (stack[-1][1] if stack else body_lines).append(line)
    while stack:  # blocs non fermés
        blocks.append(stack.pop())

    title = meta.get("title") or meta.get("titre") or "Sans titre"
    lang = meta.get("lang", "fr")
    icon = meta.get("icon", DEFAULT_ICON)
    footer = meta.get("footer", DEFAULT_FOOTER)
    css = meta.get("css", "style.css")
    head_class = meta.get("heading-class") or meta.get("classe") or ""

    # Encadré latéral (le bloc inftit est toujours généré, titre = title)
    boxes = [b for b in blocks if b[0] == "infobox"] or [("infobox", [])]
    info = [render_infobox(b[1], title, head_class) for b in boxes]
    info += [render_nav(b[1]) for b in blocks if b[0] in ("nav", "hor_tab")]
    info_html = "\n".join(x for x in info if x)

    html = f"""<!DOCTYPE html>
<html lang="{lang}">


<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>
    <link rel="stylesheet" href="{esc(css)}">
    <link rel="icon"
        href="{esc(icon)}">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+SC:wght@300;400;500;600;700&display=swap');
    </style>


</head>


<body>


    <div class="head">
        <h1>{inline(title)}</h1>
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
{info_html}
        </div>
{render_body(body_lines)}
        <p class="footerp">{esc(footer)}</p>
    </div>
</body>


</html>
"""
    return html, meta


# ---------- ligne de commande ----------


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage : python md2wiki.py <fichier.md|dossier> [sortie.html|dossier]",
              file=sys.stderr)
        sys.exit(1)
    entree = Path(args[0])
    sortie = Path(args[1]) if len(args) > 1 else None

    if entree.is_dir():
        dossier_sortie = sortie or entree
        dossier_sortie.mkdir(parents=True, exist_ok=True)
        for f in sorted(entree.glob("*.md")):
            html, meta = convert(f.read_text(encoding="utf-8"))
            dest = dossier_sortie / (meta.get("output") or f.with_suffix(".html").name)
            dest.write_text(html, encoding="utf-8", newline="\n")
            print("✔", dest)
    else:
        html, meta = convert(entree.read_text(encoding="utf-8"))
        # priorité : argument > "output" du front matter > nom du .md
        if sortie:
            dest = sortie
        elif meta.get("output"):
            dest = entree.parent / meta["output"]
        else:
            dest = entree.with_suffix(".html")
        dest.write_text(html, encoding="utf-8", newline="\n")
        print("✔", dest)


if __name__ == "__main__":
    main()
