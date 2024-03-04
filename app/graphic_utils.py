import matplotlib.pyplot as plt
import re
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates  # Importe o módulo matplotlib.dates

def medium(list_aux):
    if not list_aux:
        return 0
    return sum(list_aux) / len(list_aux)


def extract_x_value(position):
    # Extrai o valor 'x' da posição no formato cddcdd(xxx, -yyy)
    x_value = re.search(r'\(([-+]?\d+)', position).group(1)
    return int(x_value)

def create_graphic(result, img_bytes, initial_date, final_date, do_adjustment):
    plt.figure(figsize=(18, 8))  # Adjust the height of the figure

    for entry in result:
        noaa_number = entry['noaaNumber']
        positions = entry['latestPositions']
        
        # Extract information for the graph
        dates = [datetime.strptime(pos['day'], '%Y-%m-%d') for pos in positions]
        longitudes = [pos['longitude'] for pos in positions]
        latitudes = [pos['latitude'] for pos in positions]


        # Check if there are enough points for linear regression
        if len(dates) >= 2:
            plt.scatter(dates, longitudes, label=f'Mancha {noaa_number}, latitude média: {medium(latitudes):.2f}', s=50, alpha=0.7)  # Add transparency for better visibility
            
            x_values = mdates.date2num(dates)
            coefficients = np.polyfit(x_values, longitudes, 1)
            a, b = coefficients

            fitted_dates = np.linspace(min(x_values), max(x_values), 100)
            fitted_dates_original_format = mdates.num2date(fitted_dates)

            if do_adjustment:
                plt.plot(fitted_dates_original_format, a * fitted_dates + b, label=f'Reta de Ajuste (a={a:.2f})', linestyle='--')

    plt.xlabel('Dia', fontsize=12)
    plt.ylabel('Longitude', fontsize=12)
    plt.title(f'Gráfico de Dispersão e Reta de Ajuste: Longitude x Tempo para cada mancha solar entre {initial_date} e {final_date}', fontsize=14)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
    plt.grid(True)
    plt.tight_layout()

    plt.subplots_adjust(left=0.1, right=0.85, top=0.85, bottom=0.1)  # Adjust the top margin

    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability

    plt.savefig(img_bytes, format='png', bbox_inches='tight')  # Use bbox_inches='tight' to include the legend
    plt.close()
