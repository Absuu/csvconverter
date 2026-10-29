import csv
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# En-tête du format de sortie (template.csv)
SORTIE = ["name", "url", "login", "password", "otp"]

# Pour chaque format source : correspondance colonne_sortie -> colonne_source
# (None = pas d'équivalent, la colonne reste vide)
FORMATS = {
    "Google Chrome": {
        "name": "name", "url": "url", "login": "username",
        "password": "password", "otp": None,
    },
    "Microsoft Edge": {
        "name": "name", "url": "url", "login": "username",
        "password": "password", "otp": None,
    },
    "Mozilla Firefox": {
        "name": "url", "url": "url", "login": "username",
        "password": "password", "otp": None,
    },
    "KeePass": {
        "name": "Account", "url": "Web Site", "login": "Login Name",
        "password": "Password", "otp": None,
    },
}


def lire_csv(chemin):
    """Lit un CSV en gérant l'encodage et le séparateur automatiquement."""
    contenu = None
    for encodage in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(chemin, "r", encoding=encodage, newline="") as f:
                contenu = f.read()
            break
        except UnicodeDecodeError:
            continue
    if contenu is None:
        raise ValueError("Impossible de lire le fichier (encodage inconnu).")

    premiere_ligne = contenu.splitlines()[0] if contenu else ""
    separateur = ";" if premiere_ligne.count(";") > premiere_ligne.count(",") else ","
    return list(csv.DictReader(io.StringIO(contenu), delimiter=separateur))


def convertir(chemin_entree, chemin_sortie, format_source):
    lignes = lire_csv(chemin_entree)
    if not lignes:
        raise ValueError("Le fichier est vide.")

    mapping = FORMATS[format_source]
    colonnes_fichier = set(lignes[0].keys())
    colonnes_requises = {v for v in mapping.values() if v}
    manquantes = colonnes_requises - colonnes_fichier
    if manquantes:
        raise ValueError(
            "Ce fichier ne correspond pas au format « %s ».\n"
            "Colonnes introuvables : %s" % (format_source, ", ".join(sorted(manquantes)))
        )

    with open(chemin_sortie, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(SORTIE)
        for ligne in lignes:
            writer.writerow([
                (ligne.get(mapping[col]) or "").strip() if mapping[col] else ""
                for col in SORTIE
            ])
    return len(lignes)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convertisseur de mots de passe CSV")
        self.resizable(False, False)

        self.format_var = tk.StringVar(value=list(FORMATS)[0])
        self.entree_var = tk.StringVar()
        self.sortie_var = tk.StringVar()

        cadre = ttk.Frame(self, padding=15)
        cadre.grid()

        ttk.Label(cadre, text="Format du fichier source :").grid(row=0, column=0, sticky="w")
        ttk.Combobox(cadre, textvariable=self.format_var, values=list(FORMATS),
                     state="readonly", width=30).grid(row=0, column=1, columnspan=2, sticky="w", pady=4)

        ttk.Label(cadre, text="Fichier à convertir :").grid(row=1, column=0, sticky="w")
        ttk.Entry(cadre, textvariable=self.entree_var, width=50).grid(row=1, column=1, pady=4, padx=(0, 5))
        ttk.Button(cadre, text="Parcourir…", command=self.parcourir).grid(row=1, column=2)

        ttk.Label(cadre, text="Enregistrer sous :").grid(row=2, column=0, sticky="w")
        ttk.Entry(cadre, textvariable=self.sortie_var, width=50).grid(row=2, column=1, pady=4, padx=(0, 5))
        ttk.Button(cadre, text="Enregistrer sous…", command=self.enregistrer_sous).grid(row=2, column=2)

        ttk.Button(cadre, text="Convertir", command=self.lancer).grid(row=3, column=0, columnspan=3, pady=(12, 0))

    def parcourir(self):
        chemin = filedialog.askopenfilename(
            parent=self,
            title="Choisir le fichier CSV à convertir",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if chemin:
            self.entree_var.set(chemin)
            if not self.sortie_var.get():
                self.sortie_var.set(chemin.rsplit(".", 1)[0] + "_converti.csv")

    def enregistrer_sous(self):
        chemin = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer le fichier converti",
            defaultextension=".csv",
            initialfile="mots_de_passe_converti.csv",
            filetypes=[("Fichiers CSV", "*.csv")])
        if chemin:
            self.sortie_var.set(chemin)

    def lancer(self):
        entree, sortie = self.entree_var.get(), self.sortie_var.get()
        if not entree or not sortie:
            messagebox.showwarning(
                "Champs manquants",
                "Choisissez un fichier à convertir et un emplacement de sortie.",
                parent=self)
            return
        try:
            nb = convertir(entree, sortie, self.format_var.get())
        except Exception as e:
            messagebox.showerror("Erreur", str(e), parent=self)
            return

        # Ramène la fenêtre principale au premier plan, puis affiche
        # la confirmation PAR-DESSUS (parent=self la garde devant).
        self.update_idletasks()
        self.lift()
        self.focus_force()
        messagebox.showinfo(
            "Conversion terminée",
            "%d entrées converties avec succès.\n\n"
            "⚠ RAPPEL DE SÉCURITÉ ⚠\n"
            "Ces fichiers contiennent vos mots de passe EN CLAIR.\n"
            "Une fois l'import terminé, supprimez :\n"
            "  • le CSV d'origine\n"
            "  • le CSV converti\n"
            "puis videz la corbeille." % nb,
            parent=self)


if __name__ == "__main__":
    Application().mainloop()
