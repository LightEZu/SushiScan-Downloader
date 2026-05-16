import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { open } from "@tauri-apps/plugin-dialog";
import "./App.css";

// ─── Constantes ───────────────────────────────────────────────────────────────

const DEFAULT_OUT_DIR = "./downloads";

// ─── Composant principal ──────────────────────────────────────────────────────

function App() {
  // Paramètres
  const [urlStart, setUrlStart]     = useState("");
  const [urlEnd, setUrlEnd]         = useState("");
  const [cbzName, setCbzName]       = useState("");
  const [outDir, setOutDir]         = useState(DEFAULT_OUT_DIR);
  const [pause, setPause]           = useState(30);
  const [headless, setHeadless]     = useState(false);
  const [splitCbz, setSplitCbz]     = useState(false);

  // État runtime
  const [running, setRunning]       = useState(false);
  const [status, setStatus]         = useState("Prêt");
  const [progress, setProgress]     = useState(0);
  const [logs, setLogs]             = useState([]);

  // Dialogue interactif
  const [dialog, setDialog]         = useState(null);
  // dialog = { type: "wait_continue" | "ask_cbz_name", msg: string, slug?: string, cbzInput?: string }

  const logsEndRef = useRef(null);

  // ─── Scroll automatique des logs ───────────────────────────────────────────

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // ─── Écoute des messages Rust ──────────────────────────────────────────────

  useEffect(() => {
    const unlisten = listen("scraper-message", (event) => {
      const raw = event.payload;

      try {
        const data = JSON.parse(raw);

        switch (data.type) {
          case "log":
            addLog(data.msg, data.tag || "info");
            break;

          case "status":
            setStatus(data.msg);
            break;

          case "progress":
            setProgress(data.val ?? 0);
            break;

          case "wait_continue":
            setDialog({ type: "wait_continue", msg: data.msg });
            break;

          case "ask_cbz_name":
            setDialog({
              type: "ask_cbz_name",
              msg: `Chapitre ${data.current}/${data.total} — Choisis le nom du CBZ`,
              slug: data.slug,
              cbzInput: data.slug,
            });
            break;

          case "done":
            setRunning(false);
            setProgress(100);
            setDialog(null);
            if (data.success) {
              addLog(`🎉 Terminé ! Fichiers dans : ${data.outDir ?? data.cbzPath}`, "ok");
              setStatus("Terminé avec succès ✓");
            } else {
              addLog("❌ Téléchargement interrompu ou échoué.", "err");
              setStatus("Échec");
            }
            break;

          case "ready":
            addLog("⚙️  Moteur prêt.", "info");
            break;

          default:
            addLog(data.msg || raw, "info");
        }
      } catch {
        // texte brut
        addLog(raw, "info");
      }
    });

    return () => { unlisten.then((f) => f()); };
  }, []);

  // ─── Helpers ───────────────────────────────────────────────────────────────

  function addLog(msg, tag = "info") {
    if (!msg) return;
    setLogs((prev) => [...prev.slice(-99), { msg, tag }]);
  }

  // ─── Actions ───────────────────────────────────────────────────────────────

  async function handleStart() {
    if (!urlStart) { setStatus("⚠️  URL de début requise"); return; }

    setLogs([]);
    setProgress(0);
    setStatus("Initialisation…");
    setRunning(true);
    setDialog(null);

    try {
      await invoke("run_downloader", {
        urlStart,
        urlEnd:   urlEnd || null,
        cbzName:  cbzName || null,
        outDir:   outDir || DEFAULT_OUT_DIR,
        pause:    Number(pause),
        headless,
        splitCbz,
      });
    } catch (err) {
      setStatus("Erreur : " + err);
      setRunning(false);
    }
  }

  async function handleStop() {
    try {
      await invoke("stop_downloader");
    } catch {}
    setRunning(false);
    setStatus("Arrêt demandé…");
    setDialog(null);
  }

  // Répond "continuer" au scraper
  async function handleContinue() {
    setDialog(null);
    try {
      await invoke("send_to_scraper", { msg: JSON.stringify({ type: "continue" }) });
    } catch {}
  }

  // Répond "stop" depuis la dialog
  async function handleDialogStop() {
    setDialog(null);
    await handleStop();
  }

  // Confirme le nom CBZ
  async function handleCbzConfirm() {
    const name = dialog?.cbzInput || dialog?.slug || "";
    setDialog(null);
    try {
      await invoke("send_to_scraper", { msg: JSON.stringify({ type: "cbz_name", name }) });
    } catch {}
  }

  // ─── Rendu ─────────────────────────────────────────────────────────────────

  return (
    <div className="app">

      {/* ── En-tête ─────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-left">
          <span className="logo-icon">🍣</span>
          <div>
            <h1 className="app-title">SushiScan</h1>
            <p className="app-subtitle">Downloader</p>
          </div>
        </div>
        <div className={`pill ${running ? "pill--running" : "pill--idle"}`}>
          {running ? "● EN COURS" : "○ PRÊT"}
        </div>
      </header>

      {/* ── Formulaire ──────────────────────────────────────────────── */}
      <section className="form-section">

        <div className="field-group">
          <label className="field-label">URL de début <span className="required">*</span></label>
          <input
            className="field-input"
            value={urlStart}
            onChange={(e) => setUrlStart(e.target.value)}
            placeholder="https://sushiscan.net/one-piece-chapitre-1100/"
            disabled={running}
          />
        </div>

        <div className="field-group">
          <label className="field-label">URL de fin <span className="optional">(optionnel — pour une plage)</span></label>
          <input
            className="field-input"
            value={urlEnd}
            onChange={(e) => setUrlEnd(e.target.value)}
            placeholder="https://sushiscan.net/one-piece-chapitre-1110/"
            disabled={running}
          />
        </div>

        <div className="field-row">
          <div className="field-group field-group--grow">
            <label className="field-label">Nom du CBZ <span className="optional">(sans .cbz)</span></label>
            <input
              className="field-input"
              value={cbzName}
              onChange={(e) => setCbzName(e.target.value)}
              placeholder="One_Piece_1100"
              disabled={running || splitCbz}
            />
          </div>

          <div className="field-group field-group--grow">
            <label className="field-label">Dossier de sortie</label>
            <div className="folder-picker">
              <span className="folder-path" title={outDir}>
                {outDir || "Non sélectionné"}
              </span>
              <button
                className="btn btn--folder"
                disabled={running}
                onClick={async () => {
                  const selected = await open({
                    directory: true,
                    multiple: false,
                    title: "Choisir le dossier de destination",
                  });
                  if (selected) setOutDir(selected);
                }}
              >
                📁 Parcourir
              </button>
            </div>
          </div>
        </div>

        <div className="field-row field-row--options">
          <div className="field-group field-group--narrow">
            <label className="field-label">Pause entre chapitres (s)</label>
            <input
              className="field-input field-input--number"
              type="number"
              min={0}
              max={300}
              value={pause}
              onChange={(e) => setPause(e.target.value)}
              disabled={running}
            />
          </div>

          <label className="toggle-label">
            <input
              type="checkbox"
              className="toggle-checkbox"
              checked={headless}
              onChange={(e) => setHeadless(e.target.checked)}
              disabled={running}
            />
            <span className="toggle-track">
              <span className="toggle-thumb" />
            </span>
            <span className="toggle-text">Mode headless</span>
          </label>

          <label className="toggle-label">
            <input
              type="checkbox"
              className="toggle-checkbox"
              checked={splitCbz}
              onChange={(e) => setSplitCbz(e.target.checked)}
              disabled={running}
            />
            <span className="toggle-track">
              <span className="toggle-thumb" />
            </span>
            <span className="toggle-text">Un CBZ par chapitre</span>
          </label>
        </div>

        {/* ── Boutons principaux ─────────────────────────────────── */}
        <div className="btn-row">
          {!running ? (
            <button className="btn btn--primary" onClick={handleStart}>
              ▶ Démarrer
            </button>
          ) : (
            <button className="btn btn--stop" onClick={handleStop}>
              ■ Arrêter
            </button>
          )}
        </div>
      </section>

      {/* ── Progression ─────────────────────────────────────────────── */}
      <section className="progress-section">
        <div className="progress-header">
          <span className="progress-status">{status}</span>
          <span className="progress-pct">{progress}%</span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
      </section>

      {/* ── Console de logs ──────────────────────────────────────────── */}
      <section className="console-section">
        <div className="console-header">
          <span>CONSOLE</span>
          <button
            className="btn-clear"
            onClick={() => setLogs([])}
            disabled={running}
          >
            Effacer
          </button>
        </div>
        <div className="console-body">
          {logs.length === 0 && (
            <div className="log-empty">En attente de logs…</div>
          )}
          {logs.map((entry, i) => (
            <div key={i} className={`log-line log-line--${entry.tag}`}>
              <span className="log-arrow">›</span> {entry.msg}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </section>

      {/* ── Dialog interactif (captcha / nom CBZ) ────────────────────── */}
      {dialog && (
        <div className="dialog-overlay">
          <div className="dialog-box">
            <div className="dialog-icon">
              {dialog.type === "wait_continue" ? "🛡️" : "📦"}
            </div>
            <p className="dialog-msg">{dialog.msg}</p>

            {dialog.type === "ask_cbz_name" && (
              <input
                className="field-input dialog-input"
                value={dialog.cbzInput}
                onChange={(e) =>
                  setDialog((d) => ({ ...d, cbzInput: e.target.value }))
                }
                onKeyDown={(e) => e.key === "Enter" && handleCbzConfirm()}
                autoFocus
              />
            )}

            <div className="dialog-actions">
              <button className="btn btn--ghost" onClick={handleDialogStop}>
                ■ Arrêter
              </button>
              {dialog.type === "wait_continue" ? (
                <button className="btn btn--primary" onClick={handleContinue}>
                  ✓ Continuer
                </button>
              ) : (
                <button className="btn btn--primary" onClick={handleCbzConfirm}>
                  ✓ Confirmer
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;