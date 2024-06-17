import matplotlib.pyplot as plt
import re
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates  # Importe o módulo matplotlib.dates

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
    plt.figure(figsize=(11, 7))  # Aumentar o tamanho da figura para melhor visualização

    for entry in result:
        noaa_number = entry['noaaNumber']
        positions = entry['latestPositions']
        
        # Extrair informações para o gráfico
        dates = [datetime.strptime(pos['day'], '%Y-%m-%d') for pos in positions]
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
    plt.legend(loc='best', fontsize=12)  # Ajuste a posição e o tamanho da legenda
    plt.grid(True, linestyle='--', linewidth=0.5)  # Adicione um grid mais claro
    plt.tight_layout()

    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Marcar todos os dias no eixo x
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))  # Formatar datas do eixo x
    
    plt.xticks(rotation=45, ha='right', fontsize=12)  # Rotacionar rótulos do eixo x e aumentar o tamanho da fonte

    plt.text(0.95, 0.01, 'Fonte dos dados: SolarMonitor.org', transform=plt.gca().transAxes, fontsize=12, ha='right', va='bottom')  # Mover texto da fonte para o canto inferior direito

    plt.savefig(img_bytes, format='png', bbox_inches='tight')  # Use bbox_inches='tight' para incluir a legenda
    plt.close()