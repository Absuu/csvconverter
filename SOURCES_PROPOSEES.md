# Référence des formats CSV pris en charge

Le convertisseur cible le template Kalydian `name;url;login;password;otp`. Les en-têtes sont comparés sans casse et sans ponctuation significative; des colonnes additionnelles sont acceptées. Les noms entre parenthèses sont des alias. Quand plusieurs champs de login existent, le premier non vide est utilisé. Les valeurs OTP sont reprises en l’état (URI `otpauth://…` ou secret brut).

| Source | En-têtes attendus / signatures | Mapping vers Kalydian et comportement |
|---|---|---|
| Google Chrome, Microsoft Edge, Brave, Opera, Vivaldi, Google Password Manager | `name,url,username,password` (note / colonnes additionnelles facultatives) | `name→name`, `url→url`, `username→login`, `password→password`; OTP vide sauf colonne otp/totp explicite. En-têtes communs : choisir le navigateur manuellement si la détection générique ne suffit pas. |
| Mozilla Firefox | `url,username,password` (signature de détection renforcée par `httpRealm,formActionOrigin`) | `url→name` et `url→url`, `username→login`, `password→password`; OTP vide. |
| Safari / Apple Passwords | `Title,URL,Username,Password` (OTPAuth / OTP Auth facultatif) | `Title→name`, `URL→url`, `Username→login`, `Password→password`, OTPAuth→otp. |
| Bitwarden | `folder,favorite,type,name,notes,fields,reprompt,login_uri,login_username,login_password` (`login_totp` facultatif) | `name→name`, `login_uri→url`, `login_username→login`, `login_password→password`, `login_totp→otp`. Les lignes dont `type` n’est pas `login` sont écartées. |
| 1Password 8 | `Title,Url` ou `URL,Username,Password` (`OTPAuth`, `OTP Auth` ou `One-time password` facultatif; Favorite, Archived, Tags, Notes optionnels) | `Title→name`, Url/URL→url, Username→login, Password→password, champ OTP reconnu→otp. |
| LastPass | `url,username,password,totp,extra,name,grouping,fav` | `name→name`, `url→url`, `username→login`, `password→password`, `totp→otp`. La ligne `url=http://sn` (Secure Note) est exclue. |
| Dashlane | `username,username2,username3,title,password,note,url,category,otpUrl` ou `otpSecret` | `title→name`, `url→url`, premier username non vide→login, `password→password`, otpUrl/otpSecret→otp. |
| KeePass | `Account,Web Site,Login Name,Password` | `Account→name`, Web Site→url, Login Name→login, Password→password, OTP vide. Format historique. |
| KeePassXC | `Group,Title,Username,Password,URL,Notes,TOTP,Icon,Last Modified,Created` | `Title→name`, URL→url, Username→login, Password→password, TOTP→otp. Colonnes additionnelles facultatives. |
| NordPass | `name,url,additional_urls,username,password,note,cardholdername,…,folder,type` | `name→name`, `url→url`, username (email en secours)→login, password→password, OTP si colonne disponible. Les types explicitement différents de login/password sont ignorés. |
| Proton Pass | `type,name,url,email,username,password,note,totp,createTime,modifyTime,vault` | `name→name`, `url→url`, username (email en secours)→login, `password→password`, totp→otp. Seules les lignes `type=login` sont converties. |

## Lecture et limites

- Les CSV UTF-8 avec BOM sont acceptés; la lecture accepte aussi Windows-1252/Latin-1.
- Détection de séparateur : virgule, point-virgule ou tabulation.
- Les signatures spécifiques détectent les exports reconnaissables. Les variantes CSV partagées (Chromium) peuvent être converties via la sélection manuelle de source dans l’interface.
- Les séparateurs de sortie et l’ordre des champs Kalydian restent fixes. Les données OTP sont copiées textuellement, sans transformation ni validation du secret.
- Les formats d’export et certains libellés varient selon plateforme, version et locale. Dashlane (champs multiples de nom d’utilisateur et OTP), NordPass (types d’éléments) et Safari/Apple Passwords (export OTP selon OS) sont particulièrement susceptibles de variantes; vérifier un export réel avant un transfert important.
- Les exports CSV contiennent les mots de passe en clair. Ils restent locaux à l’application; supprimer les fichiers source et résultat après import.

## Références publiques consultées

- Apple, export des mots de passe depuis iPhone : https://support.apple.com/guide/iphone/export-passwords-iphf28f2e93e/ios
- Apple, import/export depuis macOS : https://support.apple.com/en-in/guide/mac-help/sfri40599/mac
- Bitwarden, export des données : https://bitwarden.com/en-gb/help/export-your-data.md
- Bitwarden, FAQ d’import/export : https://bitwarden.com/help/import-faqs/
- 1Password, export et champs inclus en CSV : https://support.1password.com/export/
- NordPass, instructions d’export depuis Chrome et Brave : https://support.nordpass.com/hc/en-us/articles/360002451798-How-to-export-passwords-from-Chrome-to-NordPass et https://support.nordpass.com/hc/en-us/articles/360005500457-How-to-export-passwords-from-Brave-to-NordPass
- NordPass, export depuis Proton Pass : https://support.nordpass.com/hc/en-us/articles/20918018467857-How-to-export-passwords-from-Proton-Pass-to-NordPass
- Firefox, export des données de connexion : https://support.mozilla.org/en-US/kb/export-login-data-firefox
