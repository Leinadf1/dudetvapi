import os
import sys
import json
import base64
import urllib.request
import subprocess
import re
from Crypto.Cipher import AES
import time

# Set terminal encoding to UTF-8
sys.stdout.reconfigure(encoding="utf-8")

CONFIG_FILE = "config.json"
STATIC_KEY = b"6ayJ7jo@ao#pxVc%"
TARGET_CHANNEL_ID = "50002"  # Solo questo canale/evento

def replace_sportzx_with_dudetv(data):
    if isinstance(data, dict):
        return {k: replace_sportzx_with_dudetv(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_sportzx_with_dudetv(item) for item in data]
    elif isinstance(data, str):
        return data.replace("SportzX", "DUDE Tv").replace("sportzx", "dudetv")
    return data

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found.")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def check_adb_devices():
    try:
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")[1:]
        devices = [line.split()[0] for line in lines if line.strip() and "device" in line]
        return devices
    except Exception as e:
        print(f"ADB is not installed or not in PATH: {e}")
        return []

def get_device_paths():
    try:
        apk_path_cmd = subprocess.run(["adb", "shell", "pm", "path", "com.sportzx.live"], capture_output=True, text=True, check=True)
        apk_path = apk_path_cmd.stdout.strip().replace("package:", "")
        if not apk_path:
            raise ValueError("DUDEtv app package (com.sportzx.live) is not installed on the emulator.")
            
        base_dir = apk_path.replace("base.apk", "")
        lib_list_cmd = subprocess.run(["adb", "shell", f"ls {base_dir}lib/"], capture_output=True, text=True, check=True)
        arch = lib_list_cmd.stdout.strip().split()[0]
        lib_path = f"{base_dir}lib/{arch}/libnative-lib.so"
        
        return apk_path, lib_path
    except Exception as e:
        print(f"Error resolving emulator paths: {e}")
        print("Please make sure the DUDEtv app is installed and the emulator is fully booted.")
        return None, None

def ensure_decryptor_jar():
    jar_name = "Decryptor.jar"
    local_jar_path = os.path.join("..", jar_name) if os.path.exists(os.path.join("..", jar_name)) else jar_name
    
    if not os.path.exists(local_jar_path):
        print("Decryptor.jar not found. Re-building...")
        try:
            java_file = "../Decryptor.java" if os.path.exists("../Decryptor.java") else "Decryptor.java"
            android_jar = "C:/Users/mdjam/AppData/Local/Android/Sdk/platforms/android-35/android.jar"
            d8_bat = "C:/Users/mdjam/AppData/Local/Android/Sdk/build-tools/34.0.0/d8.bat"
            
            subprocess.run(["javac", "--release", "8", "-cp", android_jar, java_file], check=True)
            subprocess.run([d8_bat, "--lib", android_jar, "--output", ".", "Decryptor.class"], check=True)
            
            import zipfile
            with zipfile.ZipFile(jar_name, "w") as z:
                z.write("classes.dex")
            
            for temp in ["classes.dex", "Decryptor.class"]:
                if os.path.exists(temp):
                    os.remove(temp)
            local_jar_path = jar_name
            print("Successfully built Decryptor.jar")
        except Exception as e:
            print(f"Failed to build Decryptor.jar: {e}")
            sys.exit(1)
            
    try:
        subprocess.run(["adb", "push", local_jar_path, "/data/local/tmp/Decryptor.jar"], check=True, capture_output=True)
        print("Decryptor.jar verified and pushed to emulator.")
    except Exception as e:
        print(f"Failed to push Decryptor.jar: {e}")
        sys.exit(1)

def clean_and_decode_b64(encrypted_b64):
    clean_str = "".join(encrypted_b64.split())
    std_b64 = clean_str.replace("-", "+").replace("_", "/")
    padding = len(std_b64) % 4
    if padding:
        std_b64 += "=" * (4 - padding)
    try:
        return base64.b64decode(std_b64)
    except Exception:
        return base64.urlsafe_b64decode(std_b64)

def decrypt_cbc(ciphertext_bytes, key, iv):
    if len(ciphertext_bytes) % 16 != 0:
        ciphertext_bytes = ciphertext_bytes[:len(ciphertext_bytes) - (len(ciphertext_bytes) % 16)]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext_bytes)
    if len(decrypted) > 0:
        pad_len = decrypted[-1]
        if 1 <= pad_len <= 16 and all(x == pad_len for x in decrypted[-pad_len:]):
            decrypted = decrypted[:-pad_len]
    return decrypted

def decrypt_local_b5cdbd48(enc_bytes, iv_str):
    dec = decrypt_cbc(enc_bytes, STATIC_KEY, iv_str.encode("utf-8"))
    dec_str = dec.decode("utf-8", errors="ignore")
    return json.loads(dec_str)

def decrypt_via_emulator(payload, apk_path, lib_path):
    temp_file = "temp_payload.txt"
    device_file = "/data/local/tmp/payload.txt"
    try:
        subprocess.run(["adb", "root"], capture_output=True)
        subprocess.run(["adb", "wait-for-device"], capture_output=True)
        whoami_res = subprocess.run(["adb", "shell", "whoami"], capture_output=True)
        whoami_out = whoami_res.stdout.decode("utf-8", errors="ignore")
        is_root = "root" in whoami_out
        
        def run_root_cmd(cmd):
            if is_root:
                subprocess.run(["adb", "shell", cmd], capture_output=True)
            else:
                res = subprocess.run(["adb", "shell", f"su -c '{cmd}'"], capture_output=True)
                res_err = res.stderr.decode("utf-8", errors="ignore")
                res_out = res.stdout.decode("utf-8", errors="ignore")
                if "invalid uid/gid" in res_err or "invalid uid/gid" in res_out:
                    subprocess.run(["adb", "shell", f"su root {cmd}"], capture_output=True)

        def run_root_cmd_bytes(cmd):
            if is_root:
                return subprocess.run(["adb", "shell", cmd], capture_output=True).stdout
            else:
                res = subprocess.run(["adb", "shell", f"su -c '{cmd}'"], capture_output=True)
                res_err = res.stderr.decode("utf-8", errors="ignore")
                res_out = res.stdout.decode("utf-8", errors="ignore")
                if "invalid uid/gid" in res_err or "invalid uid/gid" in res_out:
                    return subprocess.run(["adb", "shell", f"su root {cmd}"], capture_output=True).stdout
                return res.stdout

        pid_check = subprocess.run(["adb", "shell", "pidof com.sportzx.live"], capture_output=True)
        pid_out = pid_check.stdout.decode("utf-8", errors="ignore").strip()
        if not pid_out:
            print("      [Frida Fallback] App is not running. Launching SportzX...")
            run_root_cmd("setenforce 0")
            subprocess.run(["adb", "shell", "am start -n com.sportzx.live/com.sportzx.live.activities.SplashActivity"], capture_output=True)
            for _ in range(12):
                pid_check = subprocess.run(["adb", "shell", "pidof com.sportzx.live"], capture_output=True)
                pid_out = pid_check.stdout.decode("utf-8", errors="ignore").strip()
                if pid_out:
                    break
                time.sleep(1)
            time.sleep(12)
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(payload)
        subprocess.run(["adb", "push", temp_file, device_file], check=True, capture_output=True)
        
        run_root_cmd("rm -f /data/user/0/com.sportzx.live/cache/decrypted_raw.bin")
        
        frida_ps = subprocess.run(["adb", "shell", "ps -A | grep frida-server"], capture_output=True)
        frida_ps_out = frida_ps.stdout.decode("utf-8", errors="ignore")
        if "frida-server" not in frida_ps_out:
            check_fs = subprocess.run(["adb", "shell", "ls /data/local/tmp/frida-server"], capture_output=True)
            check_fs_err = check_fs.stderr.decode("utf-8", errors="ignore")
            check_fs_out = check_fs.stdout.decode("utf-8", errors="ignore")
            if "No such file" in check_fs_err or "frida-server" not in check_fs_out:
                print("      [Frida Fallback] frida-server not found on device. Preparing push...")
                if os.path.exists("frida-server"):
                    subprocess.run(["adb", "push", "frida-server", "/data/local/tmp/frida-server"], check=True)
                elif os.path.exists("frida-server.xz"):
                    print("      [Frida Fallback] Extracting frida-server.xz on host...")
                    import lzma
                    with lzma.open("frida-server.xz", "rb") as f_in:
                        with open("frida-server", "wb") as f_out:
                            f_out.write(f_in.read())
                    subprocess.run(["adb", "push", "frida-server", "/data/local/tmp/frida-server"], check=True)
                else:
                    print("      [Frida Fallback] Warning: frida-server binary or xz archive not found locally.")
                run_root_cmd("chmod 755 /data/local/tmp/frida-server")

            print("      [Frida Fallback] Starting frida-server...")
            if is_root:
                subprocess.Popen(["adb", "shell", "nohup /data/local/tmp/frida-server > /dev/null 2>&1 &"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                test_mm = subprocess.run(["adb", "shell", "su -mm -c 'id'"], capture_output=True)
                test_mm_err = test_mm.stderr.decode("utf-8", errors="ignore")
                test_mm_out = test_mm.stdout.decode("utf-8", errors="ignore")
                if "invalid uid/gid" in test_mm_err or "invalid uid/gid" in test_mm_out:
                    subprocess.Popen(["adb", "shell", "su root nohup /data/local/tmp/frida-server > /dev/null 2>&1 &"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["adb", "shell", "su -mm -c 'nohup /data/local/tmp/frida-server > /dev/null 2>&1 &'"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(10):
                res = subprocess.run(["frida-ps", "-U"], capture_output=True)
                if res.returncode == 0:
                    break
                time.sleep(1.5)
            
        pid_res = subprocess.run(["adb", "shell", "pidof com.sportzx.live"], capture_output=True)
        pid = pid_res.stdout.decode("utf-8", errors="ignore").strip()
        if not pid:
            ps_cmd = subprocess.run(["adb", "shell", "ps | grep com.sportzx.live"], capture_output=True)
            ps_out = ps_cmd.stdout.decode("utf-8", errors="ignore")
            match = re.search(r'\s+(\d+)\s+', ps_out)
            if match:
                pid = match.group(1)
        
        if pid:
            frida_cmd = ["frida", "-U", "-p", pid, "-l", "decrypt_script.js"]
        else:
            frida_cmd = ["frida", "-U", "-n", "com.sportzx.live", "-l", "decrypt_script.js"]
        output = ""
        stderr_output = ""
        try:
            res = subprocess.run(frida_cmd, capture_output=True, stdin=subprocess.DEVNULL, timeout=15)
            output = res.stdout.decode("utf-8", errors="ignore") if res.stdout else ""
            stderr_output = res.stderr.decode("utf-8", errors="ignore") if res.stderr else ""
        except subprocess.TimeoutExpired as te:
            output = te.stdout.decode("utf-8", errors="ignore") if te.stdout else ""
            stderr_output = te.stderr.decode("utf-8", errors="ignore") if te.stderr else ""
        except Exception as fe:
            print(f"      [Frida Fallback] process error: {fe}")
                
        success = False
        saved_path = None
        for line in output.splitlines():
            if "SUCCESS!" in line:
                success = True
                parts = line.split("saved to:")
                if len(parts) > 1:
                    saved_path = parts[1].strip()
                break
            
        if not success or not saved_path:
            print("      [Frida Fallback] Frida decryption failed or output path not parsed.")
            print(f"      [Frida Debug] stdout: {output}")
            print(f"      [Frida Debug] stderr: {stderr_output}")
            saved_path = "/data/user/0/com.sportzx.live/cache/decrypted_raw.bin"
            
        local_temp = os.path.join(os.getcwd(), "temp_decrypted.bin")
        if os.path.exists(local_temp):
            os.remove(local_temp)
            
        if is_root:
            subprocess.run(["adb", "shell", f"cp {saved_path} /data/local/tmp/decrypted_raw.bin"], capture_output=True)
            subprocess.run(["adb", "shell", "chmod 666 /data/local/tmp/decrypted_raw.bin"], capture_output=True)
        else:
            res = subprocess.run(["adb", "shell", f"su -c 'cp {saved_path} /data/local/tmp/decrypted_raw.bin && chmod 666 /data/local/tmp/decrypted_raw.bin'"], capture_output=True)
            res_err = res.stderr.decode("utf-8", errors="ignore")
            res_out = res.stdout.decode("utf-8", errors="ignore")
            if "invalid uid/gid" in res_err or "invalid uid/gid" in res_out:
                subprocess.run(["adb", "shell", f"su root 'cp {saved_path} /data/local/tmp/decrypted_raw.bin && chmod 666 /data/local/tmp/decrypted_raw.bin'"], capture_output=True)
                
        subprocess.run(["adb", "pull", "/data/local/tmp/decrypted_raw.bin", local_temp], capture_output=True)
        
        raw_bytes = b""
        if os.path.exists(local_temp):
            with open(local_temp, "rb") as lf:
                raw_bytes = lf.read()
            os.remove(local_temp)
        subprocess.run(["adb", "shell", "rm -f /data/local/tmp/decrypted_raw.bin"], capture_output=True)
        
        if len(raw_bytes) == 0:
            print("      [Frida Fallback] Decrypted file is empty or not readable.")
            return None
            
        try:
            text = raw_bytes.decode("utf-16be", errors="ignore").strip()
        except Exception:
            low_bytes = bytes(raw_bytes[i+1] for i in range(0, len(raw_bytes)-1, 2))
            text = low_bytes.decode("utf-8", errors="ignore").strip()

        start_idx = -1
        first_bracket = text.find('[')
        first_brace = text.find('{')
        if first_bracket != -1 and first_brace != -1:
            start_idx = min(first_bracket, first_brace)
        elif first_bracket != -1:
            start_idx = first_bracket
        elif first_brace != -1:
            start_idx = first_brace

        if start_idx != -1:
            text = text[start_idx:]

        last_bracket = text.rfind(']')
        last_brace = text.rfind('}')
        end_idx = max(last_bracket, last_brace)
        if end_idx != -1:
            text = text[:end_idx + 1]

        if not text:
            print("      [Frida Fallback] Output does not contain valid JSON boundaries.")
            return None

        try:
            return json.loads(text, strict=False)
        except Exception as je:
            print(f"      [Frida Fallback] json.loads initial attempt failed: {je}")
            if last_bracket != -1 and text.startswith('['):
                try:
                    return json.loads(text[:last_bracket + 1], strict=False)
                except Exception:
                    pass
            if last_brace != -1 and text.startswith('{'):
                try:
                    return json.loads(text[:last_brace + 1], strict=False)
                except Exception:
                    pass
            cleaned_text = re.sub(r',(\s*[\]}])', r'\1', text)
            try:
                return json.loads(cleaned_text, strict=False)
            except Exception as final_e:
                print(f"      [Frida Fallback] JSON parsing recovery failed: {final_e}")
                return None
            
    except Exception as e:
        print(f"      [Frida Fallback] Unexpected error: {e}")
        return None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def decrypt_data(payload, apk_path=None, lib_path=None):
    try:
        enc_bytes = clean_and_decode_b64(payload)
        
        if len(enc_bytes) >= 20 and enc_bytes[:4] == b'\xde\xad\xbe\xef':
            iv = enc_bytes[4:20]
            ciphertext = enc_bytes[20:]
            dec = decrypt_cbc(ciphertext, STATIC_KEY, iv)
        elif len(enc_bytes) >= 21 and enc_bytes[1:5] == b'\xde\xad\xbe\xef':
            iv = enc_bytes[5:21]
            ciphertext = enc_bytes[21:]
            dec = decrypt_cbc(ciphertext, STATIC_KEY, iv)
        elif len(enc_bytes) >= 17 and enc_bytes[0] == 2:
            iv = enc_bytes[1:17]
            ciphertext = enc_bytes[17:]
            dec = decrypt_cbc(ciphertext, STATIC_KEY, iv)
        else:
            dec = decrypt_cbc(enc_bytes, STATIC_KEY, b"HsjJTCA7jJztpL2w")
            
        dec_str = dec.decode("utf-8", errors="ignore").strip().rstrip('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10').strip()
        
        if dec_str.startswith('[') and not dec_str.endswith(']'):
            last_bracket = dec_str.rfind(']')
            if last_bracket >= 0:
                dec_str = dec_str[:last_bracket + 1]

        try:
            return json.loads(dec_str, strict=False)
        except Exception:
            last_bracket = dec_str.rfind(']')
            if last_bracket >= 0:
                clean_json = dec_str[:last_bracket + 1]
                return json.loads(clean_json, strict=False)
                
    except Exception as e:
        print(f"      Decryption attempt failed: {e}")
        if apk_path and lib_path:
            try:
                print("      Trying emulator JNI fallback...")
                return decrypt_via_emulator(payload, apk_path, lib_path)
            except Exception as jnie:
                print(f"      JNI fallback failed: {jnie}")
        return None

def main():
    config = load_config()
    out_dir = config.get("output_directory", "public_decrypted")
    os.makedirs(out_dir, exist_ok=True)
    
    import urllib.parse
    cats_url = config["endpoints"]["cats"]["url"]
    parsed_url = urllib.parse.urlparse(cats_url)
    base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    devices = check_adb_devices()
    apk_path, lib_path = None, None
    
    if not devices:
        print("WARNING: No emulator/device detected via ADB.")
        print("Continuing with local decryption only.")
    else:
        print(f"Connected devices: {devices}")
        print("Ensuring adb runs as root...")
        subprocess.run(["adb", "root"], capture_output=True)
        subprocess.run(["adb", "wait-for-device"], capture_output=True)
        apk_path, lib_path = get_device_paths()
        if apk_path and lib_path:
            ensure_decryptor_jar()
            print("Emulator decryption engine is READY!")
            
            # --- Dynamic Domain Resolution ---
            print("\n=== Resolving Active API Domain from Emulator ===")
            try:
                print("    Launching SportzX on emulator to trigger Remote Config fetch...")
                subprocess.run(["adb", "shell", "am force-stop com.sportzx.live"], capture_output=True)
                subprocess.run(["adb", "shell", "am start -n com.sportzx.live/com.sportzx.live.activities.SplashActivity"], capture_output=True)
                time.sleep(12)
                subprocess.run(["adb", "shell", "am force-stop com.sportzx.live"], capture_output=True)
                
                local_xml = os.path.join(os.getcwd(), "temp_appPref.xml")
                if os.path.exists(local_xml):
                    os.remove(local_xml)
                    
                subprocess.run(["adb", "shell", "rm -f /data/local/tmp/appPref.xml"], capture_output=True)
                subprocess.run(["adb", "root"], capture_output=True)
                subprocess.run(["adb", "wait-for-device"], capture_output=True)
                    
                whoami_res = subprocess.run(["adb", "shell", "whoami"], capture_output=True)
                whoami_out = whoami_res.stdout.decode("utf-8", errors="ignore")
                is_root = "root" in whoami_out
                
                shared_prefs_path = "/data/data/com.sportzx.live/shared_prefs/appPref.xml"
                if is_root:
                    subprocess.run(["adb", "shell", f"cp {shared_prefs_path} /data/local/tmp/appPref.xml"], capture_output=True)
                    subprocess.run(["adb", "shell", "chmod 666 /data/local/tmp/appPref.xml"], capture_output=True)
                else:
                    res = subprocess.run(["adb", "shell", f"su -c 'cp {shared_prefs_path} /data/local/tmp/appPref.xml && chmod 666 /data/local/tmp/appPref.xml'"], capture_output=True)
                    res_err = res.stderr.decode("utf-8", errors="ignore")
                    res_out = res.stdout.decode("utf-8", errors="ignore")
                    if "invalid uid/gid" in res_err or "invalid uid/gid" in res_out:
                        subprocess.run(["adb", "shell", f"su root 'cp {shared_prefs_path} /data/local/tmp/appPref.xml && chmod 666 /data/local/tmp/appPref.xml'"], capture_output=True)
                
                pull_res = subprocess.run(["adb", "pull", "/data/local/tmp/appPref.xml", local_xml], capture_output=True)
                subprocess.run(["adb", "shell", "rm -f /data/local/tmp/appPref.xml"], capture_output=True)
                
                if os.path.exists(local_xml):
                    with open(local_xml, "r", encoding="utf-8", errors="ignore") as xf:
                        xml_content = xf.read()
                    os.remove(local_xml)
                    
                    import re
                    match = re.search(r'<string name="last_success_api_url">(https?://[^<]+)</string>', xml_content)
                    if match:
                        detected_url = match.group(1).strip()
                        if detected_url.endswith("/"):
                            detected_url = detected_url[:-1]
                        print(f"    [Auto Domain] Detected active API base domain: {detected_url}")
                        base_domain = detected_url
                        
                        for ep_name in config["endpoints"]:
                            old_url = config["endpoints"][ep_name]["url"]
                            parsed_ep = urllib.parse.urlparse(old_url)
                            new_url = f"{base_domain}{parsed_ep.path}"
                            config["endpoints"][ep_name]["url"] = new_url
                            
                        with open("config.json", "w", encoding="utf-8") as f:
                            json.dump(config, f, indent=2, ensure_ascii=False)
                        print("    [Auto Domain] Updated config.json with active domain URLs.")
                    else:
                        print("    [Auto Domain] last_success_api_url not found in appPref.xml.")
                else:
                    print("    [Auto Domain] Failed to pull appPref.xml from emulator.")
            except Exception as ade:
                print(f"    [Auto Domain] Error resolving domain: {ade}")
    
    # ==============================================================
    # FETCH SOLO IL CANALE 50002 (sia main che fallback)
    # ==============================================================
    print(f"\n=== Recupero del canale/evento {TARGET_CHANNEL_ID} ===")
    
    ch_dir = os.path.join(out_dir, "channels")
    os.makedirs(ch_dir, exist_ok=True)
    ch_out_file = os.path.join(ch_dir, f"{TARGET_CHANNEL_ID}.json")
    
    channels1 = []
    channels2 = []
    fetched_successfully = False
    merged_channels = []

    # 1. Fetch main ID channels
    print(f"  Fetching main: {TARGET_CHANNEL_ID}.json...")
    try:
        ch_url = f"{base_domain}/channels/{TARGET_CHANNEL_ID}.json"
        ch_req = urllib.request.Request(ch_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(ch_req, timeout=15) as ch_res:
            ch_json = json.loads(ch_res.read().decode("utf-8"))
        
        ch_payload = ch_json.get("data")
        if ch_payload:
            dec_ch = decrypt_data(ch_payload, apk_path, lib_path)
            if dec_ch:
                channels1 = replace_sportzx_with_dudetv(dec_ch)
                fetched_successfully = True
                print(f"      Fetched main: {len(channels1)} channels")
    except Exception as ce:
        print(f"      Main attempt failed: {ce}")

    # 2. Fetch fallback ID 'e' channels
    print(f"  Fetching fallback: {TARGET_CHANNEL_ID}e.json...")
    try:
        ch_url = f"{base_domain}/channels/{TARGET_CHANNEL_ID}e.json"
        ch_req = urllib.request.Request(ch_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(ch_req, timeout=15) as ch_res:
            ch_json = json.loads(ch_res.read().decode("utf-8"))
        
        ch_payload = ch_json.get("data")
        if ch_payload:
            dec_ch = decrypt_data(ch_payload, apk_path, lib_path)
            if dec_ch:
                channels2 = replace_sportzx_with_dudetv(dec_ch)
                fetched_successfully = True
                print(f"      Fetched fallback: {len(channels2)} channels")
    except Exception as ce2:
        print(f"      Fallback attempt failed: {ce2}")

    # 3. Merge and deduplicate
    if fetched_successfully:
        seen_links = set()
        for ch in (channels1 + channels2):
            link = ch.get("link", "").split("|")[0].strip()
            if link and link not in seen_links:
                seen_links.add(link)
                merged_channels.append(ch)
        
        with open(ch_out_file, "w", encoding="utf-8") as ch_f:
            json.dump(merged_channels, ch_f, indent=2, ensure_ascii=False)
        print(f"\n✅ [SUCCESS] Salvato: {ch_out_file} ({len(merged_channels)} canali) [LIVE]")
    else:
        # Usa la cache se esiste
        if os.path.exists(ch_out_file):
            try:
                with open(ch_out_file, "r", encoding="utf-8") as cached_f:
                    merged_channels = json.load(cached_f)
                merged_channels = replace_sportzx_with_dudetv(merged_channels)
                print(f"\n📦 [CACHED] Usato file esistente: {ch_out_file} ({len(merged_channels)} canali)")
            except Exception as cached_err:
                print(f"\n❌ [ERROR] Cache non leggibile: {cached_err}")
        else:
            print(f"\n❌ [FAILED] Impossibile recuperare il canale {TARGET_CHANNEL_ID}")
    
    print("\nProcessing complete! (solo 50002.json)")

if __name__ == "__main__":
    main()
