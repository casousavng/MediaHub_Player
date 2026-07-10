#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# <swiftbar.title>Media Hub (Rádio & YouTube)</swiftbar.title>
# <swiftbar.version>1.0.0</swiftbar.version>
# <swiftbar.author>Antigravity</swiftbar.author>
# <swiftbar.desc>Leitor Unificado de Rádio e YouTube em Background (mpv IPC)</swiftbar.desc>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

import sys
import os
import json
import socket
import subprocess
import time
import shutil
import re
import html

# Prevent python from creating __pycache__ folders and .pyc files
sys.dont_write_bytecode = True

# Prepend typical Homebrew folders to make sure we find 'mpv' and 'yt-dlp'
for path in ["/opt/homebrew/bin", "/usr/local/bin"]:
    if path not in os.environ["PATH"]:
        os.environ["PATH"] = path + os.path.pathsep + os.environ["PATH"]

# Constants
SOCKET_PATH = "/tmp/media-player.sock"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".media_player_state.json")
FAVORITES_FILE = os.path.join(SCRIPT_DIR, ".media_player_favorites.json")
HISTORY_FILE = os.path.join(SCRIPT_DIR, ".media_player_history.json")
IDLE_TITLE = "Em Espera (Sem faixa ativa)"

# Preset Stations (Radios)
STATIONS = [
    # Category: Nacionais e Populares
    {"name": "Rádio Comercial", "url": "https://stream-hls.bauermedia.pt/comercial.aac/playlist.m3u8", "category": "Nacionais"},
    {"name": "Rádio RFM", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/RFMAAC.aac", "category": "Nacionais"},
    {"name": "Rádio M80", "url": "https://stream-hls.bauermedia.pt/m80.aac/playlist.m3u8", "category": "Nacionais"},
    {"name": "Rádio Renascença", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/RADIO_RENASCENCAAAC.aac", "category": "Nacionais"},
    {"name": "Rádio TSF", "url": "http://tsfdirecto.tsf.pt/tsfdirecto.mp3", "category": "Nacionais"},
    {"name": "Rádio Mega Hits", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC.aac", "category": "Nacionais"},
    {"name": "Rádio Cidade FM", "url": "https://stream-hls.bauermedia.pt/cidade.aac/playlist.m3u8", "category": "Nacionais"},
    {"name": "Rádio Observador", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/OBSERVADOR_ADP.m3u8", "category": "Nacionais"},
    {"name": "Batida FM", "url": "https://stream-hls.bauermedia.pt/batidafm.aac/playlist.m3u8", "category": "Nacionais"},

    # Category: Públicas (RTP)
    {"name": "Antena 1", "url": "https://streaming-live.rtp.pt/liveradio/antena180a/playlist.m3u8", "category": "RTP"},
    {"name": "Antena 2", "url": "https://streaming-live.rtp.pt/liveradio/antena280a/playlist.m3u8", "category": "RTP"},
    {"name": "Antena 3", "url": "https://streaming-live.rtp.pt/liveradio/antena380a/playlist.m3u8", "category": "RTP"},
    {"name": "RDP África", "url": "https://streaming-live.rtp.pt/liveradio/rdpafrica80a/playlist.m3u8", "category": "RTP"},
    {"name": "RTP Zig Zag", "url": "https://streaming-live.rtp.pt/liveradio/zigzag80a/playlist.m3u8", "category": "RTP"},

    # Category: Música e Temáticas
    {"name": "Smooth FM", "url": "https://stream-hls.bauermedia.pt/smooth.aac/playlist.m3u8", "category": "Música"},
    {"name": "Smooth FM Soul", "url": "https://stream-icy.bauermedia.pt/smoothsoul.aac", "category": "Música"},
    {"name": "Rádio Orbital", "url": "http://centova.radios.pt:8401/;", "category": "Música"},
    {"name": "Rádio Marginal", "url": "http://centova.radio.com.pt:8499/;", "category": "Música"},
    {"name": "Rádio Radar", "url": "https://proic1.evspt.com/radar_aac", "category": "Música"},
    {"name": "Rádio Oxigénio", "url": "https://proic1.evspt.com/oxigenio_aac", "category": "Música"},
    {"name": "Rádio MEO Music", "url": "http://centova.radio.com.pt:8495/;", "category": "Música"},
    {"name": "Rádio Amália", "url": "http://link.radios.pt/amalia?1487014253471.mp3", "category": "Música"},
    {"name": "RFM Oitentas", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/GR80SRFMAAC.aac", "category": "Música"},
    {"name": "RFM Oceano Pacífico", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/OCEANPACIFICAAC.aac", "category": "Música"},
    {"name": "RFM Dance", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/DANCEONTHEFLOORAAC.aac", "category": "Música"},
    {"name": "RFM Jazzy", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/RFM_JAZZYAAC.aac", "category": "Música"},
    {"name": "M80 80s", "url": "https://stream-hls.bauermedia.pt/m8080.aac/playlist.m3u8", "category": "Música"},
    {"name": "M80 Dance", "url": "https://stream-hls.bauermedia.pt/m80dance.aac/playlist.m3u8", "category": "Música"},
    {"name": "Comercial Rock", "url": "https://stream-hls.bauermedia.pt/rcrock.aac/playlist.m3u8", "category": "Música"},
    {"name": "Comercial Dance", "url": "https://stream-hls.bauermedia.pt/rcdance.aac/playlist.m3u8", "category": "Música"},

    # Category: Locais e Universitárias
    {"name": "Rádio Nova Era", "url": "http://centova.radios.pt:9478/", "category": "Locais"},
    {"name": "Rádio Nova (Porto)", "url": "http://centova.radio.com.pt:9528/;", "category": "Locais"},
    {"name": "Rádio Festival Madeira", "url": "https://audio.serv.pt/8012/stream.mp3", "category": "Locais"},
    {"name": "RUC Coimbra", "url": "https://stream.ruc.pt/high", "category": "Locais"},
    {"name": "RUM Minho", "url": "https://centova.radio.com.pt/proxy/558?mp=/stream", "category": "Locais"},
    {"name": "Rádio Sines", "url": "https://sp0.redeaudio.com/9580/stream", "category": "Locais"},
    {"name": "Fama Rádio", "url": "https://eu10.fastcast4u.com/famaradio", "category": "Locais"},
]

# Dependency Verification
def check_dependencies():
    mpv_ok = shutil.which("mpv") is not None
    ytdl_ok = shutil.which("yt-dlp") is not None
    return mpv_ok, ytdl_ok

# macOS Native Notifications
def show_notification(title, message):
    escaped_title = title.replace('"', '\\"')
    escaped_message = message.replace('"', '\\"')
    applescript = f'display notification "{escaped_message}" with title "{escaped_title}"'
    subprocess.run(["osascript", "-e", applescript])

def get_clipboard_url():
    try:
        proc = subprocess.run(["/usr/bin/pbpaste"], capture_output=True, text=True)
        url = proc.stdout.strip()
        if url.startswith(("http://", "https://")):
            return url
    except Exception:
        pass
    return None

def clean_stream_title(title):
    if not title:
        return ""
    title_str = title.strip()
    
    # Check if this looks like XML/HTML data
    if "<?xml" in title_str or "<RadioInfo" in title_str or (title_str.startswith("<") and title_str.endswith(">")):
        # Extract artist and song title using standard XML tags found in Dalet/Bauer systems
        artist_match = re.search(r"<DB_DALET_ARTIST_NAME>(.*?)</DB_DALET_ARTIST_NAME>", title_str, re.IGNORECASE)
        song_match = re.search(r"<DB_DALET_TITLE_NAME>(.*?)</DB_DALET_TITLE_NAME>", title_str, re.IGNORECASE)
        
        artist = artist_match.group(1).strip() if artist_match else ""
        song = song_match.group(1).strip() if song_match else ""
        
        # Decode HTML/XML entities (like &amp; or &quot;)
        artist = html.unescape(artist)
        song = html.unescape(song)
        
        if artist and song:
            res = f"{artist} - {song}"
        elif song:
            res = song
        elif artist:
            res = artist
        else:
            # Fallback: remove all XML/HTML tags
            cleaned = re.sub(r"<[^>]+>", "", title_str).strip()
            res = html.unescape(" ".join(cleaned.split()))
        return res
        
    # Also strip any generic HTML tags if they exist in normal strings
    if "<" in title_str and ">" in title_str:
        cleaned = re.sub(r"<[^>]+>", "", title_str).strip()
        return html.unescape(" ".join(cleaned.split()))
        
    return html.unescape(title_str)

# State, Custom Stations, Favorites & History Management
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def get_custom_stations():
    state = load_state()
    return state.get("custom_stations", [])

def add_custom_station(name, url):
    state = load_state()
    customs = state.setdefault("custom_stations", [])
    for c in customs:
        if c["url"] == url:
            c["name"] = name
            save_state(state)
            return
    customs.append({"name": name, "url": url, "category": "Personalizadas"})
    save_state(state)
    show_notification("Rádio Adicionada", f"'{name}' foi adicionada às rádios personalizadas.")

def remove_custom_station(url):
    state = load_state()
    customs = state.get("custom_stations", [])
    new_customs = [c for c in customs if c["url"] != url]
    if len(new_customs) < len(customs):
        state["custom_stations"] = new_customs
        save_state(state)
        remove_from_favorites(url)
        show_notification("Rádio Removida", "A estação personalizada foi removida.")

def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_favorites(favorites):
    try:
        with open(FAVORITES_FILE, "w") as f:
            json.dump(favorites, f, indent=2)
    except Exception:
        pass

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def add_to_history(url, title=None, media_type=None):
    if not url:
        return
    history = load_history()
    url = url.strip()
    
    if not media_type:
        media_type = "youtube" if ("youtube.com" in url or "youtu.be" in url) else "radio"
        
    # Check if the most recent item is already this URL
    if history and history[0].get("url") == url:
        if title and not title.startswith("http") and (history[0].get("title") == url or history[0].get("title", "").startswith("http")):
            history[0]["title"] = title
            save_history(history)
        return
        
    history = [item for item in history if item.get("url") != url]
    new_item = {
        "url": url,
        "title": title or url,
        "type": media_type,
        "timestamp": time.time()
    }
    history.insert(0, new_item)
    save_history(history[:50])
    
    if media_type == "youtube" and (not title or title == url or title.startswith("http")):
        resolve_title_background(url)

def clear_history_command(target=None):
    try:
        if not os.path.exists(HISTORY_FILE):
            show_notification("Histórico Limpo", "O histórico de reprodução já está vazio.")
            return
            
        if target is None:
            os.remove(HISTORY_FILE)
            show_notification("Histórico Limpo", "O histórico completo foi apagado.")
            return
            
        history = load_history()
        new_history = []
        for item in history:
            h_type = item.get("type", "radio")
            h_url = item.get("url", "")
            is_playlist = "list=" in h_url or "playlist" in h_url
            
            if target == "radio" and h_type != "radio":
                new_history.append(item)
            elif target == "youtube" and h_type != "youtube":
                new_history.append(item)
            elif target == "songs" and not (h_type == "youtube" and not is_playlist):
                new_history.append(item)
            elif target == "playlists" and not (h_type == "youtube" and is_playlist):
                new_history.append(item)
                
        save_history(new_history)
        
        if target == "radio":
            show_notification("Histórico Rádios", "O histórico de rádios foi apagado.")
        elif target == "youtube":
            show_notification("Histórico YouTube", "O histórico de YouTube foi apagado.")
        elif target == "songs":
            show_notification("Músicas Limpas", "O histórico de músicas do YouTube foi apagado.")
        elif target == "playlists":
            show_notification("Playlists Limpas", "O histórico de playlists do YouTube foi apagado.")
    except Exception as e:
        show_notification("Erro", f"Não foi possível limpar o histórico: {e}")

def remove_history_item(url):
    try:
        history = load_history()
        new_history = [item for item in history if item.get("url") != url]
        save_history(new_history)
        show_notification("Item Removido", "O item foi removido do histórico.")
    except Exception as e:
        show_notification("Erro", f"Não foi possível remover o item: {e}")

def add_current_to_favorites():
    if not is_mpv_running():
        show_notification("Erro", "O player não está a correr.")
        return False
        
    state = load_state()
    mode = state.get("mode", "radio")
    
    path_res = send_mpv_command(["get_property", "path"])
    current_path = path_res.get("data") if path_res.get("error") == "success" else None
    
    if not current_path:
        show_notification("Erro", "Nenhum áudio a tocar no momento.")
        return False
        
    favorites = load_favorites()
    for item in favorites:
        if item.get("url") == current_path:
            show_notification("Favoritos", "Já está nos favoritos.")
            return True
            
    if mode == "radio":
        name = state.get("last_radio_name", current_path)
        for s in STATIONS + state.get("custom_stations", []):
            if s["url"] == current_path:
                name = s["name"]
                break
        new_fav = {
            "url": current_path,
            "title": name,
            "type": "radio",
            "timestamp": time.time()
        }
        favorites.insert(0, new_fav)
        save_favorites(favorites)
        show_notification("Favorito Adicionado", f"Rádio '{name}' adicionada aos favoritos.")
    else:
        title_res = send_mpv_command(["get_property", "media-title"])
        title = title_res.get("data", "") if title_res.get("error") == "success" else ""
        friendly_title = get_cached_title(current_path, title) or title or current_path
        new_fav = {
            "url": current_path,
            "title": friendly_title,
            "type": "youtube",
            "timestamp": time.time()
        }
        favorites.insert(0, new_fav)
        save_favorites(favorites)
        show_notification("Favorito Adicionado", f"Música '{friendly_title}' adicionada aos favoritos.")
    return True

def remove_from_favorites(url):
    favorites = load_favorites()
    new_favs = [item for item in favorites if item.get("url") != url]
    if len(new_favs) < len(favorites):
        save_favorites(new_favs)
        show_notification("Favoritos", "Removido dos favoritos.")
        return True
    return False

def play_all_youtube_favorites():
    favorites = load_favorites()
    yt_favs = [f for f in favorites if f.get("type") == "youtube"]
    if not yt_favs:
        show_notification("Favoritos Vazios", "A sua lista de músicas favoritas está vazia.")
        return False
        
    if not start_mpv():
        return False
        
    send_mpv_command(["playlist-clear"])
    for i, item in enumerate(yt_favs):
        url = item.get("url")
        mode = "replace" if i == 0 else "append"
        send_mpv_command(["loadfile", url, mode])
        
    send_mpv_command(["set_property", "pause", False])
    
    state = load_state()
    state["mode"] = "youtube"
    state["paused"] = False
    save_state(state)
    
    time.sleep(0.2)
    save_current_playlist()
    show_notification("Favoritos", f"A reproduzir {len(yt_favs)} músicas em fila.")
    return True

# IPC Communication with mpv
def send_mpv_command(command_list):
    if not os.path.exists(SOCKET_PATH):
        return {"error": "socket_not_found"}
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1.2)
        s.connect(SOCKET_PATH)
        
        request_id = int(time.time() * 1000)
        payload = {"command": command_list, "request_id": request_id}
        s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        
        buffer = ""
        while True:
            chunk = s.recv(4096).decode("utf-8", errors="ignore")
            if not chunk:
                break
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    data = json.loads(line)
                    if data.get("request_id") == request_id:
                        s.close()
                        return data
                except json.JSONDecodeError:
                    continue
        s.close()
        return {"error": "no_response"}
    except ConnectionRefusedError:
        try:
            os.remove(SOCKET_PATH)
        except OSError:
            pass
        return {"error": "connection_refused"}
    except Exception as e:
        return {"error": str(e)}

def is_mpv_running():
    if not os.path.exists(SOCKET_PATH):
        return False
    res = send_mpv_command(["get_property", "mpv-version"])
    return res.get("error") == "success"

# Background Title Resolution (YouTube)
def resolve_title_background(url):
    python_bin = sys.executable
    script = f"""
import subprocess, json, os, sys
url = {repr(url)}
state_file = {repr(STATE_FILE)}
history_file = {repr(HISTORY_FILE)}

for path in ["/opt/homebrew/bin", "/usr/local/bin"]:
    if path not in os.environ["PATH"]:
        os.environ["PATH"] = path + os.path.pathsep + os.environ["PATH"]

try:
    title = None
    entries_map = {{}}
    
    # 1. Check if it's a playlist URL
    if "list=" in url or "playlist" in url:
        proc_pl = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", url],
            capture_output=True,
            text=True,
            timeout=15
        )
        if proc_pl.returncode == 0:
            data = json.loads(proc_pl.stdout)
            title = data.get("title")
            for entry in data.get("entries", []):
                e_url = entry.get("url") or (f"https://www.youtube.com/watch?v={{entry.get('id')}}" if entry.get('id') else None)
                e_title = entry.get("title")
                if e_url and e_title:
                    entries_map[e_url] = e_title
                    
    # 2. If not a playlist, or if playlist title fetch failed, treat as single video
    if not title:
        proc = subprocess.run(
            ["yt-dlp", "--get-title", "--no-warnings", "--playlist-items", "1", url],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode == 0:
            title = proc.stdout.strip()
            if title:
                entries_map[url] = title

    # 3. Update titles_cache in state_file
    if entries_map or title:
        state = {{}}
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
            except Exception:
                pass
                
        cache = state.setdefault("titles_cache", {{}})
        updated = False
        
        # Add playlist/video title itself to cache
        if title and cache.get(url) != title:
            cache[url] = title
            updated = True
            
        # Add all individual playlist entries to cache
        for e_url, e_title in entries_map.items():
            if cache.get(e_url) != e_title:
                cache[e_url] = e_title
                updated = True
                
        if updated:
            try:
                with open(state_file, "w") as f:
                    json.dump(state, f, indent=2)
            except Exception:
                pass

        # 4. Also update history file safely for any matching URLs
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
                h_updated = False
                for item in history:
                    item_url = item.get("url")
                    if item_url == url and title and item.get("title") != title:
                        item["title"] = title
                        h_updated = True
                    elif item_url in entries_map and item.get("title") != entries_map[item_url]:
                        item["title"] = entries_map[item_url]
                        h_updated = True
                if h_updated:
                    with open(history_file, "w") as f:
                        json.dump(history, f, indent=2)
            except Exception:
                pass
except Exception:
    pass
"""
    subprocess.Popen(
        [python_bin, "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

def resolve_missing_titles():
    python_bin = sys.executable
    script = f"""
import subprocess, json, os, sys, time
state_file = {repr(STATE_FILE)}
history_file = {repr(HISTORY_FILE)}

for path in ["/opt/homebrew/bin", "/usr/local/bin"]:
    if path not in os.environ["PATH"]:
        os.environ["PATH"] = path + os.path.pathsep + os.environ["PATH"]

try:
    if not os.path.exists(state_file):
        sys.exit(0)
        
    with open(state_file, "r") as f:
        state = json.load(f)
        
    urls = state.get("yt_urls", [])
    cache = state.setdefault("titles_cache", {{}})
    
    missing_urls = [u for u in urls if u and u not in cache]
    if not missing_urls:
        sys.exit(0)
        
    updated = False
    for url in missing_urls[:15]:
        title = None
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
                for item in history:
                    if item.get("url") == url:
                        t = item.get("title")
                        if t and not t.startswith("http"):
                            title = t
                            break
            except Exception:
                pass
                
        if not title:
            proc = subprocess.run(
                ["yt-dlp", "--get-title", "--no-warnings", "--playlist-items", "1", url],
                capture_output=True,
                text=True,
                timeout=8
            )
            if proc.returncode == 0:
                title = proc.stdout.strip()
                
        if title:
            try:
                with open(state_file, "r") as f:
                    curr_state = json.load(f)
            except Exception:
                curr_state = state
            
            curr_cache = curr_state.setdefault("titles_cache", {{}})
            curr_cache[url] = title
            state = curr_state
            updated = True
            
            try:
                with open(state_file, "w") as f:
                    json.dump(state, f, indent=2)
            except Exception:
                pass
                
            time.sleep(0.5)
except Exception:
    pass
"""
    subprocess.Popen(
        [python_bin, "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

def update_title_cache(url, title):
    if not url or not title or title.startswith(("http://", "https://", "A carregar stream")):
        return
    try:
        state = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        
        cache = state.setdefault("titles_cache", {})
        if cache.get(url) != title:
            cache[url] = title
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
    except Exception:
        pass

def get_cached_title(url, mpv_title=None):
    if mpv_title and not mpv_title.startswith(("http://", "https://", "A carregar stream")):
        update_title_cache(url, mpv_title)
        return mpv_title
        
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            cache = state.get("titles_cache", {})
            if url in cache:
                title = cache[url]
                if title and not title.startswith(("http://", "https://", "A carregar stream")):
                    return title
        except Exception:
            pass
            
    history = load_history()
    for item in history:
        if item.get("url") == url:
            title = item.get("title")
            if title and not title.startswith(("http://", "https://", "A carregar stream")):
                update_title_cache(url, title)
                return title
    return None

def save_current_playlist():
    if not os.path.exists(SOCKET_PATH):
        return
    res = send_mpv_command(["get_property", "playlist"])
    if res.get("error") == "success" and res.get("data"):
        playlist = res.get("data")
        urls = [item.get("filename") for item in playlist if item.get("filename")]
        current_index = 0
        for i, item in enumerate(playlist):
            if item.get("current"):
                current_index = i
                break
                
        state = load_state()
        if state.get("mode") == "youtube":
            if state.get("yt_urls") == urls and state.get("yt_current_index") == current_index:
                return
                
            state["yt_urls"] = urls
            state["yt_current_index"] = current_index
            state["updated_at"] = time.time()
            
            titles_cache = state.setdefault("titles_cache", {})
            for item in playlist:
                f_name = item.get("filename")
                t_title = item.get("title")
                if f_name and t_title and not t_title.startswith("http"):
                    titles_cache[f_name] = t_title
                    
            save_state(state)
            resolve_missing_titles()

# Core Controls
def start_mpv():
    if is_mpv_running():
        return True
        
    mpv_bin = shutil.which("mpv")
    if not mpv_bin:
        return False
        
    if os.path.exists(SOCKET_PATH):
        try:
            os.remove(SOCKET_PATH)
        except OSError:
            pass
            
    # Optimized background mpv parameters for Apple Silicon (M1+)
    cmd = [
        mpv_bin,
        "--no-video",
        f"--input-ipc-server={SOCKET_PATH}",
        "--idle=yes",
        "--loop-playlist=force",
        "--ytdl-raw-options=yes-playlist=",
        "--ytdl-format=bestaudio[ext=m4a]/bestaudio",
        "--demuxer-max-bytes=5M",
        "--demuxer-max-back-bytes=1M",
        "--audio-pitch-correction=no",
    ]
    
    state = load_state()
    normalize_audio = state.get("normalize_audio", True)
    if normalize_audio:
        cmd.append("--af=dynaudnorm")
        
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )
    
    for _ in range(30):
        if is_mpv_running():
            state = load_state()
            mode = state.get("mode")
            was_paused = state.get("paused", False)
            
            if mode == "radio":
                last_url = state.get("last_radio_url")
                if last_url:
                    send_mpv_command(["loadfile", last_url, "replace"])
                    if was_paused:
                        send_mpv_command(["set_property", "pause", True])
            elif mode == "youtube":
                yt_urls = state.get("yt_urls", [])
                current_index = state.get("yt_current_index", 0)
                if yt_urls:
                    for i, url in enumerate(yt_urls):
                        m = "replace" if i == 0 else "append"
                        send_mpv_command(["loadfile", url, m])
                    if 0 <= current_index < len(yt_urls):
                        send_mpv_command(["set_property", "playlist-pos", current_index])
                    if was_paused:
                        send_mpv_command(["set_property", "pause", True])
            return True
        time.sleep(0.1)
        
    return False

def play_command(url, name=None, media_type=None):
    if not start_mpv():
        return False
        
    if not media_type:
        media_type = "youtube" if ("youtube.com" in url or "youtu.be" in url) else "radio"
        
    if media_type == "radio":
        send_mpv_command(["playlist-clear"])
        res = send_mpv_command(["loadfile", url, "replace"])
        if res.get("error") == "success":
            state = load_state()
            state["mode"] = "radio"
            state["last_radio_url"] = url
            state["last_radio_name"] = name or url
            state["paused"] = False
            save_state(state)
            
            add_to_history(url, name, "radio")
            show_notification("Rádio Sintonizada", name or url)
            return True
            
    elif media_type == "youtube":
        res = send_mpv_command(["loadfile", url, "replace"])
        if res.get("error") == "success":
            state = load_state()
            state["mode"] = "youtube"
            state["last_youtube_url"] = url
            state["paused"] = False
            save_state(state)
            
            time.sleep(0.2)
            save_current_playlist()
            add_to_history(url, None, "youtube")
            
            friendly_title = get_cached_title(url) or url
            show_notification("A Reproduzir (YT)", friendly_title)
            return True
            
    return False

def add_youtube_url(url):
    if not start_mpv():
        return False
        
    state = load_state()
    current_mode = state.get("mode")
    
    if current_mode == "radio":
        send_mpv_command(["playlist-clear"])
        res = send_mpv_command(["loadfile", url, "replace"])
    else:
        res = send_mpv_command(["loadfile", url, "append-play"])
        
    state["mode"] = "youtube"
    state["paused"] = False
    save_state(state)
    
    time.sleep(0.25)
    save_current_playlist()
    add_to_history(url, None, "youtube")
    
    friendly_title = get_cached_title(url) or url
    show_notification("Fila / Playlist YT", f"Adicionado: {friendly_title}")
    return res.get("error") == "success"

def toggle_normalize_command():
    state = load_state()
    current = state.get("normalize_audio", True)
    new_state = not current
    state["normalize_audio"] = new_state
    save_state(state)
    
    if is_mpv_running():
        if new_state:
            send_mpv_command(["set_property", "af", "dynaudnorm"])
        else:
            send_mpv_command(["set_property", "af", ""])
            
    status_str = "Ativada" if new_state else "Desativada"
    show_notification("Normalização de Áudio", f"A normalização foi {status_str.lower()}.")
    return True

def pause_command():
    res = send_mpv_command(["set_property", "pause", True])
    if res.get("error") == "success":
        state = load_state()
        state["paused"] = True
        save_state(state)
        show_notification("Player Pausado", "A reprodução foi interrompida.")
        return True
    return False

def resume_command():
    if not is_mpv_running():
        return start_mpv()
    res = send_mpv_command(["set_property", "pause", False])
    if res.get("error") == "success":
        state = load_state()
        state["paused"] = False
        save_state(state)
        show_notification("Player Retomado", "A reprodução foi retomada.")
        return True
    return False

def toggle_command():
    if not is_mpv_running():
        return start_mpv()
        
    pause_res = send_mpv_command(["get_property", "pause"])
    was_paused = pause_res.get("data", False) if pause_res.get("error") == "success" else False
    
    res = send_mpv_command(["cycle", "pause"])
    if res.get("error") == "success":
        state = load_state()
        state["paused"] = not was_paused
        save_state(state)
        action = "retomada" if was_paused else "pausada"
        show_notification("Media Hub", f"Reprodução {action}.")
        return True
    return False

def mute_command():
    if not is_mpv_running():
        return False
    res = send_mpv_command(["cycle", "mute"])
    if res.get("error") == "success":
        mute_res = send_mpv_command(["get_property", "mute"])
        is_muted = mute_res.get("data", False) if mute_res.get("error") == "success" else False
        status_msg = "Mudo ativado." if is_muted else "Mudo desativado."
        show_notification("Saída de Áudio", status_msg)
        return True
    return False

def adjust_volume_command(amount):
    if not is_mpv_running():
        return False
    res = send_mpv_command(["get_property", "volume"])
    if res.get("error") == "success":
        current = res.get("data", 100.0)
        if current is None:
            current = 100.0
        new_vol = max(0.0, min(130.0, current + amount))
        set_res = send_mpv_command(["set_property", "volume", new_vol])
        if set_res.get("error") == "success":
            show_notification("Volume", f"Volume: {int(new_vol)}%")
            return True
    return False

def stop_command():
    if not is_mpv_running():
        return True
    send_mpv_command(["quit"])
    if os.path.exists(SOCKET_PATH):
        try:
            os.remove(SOCKET_PATH)
        except OSError:
            pass
            
    state = load_state()
    state["paused"] = True
    save_state(state)
    show_notification("Media Hub Desligado", "O leitor em background foi parado.")
    return True

def next_command():
    if not is_mpv_running():
        return False
    res = send_mpv_command(["playlist-next"])
    if res.get("error") == "success":
        time.sleep(0.3)
        path_res = send_mpv_command(["get_property", "path"])
        current_path = path_res.get("data") if path_res.get("error") == "success" else None
        if current_path:
            title_res = send_mpv_command(["get_property", "media-title"])
            title = title_res.get("data", "") if title_res.get("error") == "success" else ""
            friendly_title = get_cached_title(current_path, title) or title or "Nova faixa"
            if len(friendly_title) > 60:
                friendly_title = friendly_title[:57] + "..."
            show_notification("Seguinte", friendly_title)
        else:
            show_notification("Media Hub", "A avançar para a próxima faixa.")
        return True
    return False

def prev_command():
    if not is_mpv_running():
        return False
    res = send_mpv_command(["playlist-prev"])
    if res.get("error") == "success":
        time.sleep(0.3)
        path_res = send_mpv_command(["get_property", "path"])
        current_path = path_res.get("data") if path_res.get("error") == "success" else None
        if current_path:
            title_res = send_mpv_command(["get_property", "media-title"])
            title = title_res.get("data", "") if title_res.get("error") == "success" else ""
            friendly_title = get_cached_title(current_path, title) or title or "Faixa anterior"
            if len(friendly_title) > 60:
                friendly_title = friendly_title[:57] + "..."
            show_notification("Anterior", friendly_title)
        else:
            show_notification("Media Hub", "A voltar para a faixa anterior.")
        return True
    return False

def clear_command():
    if not is_mpv_running():
        return False
    res = send_mpv_command(["playlist-clear"])
    save_current_playlist()
    if res.get("error") == "success":
        show_notification("Fila de Reprodução", "Fila limpa com sucesso.")
        return True
    return False

def select_track(index):
    if not is_mpv_running():
        return False
    try:
        idx = int(index)
        res = send_mpv_command(["set_property", "playlist-pos", idx])
        if res.get("error") == "success":
            time.sleep(0.3)
            path_res = send_mpv_command(["get_property", "path"])
            current_path = path_res.get("data") if path_res.get("error") == "success" else None
            if current_path:
                title_res = send_mpv_command(["get_property", "media-title"])
                title = title_res.get("data", "") if title_res.get("error") == "success" else ""
                friendly_title = get_cached_title(current_path, title) or title or "Faixa selecionada"
                if len(friendly_title) > 60:
                    friendly_title = friendly_title[:57] + "..."
                show_notification("Música Selecionada", friendly_title)
            else:
                show_notification("Media Hub", "Música alterada.")
            return True
        return False
    except ValueError:
        return False

def set_audio_device(device_name):
    if not is_mpv_running():
        return False
    res = send_mpv_command(["set_property", "audio-device", device_name])
    if res.get("error") == "success":
        desc = device_name
        dev_res = send_mpv_command(["get_property", "audio-device-list"])
        if dev_res.get("error") == "success":
            for d in dev_res.get("data", []):
                if d.get("name") == device_name:
                    desc = d.get("description", device_name)
                    break
        show_notification("Saída de Áudio", f"Alterada para: {desc}")
        return True
    return False

def get_player_status():
    state = load_state()
    current_mode = state.get("mode", "radio")
    
    if not is_mpv_running():
        if current_mode == "radio":
            station_name = state.get("last_radio_name", "Nenhuma rádio")
            path = state.get("last_radio_url")
            title = IDLE_TITLE
        else:
            station_name = "Nenhuma rádio"
            path = state.get("last_youtube_url")
            title = state.get("last_youtube_title", IDLE_TITLE)
            
        return {
            "status": "stopped",
            "paused": True,
            "muted": False,
            "path": path,
            "mode": current_mode,
            "title": title,
            "station_name": station_name,
            "time_pos": 0.0,
            "duration": 0.0,
            "media_title": "",
            "volume": 100.0,
            "codec": "",
            "bitrate": 0,
            "samplerate": 0,
            "channels": 0
        }
        
    pause_res = send_mpv_command(["get_property", "pause"])
    mute_res = send_mpv_command(["get_property", "mute"])
    path_res = send_mpv_command(["get_property", "path"])
    title_res = send_mpv_command(["get_property", "media-title"])
    time_res = send_mpv_command(["get_property", "time-pos"])
    duration_res = send_mpv_command(["get_property", "duration"])
    vol_res = send_mpv_command(["get_property", "volume"])
    codec_res = send_mpv_command(["get_property", "audio-codec"])
    bitrate_res = send_mpv_command(["get_property", "audio-bitrate"])
    audio_params_res = send_mpv_command(["get_property", "audio-params"])
    
    is_paused = pause_res.get("data", False) if pause_res.get("error") == "success" else False
    is_muted = mute_res.get("data", False) if mute_res.get("error") == "success" else False
    current_path = path_res.get("data") if path_res.get("error") == "success" else None
    media_title = title_res.get("data", "") if title_res.get("error") == "success" else ""
    vol = vol_res.get("data", 100.0) if vol_res.get("error") == "success" else 100.0
    vol = vol if vol is not None else 100.0
    codec = codec_res.get("data", "") if codec_res.get("error") == "success" else ""
    bitrate = bitrate_res.get("data", 0) if bitrate_res.get("error") == "success" else 0
    
    audio_params = audio_params_res.get("data") if audio_params_res.get("error") == "success" else None
    samplerate = 0
    channels = 0
    if audio_params and isinstance(audio_params, dict):
        samplerate = audio_params.get("samplerate", 0)
        channels = audio_params.get("channels", "") or audio_params.get("channel-count", 0)
    if media_title:
        is_youtube = False
        if current_path and ("youtube.com" in current_path or "youtu.be" in current_path):
            is_youtube = True
        elif current_mode == "youtube":
            is_youtube = True
        if not is_youtube:
            media_title = clean_stream_title(media_title)
    time_pos = time_res.get("data", 0.0) if time_res.get("error") == "success" else 0.0
    duration = duration_res.get("data", 0.0) if duration_res.get("error") == "success" else 0.0
    
    if current_path:
        if "youtube.com" in current_path or "youtu.be" in current_path:
            if current_mode != "youtube":
                current_mode = "youtube"
                state["mode"] = "youtube"
                save_state(state)
        else:
            is_radio = False
            for s in STATIONS + state.get("custom_stations", []):
                if s["url"] == current_path:
                    is_radio = True
                    break
            if not is_radio and not ("youtube.com" in current_path or "youtu.be" in current_path):
                is_radio = True
            if is_radio and current_mode != "radio":
                current_mode = "radio"
                state["mode"] = "radio"
                save_state(state)
                
    station_name = "Estação Personalizada"
    youtube_title = IDLE_TITLE
    
    if current_mode == "radio":
        if current_path:
            found = False
            for s in STATIONS + state.get("custom_stations", []):
                if s["url"] == current_path:
                    station_name = s["name"]
                    found = True
                    break
            if not found:
                station_name = state.get("last_radio_name", "Estação Personalizada")
        else:
            station_name = state.get("last_radio_name", "Nenhuma rádio")
            
        if media_title and (media_title == current_path or media_title == station_name or media_title.startswith("http")):
            media_title = ""
    else:
        if current_path:
            youtube_title = get_cached_title(current_path, media_title) or media_title or current_path
            if youtube_title.startswith(("http://", "https://")):
                youtube_title = "A carregar stream do YouTube..."
            state["last_youtube_title"] = youtube_title
            state["last_youtube_url"] = current_path
            save_state(state)
        else:
            youtube_title = state.get("last_youtube_title", IDLE_TITLE)
            
    if current_mode == "youtube" and current_path:
        save_current_playlist()
        friendly_title = youtube_title if (youtube_title and not youtube_title.startswith(("http://", "https://", "A carregar stream"))) else None
        add_to_history(current_path, friendly_title, "youtube")
    elif current_mode == "radio" and current_path:
        add_to_history(current_path, station_name, "radio")
        
    return {
        "status": "paused" if is_paused else ("playing" if current_path else "stopped"),
        "paused": is_paused,
        "muted": is_muted,
        "path": current_path or state.get("last_radio_url" if current_mode == "radio" else "last_youtube_url"),
        "mode": current_mode,
        "title": youtube_title,
        "station_name": station_name,
        "time_pos": time_pos,
        "duration": duration,
        "media_title": media_title,
        "volume": vol,
        "codec": codec,
        "bitrate": bitrate,
        "samplerate": samplerate,
        "channels": channels
    }

# Dialog Handlers
def add_via_clipboard():
    url = get_clipboard_url()
    if url:
        if "youtube.com" in url or "youtu.be" in url:
            add_youtube_url(url)
        else:
            applescript = """
            tell application "System Events"
                activate
                try
                    set theResponse to display dialog "URL de Rádio detetado. Insira o nome da rádio personalizada:" default answer "Rádio Personalizada" with title "Media Hub" buttons {"Cancelar", "Adicionar"} default button "Adicionar"
                    return text returned of theResponse
                on error
                    return ""
                end try
            end tell
            """
            try:
                proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
                if proc.returncode == 0:
                    name = proc.stdout.strip()
                    if name:
                        add_custom_station(name, url)
                        play_command(url, name, "radio")
            except Exception as e:
                show_notification("Erro", str(e))
    else:
        show_notification("Clipboard Vazio", "Nenhum URL válido detetado no clipboard.")

def add_via_applescript():
    applescript = """
    tell application "System Events"
        activate
        try
            set theChoice to choose from list {"📻 Rádio Personalizada", "🎥 URL do YouTube"} with title "Media Hub" with prompt "O que deseja adicionar?" default items {"📻 Rádio Personalizada"} OK button name "Seguinte" cancel button name "Cancelar"
            if theChoice is false then return ""
            set choiceText to item 1 of theChoice
            
            if choiceText is "📻 Rádio Personalizada" then
                set theName to display dialog "Nome da Estação de Rádio:" default answer "" with title "Adicionar Rádio" buttons {"Cancelar", "Seguinte"} default button "Seguinte"
                set nameText to text returned of theName
                if nameText is "" then return ""
                
                set theURL to display dialog "URL de Streaming (mp3, aac, m3u8):" default answer "http://" with title "Adicionar Rádio" buttons {"Cancelar", "Adicionar"} default button "Adicionar"
                set urlText to text returned of theURL
                if urlText is "" then return ""
                
                return "radio|||" & nameText & "|||" & urlText
            else
                set theURL to display dialog "Insira o URL do YouTube (vídeos ou playlists):" default answer "" with title "Adicionar YouTube" buttons {"Cancelar", "Adicionar"} default button "Adicionar"
                set urlText to text returned of theURL
                if urlText is "" then return ""
                
                return "youtube|||" & urlText
            end if
        on error
            return ""
        end try
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if proc.returncode == 0:
            result = proc.stdout.strip()
            if not result:
                return
            if result.startswith("radio|||"):
                _, name, url = result.split("|||", 2)
                add_custom_station(name.strip(), url.strip())
                play_command(url.strip(), name.strip(), "radio")
            elif result.startswith("youtube|||"):
                _, url = result.split("|||", 1)
                add_youtube_url(url.strip())
    except Exception as e:
        show_notification("Erro", str(e))

def add_radio_clipboard():
    url = get_clipboard_url()
    if not url:
        show_notification("Clipboard Vazio", "Nenhum URL válido no clipboard.")
        return
    if "youtube.com" in url or "youtu.be" in url:
        show_notification("Media Hub", "O URL detetado é do YouTube. Use a opção correspondente.")
        return
    applescript = f"""
    tell application "System Events"
        activate
        try
            set theResponse to display dialog "URL de Rádio detetado. Insira o nome da rádio personalizada:" default answer "Rádio Personalizada" with title "Adicionar Rádio" buttons {{"Cancelar", "Adicionar"}} default button "Adicionar"
            return text returned of theResponse
        on error
            return ""
        end try
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if proc.returncode == 0:
            name = proc.stdout.strip()
            if name:
                add_custom_station(name, url)
                play_command(url, name, "radio")
    except Exception as e:
        show_notification("Erro", str(e))

def add_radio_gui():
    applescript = """
    tell application "System Events"
        activate
        try
            set theName to display dialog "Nome da Estação de Rádio:" default answer "" with title "Adicionar Rádio" buttons {"Cancelar", "Seguinte"} default button "Seguinte"
            set nameText to text returned of theName
            if nameText is "" then return ""
            
            set theURL to display dialog "URL de Streaming (mp3, aac, m3u8):" default answer "http://" with title "Adicionar Rádio" buttons {"Cancelar", "Adicionar"} default button "Adicionar"
            set urlText to text returned of theURL
            if urlText is "" then return ""
            
            return nameText & "|||" & urlText
        on error
            return ""
        end try
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if proc.returncode == 0:
            result = proc.stdout.strip()
            if result and "|||" in result:
                name, url = result.split("|||", 1)
                add_custom_station(name.strip(), url.strip())
                play_command(url.strip(), name.strip(), "radio")
    except Exception as e:
        show_notification("Erro", str(e))

def add_youtube_clipboard():
    url = get_clipboard_url()
    if not url:
        show_notification("Clipboard Vazio", "Nenhum URL de YouTube no clipboard.")
        return
    if not ("youtube.com" in url or "youtu.be" in url):
        show_notification("Media Hub", "O URL no clipboard não pertence ao YouTube.")
        return
    add_youtube_url(url)

def add_youtube_gui():
    applescript = """
    tell application "System Events"
        activate
        try
            set theURL to display dialog "Insira o URL do YouTube (vídeos ou playlists):" default answer "" with title "Adicionar YouTube" buttons {"Cancelar", "Adicionar"} default button "Adicionar"
            set urlText to text returned of theURL
            return urlText
        on error
            return ""
        end try
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if proc.returncode == 0:
            url = proc.stdout.strip()
            if url:
                add_youtube_url(url)
    except Exception as e:
        show_notification("Erro", str(e))

def search_youtube_gui(search_type):
    state = load_state()
    search_limit = state.get("search_limit", 5)
    
    prompt = "Introduza o termo a pesquisar (Música/Vídeo):" if search_type == "video" else "Introduza o termo a pesquisar (Playlist):"
    title = "Pesquisa no YouTube"
    
    applescript_prompt = f"""
    tell application "System Events"
        activate
        try
            set theResponse to display dialog "{prompt}" default answer "" with title "{title}" buttons {{"Cancelar", "Pesquisar"}} default button "Pesquisar"
            return text returned of theResponse
        on error
            return ""
        end try
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", applescript_prompt], capture_output=True, text=True)
        if proc.returncode != 0:
            return
        query = proc.stdout.strip()
        if not query:
            return
    except Exception as e:
        show_notification("Erro", str(e))
        return

    # Check if the query is actually a URL, and if so, add it directly
    if query.startswith(("http://", "https://", "www.")):
        add_youtube_url(query)
        return

    show_notification("Pesquisa YouTube", f"A procurar '{query}'...")

    if search_type == "video":
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--skip-download",
            "--no-warnings",
            "--ignore-errors",
            "--playlist-end", str(search_limit),
            f"ytsearch{search_limit}:{query}"
        ]
    else:
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAw%253D%253D"
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--skip-download",
            "--no-warnings",
            "--ignore-errors",
            "--playlist-end", str(search_limit),
            search_url
        ]

    try:
        proc_search = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        results = []
        for line in proc_search.stdout.splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                title_val = data.get("title")
                url_val = data.get("url")
                if not url_val and data.get("id"):
                    url_val = f"https://www.youtube.com/watch?v={data.get('id')}"
                if title_val and url_val:
                    results.append((title_val, url_val))
            except Exception:
                pass
    except subprocess.TimeoutExpired:
        show_notification("Pesquisa Expirou", "A pesquisa demorou demasiado tempo. Verifique a sua ligação.")
        return
    except Exception as e:
        show_notification("Erro de Pesquisa", str(e))
        return

    if not results:
        err_msg = proc_search.stderr.strip() if 'proc_search' in locals() else ""
        if err_msg:
            lines = [l.strip() for l in err_msg.splitlines() if l.strip()]
            first_err = lines[0] if lines else err_msg
            if first_err.startswith("ERROR:"):
                first_err = first_err[6:].strip()
            show_notification("Pesquisa Sem Resultados", f"Erro: {first_err[:80]}")
        else:
            show_notification("Pesquisa YouTube", "Nenhum resultado encontrado.")
        return

    list_items = []
    url_map = {}
    for idx, (t, u) in enumerate(results, 1):
        clean_t = t.replace('\\', '\\\\').replace('"', '\\"')
        if len(clean_t) > 75:
            clean_t = clean_t[:72] + "..."
        display_str = f"{idx}. {clean_t}"
        list_items.append(f'"{display_str}"')
        url_map[display_str] = u

    items_list_str = ", ".join(list_items)
    prompt_choose = "Selecione o item para adicionar à reprodução:"
    applescript_choose = f"""
    tell application "System Events"
        activate
        try
            set theChoice to choose from list {{{items_list_str}}} with title "Resultados da Pesquisa" with prompt "{prompt_choose}" OK button name "Adicionar" cancel button name "Cancelar"
            if theChoice is false then return ""
            return item 1 of theChoice
        on error
            return ""
        end try
    end tell
    """
    try:
        proc_choose = subprocess.run(["osascript", "-e", applescript_choose], capture_output=True, text=True)
        if proc_choose.returncode != 0:
            return
        chosen = proc_choose.stdout.strip()
        if not chosen:
            return
        if chosen in url_map:
            chosen_url = url_map[chosen]
            add_youtube_url(chosen_url)
    except Exception as e:
        show_notification("Erro", str(e))

def change_search_limit_gui():
    state = load_state()
    current = state.get("search_limit", 5)
    applescript = f"""
    tell application "System Events"
        activate
        try
            set theResponse to display dialog "Introduza o número de resultados a obter nas pesquisas (1-20):" default answer "{current}" with title "Limite de Pesquisa YouTube" buttons {{"Cancelar", "Confirmar"}} default button "Confirmar"
            return text returned of theResponse
        on error
            return ""
        end try
    end tell
    """
    try:
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if proc.returncode == 0:
            val_str = proc.stdout.strip()
            if val_str.isdigit():
                val = int(val_str)
                if 1 <= val <= 20:
                    state["search_limit"] = val
                    save_state(state)
                    show_notification("Configuração Guardada", f"O limite de pesquisa foi alterado para {val} resultados.")
                else:
                    show_notification("Valor Inválido", "O limite deve estar entre 1 e 20.")
    except Exception as e:
        show_notification("Erro", str(e))

# Helpers
def format_time(seconds):
    if seconds is None:
        return "00:00"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def install_dependencies():
    print("=" * 60)
    print(" Media Hub - Instalação de Dependências ".center(60, "="))
    print("=" * 60)
    print("Este assistente irá instalar o 'mpv' e o 'yt-dlp' via Homebrew.")
    print("Por favor, aguarde...")
    print()
    
    brew_bin = shutil.which("brew")
    if not brew_bin:
        for p in ["/opt/homebrew/bin/brew", "/usr/local/bin/brew"]:
            if os.path.exists(p):
                brew_bin = p
                break
    if not brew_bin:
        brew_bin = "/opt/homebrew/bin/brew"
        
    if not os.path.exists(brew_bin):
        print("Homebrew não encontrado!")
        print("Por favor, instale o Homebrew em https://brew.sh e voltar a tentar.")
        print()
        print("Pressione ENTER para fechar esta janela...")
        input()
        return
        
    cmd = [brew_bin, "install", "mpv", "yt-dlp"]
    print(f"A executar: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    print()
    print("=" * 60)
    print("Instalação concluída com sucesso! Já pode usar o Media Hub.")
    print("Pressione ENTER para fechar esta janela...")
    input()

def resize_terminal():
    if os.environ.get("TERM_PROGRAM") == "Apple_Terminal" or "TERM" in os.environ:
        applescript = """
        tell application "Terminal"
            try
                set number of columns of window 1 to 72
                set number of rows of window 1 to 26
            end try
        end tell
        """
        try:
            subprocess.run(["osascript", "-e", applescript], capture_output=True)
        except Exception:
            pass

# Interactive TUI Terminal Interface
def draw_tui(current_tab, input_buffer="", input_prompt_type=""):
    status = get_player_status()
    mpv_ok, ytdl_ok = check_dependencies()
    
    # ANSI color codes
    CLR_RST = "\033[0m"
    CLR_BLD = "\033[1m"
    CLR_RED = "\033[1;31m"
    CLR_GRN = "\033[1;32m"
    CLR_YLW = "\033[1;33m"
    CLR_BLU = "\033[1;34m"
    CLR_CYN = "\033[1;36m"
    CLR_WHT = "\033[1;37m"
    CLR_GRY = "\033[90m"
    
    lines = []
    lines.append("\033[H\033[2J")  # Clear terminal screen
    lines.append(f"{CLR_CYN}┌──────────────────────────────────────────────────────────────┐{CLR_RST}")
    
    title_text = "🎧  MEDIA HUB - RÁDIO & YOUTUBE PLAYER"
    lines.append(f"{CLR_CYN}│{CLR_RST}{CLR_BLD}{title_text.center(60)}{CLR_RST}{CLR_CYN}│{CLR_RST}")
    lines.append(f"{CLR_CYN}├──────────────────────────────────────────────────────────────┤{CLR_RST}")
    
    if not mpv_ok or not ytdl_ok:
        lines.append(f"{CLR_CYN}│{CLR_RST}  {CLR_RED}⚠️  ATENÇÃO: Faltam dependências no sistema!{CLR_RST}                 {CLR_CYN}│{CLR_RST}")
        if not mpv_ok:
            lines.append(f"{CLR_CYN}│{CLR_RST}     • mpv está em falta                                      {CLR_CYN}│{CLR_RST}")
        if not ytdl_ok:
            lines.append(f"{CLR_CYN}│{CLR_RST}     • yt-dlp está em falta                                   {CLR_CYN}│{CLR_RST}")
        lines.append(f"{CLR_CYN}│{CLR_RST}  Pressione 's' para fechar e execute o helper.               {CLR_CYN}│{CLR_RST}")
        lines.append(f"{CLR_CYN}└──────────────────────────────────────────────────────────────┘{CLR_RST}")
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
        return

    if status["status"] == "stopped":
        lines.append(f"{CLR_CYN}│{CLR_RST}  Estado: {CLR_RED}⏹️  PARADO{CLR_RST}                                            {CLR_CYN}│{CLR_RST}")
        lines.append(f"{CLR_CYN}│{CLR_RST}  Sem áudio ativo no momento.                                 {CLR_CYN}│{CLR_RST}")
        lines.append(f"{CLR_CYN}│{CLR_RST}                                                              {CLR_CYN}│{CLR_RST}")
    else:
        state_icon = f"{CLR_GRN}▶️  A TOCAR{CLR_RST}" if status["status"] == "playing" else f"{CLR_YLW}⏸️  PAUSADO{CLR_RST}"
        if status["muted"]:
            state_icon += f" {CLR_RED}(Silenciado){CLR_RST}"
            
        mode_str = f"{CLR_GRN}[📻 RÁDIO]{CLR_RST}" if status["mode"] == "radio" else f"{CLR_BLU}[🎥 YOUTUBE]{CLR_RST}"
        lines.append(f"{CLR_CYN}│{CLR_RST}  Estado: {state_icon:<25} Modo: {mode_str:<25} {CLR_CYN}│{CLR_RST}")
        
        if status["mode"] == "radio":
            station = status["station_name"]
            if len(station) > 50:
                station = station[:47] + "..."
            lines.append(f"{CLR_CYN}│{CLR_RST}  Rádio: {CLR_WHT}{station:<51}{CLR_RST} {CLR_CYN}│{CLR_RST}")
            
            track = status["media_title"]
            if track:
                if len(track) > 50:
                    track = track[:47] + "..."
                lines.append(f"{CLR_CYN}│{CLR_RST}  Música: {CLR_GRY}{track:<50}{CLR_RST} {CLR_CYN}│{CLR_RST}")
            else:
                lines.append(f"{CLR_CYN}│{CLR_RST}                                                              {CLR_CYN}│{CLR_RST}")
        else:
            track = "Youtube Playing"
            lines.append(f"{CLR_CYN}│{CLR_RST}  Música: {CLR_WHT}{track:<50}{CLR_RST} {CLR_CYN}│{CLR_RST}")
            
            time_pos = status["time_pos"]
            duration = status["duration"]
            percent = 0.0
            if duration > 0:
                percent = (time_pos / duration) * 100.0
            
            time_str = format_time(time_pos)
            duration_str = format_time(duration)
            
            bar_width = 30
            filled = int(percent / 100.0 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            progress_line = f"⏱️  {time_str}/{duration_str} [{bar}] {percent:.1f}%"
            lines.append(f"{CLR_CYN}│{CLR_RST}  {CLR_GRY}{progress_line:<57}{CLR_RST} {CLR_CYN}│{CLR_RST}")
            
    lines.append(f"{CLR_CYN}└──────────────────────────────────────────────────────────────┘{CLR_RST}")
    lines.append("")
    
    # Render tabs
    tab1_style = f"{CLR_WHT}{CLR_BLD} [1] 📻 RÁDIOS {CLR_RST}" if current_tab == 1 else f"{CLR_GRY} [1] 📻 Rádios {CLR_RST}"
    tab2_style = f"{CLR_WHT}{CLR_BLD} [2] 🎥 YOUTUBE {CLR_RST}" if current_tab == 2 else f"{CLR_GRY} [2] 🎥 YouTube {CLR_RST}"
    tab3_style = f"{CLR_WHT}{CLR_BLD} [3] ⚙️ DEFINIÇÕES {CLR_RST}" if current_tab == 3 else f"{CLR_GRY} [3] ⚙️ Definições {CLR_RST}"
    
    lines.append(f"  {tab1_style} │ {tab2_style} │ {tab3_style} ")
    lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
    lines.append("")
    
    if current_tab == 1:
        lines.append(f"  {CLR_BLD}--- Estações de Rádio Disponíveis ---{CLR_RST}")
        col_width = 28
        total_presets = len(STATIONS)
        rows = (total_presets + 1) // 2
        for r in range(rows):
            row_str = "   "
            # Col 1
            idx1 = r
            prefix1 = f"{CLR_GRN}👉{CLR_RST}" if status["path"] == STATIONS[idx1]["url"] and status["status"] != "stopped" and status["mode"] == "radio" else "  "
            name1 = STATIONS[idx1]["name"]
            if len(name1) > 20: name1 = name1[:18] + ".."
            item1 = f"{prefix1}[{idx1+1:2d}] {name1}"
            row_str += item1.ljust(col_width)
            
            # Col 2
            idx2 = r + rows
            if idx2 < total_presets:
                prefix2 = f"{CLR_GRN}👉{CLR_RST}" if status["path"] == STATIONS[idx2]["url"] and status["status"] != "stopped" and status["mode"] == "radio" else "  "
                name2 = STATIONS[idx2]["name"]
                if len(name2) > 20: name2 = name2[:18] + ".."
                item2 = f"{prefix2}[{idx2+1:2d}] {name2}"
                row_str += "   " + item2.ljust(col_width)
            lines.append(row_str)
            
        customs = get_custom_stations()
        if customs:
            lines.append("")
            lines.append(f"  {CLR_BLD}--- Estações Personalizadas ---{CLR_RST}")
            for i, c in enumerate(customs):
                idx = total_presets + i + 1
                prefix = f"{CLR_GRN}👉{CLR_RST}" if status["path"] == c["url"] and status["status"] != "stopped" and status["mode"] == "radio" else "  "
                c_name = c["name"]
                if len(c_name) > 25: c_name = c_name[:22] + "..."
                c_url = c["url"]
                if len(c_url) > 25: c_url = c_url[:22] + "..."
                lines.append(f"   {prefix}[{idx:2d}] {c_name} {CLR_GRY}({c_url}){CLR_RST}")
                
        lines.append("")
        lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
        lines.append(f"  {CLR_BLD}[Espaço]{CLR_RST} Play/Pause   {CLR_BLD}[M]{CLR_RST} Mute/Unmute   {CLR_BLD}[S]{CLR_RST} Parar Player   {CLR_BLD}[Q]{CLR_RST} Fechar TUI")
        lines.append(f"  {CLR_BLD}[C]{CLR_RST} Colar Clipboard  {CLR_BLD}[A]{CLR_RST} Adicionar Rádio Manualmente")
        lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
        
        if input_prompt_type == "station_number":
            lines.append(f"  Sintonizar estação nº: {CLR_WHT}{input_buffer}█{CLR_RST}")
        elif input_prompt_type == "add_radio_name":
            lines.append(f"  Nome da nova rádio: {CLR_WHT}{input_buffer}█{CLR_RST}")
        elif input_prompt_type == "add_radio_url":
            lines.append(f"  URL da rádio: {CLR_WHT}{input_buffer}█{CLR_RST}")
        else:
            lines.append("  Digite o número da rádio e prima ENTER para sintonizar...")
            
    elif current_tab == 2:
        lines.append(f"  {CLR_BLD}--- Fila de Reprodução (Queue) ---{CLR_RST}")
        playlist_res = send_mpv_command(["get_property", "playlist"])
        playlist = playlist_res.get("data", []) if playlist_res.get("error") == "success" else []
        
        if playlist and status["mode"] == "youtube":
            for i, item in enumerate(playlist[:4]):
                filename = item.get("filename")
                t = item.get("title")
                
                cached_t = get_cached_title(filename, t)
                if cached_t:
                    t = cached_t
                elif not t or t.startswith("http"):
                    t = filename or "Sem título"
                    
                if t.startswith("http"):
                    t = "A carregar stream..."
                    
                if len(t) > 52:
                    t = t[:49] + "..."
                marker = f"{CLR_BLU}👉{CLR_RST}" if item.get("current") else "  "
                lines.append(f"   {marker} [{i+1}] {t}")
            if len(playlist) > 4:
                lines.append(f"      ... e mais {len(playlist) - 4} faixas na fila.")
        else:
            lines.append("   (A fila de reprodução está vazia)")
            
        lines.append("")
        lines.append(f"  {CLR_BLD}--- Histórico Recente (YouTube) ---{CLR_RST}")
        history = load_history()
        yt_history = [h for h in history if h.get("type") == "youtube"]
        if yt_history:
            for i, item in enumerate(yt_history[:5]):
                h_title = item.get("title", item["url"])
                if len(h_title) > 52:
                    h_title = h_title[:49] + "..."
                lines.append(f"   • [{i+1}] {h_title}")
        else:
            lines.append("   (Nenhum vídeo no histórico recente)")
            
        lines.append("")
        lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
        lines.append(f"  {CLR_BLD}[Espaço]{CLR_RST} Play/Pause  {CLR_BLD}[M]{CLR_RST} Mute  {CLR_BLD}[N]{CLR_RST} Seguinte  {CLR_BLD}[P]{CLR_RST} Anterior  {CLR_BLD}[X]{CLR_RST} Limpar Fila")
        lines.append(f"  {CLR_BLD}[C]{CLR_RST} Clipboard  {CLR_BLD}[A]{CLR_RST} Adicionar URL  {CLR_BLD}[T]{CLR_RST} Fila index  {CLR_BLD}[H]{CLR_RST} Histórico index")
        lines.append(f"  {CLR_BLD}[F]{CLR_RST} Favoritar  {CLR_BLD}[V]{CLR_RST} Tocar Favoritos")
        lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
        
        if input_prompt_type == "select_track":
            lines.append(f"  Tocar faixa da fila nº: {CLR_WHT}{input_buffer}█{CLR_RST}")
        elif input_prompt_type == "select_history":
            lines.append(f"  Tocar do histórico nº: {CLR_WHT}{input_buffer}█{CLR_RST}")
        elif input_prompt_type == "add_yt_url":
            lines.append(f"  URL do YouTube (vídeo ou playlist): {CLR_WHT}{input_buffer}█{CLR_RST}")
        else:
            lines.append("  Prima [A] para digitar um URL, ou [C] para colar do clipboard...")
            
    elif current_tab == 3:
        lines.append(f"  {CLR_BLD}--- Dispositivos de Saída de Áudio ---{CLR_RST}")
        if is_mpv_running():
            dev_res = send_mpv_command(["get_property", "audio-device-list"])
            current_dev_res = send_mpv_command(["get_property", "audio-device"])
            if dev_res.get("error") == "success":
                devices = dev_res.get("data", [])
                current_dev = current_dev_res.get("data", "auto")
                
                seen_descriptions = set()
                unique_devices = []
                
                for d in devices:
                    if d.get("name") == "auto":
                        unique_devices.append(d)
                        seen_descriptions.add(d.get("description", "").lower())
                        break
                for d in devices:
                    name = d.get("name")
                    desc = d.get("description", "")
                    if name.startswith("coreaudio/") and desc.lower() not in seen_descriptions:
                        unique_devices.append(d)
                        seen_descriptions.add(desc.lower())
                for d in devices:
                    name = d.get("name")
                    desc = d.get("description", "")
                    if desc.lower() not in seen_descriptions:
                        unique_devices.append(d)
                        seen_descriptions.add(desc.lower())
                        
                for i, d in enumerate(unique_devices[:8]):
                    name = d.get("name")
                    desc = d.get("description", name)
                    marker = f"{CLR_GRN}✓{CLR_RST} " if name == current_dev else "  "
                    lines.append(f"   {marker}[{i+1}] {desc}")
            else:
                lines.append("   ⚠️ Erro ao listar dispositivos.")
        else:
            lines.append("   ⚠️ Inicie o player para ver e alterar dispositivos de áudio.")
        state = load_state()
        search_limit = state.get("search_limit", 5)
        lines.append("")
        lines.append(f"  {CLR_BLD}--- Configurações ---{CLR_RST}")
        lines.append(f"   Limite de Pesquisa YouTube: {CLR_WHT}{search_limit}{CLR_RST} resultados")
        lines.append(f"   {CLR_BLD}[L]{CLR_RST} Alterar Limite de Pesquisa")
        
        lines.append("")
        lines.append(f"  {CLR_BLD}--- Limpeza de Dados ---{CLR_RST}")
        lines.append(f"   {CLR_BLD}[R]{CLR_RST} Limpar Histórico de Rádios")
        lines.append(f"   {CLR_BLD}[Y]{CLR_RST} Limpar Histórico de YouTube")
        lines.append(f"   {CLR_BLD}[D]{CLR_RST} Apagar Todas as Rádios Personalizadas")
        lines.append(f"   {CLR_BLD}[K]{CLR_RST} Limpar Histórico Completo")
        
        lines.append("")
        lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
        lines.append(f"  {CLR_BLD}[Q]{CLR_RST} Fechar TUI Dashboard (Mantém áudio em background)")
        lines.append(f" {CLR_CYN}────────────────────────────────────────────────────────────────{CLR_RST}")
        
        if input_prompt_type == "select_device":
            lines.append(f"  Selecionar dispositivo de áudio nº: {CLR_WHT}{input_buffer}█{CLR_RST}")
        elif input_prompt_type == "change_limit":
            lines.append(f"  Introduza o limite de pesquisa (1-20): {CLR_WHT}{input_buffer}█{CLR_RST}")
        else:
            lines.append("  Digite o número do dispositivo de áudio para mudar de saída...")
            
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()

def run_tui():
    import select
    try:
        import tty
        import termios
    except ImportError:
        print("TUI não suportada neste terminal. Use via SwiftBar ou linha de comandos.")
        return
        
    start_mpv()
    resize_terminal()
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        tty.setraw(fd)
        input_buffer = ""
        input_prompt_type = ""
        temp_radio_name = ""
        current_tab = 1
        last_refresh = 0
        
        while True:
            now = time.time()
            if now - last_refresh >= 1.0:
                draw_tui(current_tab, input_buffer, input_prompt_type)
                last_refresh = now
                
            rlist, _, _ = select.select([sys.stdin], [], [], 0.2)
            if rlist:
                ch = sys.stdin.read(1)
                
                # If prompt is active, handle input buffer
                if input_prompt_type:
                    if ch in ('\r', '\n'):
                        if input_prompt_type == "station_number":
                            try:
                                idx = int(input_buffer) - 1
                                all_stations = STATIONS + get_custom_stations()
                                if 0 <= idx < len(all_stations):
                                    play_command(all_stations[idx]["url"], all_stations[idx]["name"], "radio")
                            except ValueError:
                                pass
                            input_prompt_type = ""
                            input_buffer = ""
                        elif input_prompt_type == "add_radio_name":
                            temp_radio_name = input_buffer.strip()
                            input_buffer = ""
                            input_prompt_type = "add_radio_url"
                        elif input_prompt_type == "add_radio_url":
                            url = input_buffer.strip()
                            if temp_radio_name and url:
                                add_custom_station(temp_radio_name, url)
                                play_command(url, temp_radio_name, "radio")
                            input_prompt_type = ""
                            input_buffer = ""
                            temp_radio_name = ""
                        elif input_prompt_type == "add_yt_url":
                            url = input_buffer.strip()
                            if url:
                                add_youtube_url(url)
                            input_prompt_type = ""
                            input_buffer = ""
                        elif input_prompt_type == "select_track":
                            try:
                                idx = int(input_buffer) - 1
                                select_track(idx)
                            except ValueError:
                                pass
                            input_prompt_type = ""
                            input_buffer = ""
                        elif input_prompt_type == "select_history":
                            try:
                                idx = int(input_buffer) - 1
                                history = load_history()
                                yt_history = [h for h in history if h.get("type") == "youtube"]
                                if 0 <= idx < len(yt_history):
                                    play_command(yt_history[idx]["url"], yt_history[idx].get("title"), "youtube")
                            except ValueError:
                                pass
                            input_prompt_type = ""
                            input_buffer = ""
                        elif input_prompt_type == "select_device":
                            try:
                                idx = int(input_buffer) - 1
                                dev_res = send_mpv_command(["get_property", "audio-device-list"])
                                if dev_res.get("error") == "success":
                                    devices = dev_res.get("data", [])
                                    seen_descriptions = set()
                                    unique_devices = []
                                    for d in devices:
                                        if d.get("name") == "auto":
                                            unique_devices.append(d)
                                            seen_descriptions.add(d.get("description", "").lower())
                                            break
                                    for d in devices:
                                        name = d.get("name")
                                        desc = d.get("description", "")
                                        if name.startswith("coreaudio/") and desc.lower() not in seen_descriptions:
                                            unique_devices.append(d)
                                            seen_descriptions.add(desc.lower())
                                    for d in devices:
                                        name = d.get("name")
                                        desc = d.get("description", "")
                                        if desc.lower() not in seen_descriptions:
                                            unique_devices.append(d)
                                            seen_descriptions.add(desc.lower())
                                            
                                    if 0 <= idx < len(unique_devices):
                                        set_audio_device(unique_devices[idx]["name"])
                            except ValueError:
                                pass
                            input_prompt_type = ""
                            input_buffer = ""
                        elif input_prompt_type == "change_limit":
                            try:
                                if input_buffer.strip().isdigit():
                                    val = int(input_buffer.strip())
                                    if 1 <= val <= 20:
                                        state = load_state()
                                        state["search_limit"] = val
                                        save_state(state)
                                        show_notification("Configuração Guardada", f"O limite foi alterado para {val} resultados.")
                            except Exception:
                                pass
                            input_prompt_type = ""
                            input_buffer = ""
                        last_refresh = 0
                    elif ord(ch) in (8, 127):  # Backspace
                        input_buffer = input_buffer[:-1]
                        last_refresh = 0
                    elif ord(ch) == 27:  # Escape/Cancel
                        input_prompt_type = ""
                        input_buffer = ""
                        temp_radio_name = ""
                        last_refresh = 0
                    elif ord(ch) == 3:  # Ctrl+C
                        break
                    else:
                        if len(ch) == 1 and 32 <= ord(ch) < 127:
                            input_buffer += ch
                            last_refresh = 0
                else:
                    if ch == '1':
                        current_tab = 1
                        last_refresh = 0
                    elif ch == '2':
                        current_tab = 2
                        last_refresh = 0
                    elif ch == '3':
                        current_tab = 3
                        last_refresh = 0
                    elif ch == ' ':
                        toggle_command()
                        last_refresh = 0
                    elif ch.lower() == 'm':
                        mute_command()
                        last_refresh = 0
                    elif ch.lower() == 's':
                        stop_command()
                        last_refresh = 0
                    elif ch.lower() == 'q':
                        break
                    elif ord(ch) == 3:  # Ctrl+C
                        break
                        
                    # Tab 1 Specific Keys
                    elif current_tab == 1:
                        if ch.isdigit():
                            input_prompt_type = "station_number"
                            input_buffer = ch
                            last_refresh = 0
                        elif ch.lower() == 'c':
                            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                            url = get_clipboard_url()
                            if url:
                                print(f"\nURL detetado: {url}")
                                name = input("Insira o nome da rádio: ").strip()
                                if name:
                                    add_custom_station(name, url)
                                    play_command(url, name, "radio")
                            else:
                                print("\nNenhum URL válido no clipboard.")
                                time.sleep(1.5)
                            tty.setraw(fd)
                            last_refresh = 0
                        elif ch.lower() == 'a':
                            input_prompt_type = "add_radio_name"
                            input_buffer = ""
                            last_refresh = 0
                            
                    # Tab 2 Specific Keys
                    elif current_tab == 2:
                        if ch.lower() == 'n':
                            next_command()
                            last_refresh = 0
                        elif ch.lower() == 'p':
                            prev_command()
                            last_refresh = 0
                        elif ch.lower() == 'x':
                            clear_command()
                            last_refresh = 0
                        elif ch.lower() == 'c':
                            url = get_clipboard_url()
                            if url:
                                add_youtube_url(url)
                            else:
                                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                                print("\nNenhum URL de YouTube válido no clipboard.")
                                time.sleep(1.5)
                                tty.setraw(fd)
                            last_refresh = 0
                        elif ch.lower() == 'a':
                            input_prompt_type = "add_yt_url"
                            input_buffer = ""
                            last_refresh = 0
                        elif ch.lower() == 't':
                            input_prompt_type = "select_track"
                            input_buffer = ""
                            last_refresh = 0
                        elif ch.lower() == 'h':
                            input_prompt_type = "select_history"
                            input_buffer = ""
                            last_refresh = 0
                        elif ch.lower() == 'f':
                            add_current_to_favorites()
                            last_refresh = 0
                        elif ch.lower() == 'v':
                            play_all_youtube_favorites()
                            last_refresh = 0
                            
                    # Tab 3 Specific Keys
                    elif current_tab == 3:
                        if ch.isdigit():
                            input_prompt_type = "select_device"
                            input_buffer = ch
                            last_refresh = 0
                        elif ch.lower() == 'r':
                            clear_history_command("radio")
                            last_refresh = 0
                        elif ch.lower() == 'y':
                            clear_history_command("youtube")
                            last_refresh = 0
                        elif ch.lower() == 'd':
                            state = load_state()
                            state["custom_stations"] = []
                            save_state(state)
                            show_notification("Media Hub", "Todas as rádios personalizadas foram apagadas.")
                            last_refresh = 0
                        elif ch.lower() == 'k':
                            clear_history_command()
                            last_refresh = 0
                        elif ch.lower() == 'l':
                            input_prompt_type = "change_limit"
                            input_buffer = ""
                            last_refresh = 0
                            
    except Exception as e:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print(f"\nErro no Dashboard TUI: {e}")
        time.sleep(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()
        print("Dashboard TUI fechado. O player continua a tocar em background!")
        print("Pode controlá-lo no SwiftBar ou reabrir o Dashboard digitando o comando no Terminal.")

# SwiftBar Menu Standard Output Generation
def run_swiftbar():
    mpv_ok, ytdl_ok = check_dependencies()
    script_path = os.path.abspath(sys.argv[0])
    
    if " " in script_path:
        symlink_path = "/Users/andresousa/swiftbar-plugins/media_player.5s.py"
        if os.path.exists(symlink_path):
            script_path = symlink_path
            
    if not mpv_ok:
        print("🎧 Media Hub (mpv em falta) | color=red")
        print("---")
        print(f"Instalar mpv e yt-dlp via Homebrew | bash={script_path} param1=install-deps terminal=true refresh=true ")
        return

    status = get_player_status()
    
    # 1. Main menu bar status text
    if status["status"] == "stopped":
        print("🎧 Media Hub | color=#90A4AE")
    else:
        icon = ""
        if status["muted"]:
            icon = "🔇 "
        elif status["paused"]:
            icon = "⏸️ "
            
        mode_prefix = "📻" if status["mode"] == "radio" else "🎥"
        
        name_to_display = ""
        if status["mode"] == "radio":
            name_to_display = status["station_name"]
        else:
            name_to_display = "Youtube Playing"
                
        if len(name_to_display) > 25:
            name_to_display = name_to_display[:22] + "..."
            
        color = "#FFEB3B" if status["paused"] else "#00E676"
        print(f"{icon}{mode_prefix} {name_to_display} | color={color}")
        
    print("---")
    
    # 2. Section: Now Playing & Controls
    if status["status"] != "stopped":
        codec = status.get("codec")
        bitrate = status.get("bitrate")
        samplerate = status.get("samplerate")
        channels = status.get("channels")
        
        details = []
        if codec:
            codec_upper = codec.upper()
            if codec_upper.startswith("PCM_"):
                codec_upper = "PCM"
            details.append(codec_upper)
        if bitrate and bitrate > 0:
            details.append(f"{int(bitrate / 1000)} kbps")
        if samplerate and samplerate > 0:
            details.append(f"{samplerate / 1000:.1f} kHz" if samplerate >= 1000 else f"{samplerate} Hz")
        if channels:
            if isinstance(channels, int):
                if channels == 2:
                    details.append("Stereo")
                elif channels == 1:
                    details.append("Mono")
                else:
                    details.append(f"{channels}ch")
            else:
                details.append(str(channels).capitalize())
        details_str = f" ({' | '.join(details)})" if details else ""

        mute_label = "🔊 Desativar Mudo" if status["muted"] else "🔇 Ativar Mudo"
        print(f"{mute_label} | bash={script_path} param1=mute terminal=false refresh=true shortcut=ctrl+option+m color=#E53935")

        vol = status.get("volume", 100.0)
        print(f"🔊 Volume: {int(vol)}% ")
        print(f"--🔊 Aumentar Volume (+10%) | bash={script_path} param1=volume-up terminal=false refresh=true shortcut=ctrl+option+up ")
        print(f"--🔉 Diminuir Volume (-10%) | bash={script_path} param1=volume-down terminal=false refresh=true shortcut=ctrl+option+down ")
        
        print("---")
        
        if status["mode"] == "radio":
            print(f"📻 Estação: {status['station_name']} | size=13  style=bold")
            if status["media_title"]:
                disp_title = status["media_title"].replace('|', '∣')
                print(f"🎵 A tocar: {disp_title} | size=12 color=#555555")
            if details:
                print(f"ℹ️ Info: {' | '.join(details)} | color=#555555 size=11")
        else:
            disp_title = status["title"].replace('|', '∣')
            print(f"🎵 Faixa: {disp_title} | size=13  style=bold")
            if status["duration"] > 0:
                time_pos = status["time_pos"]
                duration = status["duration"]
                percent = (time_pos / duration) * 100.0
                time_str = format_time(time_pos)
                duration_str = format_time(duration)
                
                bar_width = 16
                filled = int(percent / 100.0 * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"⏱️ {time_str} / {duration_str} [{bar}] ({percent:.1f}%) | color=#37474F font=Monaco size=11")
            if details:
                print(f"ℹ️ Info: {' | '.join(details)} | color=#555555 size=11")
                
        print("---")
        
        play_pause_label = "⏸️ Pausar Áudio" if not status["paused"] else "▶️ Retomar Áudio"
        print(f"{play_pause_label} | bash={script_path} param1=toggle terminal=false refresh=true shortcut=ctrl+option+space ")
        
        if status["mode"] == "youtube":
            playlist_res = send_mpv_command(["get_property", "playlist"])
            playlist = playlist_res.get("data", []) if playlist_res.get("error") == "success" else []
            if len(playlist) > 1:
                print(f"⏭ Próxima Faixa | bash={script_path} param1=next terminal=false refresh=true shortcut=ctrl+option+right ")
                print(f"⏮ Faixa Anterior | bash={script_path} param1=prev terminal=false refresh=true shortcut=ctrl+option+left ")
                
        print(f"⏹️ Parar Player (Sair) | bash={script_path} param1=stop terminal=false refresh=true shortcut=ctrl+option+s color=#E53935")
        
        current_path = status["path"]
        if current_path:
            favorites = load_favorites()
            is_fav = any(item.get("url") == current_path for item in favorites)
            if is_fav:
                print(f"⭐ Remover das Favoritas | bash={script_path} param1=remove-favorite param2='{current_path}' terminal=false refresh=true ")
            else:
                print(f"⭐ Adicionar às Favoritas | bash={script_path} param1=add-favorite terminal=false refresh=true ")
    else:
        state = load_state()
        mode = state.get("mode")
        if mode == "radio":
            last_url = state.get("last_radio_url")
            last_name = state.get("last_radio_name", "Última Rádio")
            print(f"▶️ Sintonizar {last_name} | bash={script_path} param1=play param2='{last_url}' param3='{last_name}' param4=radio terminal=false refresh=true ")
        elif mode == "youtube":
            yt_urls = state.get("yt_urls", [])
            if yt_urls:
                print(f"▶️ Retomar Playback YouTube | bash={script_path} param1=resume terminal=false refresh=true ")
            else:
                print("▶️ Iniciar Player | bash={script_path} param1=resume terminal=false refresh=true ")
        else:
            print("▶️ Iniciar Player | bash={script_path} param1=resume terminal=false refresh=true ")
            
    # 3. Section: Radio Module
    print("---")
    print("📻 RÁDIOS DE PORTUGAL | style=bold")
    
    favorites = load_favorites()
    radio_favs = [f for f in favorites if f.get("type") == "radio"]
    print("⭐ Rádios Favoritas ")
    if radio_favs:
        for item in radio_favs:
            f_url = item.get("url")
            f_name = item.get("title", f_url)
            f_name_escaped = f_name.replace('|', '∣')
            bullet = "👉 " if status["path"] == f_url and status["status"] != "stopped" and status["mode"] == "radio" else "📻 "
            print(f"--{bullet}{f_name_escaped} | bash={script_path} param1=play param2='{f_url}' param3='{f_name}' param4=radio terminal=false refresh=true ")
            print(f"--{bullet}🗑️ Remover Favorita | bash={script_path} param1=remove-favorite param2='{f_url}' terminal=false refresh=true alternate=true ")
    else:
        print("--🚫 Nenhuma favorita adicionada ")
        
    categories = ["Nacionais", "RTP", "Música", "Locais"]
    cat_names = {
        "Nacionais": "🇵🇹 Estações Nacionais",
        "RTP": "🏛️ Estações Públicas (RTP)",
        "Música": "🎶 Música e Temáticas",
        "Locais": "🎓 Locais e Universitárias"
    }
    
    for cat in categories:
        print(f"{cat_names[cat]} ")
        for s in STATIONS:
            if s["category"] == cat:
                bullet = "👉 " if status["path"] == s["url"] and status["status"] != "stopped" and status["mode"] == "radio" else "📻 "
                print(f"--{bullet}{s['name']} | bash={script_path} param1=play param2='{s['url']}' param3={repr(s['name'])} param4=radio terminal=false refresh=true ")
                
    customs = get_custom_stations()
    print("👤 Rádios Personalizadas ")
    if customs:
        for c in customs:
            c_url = c["url"]
            c_name = c["name"]
            bullet = "👉 " if status["path"] == c_url and status["status"] != "stopped" and status["mode"] == "radio" else "📻 "
            print(f"--{bullet}{c_name} | bash={script_path} param1=play param2='{c_url}' param3={repr(c_name)} param4=radio terminal=false refresh=true ")
            print(f"--{bullet}🗑️ Remover Personalizada | bash={script_path} param1=remove-custom param2='{c_url}' terminal=false refresh=true alternate=true ")
        print("-- ---")
    else:
        print("--🚫 Nenhuma rádio personalizada ")
        print("-- ---")
    print(f"--📋 Adicionar do Clipboard | bash={script_path} param1=add-radio-clipboard terminal=false refresh=true ")
    print(f"--✍️ Adicionar Manualmente... | bash={script_path} param1=add-radio-gui terminal=false refresh=true ")
        
    history = load_history()
    radio_history = [h for h in history if h.get("type") == "radio"]
    print("📜 Histórico Rádios ")
    if radio_history:
        for item in radio_history[:8]:
            h_url = item.get("url")
            h_name = item.get("title", h_url)
            h_name_escaped = h_name.replace('|', '∣')
            print(f"--📻 {h_name_escaped} | bash={script_path} param1=play param2='{h_url}' param3={repr(h_name)} param4=radio terminal=false refresh=true ")
        print("-- ---")
        print(f"--🧹 Limpar Histórico Rádios | bash={script_path} param1=clear-history param2=radio terminal=false refresh=true ")
    else:
        print("--🚫 Histórico vazio ")

    # 4. Section: YouTube Module
    print("---")
    print("🎥 YOUTUBE AUDIO PLAYER | style=bold")
    
    yt_favs = [f for f in favorites if f.get("type") == "youtube"]
    print("⭐ Músicas Favoritas ")
    if yt_favs:
        print(f"--▶️ Tocar Todos os Favoritos ({len(yt_favs)}) | bash={script_path} param1=play-favorites terminal=false refresh=true ")
        print("-- ---")
        for item in yt_favs:
            f_url = item.get("url")
            f_title = item.get("title", f_url).replace('|', '∣')
            if len(f_title) > 40:
                f_title = f_title[:37] + "..."
            bullet = "👉 " if status["path"] == f_url and status["status"] != "stopped" and status["mode"] == "youtube" else "🎵 "
            print(f"--{bullet}{f_title} | bash={script_path} param1=play param2='{f_url}' param3=None param4=youtube terminal=false refresh=true ")
            print(f"--{bullet}🗑️ Remover Favorita | bash={script_path} param1=remove-favorite param2='{f_url}' terminal=false refresh=true alternate=true ")
    else:
        print("--🚫 Nenhuma favorita adicionada ")
        
    playlist_res = send_mpv_command(["get_property", "playlist"])
    playlist = playlist_res.get("data", []) if playlist_res.get("error") == "success" else []
    print("⏳ Fila de Reprodução (Queue) ")
    if playlist and status["mode"] == "youtube":
        print(f"--🧹 Limpar Fila ({len(playlist)}) | bash={script_path} param1=clear terminal=false refresh=true ")
        print("-- ---")
        for i, item in enumerate(playlist):
            filename = item.get("filename")
            t = item.get("title")
            
            cached_t = get_cached_title(filename, t)
            if cached_t:
                t = cached_t
            elif not t or t.startswith("http"):
                t = filename or "Sem título"
                
            if t.startswith("http"):
                t = "A carregar stream..."
                
            t_escaped = t.replace('|', '∣')
            if len(t_escaped) > 35:
                t_escaped = t_escaped[:32] + "..."
                
            bullet = "👉 " if item.get("current") else "🎵 "
            print(f"--{bullet}{t_escaped} | bash={script_path} param1=select-track param2={i} terminal=false refresh=true ")
        print("-- ---")
    else:
        print("--🚫 Fila vazia ")
    print(f"--🔍 Pesquisar Música... | bash={script_path} param1=search-youtube-video terminal=false refresh=true ")
    print(f"--🔍 Pesquisar Playlist... | bash={script_path} param1=search-youtube-playlist terminal=false refresh=true ")
    print(f"--📋 Adicionar do Clipboard | bash={script_path} param1=add-youtube-clipboard terminal=false refresh=true ")
    print(f"--✍️ Adicionar Manualmente... | bash={script_path} param1=add-youtube-gui terminal=false refresh=true ")
        
    yt_history = [h for h in history if h.get("type") == "youtube"]
    print("📜 Histórico YouTube ")
    if yt_history:
        yt_playlists = [h for h in yt_history if "list=" in h["url"] or "playlist" in h["url"]]
        yt_songs = [h for h in yt_history if not ("list=" in h["url"] or "playlist" in h["url"])]
        
        if yt_playlists:
            print("--📁 Playlists Recentes: ")
            for item in yt_playlists[:8]:
                h_url = item.get("url")
                h_title = item.get("title", h_url).replace('|', '∣')
                if len(h_title) > 35:
                    h_title = h_title[:32] + "..."
                print(f"--   📁 {h_title} | bash={script_path} param1=play param2='{h_url}' param3=None param4=youtube terminal=false refresh=true ")
                print(f"--   🗑️ Remover Item | bash={script_path} param1=remove-history-item param2='{h_url}' terminal=false refresh=true alternate=true ")
                
        if yt_playlists and yt_songs:
            print("-----")
            
        if yt_songs:
            print("--🎵 Músicas Recentes: ")
            for item in yt_songs[:12]:
                h_url = item.get("url")
                h_title = item.get("title", h_url).replace('|', '∣')
                if len(h_title) > 35:
                    h_title = h_title[:32] + "..."
                print(f"--   🎵 {h_title} | bash={script_path} param1=play param2='{h_url}' param3=None param4=youtube terminal=false refresh=true ")
                print(f"--   🗑️ Remover Item | bash={script_path} param1=remove-history-item param2='{h_url}' terminal=false refresh=true alternate=true ")
                
        print("-----")
        print(f"--🧹 Limpar Histórico Músicas | bash={script_path} param1=clear-history param2=songs terminal=false refresh=true ")
        print(f"--🧹 Limpar Histórico Playlists | bash={script_path} param1=clear-history param2=playlists terminal=false refresh=true ")
        print(f"--🧹 Limpar Todo o Histórico YouTube | bash={script_path} param1=clear-history param2=youtube terminal=false refresh=true ")
    else:
        print("--🚫 Histórico vazio ")

    # 5. Section: General Settings & Actions
    print("---")
    print("⚙️ DEFINIÇÕES & GERAL | style=bold")
    
    state = load_state()
    search_limit = state.get("search_limit", 5)
    print(f"🔍 Limite de Pesquisa: {search_limit} resultados ")
    print(f"--✍️ Alterar Limite... | bash={script_path} param1=change-search-limit terminal=false refresh=true ")
    
    normalize_audio = state.get("normalize_audio", True)
    norm_status = "Ativada" if normalize_audio else "Desativada"
    print(f"🔊 Normalização de Volume: {norm_status} | bash={script_path} param1=toggle-normalize terminal=false refresh=true")
    
    if is_mpv_running():
        dev_res = send_mpv_command(["get_property", "audio-device-list"])
        current_dev_res = send_mpv_command(["get_property", "audio-device"])
        if dev_res.get("error") == "success":
            devices = dev_res.get("data", [])
            current_dev = current_dev_res.get("data", "auto")
            
            seen_descriptions = set()
            unique_devices = []
            
            for d in devices:
                if d.get("name") == "auto":
                    unique_devices.append(d)
                    seen_descriptions.add(d.get("description", "").lower())
                    break
            for d in devices:
                name = d.get("name")
                desc = d.get("description", "")
                if name.startswith("coreaudio/") and desc.lower() not in seen_descriptions:
                    unique_devices.append(d)
                    seen_descriptions.add(desc.lower())
            for d in devices:
                name = d.get("name")
                desc = d.get("description", "")
                if desc.lower() not in seen_descriptions:
                    unique_devices.append(d)
                    seen_descriptions.add(desc.lower())
                    
            current_desc = "Automático"
            for d in unique_devices:
                if d.get("name") == current_dev:
                    current_desc = d.get("description", "Automático")
                    break
                    
            print(f"🔈 Saída: {current_desc} ")
            for d in unique_devices:
                name = d.get("name")
                desc = d.get("description", name)
                bullet = "✓ " if name == current_dev else "🔈 "
                desc_escaped = desc.replace('|', '∣')
                print(f"--{bullet}{desc_escaped} | bash={script_path} param1=set-audio-device param2='{name}' terminal=false refresh=true ")
        else:
            print("🔈 Saída de Áudio ")
            print("--⚠️ Erro ao obter dispositivos ")
    else:
        print("🔈 Saída de Áudio ")
        print("--⚠️ Iniciar Player para ver dispositivos ")
        
    print("---")
    print(f"🛠️ Abrir Dashboard TUI Interativo | bash=open param1=-a param2=Terminal.app param3={script_path} terminal=false ")
    
    if not ytdl_ok:
        print(f"📥 Instalar Dependências (yt-dlp/mpv) | bash={script_path} param1=install-deps terminal=true refresh=true color=#E53935")
        
    print("---")
    print("🏷️ Versão: 1.0.0 | color=#999999 size=11")

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "play":
            url = sys.argv[2] if len(sys.argv) > 2 else None
            name = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "None" else None
            media_type = sys.argv[4] if len(sys.argv) > 4 else None
            if url:
                play_command(url, name, media_type)
        elif cmd == "pause":
            pause_command()
        elif cmd == "resume":
            resume_command()
        elif cmd == "toggle":
            toggle_command()
        elif cmd == "mute":
            mute_command()
        elif cmd == "volume-up":
            adjust_volume_command(10)
        elif cmd == "volume-down":
            adjust_volume_command(-10)
        elif cmd == "stop":
            stop_command()
        elif cmd == "next":
            next_command()
        elif cmd == "prev":
            prev_command()
        elif cmd == "clear":
            clear_command()
        elif cmd == "clear-history":
            target = sys.argv[2] if len(sys.argv) > 2 else None
            clear_history_command(target)
        elif cmd == "remove-history-item":
            if len(sys.argv) > 2:
                remove_history_item(sys.argv[2])
        elif cmd == "add":
            if len(sys.argv) > 2:
                add_youtube_url(sys.argv[2])
        elif cmd == "add-clipboard":
            add_via_clipboard()
        elif cmd == "add-gui":
            add_via_applescript()
        elif cmd == "add-radio-clipboard":
            add_radio_clipboard()
        elif cmd == "add-radio-gui":
            add_radio_gui()
        elif cmd == "add-youtube-clipboard":
            add_youtube_clipboard()
        elif cmd == "add-youtube-gui":
            add_youtube_gui()
        elif cmd == "search-youtube-video":
            search_youtube_gui("video")
        elif cmd == "search-youtube-playlist":
            search_youtube_gui("playlist")
        elif cmd == "change-search-limit":
            change_search_limit_gui()
        elif cmd == "toggle-normalize":
            toggle_normalize_command()
        elif cmd == "select-track":
            if len(sys.argv) > 2:
                select_track(sys.argv[2])
        elif cmd == "set-audio-device":
            if len(sys.argv) > 2:
                set_audio_device(sys.argv[2])
        elif cmd == "add-favorite":
            add_current_to_favorites()
        elif cmd == "remove-favorite":
            if len(sys.argv) > 2:
                remove_from_favorites(sys.argv[2])
        elif cmd == "remove-custom":
            if len(sys.argv) > 2:
                remove_custom_station(sys.argv[2])
        elif cmd == "play-favorites":
            play_all_youtube_favorites()
        elif cmd == "install-deps":
            install_dependencies()
        elif cmd == "swiftbar":
            run_swiftbar()
        else:
            print(f"Comando '{cmd}' desconhecido.")
    else:
        if sys.stdin.isatty():
            run_tui()
        else:
            run_swiftbar()

if __name__ == "__main__":
    main()
