import re
import gdown
import hashlib
import csv
from difflib import SequenceMatcher

# ================= NAMA FILE (JANGAN DIUBAH) =================
PLAYLIST_IN = "live_epg_sports.m3u"
EPG_FILE = "epg_wib_sports.xml"
OUT_FILE = "playlist_final_epg.m3u"

REPORT_MATCH = "report_match.csv"
REPORT_ALIAS = "report_alias.csv"
REPORT_UNMATCH = "report_unmatch.csv"

# GOOGLE DRIVE EPG (FILE ID)
GDRIVE_ID = "1N1gsbY4VBcNfdXd1TxlFXwG-3e3NHCFQ"

# ================= KONFIG =================
CHANNEL_BOLA_KEYS = [
    "bein","tnt","sky","spotv","soccer","football",
    "epl","ucl","champions","liga","laliga",
    "serie","bundes","premier"
]

# ================= UTIL =================
def normalize(name):
    name = name.lower()
    name = re.sub(r'(hd|fhd|uhd|4k|event|live|match)', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def is_channel_bola(name):
    n = name.lower()
    return any(k in n for k in CHANNEL_BOLA_KEYS)

def gen_internal_id(text):
    return "internal_" + hashlib.md5(text.encode()).hexdigest()[:8]

# ================= DOWNLOAD EPG =================
gdown.download(
    f"https://drive.google.com/uc?id={GDRIVE_ID}",
    EPG_FILE,
    quiet=True
)

# ================= LOAD EPG (NAME BASED) =================
epg_map = {}   # norm_name -> (id, original_name)
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
            epg_map[normalize(name)] = (current_id, name)
            current_id = None

# ================= MATCH FUNCTION (NAME FIRST) =================
def match_epg_by_name(ch_name):
    key = normalize(ch_name)
    best = (None, None, 0)

    for epg_key, (epg_id, epg_name) in epg_map.items():
        score = SequenceMatcher(None, key, epg_key).ratio()
        if score > best[2]:
            best = (epg_id, epg_name, score)

    if best[2] >= 0.75:
        return best
    return (None, None, 0)

# ================= PROCESS PLAYLIST =================
with open(PLAYLIST_IN, encoding="utf-8", errors="ignore") as f:
    lines = f.read().splitlines()

out = ["#EXTM3U"]
matched, aliased, unmatched = [], [], []

i = 0
while i < len(lines):
    if lines[i].startswith("#EXTINF"):
        block = [lines[i]]
        i += 1
        while i < len(lines) and not lines[i].startswith("#EXTINF"):
            block.append(lines[i])
            i += 1

        extinf = block[0]
        ch_name = extinf.split(",", 1)[-1].strip()

        epg_id, epg_name, score = match_epg_by_name(ch_name)

        # ===== LOGIKA FINAL =====
        if epg_id:
            tvg_id = epg_id
            matched.append([ch_name, epg_name, tvg_id, f"{score:.2f}"])

        elif is_channel_bola(ch_name):
            tvg_id = gen_internal_id(ch_name)
            aliased.append([ch_name, "NAME_BASED", tvg_id])

        else:
            tvg_id = gen_internal_id(ch_name)
            unmatched.append([ch_name, tvg_id])

        # set tvg-id (BLOK UTUH)
        if 'tvg-id="' in extinf:
            block[0] = re.sub(
                r'tvg-id="[^"]+"',
                f'tvg-id="{tvg_id}"',
                extinf
            )
        else:
            block[0] = extinf.replace(
                "#EXTINF:-1",
                f'#EXTINF:-1 tvg-id="{tvg_id}"'
            )

        out.extend(block)
    else:
        i += 1

# ================= SAVE OUTPUT =================
with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

with open(REPORT_MATCH, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["M3U Channel","EPG Channel","tvg-id","score"]] + matched
    )

with open(REPORT_ALIAS, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["M3U Channel","method","tvg-id"]] + aliased
    )

with open(REPORT_UNMATCH, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["M3U Channel","assigned tvg-id"]] + unmatched
    )

print("DONE → nama sesuai repo, YML tidak berubah")
