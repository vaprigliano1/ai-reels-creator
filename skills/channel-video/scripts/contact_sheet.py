#!/usr/bin/env python3
"""Render an approval contact sheet from asset_manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def safe_url(value, local=False):
    value = str(value or "")
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        return value
    if local and not parsed.scheme and not value.startswith(("//", "\\\\")):
        return value
    return ""


def youtube_embed(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be"}:
        video_id = parsed.path.strip("/")
    elif parsed.hostname in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    else:
        return None
    return f"https://www.youtube-nocookie.com/embed/{video_id}" if video_id else None


def card(slot: dict) -> str:
    slot_id = html.escape(str(slot.get("id", "slot")))
    media_url = html.escape(safe_url(slot.get("media_url")), quote=True)
    preview_url = html.escape(safe_url(slot.get("preview_url"), local=True), quote=True)
    preview_video_url = html.escape(safe_url(slot.get("preview_video_url"), local=True), quote=True)
    source_url = html.escape(safe_url(slot.get("source_page_url")), quote=True)
    media_type = slot.get("media_type", "image")
    embed_url = youtube_embed(str(slot.get("media_url") or ""))
    if preview_video_url:
        preview = f'<video src="{preview_video_url}" poster="{preview_url}" controls muted loop playsinline></video>'
    elif preview_url:
        play = '<span class="play">▶</span>' if media_type == "video" else ""
        preview = f'<a class="preview-link" href="{source_url}" target="_blank" rel="noreferrer"><img src="{preview_url}" alt="Preview {slot_id}">{play}</a>'
    elif embed_url:
        preview = f'<iframe src="{html.escape(embed_url, quote=True)}" title="Preview {slot_id}" allowfullscreen></iframe>'
    elif media_type == "video":
        preview = f'<video src="{media_url}" controls muted playsinline></video>'
    else:
        preview = f'<img src="{media_url}" alt="Preview {slot_id}">'
    return f"""
    <article class="card" data-id="{slot_id}">
      <div class="preview">{preview}</div>
      <div class="body">
        <div class="time">{html.escape(str(slot.get('start', '')))}s–{html.escape(str(slot.get('end', '')))}s</div>
        <h2>{slot_id}</h2>
        <p><strong>Narração:</strong> {html.escape(str(slot.get('narration', '')))}</p>
        <p><strong>Intenção:</strong> {html.escape(str(slot.get('intent', '')))}</p>
        <p><strong>Fonte:</strong> <a href="{source_url}" target="_blank" rel="noreferrer">{html.escape(str(slot.get('source_name', source_url)))}</a></p>
        <p><strong>Crédito:</strong> {html.escape(str(slot.get('credit') or 'não informado'))}</p>
        <p><strong>Direitos:</strong> {html.escape(str(slot.get('rights_status') or 'não verificado'))}</p>
        <p><strong>Tratamento:</strong> {html.escape(str(slot.get('fit') or 'cover'))}</p>
        <p><strong>Trecho da fonte:</strong> {html.escape(str(slot.get('source_in') or 'a definir'))}–{html.escape(str(slot.get('source_out') or 'a definir'))}</p>
        <p><strong>Texto incorporado:</strong> {html.escape(str(slot.get('source_text_status') or ('não se aplica' if media_type != 'video' else 'não verificado')))}</p>
        <textarea placeholder="Observação"></textarea>
        <div class="actions">
          <button data-decision="approved">Aprovar</button>
          <button data-decision="rejected">Rejeitar</button>
        </div>
      </div>
    </article>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.manifest.read_text())
    slots = raw.get("slots", raw) if isinstance(raw, dict) else raw
    cards = "\n".join(card(slot) for slot in slots)
    revision = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    page = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aprovação de mídia</title><style>
:root{{--bg:#0b0b0b;--panel:#171717;--text:#f7f7f7;--accent:#496fed}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui;padding:28px}}
header{{max-width:1180px;margin:auto auto 24px}}h1{{margin:0 0 8px}}.grid{{max-width:1180px;margin:auto;display:grid;gap:20px}}
.card{{display:grid;grid-template-columns:minmax(280px,42%) 1fr;background:var(--panel);border:1px solid #2b2b2b;border-radius:16px;overflow:hidden}}
.preview{{position:relative;min-height:300px;background:#050505;display:grid;place-items:center}}img,video,iframe{{width:100%;height:100%;min-height:300px;max-height:460px;object-fit:contain;border:0}}
.preview-link{{position:relative;display:grid;place-items:center;width:100%;height:100%}}
.play{{position:absolute;display:grid;place-items:center;width:64px;height:64px;border-radius:50%;background:#000b;color:white;font-size:28px;padding-left:4px;pointer-events:none}}
.body{{padding:22px}}.time{{color:var(--accent);font-weight:700}}h2{{margin:4px 0 16px}}p{{color:#ddd}}a{{color:#9cc9ff}}
textarea{{width:100%;min-height:70px;background:#101010;color:white;border:1px solid #444;border-radius:8px;padding:10px}}
.actions{{display:flex;gap:10px;margin-top:12px}}button{{padding:10px 16px;border-radius:999px;border:1px solid #555;background:#252525;color:white;cursor:pointer}}
button.active{{background:var(--accent);border-color:var(--accent)}}#export{{position:fixed;right:24px;bottom:24px;background:var(--accent);border:0}}
@media(max-width:760px){{.card{{grid-template-columns:1fr}}body{{padding:14px}}}}
</style></head><body><header><h1>Aprovação de mídia</h1><p>Uma recomendação por trecho. As decisões ficam salvas neste navegador.</p></header>
<main class="grid">{cards}</main><button id="export">Exportar decisões</button>
<script>
const revision='{revision}';const key='channel-media-approval:'+revision;const state=JSON.parse(localStorage.getItem(key)||'{{}}');
document.querySelectorAll('.card').forEach(card=>{{const id=card.dataset.id;const note=card.querySelector('textarea');note.value=state[id]?.note||'';
card.querySelectorAll('[data-decision]').forEach(btn=>{{if(state[id]?.decision===btn.dataset.decision)btn.classList.add('active');btn.onclick=()=>{{card.querySelectorAll('button').forEach(b=>b.classList.remove('active'));btn.classList.add('active');state[id]={{decision:btn.dataset.decision,note:note.value}};localStorage.setItem(key,JSON.stringify(state));}}}});
note.oninput=()=>{{state[id]={{decision:state[id]?.decision||'pending',note:note.value}};localStorage.setItem(key,JSON.stringify(state));}};}});
document.querySelector('#export').onclick=()=>{{const blob=new Blob([JSON.stringify({{manifest_sha256:revision,decisions:state}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='media_approval.json';a.click();URL.revokeObjectURL(a.href);}};
</script></body></html>"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
