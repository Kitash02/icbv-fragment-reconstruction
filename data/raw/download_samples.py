"""
Download script for real archaeological fragment images.

Run this script once from the project root to populate data/real/ with
freely-licensed pottery sherd and scroll fragment photographs from Wikimedia Commons.

Usage:
    python data/real/download_samples.py

All images are licensed under Creative Commons (CC BY or CC BY-SA).
Attribution is included in the SOURCES list below.

Image categories:
  - Pottery sherds (fragments of fired clay vessels)
  - Dead Sea Scroll fragments (torn parchment with ancient Hebrew text)
  - Cuneiform tablets and inscribed stone fragments
  - Museum-grade photographs with neutral/white backgrounds suitable for
    Canny edge detection and Otsu segmentation
"""

import os
import urllib.request
import sys

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# (filename, url, attribution)
# URLs are Wikimedia Commons thumbnails at 600px width.
# Thumbnail path = /thumb/{md5[0]}/{md5[:2]}/{filename}/{width}px-{display}
# All images are CC BY-SA 3.0 unless noted.
SOURCES = [
    # -------------------------------------------------------------------------
    # Pottery sherds — clean museum backgrounds, clear contour edges
    # -------------------------------------------------------------------------
    (
        "shard_01_british.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/"
        "Cord_marked_pottery_sherd%2C_St._Catherine%27s_Period%2C_AD_800-1300"
        "_-_Fernbank_Museum_of_Natural_History_-_DSC00183.JPG/"
        "600px-Cord_marked_pottery_sherd%2C_St._Catherine%27s_Period%2C_AD_800-1300"
        "_-_Fernbank_Museum_of_Natural_History_-_DSC00183.JPG",
        "Cord-marked pottery sherd, Fernbank Museum — CC BY-SA 3.0",
    ),
    (
        "shard_02_kintampo.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/"
        "Stone_rasps_and_a_pottery_shard_of_Kintampo_Culture.JPG/"
        "600px-Stone_rasps_and_a_pottery_shard_of_Kintampo_Culture.JPG",
        "Kintampo Culture pottery shard — CC BY-SA 3.0",
    ),
    (
        "shard_03_wilmington.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/"
        "Grog_tempered_pottery%2C_Wilmington_cord_marked%2C_Wilmington_Period%2C_AD_350-800"
        "%2C_AMNH_110%2C_Pit_fill_9-11-69_-_Fernbank_Museum_of_Natural_History_-_DSC00188.JPG/"
        "600px-thumbnail.jpg",
        "Wilmington cord-marked pottery, Fernbank Museum — CC BY-SA 3.0",
    ),
    (
        "shard_04_cappadocian.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/"
        "Pottery_fragment_with_%27Cappadocian_Symbol%27%2C_Alishar%2C_Middle_Bronze_Age_III"
        "%2C_1759-1650_BC%2C_ceramic_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC07653.JPG/600px-thumbnail.jpg",
        "Pottery fragment with Cappadocian Symbol, Oriental Institute — CC BY-SA 3.0",
    ),
    # -------------------------------------------------------------------------
    # Ancient Near East pottery — Oriental Institute Museum, CC BY-SA 3.0
    # -------------------------------------------------------------------------
    (
        "pottery_01_ubaid.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/"
        "Northern_Ubaid_pottery_from_Tepe_Gawra_and_other_sites_-_Oriental_Institute_Museum"
        "%2C_University_of_Chicago_-_DSC06940.JPG/"
        "600px-Northern_Ubaid_pottery_from_Tepe_Gawra_and_other_sites_-_Oriental_Institute"
        "_Museum%2C_University_of_Chicago_-_DSC06940.JPG",
        "Northern Ubaid pottery, Oriental Institute Museum — CC BY-SA 3.0",
    ),
    (
        "pottery_02_assyrian.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/"
        "Middle_Assyrian_pottery_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC07024.JPG/"
        "600px-Middle_Assyrian_pottery_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC07024.JPG",
        "Middle Assyrian pottery, Oriental Institute Museum — CC BY-SA 3.0",
    ),
    (
        "pottery_03_akkadian.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/"
        "Akkadian_pottery_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC06977.JPG/"
        "600px-Akkadian_pottery_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC06977.JPG",
        "Akkadian pottery, Oriental Institute Museum — CC BY-SA 3.0",
    ),
    (
        "pottery_04_jamdat.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/"
        "Jamdat_Nasr_Period_pottery_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC06951.JPG/"
        "600px-Jamdat_Nasr_Period_pottery_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC06951.JPG",
        "Jamdat Nasr Period pottery, Oriental Institute Museum — CC BY-SA 3.0",
    ),
    # -------------------------------------------------------------------------
    # Scroll and inscribed fragments — parchment, clay tablet, stone
    # -------------------------------------------------------------------------
    (
        "scroll_01_dead_sea.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/"
        "Dead_Sea_Scroll_fragment_with_Hebrew_text%2C_Wadi_Qumran%2C_Cave_IV%2C_50_BC_to"
        "_50_AD%2C_parchment_and_ink_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC07748.JPG/"
        "600px-thumbnail.jpg",
        "Dead Sea Scroll fragment (Cave IV), Oriental Institute — CC BY-SA 3.0",
    ),
    (
        "fragment_01_cuneiform.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/"
        "Cuneiform-inscribed_fragment%2C_Amuq_Valley%2C_Tell_Tayinat%2C_Amuq_O%2C_Iron_Age"
        "_III%2C_750-650_BC%2C_basalt_-_Oriental_Institute_Museum%2C_University_of_Chicago"
        "_-_DSC07664.JPG/"
        "600px-thumbnail.jpg",
        "Cuneiform-inscribed basalt fragment, Oriental Institute — CC BY-SA 3.0",
    ),
]


def download(url: str, dest: str, attribution: str) -> bool:
    headers = {"User-Agent": "ArchaeologicalReconstructionProject/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) < 5000:   # reject HTML error pages
            print(f"  SKIP  {os.path.basename(dest)} — response too small ({len(data)} B)")
            return False
        with open(dest, "wb") as fh:
            fh.write(data)
        size_kb = len(data) // 1024
        print(f"  OK    {os.path.basename(dest)}  ({size_kb} KB)  {attribution}")
        return True
    except Exception as exc:
        print(f"  FAIL  {os.path.basename(dest)}: {exc}")
        return False


def main() -> None:
    print(f"Downloading to: {OUTPUT_DIR}\n")
    ok = 0
    for filename, url, attribution in SOURCES:
        dest = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(dest) and os.path.getsize(dest) > 5000:
            print(f"  EXISTS {filename} — skipping")
            ok += 1
            continue
        if download(url, dest, attribution):
            ok += 1

    print(f"\n{ok}/{len(SOURCES)} images ready in data/real/")
    if ok == 0:
        print(
            "\nNote: if all downloads failed, your network may block Wikimedia.\n"
            "In that case, manually download any of these images and place them\n"
            "in data/real/ — see README.md for sources.\n"
            "\nAlternatively, run with a direct internet connection (not a corporate proxy)."
        )
    elif ok < len(SOURCES):
        print(
            f"\n{len(SOURCES) - ok} image(s) failed. The pipeline will still work with "
            f"the {ok} downloaded image(s). You can add images manually to data/real/."
        )


if __name__ == "__main__":
    main()
