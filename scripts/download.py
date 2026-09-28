#!/usr/bin/env python3
"""Fetch every source in reference/sources.txt into data/_src/<slug>.mp4 and log fps.

developer.apple.com pages: scrape the "HD Video" resource link, download with curl.
YouTube: yt-dlp, best <=1080p, preferring H.264 (OpenCV's FFmpeg decodes it reliably;
AV1 at the same resolution is not decodable frame-accurately here). Native fps kept.
Run with scripts/env.sh sourced.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
SRC = ROOT / "data" / "_src"
TMP = os.environ["TMPDIR"]

# slug per source, in sources.txt order
SLUGS = {
    "wwdc2023/111486": "wwdc23-17things",
    "wwdc2022/110929": "wwdc22-day1-recap",
    "wwdc2025/364": "wwdc25-welcome",
    "wwdc2026/122": "wwdc26-sotu-recap",
    "3fAHjTPvF1E": "sept26-event-recap",
    "jGztGfRujSE": "ios26-liquid-glass",
}


def slug_for(url):
    for key, slug in SLUGS.items():
        if key in url:
            return slug
    raise SystemExit(f"no slug for {url}")


def head_info(url):
    """Content-Length and Content-Type after redirects."""
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.headers.get("Content-Length", 0)), r.headers.get("Content-Type", "")


def apple(url, out):
    html = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "replace")
    m = re.search(r'href="([^"]+)"[^>]*>\s*HD Video', html)
    if not m:
        raise SystemExit(f"HD Video link not found on {url}")
    hd = m.group(1)
    title = re.search(r"<title>([^<]*)", html).group(1).strip()
    size, ctype = head_info(hd)
    if ctype.startswith("video/"):
        if out.exists() and out.stat().st_size == size:
            print(f"  cached, size matches ({size} B)")
        else:
            subprocess.run(["curl", "-sSL", "-o", str(out), hd], check=True)
        return {"title": title, "media_url": hd, "bytes": out.stat().st_size, "via": "hd_mp4"}
    # HD link redirects to an HTML page (dead on the CDN): fall back to the page's HLS stream
    hls = re.search(r'(https://[^"]+\.m3u8)', html)
    if not hls:
        raise SystemExit(f"HD Video link dead ({ctype}) and no HLS stream on {url}")
    print(f"  HD Video link dead (served {ctype}); falling back to HLS {hls.group(1)}")
    if out.exists() and out.stat().st_size > 1_000_000:
        print("  cached")
    else:
        subprocess.run(["yt-dlp", "--cache-dir", os.environ["YTDLP_CACHE_DIR"],
                        "--paths", f"temp:{TMP}", "--paths", str(SRC),
                        "-f", "bv*[height<=1080]+ba/b[height<=1080]", "--merge-output-format", "mp4",
                        "-o", out.name, hls.group(1)], check=True)
    return {"title": title, "media_url": hls.group(1), "hd_link_dead": hd,
            "bytes": out.stat().st_size, "via": "hls_fallback"}


def youtube(url, out):
    fmt = "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]"
    meta = json.loads(subprocess.run(
        ["yt-dlp", "--cache-dir", os.environ["YTDLP_CACHE_DIR"], "-f", fmt, "-J", url],
        check=True, capture_output=True, text=True).stdout)
    if out.exists() and out.stat().st_size > 1_000_000:
        print("  cached")
    else:
        subprocess.run(["yt-dlp", "--cache-dir", os.environ["YTDLP_CACHE_DIR"],
                        "--paths", f"temp:{TMP}", "--paths", str(SRC),
                        "-f", fmt, "--merge-output-format", "mp4",
                        "-o", out.name, url], check=True)
    return {"title": meta["title"], "media_url": url, "format_id": meta.get("format_id"),
            "bytes": out.stat().st_size}


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
                        "-show_format", str(path)], check=True, capture_output=True, text=True)
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    return {
        "width": v["width"], "height": v["height"], "vcodec": v["codec_name"],
        "fps": num / den, "fps_rational": v["r_frame_rate"],
        "nb_frames": int(v.get("nb_frames", 0)),
        "duration_s": float(j["format"]["duration"]),
        "acodec": a["codec_name"] if a else None,
        "sample_rate": int(a["sample_rate"]) if a else None,
        "channels": a["channels"] if a else None,
    }


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    urls = [l.strip() for l in (ROOT / "reference" / "sources.txt").read_text().splitlines() if l.strip()]
    manifest = []
    for url in urls:
        slug = slug_for(url)
        out = SRC / f"{slug}.mp4"
        print(f"[{slug}] {url}")
        info = apple(url, out) if "developer.apple.com" in url else youtube(url, out)
        info.update(probe(out))
        info.update({"slug": slug, "source": url, "path": str(out)})
        (ROOT / "data" / slug).mkdir(parents=True, exist_ok=True)
        (ROOT / "data" / slug / "meta.json").write_text(json.dumps(info, indent=2))
        print(f"  {info['width']}x{info['height']} {info['fps_rational']} ({info['fps']:.3f} fps) "
              f"{info['nb_frames']} frames {info['duration_s']:.2f}s {info['vcodec']}/{info['acodec']}")
        manifest.append(info)
    (ROOT / "reference" / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    sys.exit(main())
