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
- 🛡️ **Gestion Cloudflare** — Chrome s'ouvre, tu résous le captcha manuellement, le script reprend automatiquement
- 🍪 **Injection de cookies** depuis Chrome pour éviter les erreurs 403
- 📦 **Export `.cbz`** organisé par chapitre, compatible Kavita, Komga, CDisplayEx, etc.
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
| **Nom CBZ** | Nom personnalisé pour le fichier de sortie (sans `.cbz`) |
| **Dossier de sortie** | Dossier où sera sauvegardé le `.cbz` |
| **Pause entre chapitres** | Délai en secondes entre chaque chapitre (recommandé : 30–60 s) |
| **Mode headless** | Chrome invisible — **décocher** si Cloudflare bloque |

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

## ⚙️ Fonctionnement

Pour chaque chapitre, le script suit ce processus en 2 étapes :

```
1. Chrome s'ouvre sur la page
   └── Si captcha Cloudflare → résous-le manuellement
   └── Clique sur ✅ Continuer

2. La page se recharge avec les images
   └── Attends que toutes les images soient visibles
   └── Clique sur ✅ Continuer

3. Téléchargement automatique de toutes les pages
4. Création du fichier .cbz
```

> 💡 Si Cloudflare te bloque après plusieurs chapitres, augmente la pause à **60 s ou plus** et désactive le mode headless.

---

## 🗃️ Structure du CBZ généré

```
the-boys-volume-1-3.cbz
├── the-boys-edition-deluxe-volume-1/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── ...
├── the-boys-edition-deluxe-volume-2/
│   └── ...
└── the-boys-edition-deluxe-volume-3/
    └── ...
```

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

```bash
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
| L'app se lance en boucle | Ne pas compiler sans le flag `--windowed`, ou mettre à jour vers la dernière version |

---

## ⚠️ Avertissement

Ce projet est destiné à un usage **personnel et éducatif** uniquement.  
Respecte les droits des auteurs et soutiens les mangakas en achetant les volumes officiels. 📚

---

## 📄 Licence

MIT License — voir [LICENSE](LICENSE)
