"""Раз в день снимает цены перепродажи билетов на чемпионат России 2027 (Челябинск, 17–20 декабря 2026).

Сохраняет текст страницы целиком (data/tickets/raw/<дата>/<id>.txt), чтобы разбор можно было переделать,
и разобранные пары «секторы — цена» в data/tickets/prices.csv.
"""
import csv, datetime as dt, html, os, re, sys, time, urllib.request

PAGES = {
    "57531": ("2026-12-18", "женщины КП / мужчины ПП"),
    "60381": ("2026-12-18", "мужчины ПП (отдельная страница)"),
    "57532": ("2026-12-19", ""),
    "57533": ("2026-12-20", "финальный день"),
}
BASE = "https://tickets-russia.ru/other/figure-skating/bilety-chempionat-rossii-po-figurnom-kataniju/{}/"
today = dt.date.today().isoformat()
raw_dir = f"data/tickets/raw/{today}"
os.makedirs(raw_dir, exist_ok=True)
out = "data/tickets/prices.csv"
new = not os.path.exists(out)
rows = []
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
    for m in re.finditer(r"(Сектор[аы]?\s+[A-ZА-Я0-9][A-ZА-Я0-9 ,]*)\s*\n\s*([\d\s]{3,})\s*₽", text):
        price = int(re.sub(r"\s", "", m.group(2)))
        rows.append([today, day, pid, note, m.group(1).strip(), price])
    for m in re.finditer(r"(Сектор[аы]?\s+[A-ZА-Я0-9][A-ZА-Я0-9 ,]*)\s*\n\s*под заказ", text):
        rows.append([today, day, pid, note, m.group(1).strip(), ""])
    time.sleep(3)
with open(out, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["snapshot_date", "event_day", "page_id", "note", "sectors", "price_rub"])
    w.writerows(rows)
print(f"{len(rows)} rows")
