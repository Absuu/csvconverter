# Convertisseur CSV vers Kalydian

Application Python 3 avec interface Tkinter/ttk, compilée sous Windows par GitHub Actions et PyInstaller (`--onefile --windowed`). Elle ne requiert aucune dépendance Python tierce. Le chemin de sortie garde le template strict `name;url;login;password;otp`.

## Sources prises en charge

- Google Chrome, Microsoft Edge, Brave, Opera, Vivaldi et Google Password Manager (exports Chromium : `name,url,username,password`; champs supplémentaires tolérés)
- Mozilla Firefox (`url,username,password`; le nom est repris de `url`)
- Safari / Apple Passwords (`Title,URL,Username,Password`; `OTPAuth`/`OTP Auth` si présent)
- Bitwarden (`name,login_uri,login_username,login_password`; `login_totp` si présent; seules les lignes `type=login` sont converties)
- 1Password 8 (`Title,Url`/`URL`, `Username`, `Password`; champs OTP si présents)
- LastPass (`url,username,password`; `totp` si présent; les Secure Notes `http://sn` sont ignorées)
- Dashlane (`title`, `url`, `username`/`username2`/`username3`, `password`; `otpUrl`/`otpSecret` si présent)
- KeePass (export générique : `Account,Web Site,Login Name,Password`)
- KeePassXC (`Group,Title,Username,Password,URL`; `TOTP` si présent)
- NordPass (`name,url,username,password`; lignes de type login/mot de passe seulement)
- Proton Pass (`type,name,url,email,username,password`; `totp` si présent; seules les lignes `type=login` sont converties)

Les en-têtes sont reconnus sans tenir compte de la casse ni de la ponctuation, avec des alias prévus pour les variantes. Les colonnes supplémentaires sont tolérées. L’application détecte les formats automatiquement quand leur signature est distinctive; les formats partagés (notamment les exports Chromium) peuvent être sélectionnés manuellement dans la liste. Les CSV UTF-8 avec BOM sont pris en charge, ainsi que les séparateurs virgule, point-virgule et tabulation.

Les noms de fichier et les variations d’en-tête évoluent selon les versions et les plateformes. Les mappings pris en charge sont documentés dans [SOURCES_PROPOSEES.md](SOURCES_PROPOSEES.md).

## Fonctionnalités

- Détection des formats sur les en-têtes, avec sélection manuelle de la source ;
- aperçu des enregistrements retenus, doublons exacts, lignes vides et entrées sans mot de passe ;
- exclusion des lignes non-identifiants connues de Bitwarden, LastPass, NordPass et Proton Pass ;
- sélection du chemin de sortie et ouverture du dossier après conversion ;
- CSV de sortie délimité par `;`, encodage UTF-8, colonnes dans l’ordre fixe `name;url;login;password;otp`.

Les fichiers source et converti ne quittent pas l’ordinateur. Les exports de mots de passe sont en clair : ne les partagez pas et effacez-les après import.

## Validation locale

`python -m py_compile convertisseur_csv.py`

Les tests de régression vérifient les sorties des formats historiques et les tests par CSV fictif couvrent les nouvelles sources, les différents séparateurs, le BOM et les lignes de non-identifiants filtrées. L’ouverture interactive Tkinter dépend de l’environnement ; sur certains systèmes sans bibliothèque Tcl/Tk, la GUI ne peut pas s’ouvrir.
