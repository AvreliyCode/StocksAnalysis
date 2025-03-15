import numpy as np
import pandas as pd
import requests
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

# Список акций из индекса Московской биржи
tickers = [
    'GAZP', 'SBER', 'LKOH', 'GMKN', 'ROSN', 'NVTK', 'TATN', 'MTSS', 'ALRS', 'PLZL',
    'MGNT', 'CHMF', 'SNGS', 'SNGSP', 'TATNP', 'PHOR', 'RUAL', 'AFKS', 'VTBR', 'MOEX'
]

# Загрузка исторических данных
start_date = "2023-01-01"
end_date = "2025-03-05"  # Исправьте дату, если она в будущем
data = pd.DataFrame()

for ticker in tickers:
    try:
        data[ticker] = get_moex_data(ticker, start_date, end_date)
    except ValueError as e:
        print(e)
        continue  # Пропустить тикер, если данные недоступны

# Удаляем строки с пропущенными значениями
data.dropna(inplace=True)

# Расчет ежедневной доходности
returns = data.pct_change().dropna()

# Функция для генерации случайных портфелей
def generate_random_portfolios(returns, num_portfolios=1000):
    num_assets = len(returns.columns)
    results = np.zeros((3 + num_assets, num_portfolios))  # Массив для хранения результатов

    for i in range(num_portfolios):
        # Генерируем случайные веса
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)  # Нормализуем веса

        # Рассчитываем доходность и риск портфеля
        portfolio_return = np.sum(returns.mean() * weights) * 252  # Годовая доходность
        portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))  # Годовой риск

        # Сохраняем результаты
        results[0, i] = portfolio_return
        results[1, i] = portfolio_risk
        results[2, i] = results[0, i] / results[1, i]  # Коэффициент Шарпа
        results[3:, i] = weights  # Веса активов

    return results

# Генерация случайных портфелей
num_portfolios = 10000
results = generate_random_portfolios(returns, num_portfolios)

# Создаем фигуру с двумя областями для графиков
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Визуализация карты портфелей
scatter = ax1.scatter(results[1, :], results[0, :], c=results[2, :], cmap='viridis', marker='o')
plt.colorbar(scatter, ax=ax1, label='Коэффициент Шарпа')
ax1.set_title('Карта портфелей')
ax1.set_xlabel('Риск (волатильность)')
ax1.set_ylabel('Доходность')
ax1.grid(True)

# Круговая диаграмма (изначально пустая)
wedges, texts, autotexts = ax2.pie([1], labels=[''], autopct='%1.1f%%', startangle=90)
ax2.set_title('Состав портфеля')

# Функция для обновления круговой диаграммы при клике
def on_click(event):
    if event.inaxes == ax1:  # Проверяем, что клик был на карте портфелей
        # Находим ближайшую точку
        x, y = event.xdata, event.ydata
        distances = np.sqrt((results[1, :] - x) ** 2 + (results[0, :] - y) ** 2)
        index = np.argmin(distances)

        # Фильтрация активов с весом больше 10%
        weights = results[3:, index]
        threshold = 0.10  # Порог для отображения (10%)
        labels = returns.columns[weights > threshold]  # Показываем только активы с весом > 10%
        sizes = weights[weights > threshold]

        # Если все веса меньше порога, показываем топ-1 актив
        if len(labels) == 0:
            labels = [returns.columns[np.argmax(weights)]]
            sizes = [np.max(weights)]

        # Обновляем круговую диаграмму
        ax2.clear()
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax2.set_title(f'Состав портфеля\nДоходность: {results[0, index]:.2%}, Риск: {results[1, index]:.2%}')
        plt.draw()

# Подключаем обработчик клика
fig.canvas.mpl_connect('button_press_event', on_click)

# Показываем график
plt.tight_layout()
plt.show()