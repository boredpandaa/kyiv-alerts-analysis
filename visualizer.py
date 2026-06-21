import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

sns.set_theme(style="whitegrid")

try:
    df = pd.read_csv("processed_time_series.csv")
except FileNotFoundError:
    sys.exit("Помилка: не знайдено processed_time_series.csv. Запусти analyzer.py")

OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Динамічне визначення періоду аналізу
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert('Europe/Kyiv')
start_date = df['timestamp'].min().strftime('%d.%m.%Y')
end_date = df['timestamp'].max().strftime('%d.%m.%Y')
period_str = f"Період: {start_date} — {end_date}"

locations = df['location'].unique()
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# =====================================================================
# ЕТАП 1: Індивідуальні 1D-профілі 
# =====================================================================
print("Генеруємо індивідуальні 1D-профілі...")
for loc in locations:
    loc_df = df[df['location'] == loc].copy()
    if loc_df.empty:
        continue
        
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. За годиною
    hourly = loc_df.groupby('hour')['is_alert'].mean() * 100
    sns.barplot(x=hourly.index, y=hourly.values, ax=axes[0], color="steelblue")
    axes[0].set_title(f"Історична частота тривог: Година доби ({loc})\n{period_str}", pad=15, fontweight='bold')
    axes[0].set_ylabel("Частота (%)")
    axes[0].set_xlabel("Година доби")
    y_max = hourly.max() * 1.2 if hourly.max() > 0 else 100
    axes[0].set_ylim(0, max(y_max, 10))

    # 2. За днем тижня
    daily = loc_df.groupby('day_of_week')['is_alert'].mean() * 100
    daily = daily.reindex(days_order)
    sns.barplot(x=daily.index, y=daily.values, ax=axes[1], color="lightslategray")
    axes[1].set_title(f"Історична частота тривог: День тижня ({loc})\n{period_str}", pad=15, fontweight='bold')
    axes[1].set_ylabel("Частота (%)")
    axes[1].set_xlabel("День тижня")
    y_max_daily = daily.max() * 1.2 if daily.max() > 0 else 100
    axes[1].set_ylim(0, max(y_max_daily, 10))
    axes[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    loc_path = os.path.join(OUTPUT_DIR, f"{loc}_1D_Profile.png")
    plt.savefig(loc_path, dpi=300)
    plt.close()

# =====================================================================
# ЕТАП 2: Зведені макро-матриці 
# =====================================================================
print("Будуємо зведені макро-матриці...")

# 1. Години
hourly_summary = df.groupby(['location', 'hour'])['is_alert'].mean() * 100
hourly_pivot = hourly_summary.reset_index().pivot(index='location', columns='hour', values='is_alert')
max_hourly = hourly_pivot.max().max()

plt.figure(figsize=(18, 6))
sns.heatmap(
    hourly_pivot, annot=True, fmt=".0f", cmap="Reds", linewidths=.5,
    cbar_kws={'label': f'Відносна частота (макс: {max_hourly:.0f}%)'}
)
plt.title(f"Зведена частота тривог за локаціями та годинами\n{period_str}", fontsize=14, pad=15, fontweight='bold')
plt.xlabel("Година доби", fontsize=12)
plt.ylabel("Локація", fontsize=12)
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "Consolidated_Hourly_Heatmap.png"), dpi=300)
plt.close()

# 2. Дні тижня
daily_summary = df.groupby(['location', 'day_of_week'])['is_alert'].mean() * 100
daily_pivot = daily_summary.reset_index().pivot(index='location', columns='day_of_week', values='is_alert')
daily_pivot = daily_pivot.reindex(columns=days_order)
max_daily = daily_pivot.max().max()

plt.figure(figsize=(14, 6))
sns.heatmap(
    daily_pivot, annot=True, fmt=".0f", cmap="Reds", linewidths=.5,
    cbar_kws={'label': f'Відносна частота (макс: {max_daily:.0f}%)'}
)
plt.title(f"Зведена частота тривог за локаціями та днями тижня\n{period_str}", fontsize=14, pad=15, fontweight='bold')
plt.xlabel("День тижня", fontsize=12)
plt.ylabel("Локація", fontsize=12)
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "Consolidated_Daily_Heatmap.png"), dpi=300)
plt.close()

print(f"Готово. Всі графіки зберегли у папку '{OUTPUT_DIR}'.")