import datetime
import scrapping
import image_utils
import json
import csv
import zipfile

def convert_to_csv(data, csv_file):
    csv_rows = []

    # Adiciona o cabeçalho
    header = ['noaaNumber', 'day', 'x_coordinate', 'y_coordinate', 'longitude', 'latitude']
    csv_rows.append(header)

    # Itera sobre os dados e adiciona as linhas ao CSV
    for entry in data:
        noaa_number = entry['noaaNumber']
        positions = entry['latestPositions']

        for position in positions:
            day = position['day']
            x_coordinate = position['x_coordinate']
            y_coordinate = position['y_coordinate']
            longitude = position['longitude']
            latitude = position['latitude']

            row = [noaa_number, day, x_coordinate, y_coordinate, longitude, latitude]
            csv_rows.append(row)

    # Escreve no arquivo CSV
    csv_writer = csv.writer(csv_file)
    csv_writer.writerows(csv_rows)


def get_by_noaa_number(result, noaa_numbers):
    selected_items_arr = []
    for item in result:
        if item['noaaNumber'] in noaa_numbers:
            selected_items_arr.append(item)
    return selected_items_arr

def get_positive_days_arr(initial_date, number_of_days): 
    return initial_date + datetime.timedelta(days=number_of_days)

def get_negative_days_arr(initial_date, number_of_days): 
    return initial_date - datetime.timedelta(days=number_of_days)

def get_solar_monitor_info(initial_date, final_date, is_backward):
    days_arr = []
    table_contents = []
    images = []
    current_date = initial_date

    if is_backward:
        while current_date >= final_date:
            current_date_str = current_date.strftime("%Y-%m-%d")

            days_arr.append(current_date_str)
            
            table_contents.append(scrapping.get_table_content_from_date(current_date_str.split("-")[0],
                                                              current_date_str.split("-")[1],
                                                              current_date_str.split("-")[2]))
            images.append(scrapping.get_table_image_from_date(current_date_str.split("-")[0],
                                                                 current_date_str.split("-")[1],
                                                                 current_date_str.split("-")[2]))
            
            current_date -= datetime.timedelta(days=1)
        return days_arr, table_contents, images
    else:
        while current_date <= final_date:
            current_date_str = current_date.strftime("%Y-%m-%d")

            days_arr.append(current_date_str)
            
            table_contents.append(scrapping.get_table_content_from_date(current_date_str.split("-")[0],
                                                            current_date_str.split("-")[1],
                                                            current_date_str.split("-")[2]))
            images.append(scrapping.get_table_image_from_date(current_date_str.split("-")[0],
                                                                current_date_str.split("-")[1],
                                                                current_date_str.split("-")[2]))
            
            current_date += datetime.timedelta(days=1)

        return days_arr, table_contents, images

def download_and_preprocess_images(images, days_arr):
    images = [scrapping.download_img(image) for image in images]
    return [image_utils.preprocess_image(image, day) for image, day in zip(images, days_arr)]

def convert_table_contents_to_json(table_contents):
    return [json.loads(table_content) for table_content in table_contents]

def process_positions(table_contents_aux, result, days_arr):
    for i, table_content in enumerate(table_contents_aux):
        for entry in table_content:
            number = entry['NOAA Number']
            position = entry['Latest Position']
            x_coordinate = entry['Coordinate X'].replace('"', '')
            y_coordinate = entry['Coordinate Y'].replace('"', '')

            longitude = int(x_coordinate)
            latitude = int(y_coordinate)

            day = days_arr[i]  # Corresponding day to the current item
            found = False
            for item in result:
                if item['noaaNumber'] == number:
                    item['latestPositions'].append({'position': position, 'day': day,'x_coordinate': x_coordinate, 
                                                    'y_coordinate': y_coordinate,
                                                    'longitude': longitude,
                                                    'latitude': latitude})
                    found = True
                    break
            if not found:
                result.append({'noaaNumber': number, 'latestPositions': 
                               [{'position': position, 
                                 'day': day, 
                                 'x_coordinate': x_coordinate, 
                                 'y_coordinate': y_coordinate,
                                 'longitude': longitude,
                                 'latitude': latitude}]})