import datetime
import scrapping
import json
from fastapi import  HTTPException
import database_service
import json
import scrapping
from image_utils import image_encode

def sunspot_backtracking(initial_date, sunspots):
    content, _ = save_and_get_solar_monitor_info_from_day(initial_date)
    right_half = get_negative_days_arr(initial_date, 0)
    left_half = get_positive_days_arr(initial_date, 0)
    full_content = {}

    while True:
        matching_content = is_sunspot_on(sunspots, content)
        full_content[right_half] = matching_content
        if matching_content == []:
            break
        right_half = get_negative_days_arr(right_half, 1)
        content, _ = save_and_get_solar_monitor_info_from_day(right_half)

    content, _ = save_and_get_solar_monitor_info_from_day(initial_date)  # Reinicia o conteúdo para a data inicial

    while True:
        matching_content = is_sunspot_on(sunspots, content)
        full_content[left_half] = matching_content
        if matching_content == []:
            break
        left_half = get_positive_days_arr(left_half, 1)
        content, _ = save_and_get_solar_monitor_info_from_day(left_half)
    
    return right_half, left_half, full_content
        



def is_sunspot_on(sunspots, table_contents):
    if table_contents is None:
        return []
    table_contents = [item for item in table_contents if item['noaaNumber'] in sunspots]
    return table_contents


def download_images(images, days_arr):
    images = [scrapping.download_img(image) for image in images]
    return images

def save_and_get_solar_monitor_info_from_day(date):
    cached_content = database_service.get_by_date(date)
    if cached_content is not None:
        print(f"Date {date} cached content")
        return cached_content.json_data, cached_content.image
    
    solar_monitor_info = get_solar_monitor_info([date])
    table_contents_aux = convert_table_contents_to_json(solar_monitor_info)
    json_data = []
    process_positions(table_contents_aux, json_data, [date])
    json_data_str = json.dumps(json_data)

    formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    images = get_solar_monitor_images(formatted_date)
    image = download_images(images, [formatted_date])[0]
    image = image_encode(image)
    database_service.save_data(json_data_str, date, image)
    print(f"Date {date} not cached content")
    return json_data_str, image

    

def get_days_arr(initial_date, number_of_days):
    if int(number_of_days) < -1:
        raise HTTPException(status_code=400, detail="Number of days limit is 14.")
    if initial_date is None or number_of_days is None:
        raise HTTPException(status_code=400, detail="Both initial_date and number_of_days must be provided.")

    #initial_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")
    
    final_date = get_positive_days_arr(initial_date, number_of_days)
    final_date = datetime.datetime.strptime(final_date, "%Y-%m-%d")
    days_arr = []
    current_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")
    while current_date <= final_date:
            current_date_str = current_date.strftime("%Y-%m-%d")
            days_arr.append(current_date_str)
            
            current_date += datetime.timedelta(days=1)
    return days_arr


def get_by_noaa_number(result, noaa_numbers):
    selected_items_arr = []
    for item in result:
        if item['noaaNumber'] in noaa_numbers:
            selected_items_arr.append(item)
    return selected_items_arr

def get_positive_days_arr(initial_date, number_of_days): 
    initial_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")
    return str(initial_date + datetime.timedelta(days=number_of_days)).replace(" 00:00:00", "")

def get_negative_days_arr(initial_date, number_of_days): 
    initial_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")
    return str(initial_date - datetime.timedelta(days=number_of_days)).replace(" 00:00:00", "")

def get_solar_monitor_images(date: datetime.datetime):
    current_date_str = date.strftime("%Y-%m-%d")
    return [scrapping.get_table_image_from_date(current_date_str.split("-")[0],
                                                                 current_date_str.split("-")[1],
                                                                 current_date_str.split("-")[2])]

def get_solar_monitor_info(date_arr):
    table_contents = []

    for day in date_arr:
        table_contents.append(scrapping.get_table_content_from_date(day.split("-")[0],
                                                              day.split("-")[1],
                                                              day.split("-")[2]))

    return table_contents

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


def data_equalizer(data: dict):
    data = dict(reversed(list(data.items())))
    for date, positions_list in data.items():
        for item in positions_list:
            for position in item['latestPositions']:
                position['day'] = date
    grouped_data = []

    for positions in data.values():
        for position_info in positions:
            noaa_number = position_info['noaaNumber']
            positions_list = position_info['latestPositions']
            if not any(d['noaaNumber'] == noaa_number for d in grouped_data):
                grouped_data.append({'noaaNumber': noaa_number, 'latestPositions': positions_list})
            else:
                for item in grouped_data:
                    if item['noaaNumber'] == noaa_number:
                        item['latestPositions'].extend(positions_list)
    return grouped_data


def is_sunspot_on(sunspots, table_contents):
    if table_contents is None:
        return []
    table_contents = [item for item in table_contents if item['noaaNumber'] in sunspots]
    return table_contents

def how_many_days_between(date1, date2):
    date1_obj = datetime.datetime.strptime(date1, '%Y-%m-%d')
    date2_obj = datetime.datetime.strptime(date2, '%Y-%m-%d')
    diff = date2_obj - date1_obj
    return diff.days