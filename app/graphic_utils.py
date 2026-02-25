import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
from scipy.optimize import curve_fit
from matplotlib.ticker import MaxNLocator, FuncFormatter


# ============================================================
# Constantes e helpers de formatação PT-BR
# ============================================================

_MONTHS_PT = {
    'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
    'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
    'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez',
}

# Paleta consistente para múltiplas manchas
_COLOR_CYCLE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
]


def _pt_month_formatter(fmt):
    """Retorna um FuncFormatter que formata datas com meses em português."""
    def _format(x, pos=None):
        dt = mdates.num2date(x)
        label = dt.strftime(fmt)
        for en, pt in _MONTHS_PT.items():
            label = label.replace(en, pt)
        return label
    return FuncFormatter(_format)


def _apply_base_style(ax, fontsize_tick=12):
    """Aplica estilo visual base a um eixo: grid, tick sizes, spine cleanup."""
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    ax.tick_params(axis='both', labelsize=fontsize_tick)
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)


def _add_source_label(ax, fontsize=10):
    """Adiciona rótulo de fonte dos dados no canto inferior direito."""
    ax.text(
        0.95, 0.01, 'Fonte dos dados: SolarMonitor.org',
        transform=ax.transAxes, fontsize=fontsize,
        ha='right', va='bottom', style='italic', alpha=0.6,
    )


# ============================================================
# Funções utilitárias
# ============================================================

def medium(list_aux):
    if not list_aux:
        return 0
    return sum(list_aux) / len(list_aux)


def date_format(data, pattern):
    """Formata uma data string (YYYY-MM-DD) com meses em português."""
    data_obj = datetime.strptime(data, "%Y-%m-%d")
    date_formatted = data_obj.strftime(pattern)
    for en, pt in _MONTHS_PT.items():
        date_formatted = date_formatted.replace(en, pt)
    return date_formatted


def extract_x_value(position):
    """Extrai o valor 'x' da posição no formato cddcdd(xxx, -yyy)."""
    x_value = re.search(r'\(([-+]?\d+)', position).group(1)
    return int(x_value)


# ============================================================
# 1) Gráfico: Longitude x Tempo (manchas individuais)
# ============================================================

def create_graphic(result, img_bytes, initial_date, final_date, do_adjustment):
    """Gráfico de dispersão: longitude vs tempo para manchas solares."""
    fig, ax = plt.subplots(figsize=(12, 7))

    for idx, entry in enumerate(result):
        noaa_number = entry['noaaNumber']
        positions = entry['latestPositions']

        dates = [datetime.strptime(pos['day'], '%Y-%m-%d') for pos in positions]
        longitudes = [pos['longitude'] for pos in positions]
        latitudes = [pos['latitude'] for pos in positions]

        if len(dates) < 2:
            continue

        color = _COLOR_CYCLE[idx % len(_COLOR_CYCLE)]
        lat_media = np.mean(latitudes)

        ax.scatter(
            dates, longitudes,
            label=f'Mancha {noaa_number} (lat. média: {lat_media:.1f}°)',
            s=90, alpha=0.8, color=color, edgecolors='white', linewidths=0.5,
            zorder=3,
        )

        if do_adjustment:
            x_num = mdates.date2num(dates)
            coefs = np.polyfit(x_num, longitudes, 1)
            a, b = coefs
            x_fit = np.linspace(min(x_num), max(x_num), 200)
            ax.plot(
                mdates.num2date(x_fit), a * x_fit + b,
                linestyle='--', linewidth=2, color=color, alpha=0.7,
                label=f'Ajuste linear ({noaa_number})',
            )

    ax.set_xlabel('Data', fontsize=14)
    ax.set_ylabel('Longitude (°)', fontsize=14)

    titulo = (
        f'Longitude × Tempo para mancha(s) solar(es)\n'
        f'{date_format(initial_date, "%d de %b. de %Y")} — '
        f'{date_format(final_date, "%d de %b. de %Y")}'
    )
    ax.set_title(titulo, fontsize=13, fontweight='bold')

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(_pt_month_formatter('%d/%m/%y'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    _apply_base_style(ax)
    ax.legend(loc='best', fontsize=11, framealpha=0.9)
    _add_source_label(ax, fontsize=10)

    fig.tight_layout()
    fig.savefig(img_bytes, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)


# ============================================================
# 2) Gráfico: Quantidade de manchas por período
# ============================================================

def _build_sunspot_series(result, search_type):
    """Extrai períodos e contagens de manchas a partir dos dados brutos."""
    noaa_by_period = {}
    for entry in result:
        for pos in entry['latestPositions']:
            pos_date = datetime.strptime(pos['date'], '%Y-%m-%d')
            noaa_number = int(entry['noaaNumber'])
            fmt = '%Y-%m' if search_type == 'MONTHLY' else '%Y'
            key = pos_date.strftime(fmt)
            noaa_by_period.setdefault(key, [])
            noaa_by_period[key].append((pos_date, noaa_number))

    for period in noaa_by_period:
        noaa_by_period[period].sort(key=lambda x: x[0])

    periods = sorted(noaa_by_period.keys())

    if search_type == 'MONTHLY':
        counts = [
            0 if len(noaa_by_period[p]) == 1
            else len(noaa_by_period[p])
            for p in periods
        ]
    else:
        counts = [
            abs(noaa_by_period[p][0][1] - noaa_by_period[p][-1][1])
            for p in periods
        ]

    fmt = '%Y-%m' if search_type == 'MONTHLY' else '%Y'
    period_dates = [datetime.strptime(p, fmt) for p in periods]

    return periods, counts, period_dates


def _configure_period_axis(ax, search_type, n_points):
    """Configura o eixo x para períodos mensais ou anuais em PT-BR."""
    if search_type == 'MONTHLY':
        interval = 1 if n_points < 24 else (3 if n_points < 72 else 6)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
        ax.xaxis.set_major_formatter(_pt_month_formatter('%b %Y'))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.setp(ax.get_xticklabels(), rotation=55, ha='right')

def create_sunspots_amount_graphic(result, img_bytes, initial_date, final_date, search_type):
    """Gráfico de dispersão: quantidade de manchas solares por período."""
    periods, counts, period_dates = _build_sunspot_series(result, search_type)

    figsize = (28, 13) if search_type == "MONTHLY" else (20, 10)
    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(
        period_dates, counts,
        marker='o', color='#1f77b4', alpha=0.8, s=50,
        edgecolors='white', linewidths=0.5,
        label='Manchas solares', zorder=2,
    )

    ax.set_xlabel('Período', fontsize=16)
    ax.set_ylabel('Quantidade de Manchas', fontsize=16)

    tipo = "mensal" if search_type == 'MONTHLY' else "anual"
    if search_type == 'MONTHLY':
        titulo = (
            f'Quantidade {tipo} de manchas solares\n'
            f'{date_format(initial_date, "%d de %b. de %Y")} — '
            f'{date_format(final_date, "%d de %b. de %Y")}'
        )
    else:
        titulo = (
            f'Quantidade {tipo} de manchas solares\n'
            f'{periods[0]} — {periods[-1]}'
        )
    ax.set_title(titulo, fontsize=17, fontweight='bold')

    _configure_period_axis(ax, search_type, len(counts))
    _apply_base_style(ax)

    ax.set_ylim(-1, max(counts) + 5)
    ax.legend(fontsize=13, loc='best', framealpha=0.9)
    _add_source_label(ax, fontsize=10)

    fig.tight_layout()
    fig.savefig(img_bytes, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)


# ============================================================
# 3) Gráfico: Ajuste senoidal (Fourier) — quantidade de manchas
# ============================================================

def _fit_sinusoidal(x, y):
    """Estima parâmetros senoidais via FFT + curve_fit. Retorna (popt, senoide_func)."""
    y_detrended = y - np.mean(y)
    yf = np.fft.fft(y_detrended)
    xf = np.fft.fftfreq(len(x), d=1)

    mask = xf > 0
    if not np.any(mask):
        raise ValueError("FFT não encontrou frequências positivas.")

    f_dom = xf[mask][np.argmax(np.abs(yf[mask]))]
    omega_ini = 2 * np.pi * f_dom

    def senoide(x, amp, omega, fase, offset):
        return amp * np.sin(omega * x + fase) + offset

    p0 = [(np.max(y) - np.min(y)) / 2, omega_ini, 0, np.mean(y)]
    popt, _ = curve_fit(senoide, x, y, p0=p0, maxfev=10000)
    return popt, senoide


def create_sunspots_amount_fourier_graphic(
    result, img_bytes, initial_date, final_date, search_type,
):
    """Gráfico com ajuste senoidal suave sobre contagem de manchas por período."""
    # --- Construir série temporal (via set para evitar duplicatas) ---
    noaa_by_period = {}
    for entry in result:
        for pos in entry["latestPositions"]:
            pos_date = datetime.strptime(pos["date"], "%Y-%m-%d")
            fmt = "%Y-%m" if search_type == "MONTHLY" else "%Y"
            key = pos_date.strftime(fmt)
            noaa_by_period.setdefault(key, set())
            noaa_by_period[key].add(entry["noaaNumber"])

    periods = sorted(noaa_by_period.keys())
    y = np.array([len(noaa_by_period[p]) for p in periods], dtype=float)

    fmt = "%Y-%m" if search_type == "MONTHLY" else "%Y"
    period_dates = [datetime.strptime(p, fmt) for p in periods]

    x = np.arange(len(y))
    if len(x) < 6:
        raise ValueError("Poucos pontos para ajuste senoidal (mínimo 6).")

    # --- Ajuste senoidal ---
    popt, senoide = _fit_sinusoidal(x, y)
    amp_fit, omega_fit, fase_fit, offset_fit = popt

    # --- Curva suave com alta resolução ---
    n_smooth = max(500, len(x) * 20)
    x_smooth = np.linspace(x[0], x[-1], n_smooth)
    y_smooth = senoide(x_smooth, *popt)

    date_start = mdates.date2num(period_dates[0])
    date_end = mdates.date2num(period_dates[-1])
    smooth_dates = mdates.num2date(np.linspace(date_start, date_end, n_smooth))

    # --- Plot ---
    figsize = (28, 13) if search_type == "MONTHLY" else (20, 10)
    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(
        period_dates, y,
        marker='o', alpha=0.7, s=60, color='#1f77b4',
        edgecolors='white', linewidths=0.5,
        label='Quantidade observada', zorder=3,
    )

    unidade = "meses" if search_type == "MONTHLY" else "anos"
    periodo_est = abs(2 * np.pi / omega_fit)
    ax.plot(
        smooth_dates, y_smooth,
        color='#ff7f0e', linewidth=3,
        label=f'Ajuste senoidal (período ≈ {periodo_est:.1f} {unidade})',
        zorder=2,
    )

    ax.set_xlabel('Período', fontsize=16)
    ax.set_ylabel('Quantidade de manchas solares', fontsize=16)

    tipo = "mensal" if search_type == 'MONTHLY' else "anual"
    if search_type == 'MONTHLY':
        titulo = (
            f'Ajuste senoidal ({tipo}) — Manchas solares\n'
            f'{date_format(initial_date, "%d de %b. de %Y")} — '
            f'{date_format(final_date, "%d de %b. de %Y")}'
        )
    else:
        titulo = (
            f'Ajuste senoidal ({tipo}) — Manchas solares\n'
            f'{periods[0]} — {periods[-1]}'
        )

    ax.set_title(titulo, fontsize=18, fontweight='bold')

    _configure_period_axis(ax, search_type, len(y))
    _apply_base_style(ax)

    ax.set_ylim(-1, max(y) + 5)
    ax.legend(fontsize=14, loc='best', framealpha=0.9)
    _add_source_label(ax, fontsize=10)

    fig.tight_layout()
    fig.savefig(img_bytes, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)


# ============================================================
# 4) Gráfico Fourier individual: Longitude x Tempo com senóide
# ============================================================

def create_fourier_graphic(result, img_bytes, initial_date, final_date):
    """Gráfico de longitude x tempo com ajuste senoidal para cada mancha."""
    fig, ax = plt.subplots(figsize=(12, 7))

    has_data = False

    for idx, entry in enumerate(result):
        noaa_number = entry['noaaNumber']
        positions = entry['latestPositions']

        dates = [datetime.strptime(pos['day'], '%Y-%m-%d') for pos in positions]
        longitudes = np.array([pos['longitude'] for pos in positions], dtype=float)

        if len(dates) < 4:
            continue

        has_data = True
        color = _COLOR_CYCLE[idx % len(_COLOR_CYCLE)]

        ax.scatter(
            dates, longitudes,
            s=90, alpha=0.8, color=color, edgecolors='white', linewidths=0.5,
            label=f'Mancha {noaa_number}', zorder=3,
        )

        # Ajuste senoidal na longitude
        x_num = mdates.date2num(dates)
        x_norm = x_num - x_num[0]

        try:
            popt, senoide = _fit_sinusoidal(x_norm, longitudes)

            n_smooth = 300
            x_smooth = np.linspace(x_norm[0], x_norm[-1], n_smooth)
            y_smooth = senoide(x_smooth, *popt)
            dates_smooth = mdates.num2date(x_smooth + x_num[0])

            ax.plot(
                dates_smooth, y_smooth,
                linewidth=2.5, color=color, alpha=0.7,
                label=f'Ajuste senoidal ({noaa_number})',
            )
        except (ValueError, RuntimeError):
            # Se o ajuste falhar, plota apenas linha simples
            ax.plot(dates, longitudes, linewidth=1, color=color, alpha=0.4)

    if not has_data:
        ax.text(
            0.5, 0.5, 'Dados insuficientes para ajuste',
            transform=ax.transAxes, ha='center', va='center', fontsize=16,
        )

    ax.set_xlabel('Data', fontsize=14)
    ax.set_ylabel('Longitude (°)', fontsize=14)

    titulo = (
        f'Ajuste senoidal — Longitude × Tempo\n'
        f'{date_format(initial_date, "%d de %b. de %Y")} — '
        f'{date_format(final_date, "%d de %b. de %Y")}'
    )
    ax.set_title(titulo, fontsize=13, fontweight='bold')

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(_pt_month_formatter('%d/%m/%y'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    _apply_base_style(ax)
    ax.legend(loc='best', fontsize=11, framealpha=0.9)
    _add_source_label(ax, fontsize=10)

    fig.tight_layout()
    fig.savefig(img_bytes, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
