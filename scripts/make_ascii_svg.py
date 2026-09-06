#!/usr/bin/env python3
"""
make_ascii_svg.py — converte assets/source-prepped.png num SVG de ASCII art
monocromático que "imprime" linha a linha (wipe da esquerda para a direita,
staggered de cima para baixo) e depois congela. Sem loop.

Uso:
    python scripts/make_ascii_svg.py
Gera:
    avi-ascii.svg   (mantém o nome do template; troca à vontade)
"""
from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path("assets/source-prepped.png")
OUT = Path("avi-ascii.svg")

RAMP = " .`:-=+*cs#%@"   # claro (esparso) -> escuro (denso)
#        ^ espaço inicial limpa o fundo para nada

COLS = 100                     # largura da grelha, em carateres
CHAR_ASPECT = 0.52              # largura/altura aproximada de um glifo monoespaçado
FONT_SIZE = 8                   # px
FILL_COLOR = "#9fb4c7"          # cinza-azulado claro, monocromático
ROW_STAGGER = 0.035             # segundos entre o início de cada linha
ROW_WIPE_DUR = 0.4              # segundos que demora cada linha a "escrever-se"


def image_to_ascii_rows(img: Image.Image, cols: int) -> list[str]:
    w, h = img.size
    cell_w = w / cols
    cell_h = cell_w / CHAR_ASPECT
    rows = max(1, round(h / cell_h))

    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(small, dtype=np.float32)

    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        chars = []
        for c in range(cols):
            brightness = arr[r, c] / 255.0          # 0 escuro .. 1 claro
            idx = int((1.0 - brightness) * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            chars.append(RAMP[idx])
        line = "".join(chars).rstrip()
        lines.append(line)

    # remove linhas em branco no topo/fundo para não desperdiçar espaço
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    return lines


def xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg_v2(lines: list[str]) -> str:
    """clipPaths em <defs>; texto/cursor no corpo visível."""
    n_rows = len(lines)
    max_len = max((len(l) for l in lines), default=0)

    char_w = FONT_SIZE * CHAR_ASPECT
    line_h = FONT_SIZE * 1.15

    width = round(max_len * char_w) + 20
    height = round(n_rows * line_h) + 20

    defs = []
    body = []
    for i, line in enumerate(lines):
        if not line:
            continue
        y = 10 + (i + 1) * line_h - 3
        row_w = len(line) * char_w + char_w
        begin = round(i * ROW_STAGGER, 3)

        clip_id = f"clip{i}"
        escaped = xml_escape(line)

        defs.append(f'''<clipPath id="{clip_id}">
      <rect x="0" y="{y - FONT_SIZE:.1f}" width="0" height="{FONT_SIZE * 1.4:.1f}">
        <animate attributeName="width" from="0" to="{row_w:.1f}"
                 begin="{begin}s" dur="{ROW_WIPE_DUR}s"
                 fill="freeze" calcMode="linear" />
      </rect>
    </clipPath>''')

        body.append(f'''<text x="10" y="{y:.1f}" clip-path="url(#{clip_id})">{escaped}</text>
    <rect y="{y - FONT_SIZE + 1:.1f}" width="{char_w * 0.8:.1f}" height="{FONT_SIZE * 1.1:.1f}"
          fill="{FILL_COLOR}" opacity="0">
      <animate attributeName="x" from="10" to="{10 + row_w:.1f}"
               begin="{begin}s" dur="{ROW_WIPE_DUR}s" fill="freeze" calcMode="linear" />
      <animate attributeName="opacity" values="0.85;0.85;0" keyTimes="0;0.9;1"
               begin="{begin}s" dur="{ROW_WIPE_DUR}s" fill="freeze" />
    </rect>''')

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" font-kerning="none">
  <defs>
    {''.join(defs)}
  </defs>
  <rect x="0" y="0" width="{width}" height="{height}" fill="transparent" />
  <g font-family="'SFMono-Regular','Consolas','Menlo',monospace" font-size="{FONT_SIZE}"
     fill="{FILL_COLOR}" xml:space="preserve">
    {''.join(body)}
  </g>
</svg>'''


def main():
    if not SRC.exists():
        raise SystemExit(f"Não encontrei {SRC}. Corre primeiro prep_photo.py.")

    img = Image.open(SRC).convert("L")
    lines = image_to_ascii_rows(img, COLS)
    svg = build_svg_v2(lines)
    OUT.write_text(svg, encoding="utf-8")
    print(f"Gravado {OUT} ({len(lines)} linhas)")


if __name__ == "__main__":
    main()
