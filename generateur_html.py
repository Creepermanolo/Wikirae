#!/usr/bin/env python3
"""
Générateur de fichier HTML pour Wikirae
Usage: python generateur_html.py
Pour chaque page, le script demande :
  - le code (nom du fichier, sans .html)
  - le titre de la page
  - les lignes de <div class="inftit"> : classes, nom (h2), sous-titre (h3), dates (p)
Entrée vide = valeur par défaut / champ laissé vide.
"""

from html import escape
from pathlib import Path


def generate_html(title, classes="", nom="", sous_titre="", dates=""):
    """Génère le contenu HTML avec le titre et l'encadré inftit spécifiés."""

    title = escape(title, quote=False)
    nom = escape(nom or title, quote=False)
    sous_titre = escape(sous_titre, quote=False)
    dates = escape(dates, quote=False)
    classes = escape(" ".join(classes.split()), quote=True)

    # class="inftit" + classes supplémentaires éventuelles (ex. "imperium gold")
    inftit_class = f"inftit {classes}" if classes else "inftit"

    html_content = f'''<!DOCTYPE html>
<html lang="en">


<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
    <link rel="icon"
        href="https://static.vecteezy.com/system/resources/thumbnails/068/811/399/small_2x/golden-sun-emblem-with-radiant-rays-and-shiny-center-design-png.png">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+SC:wght@300;400;500;600;700&display=swap');
    </style>


</head>


<body>


    <div class="head">
    <h1>{title}</h1>
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
            <div class="{inftit_class}">
                <h2>{nom}</h2>
                <h3>{sous_titre}</h3>
                <p>{dates}</p>
            </div>
            <h2>Description</h2>
            <table>
                <tr>
                    <th>Devises</th>
                    <td>(Voir citations)</td>
                </tr>
                <tr>
                    <th>Fête Nationale</th>
                    <td></td>
                </tr>
            </table>
            <h2>Administration</h2>
            <table>
                <tr>
                    <th></th>
                    <td>
                        <ul>
                            <li></li>
                        </ul>
                    </td>
                </tr>
                <tr>
                    <th>Forme</th>
                    <td></td>
                </tr>
            </table>
        </div>
    </div>
</body>


</html>'''

    return html_content


def sauvegarder_html():
    while True:
        titre = input("Code de la page (n pour quitter) : ").strip()

        if titre == "n":
            break

        if not titre:
            print("Erreur : le code ne peut pas être vide.")
            return

        fichier = Path(f"{titre}.html")

        if fichier.exists():
            confirmation = input(
                f"{fichier.name} existe déjà. Remplacer ? (o/n) : "
            ).strip().lower()

            if confirmation not in ("o", "oui"):
                print("Sauvegarde annulée.")
                return

        titre_page = input("Titre de la page : ").strip()

        # Lignes de <div class="inftit ...">
        classes = input("Classes de inftit (ex. imperium gold, vide = aucune) : ").strip()
        nom = input(f"Nom <h2> (vide = {titre_page}) : ").strip()
        sous_titre = input("Sous-titre <h3> (ex. Imperium Sanctus) : ").strip()
        dates = input("Dates <p> (ex. 1 - 705) : ").strip()

        try:
            fichier.write_text(
                generate_html(titre_page, classes, nom, sous_titre, dates),
                encoding="utf-8",
            )
            print(f"Fichier sauvegardé : {fichier.resolve()}")
        except OSError as erreur:
            print(f"Erreur lors de la sauvegarde : {erreur}")


if __name__ == "__main__":
    sauvegarder_html()
