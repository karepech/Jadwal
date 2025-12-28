import re
import xml.etree.ElementTree as ET

PLAYLIST_IN = "live_epg_sports.m3u"
EPG_XML     = "epg_wib_sports.xml"
OUT_FILE   = "playlist_final_epg.m3u"

def normalize(txt):
    return re.sub(r'[^a-z0-9]', '', txt.lower())

# ==== LOAD EPG ====
tree = ET.parse(EPG_XML)
root = tree.getroot()

epg_map = {}
for ch in root.findall("channel"):
    cid = ch.get("id")
    name_el = ch.find("display-name")
    if cid and name_el is not None:
        epg_map[normalize(name_el.text)] = cid

# ==== PROCESS PLAYLIST (BLOK UTUH) ====
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
        name = extinf.split(",", 1)[-1]
        key = normalize(name)

        for epg_name, epg_id in epg_map.items():
            if epg_name in key or key in epg_name:
                if 'tvg-id="' in extinf:
                    block[0] = re.sub(
                        r'tvg-id="[^"]+"',
                        f'tvg-id="{epg_id}"',
                        extinf
                    )
                else:
                    block[0] = extinf.replace(
                        "#EXTINF:-1",
                        f'#EXTINF:-1 tvg-id="{epg_id}"'
                    )
                break

        out.extend(block)
    else:
        i += 1

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE → playlist_final_epg.m3u (SEMUA BLOK UTUH)")
