import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime


# Функция для получения данных с MOEX
def get_moex_data(ticker, start, end):
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}/candles.json"
    params = {
        'from': start,
        'till': end,
        'interval': 24,  # Дневные данные
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Проверяем, есть ли данные в ответе
    if 'candles' not in data or 'data' not in data['candles']:
        raise ValueError(f"Нет данных для тикера {ticker}")

    # Извлекаем данные
    candles = data['candles']['data']
    df = pd.DataFrame(candles, columns=['open', 'close', 'high', 'low', 'value', 'volume', 'begin', 'end'])
    df['date'] = pd.to_datetime(df['end'])  # Используем колонку 'end' как дату
    df.set_index('date', inplace=True)
    return df['close']  # Возвращаем только цены закрытия


# Список акций, входящих в индекс Московской биржи (пример)
tickers = ['GAZP', 'SBER', 'LKOH', 'GMKN', 'ROSN', 'NVTK', 'TATN', 'MTSS', 'ALRS', 'PLZL']

# Период для получения данных
start_date = '2015-01-01'
end_date = '2025-03-05'

# Собираем данные по всем акциям
data = {}
for ticker in tickers:
    try:
        data[ticker] = get_moex_data(ticker, start_date, end_date)
        print(f"Данные для {ticker} успешно загружены")
    except Exception as e:
        print(f"Не удалось получить данные для {ticker}: {e}")

# Проверяем, есть ли данные для построения графика
if not data:
    print("Нет данных для построения графика.")
else:
    # Создаем DataFrame из собранных данных
    df = pd.DataFrame(data)

    # Рассчитываем корреляционную матрицу
    correlation_matrix = df.corr()

    # Визуализация тепловой карты
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='RdYlGn', vmin=0, vmax=1, linewidths=0.5)
    plt.title('Тепловая карта корреляции акций')
    plt.tight_layout()  # Улучшаем расположение элементов

    # Поиск пар акций с низкой корреляцией (например, меньше 0.1)
    low_corr_pairs = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i + 1, len(correlation_matrix.columns)):
            corr_value = correlation_matrix.iloc[i, j]
            if abs(corr_value) < 0.1:  # Порог корреляции
                pair = (correlation_matrix.columns[i], correlation_matrix.columns[j], corr_value)
                low_corr_pairs.append(pair)


    # Собираем уникальные тикеры из пар с низкой корреляцией
    unique_tickers = set()
    for pair in low_corr_pairs:
        unique_tickers.add(pair[0])
        unique_tickers.add(pair[1])

    # Выводим полный список тикеров для покупки
    print("\nПолный список тикеров для покупки:")
    print(", ".join(unique_tickers))

    # Предложение портфеля парами с указанием корреляции
    if low_corr_pairs:
        print("\nПредложение для портфеля парами:")
        for pair in low_corr_pairs:
            print(f"Портфель: {pair[0]} + {pair[1]} (корреляция: {pair[2]:.4f})")
    else:
        print("\nНет пар акций с низкой корреляцией для формирования портфеля.")

    # Добавляем информацию о периоде данных и уровне корреляции
    print(f"\nЭти акции с периода {start_date} по {end_date} имели корреляцию ниже 0.1.")
    plt.show()