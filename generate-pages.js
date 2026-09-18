const fs = require("fs");
const path = require("path");

const dossier = __dirname;

const fichiersExclus = [
    "recherche.html"
];

function extraireTitre(contenu, nomFichier) {
    const correspondance = contenu.match(
        /<title[^>]*>([\s\S]*?)<\/title>/i
    );

    if (correspondance) {
        return correspondance[1]
            .replace(/\s+/g, " ")
            .trim();
    }

    return path.basename(nomFichier, ".html");
}

const pages = fs.readdirSync(dossier)
    .filter(nom => nom.toLowerCase().endsWith(".html"))
    .filter(nom => !fichiersExclus.includes(nom))
    .map(nom => {
        const chemin = path.join(dossier, nom);
        const contenu = fs.readFileSync(chemin, "utf8");

        return {
            nom: extraireTitre(contenu, nom),
            fichier: nom
        };
    })
    .sort((a, b) => a.nom.localeCompare(b.nom, "fr"));

const fichierSortie = path.join(dossier, "pages.json");

fs.writeFileSync(
    fichierSortie,
    JSON.stringify(pages, null, 4),
    "utf8"
);

console.log(
    `${pages.length} page(s) enregistrée(s) dans ${fichierSortie}`
);