import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates  # Importe o módulo matplotlib.dates
import locale
from scipy.optimize import curve_fit
from matplotlib.ticker import MaxNLocator
from scipy.optimize import curve_fit

from matplotlib.ticker import MaxNLocator
def medium(list_aux):
    if not list_aux:
        return 0
    return sum(list_aux) / len(list_aux)


def date_format(data, pattern):
    # Mapeamento de meses em inglês para português
    months_translation = {
        'Jan': 'Jan',
        'Feb': 'Fev',
        'Mar': 'Mar',
        'Apr': 'Abr',
        'May': 'Mai',
        'Jun': 'Jun',
        'Jul': 'Jul',
        'Aug': 'Ago',
        'Sep': 'Set',
        'Oct': 'Out',
        'Nov': 'Nov',
        'Dec': 'Dez'
    }

    # Converter a data para um objeto datetime
    data_obj = datetime.strptime(data, "%Y-%m-%d")

    # Formatar a data conforme o padrão fornecido
    date_formatted = data_obj.strftime(pattern)

    # Substituir os nomes dos meses em inglês pelos nomes em português
    for month_en, month_pt in months_translation.items():
        date_formatted = date_formatted.replace(month_en, month_pt)

    return date_formatted


def extract_x_value(position):
    # Extrai o valor 'x' da posição no formato cddcdd(xxx, -yyy)
    x_value = re.search(r'\(([-+]?\d+)', position).group(1)
    return int(x_value)


def create_graphic(result, img_bytes, initial_date, final_date, do_adjustment):
    # Aumentar o tamanho da figura para melhor visualização
    plt.figure(figsize=(11, 7))

    for entry in result:
        noaa_number = entry['noaaNumber']
        positions = entry['latestPositions']

        # Extrair informações para o gráfico
        dates = [datetime.strptime(pos['day'], '%Y-%m-%d')
                 for pos in positions]
        longitudes = [pos['longitude'] for pos in positions]
        latitudes = [pos['latitude'] for pos in positions]

        # Verificar se há pontos suficientes para regressão linear
        if len(dates) >= 2:
            plt.scatter(dates, longitudes, label=f'Mancha {noaa_number}, latitude média: {np.mean(latitudes):.2f}', s=100, alpha=0.7)  # Ajuste o tamanho e a transparência dos pontos

            x_values = mdates.date2num(dates)
            coefficients = np.polyfit(x_values, longitudes, 1)
            a, b = coefficients

            fitted_dates = np.linspace(min(x_values), max(x_values), 100)
            fitted_dates_original_format = mdates.num2date(fitted_dates)

            if do_adjustment:
                plt.plot(fitted_dates_original_format, a * fitted_dates + b, label=f'Reta de Ajuste (y={a:.2f}x + b)', linestyle='--', linewidth=2)  # Ajuste o estilo e a largura da linha

    plt.xlabel('Data (formato dd/mm/yy)', fontsize=14)
    plt.ylabel('Longitude (°)', fontsize=14)
    plt.title(f'Gráfico: Longitude x Tempo para mancha(s) solar(es) entre {date_format(initial_date, "%d de %b. de %Y")} e {date_format(final_date, "%d de %b. de %Y")}', fontsize=11)
    # Ajuste a posição e o tamanho da legenda
    plt.legend(loc='best', fontsize=12)
    # Adicione um grid mais claro
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.tight_layout()

    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Marcar todos os dias no eixo x
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))  # Formatar datas do eixo x

    # Rotacionar rótulos do eixo x e aumentar o tamanho da fonte
    plt.xticks(rotation=45, ha='right', fontsize=12)

    plt.text(0.95, 0.01, 'Fonte dos dados: SolarMonitor.org', transform=plt.gca().transAxes,fontsize=12, ha='right', va='bottom')

    # Use bbox_inches='tight' para incluir a legenda
    plt.savefig(img_bytes, format='png', bbox_inches='tight')
    plt.close()


def create_sunspots_amount_graphic(result, img_bytes, initial_date, final_date, search_type):
    if search_type == "MONTHLY":
        plt.figure(figsize=(30, 15))
    else:
        plt.figure(figsize=(22, 10))
    # Coleta de dados de manchas solares por período
    # Em vez de armazenar apenas o noaa_number, armazene uma tupla (data, noaa_number)
    noaa_numbers_by_period = {}
    for entry in result:
        positions = entry['latestPositions']
        for pos in positions:
            pos_date = datetime.strptime(pos['date'], '%Y-%m-%d')
            noaa_number = int(entry['noaaNumber'])
            period_key = pos_date.strftime('%Y-%m' if search_type == 'MONTHLY' else '%Y')

            if period_key not in noaa_numbers_by_period:
                noaa_numbers_by_period[period_key] = []
            noaa_numbers_by_period[period_key].append((pos_date, noaa_number))

    # Ordena os dados de cada período pela data
    for period in noaa_numbers_by_period:
        noaa_numbers_by_period[period].sort(key=lambda x: x[0])

    # Calcula a contagem com base no primeiro e último valor ordenado
    periods = sorted(noaa_numbers_by_period.keys())

    sunspot_counts = 0
    if search_type == 'MONTHLY':    
        sunspot_counts = [
            0 if len(noaa_numbers_by_period[period]) ==  1
            else len(noaa_numbers_by_period[period])
            for period in periods
        ]
    else:
        sunspot_counts = [
        abs(noaa_numbers_by_period[period][0][1] - noaa_numbers_by_period[period][-1][1])
        for period in periods
    ]

    period_dates = [datetime.strptime(period, '%Y-%m' if search_type == 'MONTHLY' else '%Y') for period in periods]

    # Plot com transparência e tamanho ajustado para evitar sobreposição
    plt.scatter(period_dates, sunspot_counts, marker='o', color='b', alpha=0.6, s=40, label='Manchas Solares')

    plt.xlabel('Período', fontsize=18)
    plt.ylabel('Quantidade de Manchas', fontsize=18)

    # Ajuste do título
    title_period = "mensal" if search_type == 'MONTHLY' else "anual"
    if search_type == 'MONTHLY':
        title = f'Gráfico {title_period}: Número de manchas entre {date_format(initial_date, "%d de %b. de %Y")} e {date_format(final_date, "%d de %b. de %Y")}'
    else:
        title = f'Gráfico {title_period}: Número de manchas entre {periods[0]} e {periods[-1]}'
    plt.title(title, fontsize=18)

    plt.grid(True, linestyle='--', linewidth=0.5)

    ax = plt.gca()
    if search_type == 'MONTHLY':
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1 if len(sunspot_counts) < 24 else 3))  # Marcar meses no eixo x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator(base=1))  
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  


    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Rotacionar rótulos do eixo x
    plt.xticks(rotation=60, ha='right', fontsize=12)

    # Limite no eixo y
    plt.ylim(-1, max(sunspot_counts) + 5)

    plt.text(0.95, 0.01, 'Fonte dos dados: SolarMonitor.org', transform=plt.gca().transAxes, fontsize=5)

    # Ajuste do layout
    plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.15)

    # Salvando a imagem no buffer
    plt.savefig(img_bytes, format='png')
    plt.close()

def create_sunspots_amount_fourier_graphic(
    result,
    img_bytes,
    initial_date,
    final_date,
    search_type,
    max_harm=10
):
    # ===============================
    # 1) Construir série temporal
    # ===============================
    noaa_numbers_by_period = {}

    for entry in result:
        for pos in entry["latestPositions"]:
            pos_date = datetime.strptime(pos["date"], "%Y-%m-%d")
            period_key = pos_date.strftime("%Y-%m" if search_type == "MONTHLY" else "%Y")

            noaa_numbers_by_period.setdefault(period_key, set())
            noaa_numbers_by_period[period_key].add(entry["noaaNumber"])

    periods = sorted(noaa_numbers_by_period.keys())
    y = np.array([len(noaa_numbers_by_period[p]) for p in periods], dtype=float)

    period_dates = [
        datetime.strptime(p, "%Y-%m" if search_type == "MONTHLY" else "%Y")
        for p in periods
    ]

    # ===============================
    # 2) Converter datas → eixo numérico
    # ===============================
    x = np.arange(len(y))

    if len(x) < 6:
        raise ValueError("Poucos pontos para ajuste senoidal.")

    dt = 1  # amostragem uniforme (1 mês ou 1 ano)

    # ===============================
    # 3) FFT para estimar período dominante
    # ===============================
    y_detrended = y - np.mean(y)

    yf = np.fft.fft(y_detrended)
    xf = np.fft.fftfreq(len(x), dt)

    mask = xf > 0
    xf = xf[mask]
    yf = np.abs(yf[mask])

    if len(xf) == 0:
        raise ValueError("FFT não encontrou frequências positivas.")

    f_dom = xf[np.argmax(yf)]
    periodo_estimado = 1 / f_dom
    omega_inicial = 2 * np.pi / periodo_estimado

    # ===============================
    # 4) Modelo senoidal
    # ===============================
    def senoide(x, A, omega, fase, C):
        return A * np.sin(omega * x + fase) + C

    estimativa_inicial = [
        (np.max(y) - np.min(y)) / 2,  # Amplitude como no código original
        omega_inicial,                # Frequência angular vinda da FFT
        0,                            # Fase inicial
        np.mean(y)                    # Offset
    ]

    popt, _ = curve_fit(senoide, x, y, p0=estimativa_inicial)
    A_fit, omega_fit, fase_fit, C_fit = popt

    y_fit = senoide(x, A_fit, omega_fit, fase_fit, C_fit)

    # ===============================
    # 5) Plot
    # ===============================
    plt.figure(figsize=(30, 15) if search_type == "MONTHLY" else (22, 10))

    plt.scatter(
        period_dates,
        y,
        marker="o",
        alpha=0.6,
        s=60,
        label="Quantidade observada",
        zorder=3
    )

    plt.plot(
        period_dates,
        y_fit,
        linewidth=3,
        label=f"Ajuste Senoidal (Período ≈ {2*np.pi/omega_fit:.1f} períodos)"
    )

    plt.xlabel("Período", fontsize=18)
    plt.ylabel("Quantidade de manchas solares", fontsize=18)

    title_period = "mensal" if search_type == 'MONTHLY' else "anual"
    if search_type == 'MONTHLY':
        title = f'Gráfico {title_period}: Número de manchas entre {initial_date} e {final_date}'
    else:
        title = f'Gráfico {title_period}: Número de manchas entre {periods[0]} e {periods[-1]}'

    plt.title(title, fontsize=20)
    plt.grid(True, linestyle="--", linewidth=0.5)

    ax = plt.gca()

    if search_type == "MONTHLY":
        ax.xaxis.set_major_locator(
            mdates.MonthLocator(interval=1 if len(y) < 24 else 3)
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xticks(rotation=60, ha="right", fontsize=12)

    plt.ylim(-1, max(y) + 5)
    plt.legend(fontsize=14)

    plt.text(
        0.95,
        0.01,
        "Fonte dos dados: SolarMonitor.org",
        transform=ax.transAxes,
        fontsize=8,
        ha="right"
    )

    plt.subplots_adjust(left=0.08, right=0.95, top=0.90, bottom=0.18)

    plt.savefig(img_bytes, format="png")
    plt.close()