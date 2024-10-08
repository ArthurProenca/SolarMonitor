import requests
from bs4 import BeautifulSoup
import re
import json
import cv2
import requests
import numpy as np

base_url = "https://www.solarmonitor.org"
solar_monitor_url = base_url + "/full_disk.php?date={}&type=shmi_maglc&indexnum=1"

def get_x_coordinate(coordinates_match):
    if coordinates_match[0] == "N":
        return "-" + coordinates_match[1:3]
    else:
        return coordinates_match[1:3]
    
def get_y_coordinate(coordinates_match):
    if coordinates_match[3] == "E":
        return "-" + coordinates_match[4:6]
    else:
        return coordinates_match[4:6]

def get_html(url):
    return requests.get(url)

def get_soup(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def get_image_links_from_date(year, month, day):
    html_content = get_soup(get_html(solar_monitor_url.format(year+month+day, "")))
    links = html_content.find_all('a', string=re.compile(r'.*fd.*'))
    links = [link.get('href') for link in links]
    links = [solar_monitor_url.format(year, month, day, link) for link in links]
    return links

def get_table_content_from_date(year, month, day):
    # Supondo que você tenha a função get_soup e a URL correta definida
    html_content = get_soup(get_html(solar_monitor_url.format(year + month + day, "")))
    tables = html_content.find_all('div', class_='noaat')

    data = []

    for table in tables:
        rows = table.find_all('tr', class_='noaaresults')
        for row in rows:
            cells = row.find_all('td')
            #Get first 6 digits from cells[1].text.strip()
            coordinates_match = cells[1].text.strip()[:6]

            coordinate_x = get_y_coordinate(coordinates_match)
            coordinate_y = get_x_coordinate(coordinates_match)
            entry = {
                "NOAA Number": cells[0].text.strip(),
                "Latest Position": cells[1].text.strip(),
                "Coordinate X": coordinate_x,
                "Coordinate Y": coordinate_y,
                "Hale Class": cells[2].text.strip(),
                "McIntosh Class": cells[3].text.strip(),
                "Sunspot Area [millionths]": cells[4].text.strip(),
                "Number of Spots": cells[5].text.strip(),
                "Recent Flares": [link.text.strip() for link in cells[6].find_all('a')],
                "Date": f"{year}-{month}-{day}"
            }
            data.append(entry)

    return json.dumps(data, indent=2, ensure_ascii=False)


def get_table_image_from_date(year, month, day):
    html_content = get_soup(get_html(solar_monitor_url.format(year + month + day, "")))
    # Encontra todas as tags de imagem <img> com a string 'shmi' no atributo src
    img_tags = html_content.find_all('img', src=lambda value: value and 'shmi_maglc_fd' in value)

    # Itera sobre as tags <img> que atendem ao critério especificado acima
    for img in img_tags:
        img_src = img.get('src')
        img_src = base_url + "/" + img_src
  # Imprime o src da imagem que contém 'shmi' no atributo src
        return (""+img_src)  # Retorna o primeiro src encontrado que satisfaz a condição



def download_img(url):
    response = requests.get(url)
    
    # Verifica se o download foi bem-sucedido
    if response.status_code == 200:
        img_array = np.frombuffer(response.content, np.uint8)
        
        # Verifica se o conteúdo da imagem não está vazio
        if img_array.size > 0:
            imagem = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if imagem is not None:
                return imagem
            else:
                raise ValueError("Falha ao decodificar a imagem.")
        else:
            print("error->", url)
            return None
    else:
        raise ValueError(f"Falha ao baixar a imagem. Status code: {response.status_code}")
