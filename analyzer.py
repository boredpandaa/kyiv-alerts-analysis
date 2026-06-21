import json
import pandas as pd
from pathlib import Path

LOCATIONS = {
    31: "Kyiv_City",
    73: "Bila_Tserkva",
    74: "Vyshhorod",
    75: "Bucha",
    76: "Obukhiv",
    77: "Fastiv",
    78: "Boryspil",
    79: "Brovary"
}

def load_raw_data(data_dir="raw_data"):
    alerts = []
    path = Path(data_dir)
    
    for file_path in path.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            alerts.extend(data.get('alerts', []))
            
    df = pd.DataFrame(alerts)
    df['location_uid'] = df['location_uid'].astype(int)
    df = df[df['location_uid'].isin(LOCATIONS.keys())].copy()
    df['location_name'] = df['location_uid'].map(LOCATIONS)
    
    return df

def build_time_series(df):
    df['started_at'] = pd.to_datetime(df['started_at']).dt.tz_convert('Europe/Kyiv')
    
    now = pd.Timestamp.now(tz='Europe/Kyiv')
    # Замінюємо null на зараз, щоб скрипт не впав, але залишаємо реальні фініші недоторканими
    df['finished_at'] = pd.to_datetime(df['finished_at']).fillna(now).dt.tz_convert('Europe/Kyiv')
    
    # Аналітичне вікно: рівно до 00:00 сьогоднішнього дня (тобто 23:59:59 вчора)
    cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Відкидаємо лише ті події, які ПОЧАЛИСЯ після дедлайну
    df = df[df['started_at'] < cutoff].copy()
    
    start_date = df['started_at'].min().floor('h')
    # Остання година сітки — це 23:00 вчорашнього дня (вона покриває інтервал 23:00-23:59)
    end_date = cutoff - pd.Timedelta(hours=1)
    
    time_grid = pd.date_range(start=start_date, end=end_date, freq='h', tz='Europe/Kyiv')
    
    # Будуємо порожню матрицю
    records = []
    for loc in LOCATIONS.values():
        for t in time_grid:
            records.append({
                'location': loc, 
                'timestamp': t, 
                'is_alert': 0, 
                'alert_minutes': 0.0
            })
            
    grid_df = pd.DataFrame(records)
    # Мультиіндекс прискорює пошук і оновлення комірок (optimizes lookup overhead)
    grid_df.set_index(['location', 'timestamp'], inplace=True)
    
    for _, row in df.iterrows():
        loc = row['location_name']
        start = row['started_at']
        finish = row['finished_at']
        
        # Визначаємо, які саме години зачепила ця тривога
        h_start = start.floor('h')
        h_finish = finish.ceil('h') 
        
        # Генеруємо список годин для конкретної події
        alert_hours = pd.date_range(start=h_start, end=h_finish, freq='h', inclusive='left')
        
        for h in alert_hours:
            # Працюємо лише якщо ця година існує в нашій аналітичній сітці
            if (loc, h) in grid_df.index:
                grid_df.loc[(loc, h), 'is_alert'] = 1
                
                # Обчислюємо точний перетин (intersection overlap)
                overlap_start = max(start, h)
                overlap_end = min(finish, h + pd.Timedelta(hours=1))
                overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
                
                # Додаємо хвилини (на випадок двох коротких тривог в одну годину)
                grid_df.loc[(loc, h), 'alert_minutes'] += overlap_minutes
                
    grid_df.reset_index(inplace=True)
    # Зрізаємо аномалії, якщо дві тривоги наклалися через помилку API і дали більше 60 хв
    grid_df['alert_minutes'] = grid_df['alert_minutes'].clip(upper=60.0)
    
    return grid_df

if __name__ == "__main__":
    print("Парсимо сирі JSON...")
    raw_df = load_raw_data()
    
    print("Генеруємо безперервну матрицю...")
    ts_df = build_time_series(raw_df)
    
    ts_df['day_of_week'] = ts_df['timestamp'].dt.day_name()
    ts_df['hour'] = ts_df['timestamp'].dt.hour
    
    # Виводимо найбрудніші години, щоб перевірити математику перетинів
    print("\nТоп-10 слотів за кількістю хвилин тривоги:")
    print(ts_df.sort_values(by='alert_minutes', ascending=False).head(10)[
        ['location', 'timestamp', 'is_alert', 'alert_minutes']
    ])
    
    print(f"\nЗагальна кількість годинних слотів: {len(ts_df)}")
    print(f"Остання зафіксована година в сітці: {ts_df['timestamp'].max()}")

    output_file = "processed_time_series.csv"
    ts_df.to_csv(output_file, index=False)
    print(f"Готову матрицю записали у {output_file}")