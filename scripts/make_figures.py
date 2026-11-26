"""Графики к README по данным из data/*.csv (каждая цифра там со ссылкой на источник)."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE, ORANGE, GREY, RED, GREEN = "#2a6fdb", "#e07a1f", "#9aa5b1", "#c8463d", "#2e9e6a"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})

ev = pd.read_csv("data/events.csv")
se = pd.read_csv("data/sessions.csv")
ru = pd.read_csv("data/russia_reports.csv")
se["fill"] = np.where(se.attendance.notna(), se.attendance / se.capacity * 100, se.fill_pct)

# 1. Заполняемость по дням турнира — по панели на турнир, у каждого свои дни
series = [("wc2023", "ЧМ 2023, Сайтама (16 000 мест)", RED), ("rgp2023omsk", "ГП России 2023, Омск (12 000)", BLUE),
          ("sa2012", "Skate America 2012, Кент (3 940)", ORANGE), ("wc2016", "ЧМ 2016, Бостон (14 971), суббота", GREEN)]
fig, axes = plt.subplots(1, 4, figsize=(15, 4.2), sharey=True, gridspec_kw={"width_ratios": [3, 2, 5, 2]})
for ax, (eid, lab, c) in zip(axes, series):
    d = se[se.event_id == eid].sort_values("day_order")
    y = d["fill"].clip(upper=100)
    ax.bar(d.day, y, color=c, alpha=0.85)
    for x, v in zip(d.day, y):
        ax.text(x, v + 2, f"{v:.0f}%", ha="center", fontsize=9)
    ax.set_title(lab, fontsize=10); ax.tick_params(axis="x", rotation=30, labelsize=8); ax.set_ylim(0, 112)
axes[0].set_ylabel("заполняемость, % мест")
fig.suptitle("Будни продаются хуже выходных: на ЧМ-2023 в среду пришло 38% зала, в субботу — аншлаг", fontsize=12)
fig.tight_layout(); fig.savefig("images/fill_by_day.png", dpi=150); plt.close(fig)

# 2. Размер арены и заполняемость
pts = []
def add(name, cap, fill, kind, show=False):
    pts.append(dict(name=name, cap=cap, fill=fill, kind=kind, show=show))
r = ev.set_index("event_id")
add("ЧМ 2016 Бостон", 14971, r.loc["wc2016", "attendance_total"] / (9 * 14971) * 100, "официально")
add("Skate America 2012", 3940, r.loc["sa2012", "attendance_total"] / (5 * 3940) * 100, "официально")
add("Skate Canada 2024", 10595, 8363 / (4 * 10595) * 100, "официально")
add("ГП России 2023 Омск", 12000, r.loc["rgp2023omsk", "attendance_total"] / (2 * 12000) * 100, "официально")
add("ЧМ 2023 Сайтама (ср–чт)", 16000, (6110 + 10428) / (2 * 16000) * 100, "официально")
for _, x in ru.dropna(subset=["capacity", "fill_pct_estimate"]).iterrows():
    add(f"{x.event} {x.city}", x.capacity, x.fill_pct_estimate, "оценка", show="Шоу" in x.event)
p = pd.DataFrame(pts)
fig, ax = plt.subplots(figsize=(9, 5))
for kind, m in [("официально", "o"), ("оценка", "s")]:
    d = p[(p.kind == kind) & ~p.show]
    ax.scatter(d.cap / 1000, d.fill, s=90, marker=m, color=BLUE if kind == "официально" else ORANGE, label=f"соревнования, {kind}", zorder=3)
d = p[p.show]
ax.scatter(d.cap / 1000, d.fill, s=110, marker="*", color=RED, label="ледовое шоу (для сравнения)", zorder=3)
offsets = {"Кубок Первого канала (юниоры) Москва": (6, 8), "Гран-при России Красноярск": (6, -12)}
for _, x in p.iterrows():
    ax.annotate(x["name"], (x.cap / 1000, x.fill), xytext=offsets.get(x["name"], (6, -3)), textcoords="offset points", fontsize=8)
ax.set_xlabel("вместимость арены, тыс. мест"); ax.set_ylabel("средняя заполняемость, %"); ax.set_ylim(0, 110); ax.set_xlim(2, 18.5)
ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.set_title("Залы на 3–4 тыс. мест заполнены на 67–100%, на 10–16 тыс. — на 20–80%", fontsize=11)
fig.tight_layout(); fig.savefig("images/arena_size_vs_fill.png", dpi=150); plt.close(fig)

# 3. США: долгий спад
fig, ax = plt.subplots(figsize=(10, 4.6))
for prefix, lab, c in [("usc", "Чемпионат США", BLUE), ("sa", "Skate America (этап Гран-при)", ORANGE)]:
    d = ev[ev.event_id.str.startswith(prefix)].sort_values("season_year")
    ax.plot(d.season_year, d.attendance_total / 1000, marker="o", ms=7, lw=1, ls=":", color=c, label=lab)
    for x, y in zip(d.season_year, d.attendance_total / 1000):
        ax.annotate(f"{y:.0f}", (x, y), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8, color=c)
ax.set_ylabel("зрителей за турнир, тыс."); ax.set_ylim(0, 180)
ax.legend(frameon=False)
ax.text(1998, 165, "пунктир — годы без данных; число сессий и арены в разные годы разные", fontsize=8, color=GREY)
ax.set_title("В США пик пришёлся на 2007–2010 годы; Skate America за 4 года потеряла две трети зрителей", fontsize=11)
fig.tight_layout(); fig.savefig("images/usa_trend.png", dpi=150); plt.close(fig)

# 4. Российский Гран-при против международного: зрителей в среднем за день
rows = [("ГП России 2023\nОмск", 17957 / 2, BLUE), ("ГП России 2024\nМагнитогорск", 16283 / 2, BLUE), ("ГП России 2025\nОмск", 17000 / 2, BLUE),
        ("Skate America 2012\nКент", 13172 / 3, ORANGE), ("Skate Canada 2024\nГалифакс", 9563 / 4, ORANGE)]
fig, ax = plt.subplots(figsize=(9, 4.4))
b = ax.bar([x[0] for x in rows], [x[1] for x in rows], color=[x[2] for x in rows])
ax.bar_label(b, labels=[f"{x[1]:,.0f}".replace(",", " ") for x in rows], padding=3, fontsize=9)
ax.set_ylabel("зрителей в среднем за день")
ax.set_title("Региональный этап Гран-при России собирает за день в 2–4 раза больше, чем этап ISU в Северной Америке", fontsize=11)
fig.tight_layout(); fig.savefig("images/russia_vs_isu.png", dpi=150); plt.close(fig)
print(p.round(1))
