#!/usr/bin/env python3
"""
fetch_contributions.py — obtém o calendário de contribuições público do
GitHub sem GraphQL API nem personal access token.

O GitHub serve o fragmento HTML do calendário em:
    https://github.com/users/<username>/contributions

que é o mesmo fragmento usado pela própria página de perfil. Fazemos
parsing dos <td> de cada dia com BeautifulSoup e gravamos os dados em
bruto + estatísticas derivadas (streak atual, streak mais longo, melhor
dia, totais mensais).

Uso:
    python scripts/fetch_contributions.py [username]
Gera:
    data/contributions.json
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

COUNT_RE = re.compile(r"^(No|\d+)\s+contribution")

DEFAULT_USERNAME = "TomasCCardoso"
OUT_PATH = Path("data/contributions.json")
URL_TMPL = "https://github.com/users/{username}/contributions"


def fetch_html(username: str) -> str:
    resp = requests.get(
        URL_TMPL.format(username=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    """
    O markup atual do GitHub já não traz a contagem no próprio <td>:
    cada dia é um <td data-date=... data-level=... id="...">, e a
    contagem real vive no texto de um <tool-tip for="<id do td>">,
    por exemplo "5 contributions on September 3rd." ou
    "No contributions on September 7th.".
    """
    soup = BeautifulSoup(html, "html.parser")

    # mapa id-do-td -> texto do tooltip associado
    tooltip_by_target = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_target[tip.get("for")] = tip.get_text(strip=True)

    days = []
    cells = soup.select("td.ContributionCalendar-day[data-date]")
    for cell in cells:
        d = cell.get("data-date")
        level = int(cell.get("data-level") or 0)

        count = 0
        tip_text = tooltip_by_target.get(cell.get("id"), "")
        m = COUNT_RE.match(tip_text)
        if m:
            count = 0 if m.group(1) == "No" else int(m.group(1))

        days.append({"date": d, "level": level, "count": count})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    total = sum(d["count"] for d in days)

    # streaks
    longest = current = 0
    running = 0
    today = date.today().isoformat()
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # streak atual: percorre do fim para trás
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            current += 1
        else:
            break

    best_day = max(days, key=lambda x: x["count"])

    monthly = defaultdict(int)
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] += d["count"]

    return {
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly.items())),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    print(f"A obter contribuições de {username}...")
    html = fetch_html(username)
    days = parse_days(html)

    if not days:
        print("Aviso: não encontrei células de contribuição — o GitHub pode ter mudado o markup.")

    stats = compute_stats(days)
    payload = {"username": username, "days": days, "stats": stats}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gravado {OUT_PATH} ({len(days)} dias, total={stats.get('total_last_year', 0)})")


if __name__ == "__main__":
    main()
