# 🍣 SushiScan Downloader

> Interface graphique pour télécharger des chapitres et volumes depuis [sushiscan.net](https://sushiscan.net) et les exporter en fichiers `.cbz` compatibles avec tous les lecteurs de manga.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium&logoColor=white)

</div>

---

## ✨ Fonctionnalités

- 🖥️ **Interface graphique** moderne avec 8 thèmes (Midnight, Café, Cyberpunk, Synthwave, Nord, Rose Gold, Dracula, Ochin)
- 📖 **Chapitre unique** ou **plage de chapitres** en une seule opération
- 📦 **Mode multi-CBZ** — un fichier `.cbz` par chapitre avec **nom personnalisé** pour chacun
- ✏️ **Nommage interactif** — une popup apparaît après chaque chapitre pour choisir le nom du fichier avant de passer au suivant
- 🛡️ **Gestion Cloudflare** — Chrome s'ouvre, tu résous le captcha manuellement, le script reprend automatiquement
- 🍪 **Injection de cookies** depuis Chrome pour éviter les erreurs 403
- 🔄 **Installation automatique** des dépendances au premier lancement (mode script)

---

## ⬇️ Téléchargement

👉 **[Télécharger la dernière version (.exe)](../../releases/latest)**

> ⚠️ Windows Defender peut signaler le fichier comme suspect — c'est un **faux positif** courant avec les exécutables PyInstaller. Le code source est entièrement disponible ici.

---

## 📋 Prérequis

| Méthode | Prérequis |
|---|---|
| `.exe` | Windows 10/11 + Google Chrome installé |
| Script `.py` | Python 3.9+ + Google Chrome installé |

---

## 🚀 Installation

### Via l'exécutable (recommandé)
1. Va dans l'onglet **[Releases](../../releases/latest)**
2. Télécharge `SushiScan Downloader.exe`
3. Lance-le directement — aucune installation requise

### Via le script Python
```bash
pip install selenium webdriver-manager requests beautifulsoup4 Pillow
python sushiscan_downloader.py
```

---

## 🖥️ Utilisation

| Champ | Description |
|---|---|
| **URL début** | URL du chapitre/tome à télécharger (ou du premier d'une plage) |
| **URL fin** | URL du dernier chapitre — optionnel, pour télécharger une plage |
| **Nom CBZ** | Nom du fichier de sortie en mode CBZ unique (sans `.cbz`) |
| **Dossier de sortie** | Dossier où seront sauvegardés les fichiers `.cbz` |
| **Pause entre chapitres** | Délai en secondes entre chaque chapitre (recommandé : 30–60 s) |
| **Mode headless** | Chrome invisible — **décocher** si Cloudflare bloque |
| **Un fichier .cbz par chapitre** | Active le mode multi-CBZ avec nommage interactif |

---

## 📖 Exemples d'URLs

```
# Un seul tome
https://sushiscan.net/the-boys-edition-deluxe-volume-1/

# Un seul chapitre
https://sushiscan.net/one-piece-chapitre-1100/

# Plage de tomes (volume 1 → 3)
URL début : https://sushiscan.net/the-boys-edition-deluxe-volume-1/
URL fin   : https://sushiscan.net/the-boys-edition-deluxe-volume-3/
```

---

## ⚙️ Modes de téléchargement

### Mode CBZ unique (défaut)
Tous les chapitres sont regroupés dans **un seul fichier `.cbz`**.
Le nom est défini dans le champ "Nom CBZ" avant de démarrer.

```
the-boys-volumes-1-3.cbz
├── the-boys-edition-deluxe-volume-1/
│   ├── 001.jpg
│   └── ...
├── the-boys-edition-deluxe-volume-2/
│   └── ...
└── the-boys-edition-deluxe-volume-3/
    └── ...
```

### Mode multi-CBZ ✨
Coche **"Un fichier .cbz par chapitre"** pour activer ce mode.

Après le téléchargement de chaque chapitre, une **popup apparaît** :

```
┌─────────────────────────────────────┐
│  Nom du fichier CBZ                 │
│                                     │
│  The Boys - Volume 1____            │
│                                     │
│        [Annuler]  [Confirmer]       │
└─────────────────────────────────────┘
```

- Le nom est **pré-rempli** avec le slug de l'URL
- Tu peux le **modifier librement** avant de confirmer
- Appuie sur **Entrée** pour confirmer rapidement
- Le `.cbz` est créé immédiatement et on passe au chapitre suivant

Résultat :
```
Downloads/
├── The Boys - Volume 1.cbz
├── The Boys - Volume 2.cbz
└── The Boys - Volume 3.cbz
```

---

## 🔄 Fonctionnement étape par étape

```
Pour chaque chapitre :

  1. Chrome s'ouvre sur la page
     └── Captcha Cloudflare ? → résous-le manuellement
     └── Clique ✅ Continuer

  2. Attends que les images apparaissent
     └── Clique ✅ Continuer

  3. Téléchargement automatique des pages

  4. Mode multi-CBZ → popup de nommage
     └── Saisis le nom → Confirmer
     └── CBZ créé immédiatement

  5. Pause configurée → chapitre suivant
```

> 💡 Si Cloudflare te bloque après plusieurs chapitres, augmente la pause à **60 s ou plus** et décoche "Mode headless".

---

## 🎨 Thèmes disponibles

| Thème | Description |
|---|---|
| 🌙 **Midnight** | Violet sombre, accent violet |
| ☕ **Café** | Tons chauds marron et dorés |
| ⚡ **Cyberpunk** | Noir profond, rose et cyan néon |
| 🎵 **Synthwave** | Violet rétro, dégradés roses |
| ❄️ **Nord** | Palette bleue arctique |
| 🌸 **Rose Gold** | Tons rosés et dorés |
| 🧛 **Dracula** | Le thème classique des développeurs |
| 🌊 **Ochin** | Bleus océan avec accents cyan |

---

## 🔨 Compiler soi-même

```powershell
# Installer PyInstaller
pip install pyinstaller

# Compiler (PowerShell)
python -m PyInstaller --onefile --windowed `
  --icon="sushi.ico" `
  --add-data="sushi.ico;." `
  --name="SushiScan Downloader" `
  --hidden-import=selenium `
  --hidden-import=selenium.webdriver.chrome.webdriver `
  --hidden-import=selenium.webdriver.chrome.service `
  --hidden-import=selenium.webdriver.chrome.options `
  --hidden-import=selenium.webdriver.common.by `
  --hidden-import=webdriver_manager `
  --hidden-import=webdriver_manager.chrome `
  --hidden-import=requests `
  --hidden-import=bs4 `
  sushiscan_downloader.py
```

---

## ❓ Problèmes courants

| Erreur | Solution |
|---|---|
| `No module named 'selenium'` | `pip install selenium webdriver-manager requests beautifulsoup4 Pillow` |
| `No module named 'webdriver_manager'` | Même commande ci-dessus |
| Erreur 403 sur les images | Les cookies Cloudflare ont expiré — relance le téléchargement |
| Chrome ne s'ouvre pas | Vérifie que Google Chrome est installé |
| Cloudflare bloque en boucle | Augmente la pause à 60 s+, décoche "Mode headless" |
| 0 image détectée | Passe en mode lecture verticale manuellement dans Chrome avant de cliquer Continuer |
| Le bouton Continuer ne répond pas | Mets à jour vers la dernière version |

---

## ⚠️ Avertissement

Ce projet est destiné à un usage **personnel et éducatif** uniquement.  
Respecte les droits des auteurs et soutiens les mangakas en achetant les volumes officiels. 📚

---

## 📄 Licence

MIT License — voir [LICENSE](LICENSE)
