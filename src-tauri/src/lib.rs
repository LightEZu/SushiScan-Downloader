// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn run_downloader(url: String, name: String) -> Result<String, String> {
    if url.trim().is_empty() || name.trim().is_empty() {
        return Err("URL et nom du manga sont requis.".into());
    }

    // Ici, tu peux lancer un script externe ou une logique de téléchargement.
    Ok(format!("Téléchargement lancé pour '{}' depuis '{}'", name, url))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet, run_downloader])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
