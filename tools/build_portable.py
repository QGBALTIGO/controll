#!/usr/bin/env python3
"""Build an offline index.html using only the Python standard library.

The source snapshot is never executed. Only the embedded-data JSON is read.
No files containing sessions or credentials are read by this build.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVITE = re.compile(r'''(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me|telegram\.dog)/(?:\+|%2b|joinchat/)[^\s<>"')\]]+|tg://join\?[^\s<>"')\]]+''', re.I)
SENSITIVE_KEYS = {"api_id", "api_hash", "phone", "session", "auth_key", "token"}

def clean(value):
    if isinstance(value, str):
        return INVITE.sub('[convite privado removido]', value)
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items() if key not in SENSITIVE_KEYS}
    return value

def build(without_invites: bool = False, output: Path | None = None) -> Path:
    source = (ROOT / 'data/snapshot.html').read_text(encoding='utf-8')
    match = re.search(r'''<script\b[^>]*\bid=["']embedded-data["'][^>]*>(.*?)</script>''', source, re.S | re.I)
    if match is None:
        raise ValueError('Bloco embedded-data não encontrado em data/snapshot.html.')
    payload = json.loads(match.group(1))
    if not isinstance(payload.get('channels'), list):
        raise ValueError('O snapshot não contém a lista channels.')
    if without_invites:
        original = payload['channels']
        payload = clean(payload)
        payload.setdefault('meta', {})['sanitized'] = True
        for row, source_row in zip(payload['channels'], original):
            row['invite_present_source'] = bool(source_row.get('private_invite_link') or source_row.get('invite_present_source'))
            row['private_invite_link'] = ''
            if row.get('visibility') == 'Privado':
                row['primary_link'] = ''
    embedded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    css = (ROOT / 'assets/controll.css').read_text(encoding='utf-8')
    js = (ROOT / 'assets/controll.js').read_text(encoding='utf-8')
    html = html.replace('<link rel="stylesheet" href="./assets/controll.css">', '<style>' + css + '</style>')
    html = html.replace('  <script src="./assets/controll.js" defer></script>', '')
    # For the portable copy, even same-origin networking is disabled.
    html = html.replace("script-src 'self' 'unsafe-inline'", "script-src 'unsafe-inline'")
    html = html.replace("style-src 'self' 'unsafe-inline'", "style-src 'unsafe-inline'")
    html = html.replace("img-src 'self' data:", "img-src data:")
    html = html.replace("connect-src 'self'", "connect-src 'none'")
    html = html.replace('</body>', '<script id="embedded-data" type="application/json">' + embedded + '</script>\n<script>' + js + '</script>\n</body>')
    destination = output or ROOT / 'dist' / ('index_sem_convites.html' if without_invites else 'index.html')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding='utf-8')
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gera um HTML portátil do Controll.')
    parser.add_argument('--without-invites', action='store_true', help='Remove convites da base e das descrições.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(build(args.without_invites, args.output))
