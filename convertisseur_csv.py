"""Convertisseur local CSV navigateur/gestionnaire vers le template Kalydian."""
import csv
import io
import os
import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

SORTIE = ["name", "url", "login", "password", "otp"]
# Sortie -> alias(s) reconnus. Les alias sont normalisés sans casse ni ponctuation.
FORMATS = {
    "Google Chrome": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ()},
    "Microsoft Edge": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ()},
    "Mozilla Firefox": {"name": ("url",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ()},
    "KeePass": {"name": ("Account",), "url": ("Web Site",), "login": ("Login Name",), "password": ("Password",), "otp": ()},
    "Brave": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ("otp", "totp")},
    "Opera": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ("otp",)},
    "Vivaldi": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ("otp",)},
    "Google Password Manager": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ("otp",)},
    "Safari / Apple Passwords": {"name": ("Title", "name"), "url": ("URL", "url"), "login": ("Username", "username"), "password": ("Password", "password"), "otp": ("OTPAuth", "OTP Auth", "otp")},
    "Bitwarden": {"name": ("name",), "url": ("login_uri", "uri", "url"), "login": ("login_username", "username"), "password": ("login_password", "password"), "otp": ("login_totp", "totp", "otp")},
    "1Password 8": {"name": ("Title", "name"), "url": ("Url", "URL", "Website", "website"), "login": ("Username", "username"), "password": ("Password", "password"), "otp": ("OTPAuth", "OTP Auth", "One-time password", "TOTP")},
    "LastPass": {"name": ("name",), "url": ("url",), "login": ("username",), "password": ("password",), "otp": ("totp", "otp")},
    "Dashlane": {"name": ("title", "name"), "url": ("url",), "login": ("username", "username2", "username3"), "password": ("password",), "otp": ("otpUrl", "otpSecret", "otp", "totp")},
    "KeePassXC": {"name": ("Title", "title"), "url": ("URL", "url"), "login": ("Username", "username"), "password": ("Password", "password"), "otp": ("TOTP", "otp")},
    "NordPass": {"name": ("name", "title"), "url": ("url",), "login": ("username", "email"), "password": ("password",), "otp": ("otp", "totp")},
    "Proton Pass": {"name": ("name", "title"), "url": ("url",), "login": ("username", "email"), "password": ("password",), "otp": ("totp", "otp")},
}


def normaliser_entete(valeur):
    return re.sub(r"[^a-z0-9]", "", (valeur or "").lstrip("\ufeff").lower())


def lire_csv(chemin):
    """Lit les CSV BOM UTF-8 inclus, et détecte virgule, point-virgule ou tabulation."""
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
    try:
        dialecte = csv.Sniffer().sniff(contenu[:65536], delimiters=",;\t")
        separateur = dialecte.delimiter
    except csv.Error:
        separateur = ","
    return list(csv.DictReader(io.StringIO(contenu), delimiter=separateur))


def _colonnes(ligne):
    return {normaliser_entete(k): k for k in ligne.keys() if k is not None}


def _resoudre_mapping(source, entetes):
    """Résout les alias d'une source en en-têtes réels du fichier."""
    norm = {normaliser_entete(k): k for k in entetes if k is not None}
    mapping = {}
    for sortie, alias in FORMATS[source].items():
        mapping[sortie] = next((norm[normaliser_entete(a)] for a in alias
                                if normaliser_entete(a) in norm), None)
    # Ces exports peuvent fournir leur titre autrement que dans la colonne name.
    if source in {"Dashlane", "LastPass"} and not mapping.get("name"):
        mapping["name"] = mapping.get("url")
    requis = {"name", "url", "login", "password"}
    if source == "Mozilla Firefox":
        requis = {"url", "login", "password"}
    manquantes = [c for c in requis if not mapping.get(c)]
    # Dashlane et Proton/NordPass acceptent des variantes d'identifiant.
    if manquantes:
        raise ValueError("Le fichier ne correspond pas au format « %s ». Colonnes introuvables : %s" %
                         (source, ", ".join(sorted(manquantes))))
    if source == "Proton Pass" and not mapping.get("login"):
        raise ValueError("Le fichier Proton Pass doit contenir username ou email.")
    return mapping


def detecter_source(entetes):
    """Détecte les signatures distinctives; les formats Chromium partagés sont génériques."""
    n = {normaliser_entete(h) for h in entetes}
    has = lambda *vals: all(normaliser_entete(v) in n for v in vals)
    if has("Account", "Web Site", "Login Name", "Password"):
        return "KeePass"
    if has("Group", "Title", "Username", "Password", "URL"):
        return "KeePassXC"
    if has("folder", "favorite", "type", "name", "notes", "fields", "reprompt", "login_uri", "login_username", "login_password"):
        return "Bitwarden"
    if has("username2") or has("username3") or has("otpUrl") or has("otpSecret"):
        return "Dashlane"
    if has("Title", "Username", "Password") and has("Favorite", "Archived"):
        return "1Password 8"
    if has("Title", "URL", "Username", "Password") and (has("OTPAuth") or has("OTP Auth") or has("Notes")):
        return "Safari / Apple Passwords"
    if has("Title", "Username", "Password") and (has("OTP Auth") or has("Url")):
        return "1Password 8"
    if has("title", "password", "url") and (has("username2") or has("username3") or has("otpUrl") or has("otpSecret")):
        return "Dashlane"
    if has("totp", "extra", "name", "grouping", "fav", "url", "username", "password"):
        return "LastPass"
    if has("type", "name", "url", "username", "password", "additional_urls") or has("additional_urls", "folder", "type"):
        return "NordPass"
    if has("type", "name", "url", "email", "username", "password") and (has("createTime") or has("modifyTime") or has("vault")):
        return "Proton Pass"
    if has("url", "username", "password", "httpRealm", "formActionOrigin"):
        return "Mozilla Firefox"
    if has("name", "url", "username", "password"):
        return "Google Chrome"
    return None


def _ligne_sortie(ligne, mapping):
    # Certains exports incluent plusieurs noms d'utilisateur possibles.
    login = (ligne.get(mapping.get("login")) or "").strip() if mapping.get("login") else ""
    if not login and mapping.get("source") == "Dashlane":
        for alias in ("username2", "username3"):
            key = _colonnes(ligne).get(normaliser_entete(alias))
            if key and (ligne.get(key) or "").strip():
                login = ligne[key].strip()
                break
    if not login and mapping.get("source") == "Proton Pass":
        key = _colonnes(ligne).get("email")
        if key:
            login = (ligne.get(key) or "").strip()
    return [(ligne.get(mapping.get(c)) or "").strip() if mapping.get(c) else "" for c in SORTIE[:2]] + [
        login,
        (ligne.get(mapping.get("password")) or "").strip() if mapping.get("password") else "",
        (ligne.get(mapping.get("otp")) or "").strip() if mapping.get("otp") else "",
    ]


def _inclure_ligne(source, ligne, entetes):
    cols = _colonnes(ligne)
    def val(nom):
        key = cols.get(normaliser_entete(nom))
        return (ligne.get(key) or "").strip() if key else ""
    if source == "Bitwarden":
        return val("type").casefold() == "login"
    if source == "LastPass":
        return val("url").casefold() != "http://sn"
    if source == "NordPass":
        typ = val("type").casefold()
        return not typ or typ in {"login", "password", "login_password", "passwords"}
    if source == "Proton Pass":
        return val("type").casefold() == "login"
    return True


def analyser(chemin_entree, format_source=None):
    lignes = lire_csv(chemin_entree)
    if not lignes:
        raise ValueError("Le fichier CSV est vide ou ne contient aucune ligne de données.")
    entetes = list(lignes[0].keys())
    source = format_source or detecter_source(entetes)
    if not source:
        raise ValueError("Format non reconnu. Vérifiez la ligne d'en-têtes ou choisissez la source manuellement.")
    mapping = _resoudre_mapping(source, entetes)
    mapping["source"] = source
    valides = [l for l in lignes if _inclure_ligne(source, l, entetes)]
    vides = sum(not any((v or "").strip() for v in l.values() if isinstance(v, str)) for l in valides)
    sorties = [_ligne_sortie(l, mapping) for l in valides]
    invalides = sum(not row[3] for row in sorties)
    return {"source": source, "lignes": valides, "entetes": entetes,
            "entrees": len(valides), "doublons": len(sorties) - len(set(tuple(x) for x in sorties)),
            "vides": vides, "invalides": invalides}


def convertir(chemin_entree, chemin_sortie, format_source):
    """Écrit le template historique, séparateur ; et encodage UTF-8."""
    lignes = lire_csv(chemin_entree)
    if not lignes:
        raise ValueError("Le fichier est vide.")
    mapping = _resoudre_mapping(format_source, list(lignes[0].keys()))
    mapping["source"] = format_source
    lignes = [l for l in lignes if _inclure_ligne(format_source, l, list(lignes[0].keys()))]
    with open(chemin_sortie, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(SORTIE)
        for ligne in lignes:
            writer.writerow(_ligne_sortie(ligne, mapping))
    return len(lignes)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kalydian · Convertisseur CSV")
        self.geometry("760x490")
        self.minsize(680, 460)
        self.configure(bg="#f3f6fa")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f3f6fa")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f3f6fa", foreground="#1d2c3d", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#12304a")
        style.configure("Sub.TLabel", foreground="#52677c")
        style.configure("Card.TLabel", background="#ffffff")
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Accent.TButton", background="#176b87", foreground="white", font=("Segoe UI", 10, "bold"))
        self.format_var = tk.StringVar(value=list(FORMATS)[0])
        self.entree_var = tk.StringVar()
        self.sortie_var = tk.StringVar()
        root = ttk.Frame(self, padding=24)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Convertisseur CSV", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Préparez vos identifiants pour l’import Kalydian — les fichiers restent sur votre appareil.", style="Sub.TLabel").pack(anchor="w", pady=(3, 16))
        card = ttk.Frame(root, style="Card.TFrame", padding=18)
        card.pack(fill="x")
        ttk.Label(card, text="1  ·  Fichier source", style="Card.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", columnspan=3, pady=(0, 8))
        ttk.Entry(card, textvariable=self.entree_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(card, text="Parcourir…", command=self.parcourir).grid(row=1, column=1)
        ttk.Label(card, text="Source détectée / à sélectionner :", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 3))
        self.combo = ttk.Combobox(card, textvariable=self.format_var, values=list(FORMATS), state="readonly", width=28)
        self.combo.grid(row=3, column=0, sticky="w")
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.maj_apercu())
        self.apercu_var = tk.StringVar(value="Choisissez un fichier CSV pour afficher l’aperçu.")
        ttk.Label(card, textvariable=self.apercu_var, style="Card.TLabel", justify="left").grid(row=4, column=0, columnspan=3, sticky="w", pady=(12, 2))
        card.columnconfigure(0, weight=1)
        out = ttk.Frame(root, style="Card.TFrame", padding=18)
        out.pack(fill="x", pady=14)
        ttk.Label(out, text="2  ·  Fichier Kalydian de sortie", style="Card.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", columnspan=3, pady=(0, 8))
        ttk.Entry(out, textvariable=self.sortie_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(out, text="Choisir…", command=self.enregistrer_sous).grid(row=1, column=1)
        out.columnconfigure(0, weight=1)
        actions = ttk.Frame(root)
        actions.pack(fill="x")
        ttk.Button(actions, text="Convertir", style="Accent.TButton", command=self.lancer).pack(side="left")
        self.ouvrir_btn = ttk.Button(actions, text="Ouvrir le dossier de sortie", command=self.ouvrir_dossier, state="disabled")
        self.ouvrir_btn.pack(side="left", padx=10)
        ttk.Label(root, text="Sécurité : les CSV contiennent des mots de passe en clair. Supprimez-les après import.", style="Sub.TLabel", wraplength=700).pack(anchor="w", pady=(14, 0))
        self.sortie_var.trace_add("write", lambda *_: self.ouvrir_btn.configure(state="disabled"))

    def parcourir(self):
        chemin = filedialog.askopenfilename(parent=self, title="Choisir le fichier CSV source", filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if chemin:
            self.entree_var.set(chemin)
            if not self.sortie_var.get():
                self.sortie_var.set(str(Path(chemin).with_name(Path(chemin).stem + "_kalydian.csv")))
            try:
                ap = analyser(chemin)
                self.format_var.set(ap["source"])
            except ValueError:
                pass
            self.maj_apercu()

    def enregistrer_sous(self):
        chemin = filedialog.asksaveasfilename(parent=self, title="Enregistrer le fichier converti", defaultextension=".csv", initialfile="kalydian_converti.csv", filetypes=[("Fichiers CSV", "*.csv")])
        if chemin:
            self.sortie_var.set(chemin)

    def maj_apercu(self):
        chemin = self.entree_var.get()
        if not chemin:
            return
        try:
            ap = analyser(chemin, self.format_var.get())
            self.format_var.set(ap["source"])
            self.apercu_var.set("{} · {} entrées · {} doublon(s) · {} ligne(s) vide(s) · {} sans mot de passe".format(ap["source"], ap["entrees"], ap["doublons"], ap["vides"], ap["invalides"]))
        except (OSError, csv.Error, ValueError) as exc:
            self.apercu_var.set("Aperçu indisponible : " + str(exc))

    def lancer(self):
        entree, sortie = self.entree_var.get().strip(), self.sortie_var.get().strip()
        if not entree or not sortie:
            messagebox.showwarning("Informations manquantes", "Choisissez un CSV source et un fichier de sortie.", parent=self)
            return
        try:
            nb = convertir(entree, sortie, self.format_var.get())
        except (OSError, csv.Error, ValueError, KeyError) as exc:
            messagebox.showerror("Conversion impossible", str(exc), parent=self)
            return
        self._dernier_sortie = sortie
        self.ouvrir_btn.configure(state="normal")
        messagebox.showinfo("Conversion terminée", "%d entrée(s) convertie(s).\n\nLe fichier contient des mots de passe en clair. Supprimez le CSV source et celui converti après import, puis videz la corbeille." % nb, parent=self)

    def ouvrir_dossier(self):
        chemin = getattr(self, "_dernier_sortie", "")
        if not chemin or not os.path.exists(chemin):
            messagebox.showerror("Fichier introuvable", "Le fichier de sortie n’existe plus.", parent=self)
            return
        dossier = str(Path(chemin).resolve().parent)
        try:
            if sys.platform == "win32":
                os.startfile(dossier)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", dossier])
            else:
                subprocess.Popen(["xdg-open", dossier])
        except OSError as exc:
            messagebox.showerror("Ouverture impossible", "Impossible d’ouvrir le dossier : %s" % exc, parent=self)


if __name__ == "__main__":
    Application().mainloop()
