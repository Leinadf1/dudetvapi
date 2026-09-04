import json
import os
import requests

# ======================= CONFIGURAZIONE =======================
JSON_FILE = "public_decrypted/channels/50002.json"
OUTPUT_M3U = "f1_playlist.m3u"  # file locale temporaneo
GIST_ID = "4246b01b8870f49e2cfa50fda49a767e"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # o un PAT se preferisci
# =============================================================

def json_to_m3u(json_data):
    """
    Converte il JSON dei canali in formato M3U con le direttive KODIPROP.
    """
    m3u_lines = ["#EXTM3U"]
    
    for channel in json_data:
        title = channel.get("title", "Canale senza titolo")
        link = channel.get("link", "")
        api = channel.get("api", "")
        logo = channel.get("logo", "")
        channel_type = channel.get("type", "0")  # 0=HLS, 1=DASH con DRM, 2=embed
        
        # Estrae eventuali header dalla link (dopo '|')
        headers = ""
        if "|" in link:
            parts = link.split("|", 1)
            link = parts[0]
            headers = parts[1]  # es. "Referer=https://gooz.aapmains.net"
        
        # Riga #EXTINF
        extinf = f'#EXTINF:-1 tvg-logo="{logo}" group-title="F1",{title}'
        m3u_lines.append(extinf)
        
        # Aggiunge le proprietà KODIPROP in base al tipo
        if channel_type == "1" and api:
            # DASH con DRM (ClearKey)
            m3u_lines.append("#KODIPROP:inputstream.adaptive.manifest_type=mpd")
            m3u_lines.append("#KODIPROP:inputstream.adaptive.license_type=org.w3.clearkey")
            m3u_lines.append(f"#KODIPROP:inputstream.adaptive.license_key={api}")
            if headers:
                m3u_lines.append(f"#KODIPROP:inputstream.adaptive.stream_headers={headers}")
        elif channel_type == "0":
            # HLS
            m3u_lines.append("#KODIPROP:inputstream.adaptive.manifest_type=hls")
            if headers:
                m3u_lines.append(f"#KODIPROP:inputstream.adaptive.stream_headers={headers}")
        elif channel_type == "2":
            # Embed (link diretto)
            # Non servono KODIPROP, è un URL HTML
            pass
        
        # Aggiunge il link
        m3u_lines.append(link)
        m3u_lines.append("")  # riga vuota per separare
    
    return "\n".join(m3u_lines)


def update_gist(gist_id, filename, content, token):
    """
    Aggiorna un file su un Gist di GitHub usando l'API.
    """
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Prima recupera il gist per avere il file sha
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    gist_data = resp.json()
    
    files = gist_data.get("files", {})
    if filename not in files:
        print(f"❌ File '{filename}' non trovato nel Gist. Verrà creato.")
        sha = None
    else:
        sha = files[filename].get("sha")
    
    # Prepara il payload per l'update
    payload = {
        "files": {
            filename: {
                "content": content
            }
        }
    }
    if sha:
        payload["files"][filename]["sha"] = sha
    
    # Invia la richiesta PATCH
    resp = requests.patch(url, headers=headers, json=payload)
    resp.raise_for_status()
    print(f"✅ Gist aggiornato: {gist_id} - {filename}")


def main():
    # Legge il JSON
    if not os.path.exists(JSON_FILE):
        print(f"❌ File {JSON_FILE} non trovato.")
        return
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)
    
    if not channels:
        print("❌ Nessun canale trovato nel JSON.")
        return
    
    print(f"📺 Convertiti {len(channels)} canali in M3U...")
    m3u_content = json_to_m3u(channels)
    
    # Salva localmente (opzionale)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"💾 Salvato localmente: {OUTPUT_M3U}")
    
    # Aggiorna il Gist
    if GITHUB_TOKEN:
        try:
            update_gist(GIST_ID, "F1_CAM_APPLE_TV.m3u", m3u_content, GITHUB_TOKEN)
        except Exception as e:
            print(f"❌ Errore nell'aggiornamento del Gist: {e}")
    else:
        print("⚠️ GITHUB_TOKEN non trovato. Salta l'update del Gist.")


if __name__ == "__main__":
    main()
