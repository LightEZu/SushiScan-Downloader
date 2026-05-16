# 🍣 SushiScan Downloader

> Application desktop pour télécharger des chapitres et volumes depuis [sushiscan.net](https://sushiscan.net) et les exporter en fichiers `.cbz` compatibles avec tous les lecteurs de manga (Komga, Kavita, CDisplayEx, etc.)

<div align="center">

![Tauri](https://img.shields.io/badge/Tauri-2.x-FFC131?style=flat-square&logo=tauri&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![Rust](https://img.shields.io/badge/Rust-stable-orange?style=flat-square&logo=rust&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## ✨ Fonctionnalités

- 🖥️ **Interface graphique** moderne et intuitive
- 📖 **Chapitre unique** ou **plage de chapitres** en une seule opération
- 📦 **Mode multi-CBZ** — un fichier `.cbz` par chapitre avec nom personnalisé
- 🛡️ **Gestion Cloudflare** — Chrome s'ouvre, tu résous le captcha manuellement si besoin, le script reprend automatiquement
- 📁 **Choix du dossier de destination** via l'explorateur de fichiers
- ⏱️ **Pause configurable** entre les chapitres
- 🔄 **Scroll automatique** pour charger toutes les images en lazy loading

---

## ⬇️ Installation recommandée

👉 **[Télécharger le setup.exe depuis les Releases](../../releases/latest)**

1. Télécharge `SushiScan-Downloader_x.x.x_x64-setup.exe`
2. Lance l'installeur
3. Suis les étapes — l'app s'installe avec un raccourci dans le menu démarrer

> ⚠️ Windows Defender peut signaler le fichier — c'est un faux positif courant avec les apps Tauri. Le code source est entièrement disponible ici.

---

## 📋 Prérequis

Quelle que soit la méthode d'installation, tu as besoin de :

| Logiciel | Version minimale | Lien |
|---|---|---|
| **Google Chrome** | Toute version récente | [Télécharger](https://www.google.com/chrome/) |
| **Node.js** | 18+ | [Télécharger](https://nodejs.org/) |

> ⚠️ **Google Chrome est obligatoire** — l'application l'utilise pour contourner la protection Cloudflare de SushiScan. Chrome doit être installé dans son emplacement par défaut : `C:/Program Files/Google/Chrome/Application/chrome.exe`

---

## 🔧 Installation depuis les sources

```bash
# 1. Clone le repo
git clone https://github.com/LightEZu/SushiScan-Downloader.git
cd SushiScan-Downloader

# 2. Installe les dépendances Node.js (frontend)
npm install

# 3. Installe les dépendances du scraper
cd src-tauri/bin
npm install
cd ../..

# 4. Installe Playwright et le navigateur
npx playwright install chromium
```

---

## 🖥️ Lancement

```bash
# Mode développement
npm run tauri dev
```

La première compilation Rust prend 2–3 minutes. Les suivantes sont rapides.

---

## 📖 Utilisation

### 1. Remplir les champs

| Champ | Description |
|---|---|
| **URL de début** | URL du chapitre/volume à télécharger |
| **URL de fin** | *(optionnel)* URL du dernier chapitre pour télécharger une plage |
| **Nom du CBZ** | Nom du fichier de sortie (sans `.cbz`) — ignoré en mode multi-CBZ |
| **Dossier de sortie** | Cliquer sur 📁 Parcourir pour choisir le dossier |
| **Pause entre chapitres** | Délai en secondes entre chaque chapitre (recommandé : 30 s) |
| **Mode headless** | Laisser décoché — Chrome doit être visible |
| **Un CBZ par chapitre** | Active le mode multi-CBZ avec nommage personnalisé |

### 2. Démarrer le téléchargement

Clique sur **▶ Démarrer**. Une fenêtre Chrome s'ouvre automatiquement.

### 3. Valider la page

Une popup apparaît dans l'application :

> *"Passe en mode lecture verticale si besoin, puis clique Continuer."*

Dans la fenêtre Chrome :
1. Résous le captcha Cloudflare si demandé
2. Attends que la page charge
3. Active le **mode lecture verticale** (bouton en haut de la page)
4. Clique **✓ Continuer** dans l'application

Le téléchargement démarre automatiquement.

---

## 📝 Exemples d'URLs

```
# Un seul volume
https://sushiscan.net/the-boys-edition-deluxe-volume-1/

# Un seul chapitre
https://sushiscan.net/one-piece-chapitre-1100/

# Plage de volumes (1 → 3)
URL début : https://sushiscan.net/the-boys-edition-deluxe-volume-1/
URL fin   : https://sushiscan.net/the-boys-edition-deluxe-volume-3/
```

---

## ⚙️ Mode multi-CBZ

Coche **"Un fichier .cbz par chapitre"** pour activer ce mode.

Après chaque chapitre téléchargé, une popup te demande le nom du fichier CBZ. Tu peux modifier le nom pré-rempli ou appuyer sur **Entrée** pour confirmer.

Résultat :
```
Downloads/
├── The Boys - Volume 1.cbz
├── The Boys - Volume 2.cbz
└── The Boys - Volume 3.cbz
```

---

## ❓ Problèmes courants

| Problème | Solution |
|---|---|
| Chrome ne s'ouvre pas | Vérifie que Chrome est installé dans `C:/Program Files/Google/Chrome/` |
| Cloudflare bloque en boucle | Augmente la pause à 60 s+ |
| 0 image détectée | Active manuellement le mode lecture verticale avant de cliquer Continuer |
| Erreur 403 sur les images | Recharge la page dans Chrome puis clique Continuer |
| `node: command not found` | Installe Node.js et redémarre le terminal |
| Erreur de compilation Rust | Installe les [Build Tools Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |

---

## 🏗️ Stack technique

- **Frontend** : React 18 + Vite
- **Backend** : Rust + Tauri 2
- **Scraper** : Node.js + Playwright (Chrome)
- **Archivage** : archiver (CBZ = ZIP)

---

## ⚠️ Avertissement

Ce projet est destiné à un usage **personnel et éducatif** uniquement.
Respecte les droits des auteurs et soutiens les mangakas en achetant les volumes officiels. 📚

---

## 📄 Licence

MIT License
