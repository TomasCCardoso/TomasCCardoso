#!/usr/bin/env python3
"""
make_info_card.py — gera um painel SVG estilo `neofetch` com as linhas
a aparecer (fade + slide) uma a uma, staggered, como se estivessem a
ser impressas ao lado do retrato ASCII.

STATIC=1 python scripts/make_info_card.py
    -> gera um frame já totalmente revelado (útil para Quick Look local).

Uso:
    python scripts/make_info_card.py
Gera:
    info-card.svg
"""
import os
from pathlib import Path

OUT = Path("info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

# ---- conteúdo -------------------------------------------------------
USERNAME = "tomas@feup"
TITLE_BAR = f"{USERNAME}: ~"

FIELDS = [
    ("Now",        "Eng. Eletrotécnica e de Computadores @ FEUP (3º ano)"),
    ("Foco",       "Telecomunicações"),
    ("Estágio",    "Automação Industrial — Pirotecnia Duarte"),
    ("Stack",      "C/C++ · Python · LTspice · Excel"),
    ("Highlights", "Bombeiro Voluntário · Motostudent FEUP (equipa elétrica, já cessada)"),
]

LABEL_COLOR = "#39d353"     # verde, tipo prompt
VALUE_COLOR = "#c9d1d9"     # cinza claro, tipo texto de terminal
BG_COLOR = "#0d1117"        # fundo estilo GitHub dark
BORDER_COLOR = "#30363d"
TITLEBAR_COLOR = "#161b22"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]

FONT = "'SFMono-Regular','Consolas','Menlo',monospace"
FONT_SIZE = 14
LINE_H = 30
PAD_X = 22
TITLEBAR_H = 34
STAGGER = 0.18
FADE_DUR = 0.5
START_DELAY = 0.15  # pequeno atraso p/ a title bar "abrir" primeiro


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    label_w = max(len(k) for k, _ in FIELDS)
    char_w = FONT_SIZE * 0.6
    longest_line = max(label_w + 2 + len(v) for _, v in FIELDS)
    width = max(560, PAD_X * 2 + round(longest_line * char_w))
    height = TITLEBAR_H + PAD_X + len(FIELDS) * LINE_H + PAD_X

    rows = []
    for i, (label, value) in enumerate(FIELDS):
        y = TITLEBAR_H + PAD_X + i * LINE_H + FONT_SIZE
        begin = START_DELAY + i * STAGGER
        label_padded = esc(label) + ":" + "&#160;" * (label_w - len(label) + 1)

        if STATIC:
            rows.append(f'''
    <text x="{PAD_X}" y="{y}" font-family="{FONT}" font-size="{FONT_SIZE}">
      <tspan fill="{LABEL_COLOR}" font-weight="600">{label_padded}</tspan><tspan fill="{VALUE_COLOR}">{esc(value)}</tspan>
    </text>''')
        else:
            rows.append(f'''
    <g opacity="0" transform="translate(-14,0)">
      <animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="{FADE_DUR}s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      <animateTransform attributeName="transform" type="translate" from="-14,0" to="0,0" begin="{begin}s" dur="{FADE_DUR}s" fill="freeze" additive="replace" calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      <text x="{PAD_X}" y="{y}" font-family="{FONT}" font-size="{FONT_SIZE}">
        <tspan fill="{LABEL_COLOR}" font-weight="600">{label_padded}</tspan><tspan fill="{VALUE_COLOR}">{esc(value)}</tspan>
      </text>
    </g>''')

    dots = "".join(
        f'<circle cx="{22 + i * 18}" cy="{TITLEBAR_H / 2}" r="5.5" fill="{c}" />'
        for i, c in enumerate(DOT_COLORS)
    )

    svg = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="card-round">
      <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" ry="10" />
    </clipPath>
  </defs>
  <g clip-path="url(#card-round)">
    <rect x="0" y="0" width="{width}" height="{height}" fill="{BG_COLOR}" />
    <rect x="0" y="0" width="{width}" height="{TITLEBAR_H}" fill="{TITLEBAR_COLOR}" />
    {dots}
    <text x="{width / 2}" y="{TITLEBAR_H / 2 + 4}" text-anchor="middle"
          font-family="{FONT}" font-size="12" fill="#8b949e">{esc(TITLE_BAR)}</text>
    {''.join(rows)}
  </g>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" ry="10"
        fill="none" stroke="{BORDER_COLOR}" />
</svg>'''

    OUT.write_text(svg, encoding="utf-8")
    print(f"Gravado {OUT} ({'estático' if STATIC else 'animado'})")


if __name__ == "__main__":
    main()
