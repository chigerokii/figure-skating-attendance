"""Раз в день снимает цены перепродажи билетов на чемпионат России 2027 (Челябинск, 17–20 декабря 2026).

Сохраняет текст страницы целиком (data/tickets/raw/<дата>/<id>.txt), чтобы разбор можно было переделать,
и разобранные пары «секторы — цена» в data/tickets/prices.csv.
"""
import csv, datetime as dt, glob, html, os, re, sys, time, urllib.request

PAGES = {
    "57531": ("2026-12-18", "женщины КП / мужчины ПП"),
    "60381": ("2026-12-18", "мужчины ПП (отдельная страница)"),
    "57532": ("2026-12-19", ""),
    "57533": ("2026-12-20", "финальный день"),
}
BASE = "https://tickets-russia.ru/other/figure-skating/bilety-chempionat-rossii-po-figurnom-kataniju/{}/"
today = dt.date.today().isoformat()


def parse(text, today, day, pid, note):
    """Блоки страницы: «Сектора <группа>» → «Сектор <X>» → «Выбрать места» → число мест → «7 500 ₽» или «под заказ»."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    out, group, sector, seats = [], "", "", ""
    for i, l in enumerate(lines):
        if l.startswith("Сектора "):
            group, sector, seats = l[len("Сектора "):], "", ""
        elif l.startswith("Сектор "):
            sector, seats = l[len("Сектор "):], ""
        elif l == "Выбрать места" and i + 1 < len(lines) and lines[i + 1].isdigit():
            seats = lines[i + 1]
        elif sector and re.fullmatch(r"[\d\s]+₽", l):
            out.append([today, day, pid, note, group, sector, seats, int(re.sub(r"\D", "", l))]); sector = ""
        elif sector and l.lower() == "под заказ":
            out.append([today, day, pid, note, group, sector, "", ""]); sector = ""
    return out
raw_dir = f"data/tickets/raw/{today}"
os.makedirs(raw_dir, exist_ok=True)
for pid, (day, note) in PAGES.items():
    try:
        req = urllib.request.Request(BASE.format(pid), headers={"User-Agent": "Mozilla/5.0 (research; one request per day)"})
        page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        print("fail", pid, e, file=sys.stderr); continue
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", text))
    text = re.sub(r"\n\s*\n+", "\n", text)
    open(f"{raw_dir}/{pid}.txt", "w").write(text)
    time.sleep(3)

# Таблица пересобирается из всех сохранённых снимков, чтобы исправленный разбор применялся и к старым дням
rows = []
for d in sorted(glob.glob("data/tickets/raw/*")):
    snap = os.path.basename(d)
    for pid, (day, note) in PAGES.items():
        f = f"{d}/{pid}.txt"
        if os.path.exists(f):
            rows.extend(parse(open(f).read(), snap, day, pid, note))
with open("data/tickets/prices.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["snapshot_date", "event_day", "page_id", "note", "sector_group", "sector", "seats_offered", "price_rub"])
    w.writerows(rows)
print(f"{len(rows)} rows")
