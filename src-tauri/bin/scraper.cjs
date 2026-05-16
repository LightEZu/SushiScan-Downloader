/**
 * SushiScan Downloader - Backend Playwright
 * Tournant comme sidecar Node.js pour Tauri
 */

const { chromium } = require("playwright");
const { ZipArchive } = require("archiver");
const fs = require("fs");
const path = require("path");
const os = require("os");
const readline = require("readline");

// ─── Communication IPC via stdout/stdin ───────────────────────────────────────

function send(type, payload) {
  process.stdout.write(JSON.stringify({ type, ...payload }) + "\n");
}

function log(msg, tag = "info") {
  send("log", { msg, tag });
}

function status(msg) {
  send("status", { msg });
}

function progress(val) {
  send("progress", { val });
}

// ─── Attente d'un message du frontend ────────────────────────────────────────

let pendingResolve = null;

// Un seul readline pour tout gérer
const rl = readline.createInterface({ input: process.stdin });

function waitMessage() {
  return new Promise((resolve) => {
    pendingResolve = resolve;
  });
}

// ─── État global ──────────────────────────────────────────────────────────────

let running = false;
let browser = null;
let page = null;

// ─── Utilitaires URL ──────────────────────────────────────────────────────────

function slug(url) {
  return url.replace(/\/$/, "").split("/").pop();
}

function buildList(urlStart, urlEnd) {
  if (!urlEnd) return [{ url: urlStart, slug: slug(urlStart) }];

  function extract(url) {
    const last = url.replace(/\/$/, "").split("/").pop();
    const m = last.match(/(\d+(?:[.,]\d+)?)(?:[^0-9]*)$/);
    if (!m) return { num: null, tmpl: null };
    const num = m[1];
    const i = url.lastIndexOf(num);
    return {
      num: parseFloat(num.replace(",", ".")),
      tmpl: url.slice(0, i) + "{N}" + url.slice(i + num.length),
    };
  }

  const { num: sNum, tmpl } = extract(urlStart);
  const { num: eNum } = extract(urlEnd);

  if (sNum === null || eNum === null) {
    return [{ url: urlStart, slug: slug(urlStart) }];
  }

  const entries = [];
  let n = sNum;
  while (n <= eNum + 0.001 && entries.length < 1000) {
    const ns = n === Math.floor(n) ? String(Math.floor(n)) : String(Math.round(n * 10) / 10);
    const u = tmpl.replace("{N}", ns);
    entries.push({ url: u, slug: slug(u) });
    n += 1;
  }
  return entries;
}

// ─── Détection d'images ───────────────────────────────────────────────────────

function isPageImage(url) {
  const u = url.toLowerCase();
  if (!/\.(jpg|jpeg|png|webp)(\?|$)/.test(u)) return false;
  const good = ["wp-content/uploads", "sushiscan", "/cdn/", "manga", "scan", "page", "chap", "vol"].some((p) => u.includes(p));
  const bad = ["logo", "icon", "avatar", "banner", "favicon", "thumbnail", "placeholder", "spinner", "gravatar"].some((p) => u.includes(p));
  const numeric = /\/\d{2,4}\.(jpg|jpeg|png|webp)(\?|$)/.test(u);
  return (good || numeric) && !bad;
}

async function extractImages() {
  let imgs = [];

  try {
    const els = await page.$$(
      "#readerarea img, .reading-content img, .read-container img, #chapter-images img, .entry-content img"
    );
    for (const el of els) {
      const src = (await el.getAttribute("src")) || (await el.getAttribute("data-src")) || (await el.getAttribute("data-lazy")) || "";
      if (src.trim() && isPageImage(src.trim())) imgs.push(src.trim());
    }
  } catch {}

  if (!imgs.length) {
    try {
      const els = await page.$$("img");
      for (const el of els) {
        const src = (await el.getAttribute("src")) || (await el.getAttribute("data-src")) || "";
        if (src.trim() && isPageImage(src.trim())) imgs.push(src.trim());
      }
    } catch {}
  }

  if (!imgs.length) {
    try {
      const html = await page.content();
      const found = [...html.matchAll(/https?:\/\/[^\s'"<>\\]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s'"<>\\]*)?/gi)].map((m) => m[0]);
      imgs = found.filter(isPageImage);
    } catch {}
  }

  const seen = new Set();
  return imgs.filter((u) => {
    const k = u.split("?")[0];
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

async function tryVerticalMode() {
  const xpaths = [
    "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'lecture verticale')]",
    "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'vertical')]",
  ];
  for (const xp of xpaths) {
    try {
      const el = await page.$(`xpath=${xp}`);
      if (el) {
        await el.click();
        await page.waitForTimeout(1000);
        log("↕️  Mode lecture verticale activé.", "info");
        return;
      }
    } catch {}
  }
}

async function scrollToLoadAll() {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      const timer = setInterval(() => {
        window.scrollBy(0, 1200);
        if ((window.scrollY + window.innerHeight) >= document.body.scrollHeight) {
          clearInterval(timer);
          resolve();
        }
      }, 80);
    });
  });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(1000);
}

function guessExt(url, ct = "") {
  const ctMap = { "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp" };
  for (const [k, v] of Object.entries(ctMap)) {
    if (ct.includes(k)) return v;
  }
  for (const ext of [".webp", ".png", ".jpg", ".jpeg"]) {
    if (url.toLowerCase().includes(ext)) return ext === ".jpeg" ? ".jpg" : ext;
  }
  return ".jpg";
}

// ─── Téléchargement d'un chapitre ─────────────────────────────────────────────

async function downloadEntry(url, entrySlug, outDir, prePause) {
  if (prePause > 0) {
    log(`💤 Pause ${prePause}s…`, "info");
    for (let i = 0; i < prePause; i++) {
      if (!running) return [];
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  log(`🌐 Ouverture : ${url}`, "info");
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  } catch (e) {
    log(`❌ Navigation échouée : ${e.message}`, "err");
    return [];
  }

  await page.waitForTimeout(3000);
  pendingResolve = null;

  log(`🔔 En attente de validation...`, "info");
  send("wait_continue", { msg: "Passe en mode lecture verticale si besoin, puis clique Continuer." });
  const r1 = await waitMessage();
  if (r1.type === "stop" || !running) return [];

  log(`📜 Scroll pour charger toutes les images...`, "info");
  await scrollToLoadAll();

  const imgUrls = await extractImages();
  if (!imgUrls.length) {
    log("⚠️  Aucune image détectée.", "warn");
    return [];
  }
  log(`🖼  ${imgUrls.length} images trouvées.`, "info");

  const chapDir = path.join(outDir, "_sushi_tmp", entrySlug);
  fs.mkdirSync(chapDir, { recursive: true });

  const saved = new Array(imgUrls.length).fill(null);

  for (let i = 0; i < imgUrls.length; i++) {
    if (!running) break;
    try {
      const response = await page.request.get(imgUrls[i], {
        timeout: 30000,
        headers: {
          "Referer": url,
          "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        }
      });
      if (!response.ok()) throw new Error(`HTTP ${response.status()}`);
      const buffer = await response.body();
      const ct = response.headers()["content-type"] || "";
      const ext = guessExt(imgUrls[i], ct);
      const fname = path.join(chapDir, `${String(i + 1).padStart(3, "0")}${ext}`);
      fs.writeFileSync(fname, buffer);
      saved[i] = fname;
      status(`${entrySlug} — page ${i + 1}/${imgUrls.length}`);
    } catch (e) {
      log(`⚠️  Image ${i + 1} : ${e.message}`, "warn");
    }
  }

  return saved.filter(Boolean);
}

// ─── Création CBZ ─────────────────────────────────────────────────────────────

function makeCbz(allImages, cbzName, outDir, entries) {
  return new Promise((resolve, reject) => {
    if (!cbzName) {
      const slugs = entries.map((e) => e.slug);
      if (slugs.length === 1) {
        cbzName = slugs[0];
      } else {
        const base = slugs[0].replace(/[-_]?\d+$/, "").replace(/[-_ ]+$/, "");
        const m0 = slugs[0].match(/\d+/);
        const m1 = slugs[slugs.length - 1].match(/\d+/);
        cbzName = m0 && m1 ? `${base}-${m0[0]}-${m1[0]}` : `${base}-multi`;
      }
    }

    const cbzPath = path.join(outDir, cbzName + ".cbz");
    const output = fs.createWriteStream(cbzPath);
    const archive = new ZipArchive({ zlib: { level: 6 } });

    output.on("close", () => resolve(cbzPath));
    archive.on("error", reject);
    archive.pipe(output);

    for (const [slug, files] of Object.entries(allImages)) {
      for (const f of files.sort()) {
        archive.file(f, { name: path.join(slug, path.basename(f)) });
      }
    }
    archive.finalize();
  });
}

// ─── Run principal ────────────────────────────────────────────────────────────

async function run(params) {
  const { urlStart, urlEnd, cbzName, outDir, pause, headless, splitCbz } = params;

  fs.mkdirSync(outDir, { recursive: true });

  const entries = buildList(urlStart, urlEnd);
  if (!entries.length) {
    log("❌ Liste vide.", "err");
    send("done", { success: false });
    return;
  }
  log(`📚 ${entries.length} entrée(s) à télécharger.`, "step");

  const chromeProfilePath = path.join(os.homedir(), "AppData", "Local", "Playwright", "ChromeProfile");
  browser = await chromium.launchPersistentContext(chromeProfilePath, {
    headless: false,
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    args: [
      "--disable-blink-features=AutomationControlled",
      "--window-size=1280,900",
    ],
    ignoreDefaultArgs: ["--enable-automation", "--no-first-run"],
    viewport: { width: 1280, height: 900 },
  });
  page = await browser.newPage();

  const allImages = {};
  const createdCbz = [];
  running = true;

  try {
    for (let idx = 0; idx < entries.length; idx++) {
      if (!running) break;
      const { url, slug: entrySlug } = entries[idx];
      log(`\n${"─".repeat(50)}`, "info");
      log(`📖 [${idx + 1}/${entries.length}] ${entrySlug}`, "step");
      progress(Math.floor((idx / entries.length) * 100));

      const imgs = await downloadEntry(url, entrySlug, outDir, idx > 0 ? pause : 0);
      if (!imgs.length) {
        log(`⚠️  Aucune image pour ${entrySlug}.`, "warn");
        continue;
      }
      log(`✅ ${imgs.length} pages.`, "ok");

      if (splitCbz) {
        send("ask_cbz_name", { slug: entrySlug, current: idx + 1, total: entries.length });
        const r = await waitMessage();
        if (r.type === "stop" || !running) break;
        const name = r.name || entrySlug;
        status("Création du CBZ…");
        const cbzPath = await makeCbz({ [entrySlug]: imgs }, name, outDir, [{ url, slug: entrySlug }]);
        log(`📦 ${path.basename(cbzPath)}`, "ok");
        createdCbz.push(cbzPath);
      } else {
        allImages[entrySlug] = imgs;
      }
    }
  } finally {
    try { await browser.close(); } catch {}
    browser = null;
    page = null;
  }

  if (!running) {
    log("⏹ Interrompu.", "warn");
    send("done", { success: false });
    return;
  }

  if (splitCbz) {
    if (createdCbz.length) {
      log(`\n🎉 ${createdCbz.length} fichier(s) CBZ créés dans :\n${outDir}`, "ok");
      send("done", { success: true, count: createdCbz.length, outDir });
    } else {
      log("❌ Aucun CBZ créé.", "err");
      send("done", { success: false });
    }
  } else if (Object.keys(allImages).length) {
    status("Création du CBZ…");
    try {
      const cbzPath = await makeCbz(allImages, cbzName, outDir, entries);
      log(`\n🎉 CBZ créé : ${cbzPath}`, "ok");
      send("done", { success: true, cbzPath, outDir });
    } catch (e) {
      log(`❌ Erreur CBZ : ${e.message}`, "err");
      send("done", { success: false });
    }
  } else {
    log("❌ Aucune image à compresser.", "err");
    send("done", { success: false });
  }

  progress(100);
  status("Terminé.");
}

// ─── Point d'entrée ───────────────────────────────────────────────────────────

let started = false;

rl.on("line", async (line) => {
  try {
    const msg = JSON.parse(line);

    // Réponse interactive transmise à waitMessage() en priorité
    if (pendingResolve) {
      const resolve = pendingResolve;
      pendingResolve = null;
      resolve(msg);
      return;
    }

    // Commandes principales
    if (msg.type === "start" && !started) {
      started = true;
      await run(msg.params).catch((e) => {
        log(`❌ Erreur fatale : ${e.message}`, "err");
        send("done", { success: false });
      });
    } else if (msg.type === "stop") {
      running = false;
      if (browser) {
        try { await browser.close(); } catch {}
      }
    }
  } catch {}
});

send("ready", {});
