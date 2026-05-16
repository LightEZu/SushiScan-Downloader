// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Emitter;
use tauri::Manager;
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader, Write};
use std::sync::{Arc, Mutex};
use std::os::windows::process::CommandExt;

// ─── État global du process scraper ──────────────────────────────────────────

struct ScraperState {
    stdin: Option<std::process::ChildStdin>,
    child: Option<std::process::Child>,
}

type SharedState = Arc<Mutex<ScraperState>>;

// ─── Commandes Tauri ──────────────────────────────────────────────────────────

/// Lance le scraper Node.js et établit la communication bidirectionnelle
#[tauri::command]
async fn run_downloader(
    app: tauri::AppHandle,
    window: tauri::Window,
    state: tauri::State<'_, SharedState>,
    url_start: String,
    url_end: Option<String>,
    cbz_name: Option<String>,
    out_dir: String,
    pause: u64,
    headless: bool,
    split_cbz: bool,
) -> Result<(), String> {

    // Si un scraper tourne déjà, on l'arrête proprement
    {
        let mut s = state.lock().unwrap();
        if let Some(ref mut child) = s.child {
            let _ = child.kill();
        }
        s.child = None;
        s.stdin = None;
    }

let scraper_path = app.path()
        .resource_dir()
        .map_err(|e| format!("Impossible de trouver resource_dir : {}", e))?
        .join("bin")
        .join("scraper.cjs");

    // Nettoie le préfixe UNC \\?\ que Node.js ne supporte pas
    let scraper_path_str = scraper_path.to_string_lossy()
        .replace("\\\\?\\", "");

    // Log du chemin pour debug
    let _ = window.emit("scraper-message", serde_json::json!({
        "type": "log",
        "msg": format!("🔍 Chemin scraper : {:?}", scraper_path),
        "tag": "info"
    }).to_string());

    let mut child = Command::new("node")
        .arg(&scraper_path_str)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(0x08000000)
        .spawn()
        .map_err(|e| format!("Impossible de lancer Node.js : {} (chemin: {:?})", e, scraper_path))?;

    let mut stdin = child.stdin.take()
        .ok_or("Impossible d'ouvrir stdin")?;
    let stdout = child.stdout.take()
        .ok_or("Impossible d'ouvrir stdout")?;
    let stderr = child.stderr.take()
        .ok_or("Impossible d'ouvrir stderr")?;

    // Envoie la commande start avec tous les paramètres
    let start_msg = serde_json::json!({
        "type": "start",
        "params": {
            "urlStart":  url_start,
            "urlEnd":    url_end,
            "cbzName":   cbz_name,
            "outDir":    out_dir,
            "pause":     pause,
            "headless":  headless,
            "splitCbz":  split_cbz,
        }
    });

    writeln!(stdin, "{}", start_msg)
        .map_err(|e| format!("Impossible d'écrire dans stdin : {}", e))?;

    // Sauvegarde l'état (stdin + child) pour pouvoir envoyer des messages plus tard
    {
        let mut s = state.lock().unwrap();
        s.stdin = Some(stdin);
        s.child = Some(child);
    }

    // Écoute stderr (erreurs Node.js) en arrière-plan
    let window_err = window.clone();
    tauri::async_runtime::spawn(async move {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(content) = line {
                let err_msg = serde_json::json!({ "type": "log", "msg": format!("⚠️ Node stderr: {}", content), "tag": "err" });
                let _ = window_err.emit("scraper-message", err_msg.to_string());
            }
        }
    });

    // Écoute les messages du scraper en arrière-plan
    let state_clone = Arc::clone(&state);
    tauri::async_runtime::spawn(async move {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(content) => {
                    let _ = window.emit("scraper-message", &content);
                }
                Err(_) => break,
            }
        }
        // Le process s'est terminé — on nettoie
        let mut s = state_clone.lock().unwrap();
        s.stdin = None;
        s.child = None;
    });

    Ok(())
}

/// Envoie un message JSON au scraper via stdin (ex: "continuer", nom CBZ)
#[tauri::command]
async fn send_to_scraper(
    state: tauri::State<'_, SharedState>,
    msg: String,
) -> Result<(), String> {
    let mut s = state.lock().unwrap();
    if let Some(ref mut stdin) = s.stdin {
        writeln!(stdin, "{}", msg)
            .map_err(|e| format!("Erreur d'écriture stdin : {}", e))?;
        Ok(())
    } else {
        Err("Aucun scraper en cours d'exécution".to_string())
    }
}

/// Envoie un signal "stop" au scraper et tue le process
#[tauri::command]
async fn stop_downloader(
    state: tauri::State<'_, SharedState>,
) -> Result<(), String> {
    let mut s = state.lock().unwrap();

    // Envoie stop proprement avant de killer
    if let Some(ref mut stdin) = s.stdin {
        let _ = writeln!(stdin, r#"{{"type":"stop"}}"#);
    }

    if let Some(ref mut child) = s.child {
        let _ = child.kill();
    }

    s.stdin = None;
    s.child = None;
    Ok(())
}

// ─── Point d'entrée ───────────────────────────────────────────────────────────

fn main() {
    let shared_state: SharedState = Arc::new(Mutex::new(ScraperState {
        stdin: None,
        child: None,
    }));

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(shared_state)
        .invoke_handler(tauri::generate_handler![
            run_downloader,
            send_to_scraper,
            stop_downloader,
        ])
        .run(tauri::generate_context!())
        .expect("Erreur au lancement de l'application Tauri");
}