const pages = [
    {
        nom: "Accueil",
        fichier: "index.html"
    },
    {
        nom: "Lydion Oldkingd",
        fichier: "Lydion-oldkingd.html"
    },
    {
        nom: "Royaume des Anciens",
        fichier: "royaume-des-anciens.html"
    },
    {
        nom: "Cormorant",
        fichier: "cormorant.html"
    }
];

const input = document.getElementById("search");
const suggestions = document.getElementById("suggestions");
const form = document.getElementById("searchForm");

input.addEventListener("input", function () {
    const recherche = input.value.trim().toLowerCase();

    suggestions.innerHTML = "";

    if (recherche === "") {
        suggestions.style.display = "none";
        return;
    }

    const resultats = pages.filter(page =>
        page.nom.toLowerCase().includes(recherche)
    );

    resultats.forEach(page => {
        const element = document.createElement("li");

        element.textContent = page.nom;
        element.setAttribute("role", "option");

        element.addEventListener("click", function () {
            input.value = page.nom;
            window.location.href = page.fichier;
        });

        suggestions.appendChild(element);
    });

    suggestions.style.display =
        resultats.length > 0 ? "block" : "none";
});

form.addEventListener("submit", function (event) {
    event.preventDefault();

    const recherche = input.value.trim().toLowerCase();

    const page = pages.find(page =>
        page.nom.toLowerCase() === recherche
    );

    if (page) {
        window.location.href = page.fichier;
    } else {
        window.location.href =
            "recherche.html?q=" + encodeURIComponent(input.value);
    }
});

document.addEventListener("click", function (event) {
    if (!event.target.closest(".search-box")) {
        suggestions.style.display = "none";
    }
});