#!/usr/bin/env python3
"""
Générateur de fichier HTML pour Wikirae
Usage: python generateur_html.py --title "Nom de la page"
"""

import argparse
from pathlib import Path


def generate_html(title):
    """Génère le contenu HTML avec le titre spécifié."""
    
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
            <div class="inftit">
                <h2>{title}</h2>
                <h3></h3>
                <p></p>
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
        titre = input("Code de la page : ").strip()

        if titre=="n":
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

        try:
            fichier.write_text(generate_html(input("Titre de la page : ")), encoding="utf-8")
            print(f"Fichier sauvegardé : {fichier.resolve()}")
        except OSError as erreur:
            print(f"Erreur lors de la sauvegarde : {erreur}")


sauvegarder_html()