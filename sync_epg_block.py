import re
import gdown

PLAYLIST_IN = "live_epg_sports.m3u"
EPG_FILE = "epg_wib_sports.xml"
OUT_FILE = "playlist_final_epg.m3u"

# FILE ID GOOGLE DRIVE (FIX)
GDRIVE_ID = "1N1gsbY4VBcNfdXd1TxlFXwG-3e3NHCFQ"

def normalize(txt):
    return re.sub(r'[^a-z0-9]', '', txt.lower())

print("Download EPG dari Google Drive...")
gdown.download(f"https://drive.google.com/uc?id={GDRIVE_ID}", EPG_FILE, quiet=False)

print("Scan EPG (SAFE MODE)...")
epg_map = {}
current_id = None

with open(EPG_FILE, encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()

        if line.startswith("<channel"):
            m = re.search(r'id="([^"]+)"', line)
            if m:
                current_id = m.group(1)

        elif "<display-name>" in line and current_id:
            name = re.sub(r"<.*?>", "", line)
            epg_map[normalize(name)] = current_id
            current_id = None

print("EPG channel loaded:", len(epg_map))

print("Process playlist (BLOK UTUH)...")
with open(PLAYLIST_IN, encoding="utf-8", errors="ignore") as f:
    lines = f.read().splitlines()

out = ["#EXTM3U"]
i = 0

while i < len(lines):
    if lines[i].startswith("#EXTINF"):
        block = [lines[i]]
        i += 1
        while i < len(lines) and not lines[i].startswith("#EXTINF"):
            block.append(lines[i])
            i += 1

        extinf = block[0]
        name = normalize(extinf.split(",", 1)[-1])

        for epg_name, epg_id in epg_map.items():
            if epg_name in name or name in epg_name:
                if 'tvg-id="' in extinf:
                    block[0] = re.sub(r'tvg-id="[^"]+"', f'tvg-id="{epg_id}"', extinf)
                else:
                    block[0] = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-id="{epg_id}"')
                break

        out.extend(block)
    else:
        i += 1

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE → playlist_final_epg.m3u (EPG Google Drive, BLOK UTUH)")
