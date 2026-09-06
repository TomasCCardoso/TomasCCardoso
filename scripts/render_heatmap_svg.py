#!/usr/bin/env python3
"""
render_heatmap_svg.py — desenha data/contributions.json como a clássica
grelha 53 semanas x 7 dias de quadrados arredondados, com uma rampa de
verdes estilo GitHub. Revela-se uma vez com um slide-down diagonal
(CSS keyframes que correm ao carregar e depois congelam — sem loop),
mais legenda Less→More e um rodapé com estatísticas.

Uso:
    python scripts/render_heatmap_svg.py
Gera:
    contrib-heatmap.svg
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_PATH = Path("data/contributions.json")
OUT = Path("contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          nenhuma -> nível 5 (topo neon, acima da escala normal do GitHub)

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 30       # espaço p/ labels dos dias da semana
TOP_PAD = 20         # espaço p/ labels dos meses
RIGHT_PAD = 12
BOTTOM_PAD = 46      # espaço p/ legenda + stats

STAGGER_COL = 0.02   # atraso entre colunas (semanas)
STAGGER_ROW = 0.01   # atraso extra por linha (dia da semana), dá o efeito diagonal
CELL_DUR = 0.35

MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
WEEKDAY_LABELS = {1: "Seg", 3: "Qua", 5: "Sex"}  # 0=Seg .. 6=Dom


def level_color(level: int) -> str:
    level = max(0, min(level, len(PALETTE) - 1))
    return PALETTE[level]


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Agrupa os dias em semanas (colunas), cada semana com 7 células (Dom..Sáb,
    à la GitHub) para desenhar a grelha 53x7."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []

    last_day = date.fromisoformat(days[-1]["date"])
    # recua até ao Domingo anterior (ou igual) ao primeiro dia, para alinhar colunas
    first_day = date.fromisoformat(days[0]["date"])
    start = first_day - timedelta(days=(first_day.weekday() + 1) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= last_day:
        iso = cur.isoformat()
        week.append(by_date.get(iso))
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)
    return weeks


def month_labels(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    labels = []
    last_month = None
    for col, week in enumerate(weeks):
        for cell in week:
            if cell is None:
                continue
            d = date.fromisoformat(cell["date"])
            if d.month != last_month:
                labels.append((col, MONTH_NAMES[d.month - 1]))
                last_month = d.month
            break
    return labels


def main():
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    days = payload["days"]
    stats = payload.get("stats", {})
    username = payload.get("username", "")

    weeks = build_weeks(days)
    n_cols = len(weeks)

    width = LEFT_PAD + n_cols * STEP + RIGHT_PAD
    height = TOP_PAD + 7 * STEP + BOTTOM_PAD

    cells_svg = []
    for col, week in enumerate(weeks):
        for row, cell in enumerate(week):
            x = LEFT_PAD + col * STEP
            y = TOP_PAD + row * STEP
            if cell is None:
                continue
            color = level_color(cell["level"])
            begin = round(col * STAGGER_COL + row * STAGGER_ROW, 3)
            title = f"{cell['count']} contribuições em {cell['date']}"
            cells_svg.append(f'''<rect x="{x}" y="{y - 8}" width="{CELL}" height="{CELL}" rx="2.5" ry="2.5"
      fill="{color}" opacity="0">
    <title>{title}</title>
    <animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="{CELL_DUR}s" fill="freeze" />
    <animate attributeName="y" from="{y - 8}" to="{y}" begin="{begin}s" dur="{CELL_DUR}s" fill="freeze"
             calcMode="spline" keySplines="0.25 0.1 0.25 1" />
  </rect>''')

    month_svg = []
    for col, name in month_labels(weeks):
        x = LEFT_PAD + col * STEP
        month_svg.append(
            f'<text x="{x}" y="{TOP_PAD - 7}" font-size="10" fill="#8b949e">{name}</text>'
        )

    weekday_svg = []
    for row, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + row * STEP + CELL
        weekday_svg.append(
            f'<text x="0" y="{y}" font-size="10" fill="#8b949e">{label}</text>'
        )

    # legenda Less -> More, ancorada à direita para nunca sair do viewBox
    legend_y = height - 12
    right_edge = width - RIGHT_PAD
    more_w = 30
    squares_end_x = right_edge - more_w - 6
    squares_start_x = squares_end_x - len(PALETTE) * (CELL + 2)

    legend_svg = [
        f'<text x="{squares_start_x - 6}" y="{legend_y + 8}" font-size="10" fill="#8b949e" text-anchor="end">Less</text>'
    ]
    for i, color in enumerate(PALETTE):
        lx = squares_start_x + i * (CELL + 2)
        legend_svg.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" ry="2.5" fill="{color}" />'
        )
    legend_svg.append(
        f'<text x="{right_edge}" y="{legend_y + 8}" font-size="10" fill="#8b949e" text-anchor="end">More</text>'
    )

    total = stats.get("total_last_year", 0)
    streak = stats.get("longest_streak", 0)
    footer = (f"{total} contribuições no último ano · "
              f"streak mais longo: {streak} dias")

    svg = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" font-family="'SFMono-Regular','Consolas','Menlo',monospace">
  <rect x="0" y="0" width="{width}" height="{height}" fill="transparent" />
  <g>{''.join(month_svg)}</g>
  <g>{''.join(weekday_svg)}</g>
  <g>{''.join(cells_svg)}</g>
  <g>{''.join(legend_svg)}</g>
  <text x="{LEFT_PAD}" y="{height - 4}" font-size="10" fill="#8b949e">{footer}</text>
</svg>'''

    OUT.write_text(svg, encoding="utf-8")
    print(f"Gravado {OUT} ({n_cols} semanas, total={total})")


if __name__ == "__main__":
    main()
