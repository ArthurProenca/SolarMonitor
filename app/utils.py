import datetime
import scrapping
import json
from fastapi import HTTPException
import calendar
import json
import scrapping
from image_utils import image_encode
import io
import csv
import tempfile
from tabulate import tabulate
import pytz
from sunspots_database_dao import SunspotsDatabaseDao
import requests
db_dao = SunspotsDatabaseDao()


def date_sanity_check(date_obj):
    tz = pytz.timezone('America/Sao_Paulo')
    date_obj = datetime.datetime.strptime(date_obj, "%Y-%m-%d").date()

    today = datetime.datetime.now(tz).date()
    if date_obj > today:
        return None
    return date_obj


def sunspot_backtracking(initial_date, sunspots):
    content, _ = cache_and_get_solar_monitor_info_from_day(initial_date, data_only=True)
    right_half = get_negative_days_arr(initial_date, 0)
    left_half = get_positive_days_arr(initial_date, 0)
    full_content = {}

    while True:
        matching_content = is_sunspot_on(sunspots, content)
        full_content[right_half] = matching_content
        if matching_content == []:
            right_half = get_positive_days_arr(right_half, 1)
            break
        right_half = get_negative_days_arr(right_half, 1)
        content, _ = cache_and_get_solar_monitor_info_from_day(right_half, data_only=True)

    content, _ = cache_and_get_solar_monitor_info_from_day(
        initial_date, data_only=True)  # Reinicia o conteúdo para a data inicial

    while True:
        matching_content = is_sunspot_on(sunspots, content)
        full_content[left_half] = matching_content
        if matching_content == []:
            left_half = get_negative_days_arr(left_half, 1)
            break
        left_half = get_positive_days_arr(left_half, 1)
        if date_sanity_check(left_half) is None:
            left_half = get_negative_days_arr(left_half, 1)
            break
        content, _ = cache_and_get_solar_monitor_info_from_day(left_half, data_only=True)

    return right_half, left_half, full_content


def create_text_table(content, bytes_io):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Prepare the data for tabulate
        table_data = []
        for item in content:
            noaa_number = item['noaaNumber']
            positions = item['latestPositions']
            for pos in positions:
                position = pos['position']
                day = pos['day']
                x_coordinate = pos['x_coordinate']
                y_coordinate = pos['y_coordinate']
                longitude = pos['longitude']
                latitude = pos['latitude']
                if ([noaa_number, position, day, x_coordinate, y_coordinate, longitude, latitude]) not in table_data:
                    table_data.append(
                        [noaa_number, position, day, x_coordinate, y_coordinate, longitude, latitude])

        # Generate the table using tabulate
        table = tabulate(table_data, headers=[
                         "Mancha", "Posição", "Dia", "Coordenada X", "Coordenada Y", "Longitude", "Latitude"], tablefmt="plain")

        # Write the formatted table to the temporary file
        with open(temp_file.name, 'w', encoding='utf-8') as f:
            f.write(table)

        # Copy the content to BytesIO
        with open(temp_file.name, 'rb') as file:
            bytes_io.write(file.read())


def create_csv(full_content, bytes_io):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        with io.TextIOWrapper(temp_file, newline='', write_through=True) as csv_file:
            # Set CSV file headers
            fieldnames = ['Mancha', 'Posição', 'Dia', 'Coordenada X',
                          'Coordenada Y', 'Longitude', 'Latitude']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write headers to the CSV file
            writer.writeheader()

            # Iterate over the data and write each line to the CSV file
            for item in full_content:
                noaa_number = item['noaaNumber']
                positions = item['latestPositions']
                for pos in positions:
                    writer.writerow({
                        'Mancha': noaa_number,
                        'Posição': pos['position'],
                        'Dia': pos['day'],
                        'Coordenada X': pos['x_coordinate'],
                        'Coordenada Y': pos['y_coordinate'],
                        'Longitude': pos['longitude'],
                        'Latitude': pos['latitude']
                    })

        # Copy the content to BytesIO
        with open(temp_file.name, 'rb') as file:
            bytes_io.write(file.read())


def is_sunspot_on(sunspots, table_contents):
    if table_contents is None:
        return []
    table_contents = [
        item for item in table_contents if item['noaaNumber'] in sunspots]
    return table_contents

def download_images(images, days_arr):
    downloaded_images = []
    
    for image in images:
        try:
            downloaded_image = scrapping.download_img(image)
            downloaded_images.append(downloaded_image)
        except requests.exceptions.MissingSchema or ValueError:
            downloaded_images.append(None)
    
    return downloaded_images


def cache_and_get_solar_monitor_info_from_day(date, data_only = False):
    json_data = db_dao.fetch_data_by_date(date)
    # Convert date to appropriate format
    formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    # Return cached data if both JSON and image are present
    if json_data is None:
        # Fetch new solar monitor information
        solar_monitor_info = get_solar_monitor_info([date])
        table_contents_aux = convert_table_contents_to_json(solar_monitor_info)
        json_data = []
        process_positions(table_contents_aux, json_data, [date])

       
        # Save data to the database, only insert the image if it's valid
        db_dao.insert_data(date, json_data)
    
    if data_only:
        return json_data, None

    # Fetch solar monitor images
    images = get_solar_monitor_images(formatted_date)
    image = download_images(images, [formatted_date])[0]  # Download image for the date

    # Encode the image if it exists
    if image is not None:
        image = image_encode(image)

    return json_data, image



def get_days_arr(initial_date, number_of_days):
    if int(number_of_days) < -1:
        raise HTTPException(
            status_code=400, detail="Number of days limit is 14.")
    if initial_date is None or number_of_days is None:
        raise HTTPException(
            status_code=400, detail="Both initial_date and number_of_days must be provided.")

    # initial_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")

    final_date = get_positive_days_arr(initial_date, number_of_days)
    final_date = datetime.datetime.strptime(final_date, "%Y-%m-%d")
    days_arr = []
    current_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")
    while current_date <= final_date:
        current_date_str = current_date.strftime("%Y-%m-%d")
        days_arr.append(current_date_str)

        current_date += datetime.timedelta(days=1)
    return days_arr

def get_days_arr_between_dates(initial_date: str, final_date: str, type: str):
    if initial_date is None or final_date is None:
        raise HTTPException(
            status_code=400, detail="Both initial_date and final_date must be provided."
        )

    try:
        initial_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d")
        final_date = datetime.datetime.strptime(final_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
        )

    if final_date < initial_date:
        raise HTTPException(
            status_code=400, detail="Final date must be greater than or equal to initial date."
        )

    days_arr = []

    if type == "MONTHLY":
        current_date = initial_date
        today = datetime.datetime.today()
        current_month = today.month
        current_year = today.year

        while current_date <= final_date:
            if current_date.month == current_month and current_date.year == current_year:
                # pula o mês atual
                current_date = (current_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
                continue

            first_day_of_month = current_date.replace(day=1)
            last_day_of_month = current_date.replace(
                day=calendar.monthrange(current_date.year, current_date.month)[1]
            )

            if first_day_of_month >= initial_date:
                days_arr.append(first_day_of_month.strftime("%Y-%m-%d"))
            if last_day_of_month <= final_date:
                days_arr.append(last_day_of_month.strftime("%Y-%m-%d"))

            current_date = (current_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

    elif type == "YEARLY":
        current_date = initial_date
        while current_date.year <= final_date.year:
            first_day_of_year = datetime.datetime(current_date.year, 1, 1)
            last_day_of_year = datetime.datetime(current_date.year, 12, 31)

            if first_day_of_year >= initial_date:
                days_arr.append(first_day_of_year.strftime("%Y-%m-%d"))

            if last_day_of_year <= final_date:
                days_arr.append(last_day_of_year.strftime("%Y-%m-%d"))
            else:
                days_arr.append(final_date.strftime("%Y-%m-%d"))
                break

            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)

    else:
        raise HTTPException(
            status_code=400, detail="Invalid type. Supported types are DAILY, MONTHLY, and YEARLY."
        )

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
                                                                    day.split(
                                                                        "-")[1],
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
            date = entry['Date']
            longitude = int(x_coordinate)
            latitude = int(y_coordinate)

            day = days_arr[i]  # Corresponding day to the current item
            found = False
            for item in result:
                if item['noaaNumber'] == number:
                    item['latestPositions'].append({'position': position, 'day': day, 'x_coordinate': x_coordinate,
                                                    'y_coordinate': y_coordinate,
                                                    'longitude': longitude,
                                                    'latitude': latitude,
                                                    'date': date})
                    found = True
                    break
            if not found:
                result.append({'noaaNumber': number, 'latestPositions':
                               [{'position': position,
                                 'day': day,
                                 'x_coordinate': x_coordinate,
                                 'y_coordinate': y_coordinate,
                                 'longitude': longitude,
                                 'latitude': latitude,
                                 'date': date}]})


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
                grouped_data.append(
                    {'noaaNumber': noaa_number, 'latestPositions': positions_list})
            else:
                for item in grouped_data:
                    if item['noaaNumber'] == noaa_number:
                        item['latestPositions'].extend(positions_list)
    return grouped_data


def is_sunspot_on(sunspots, table_contents):
    if table_contents is None:
        return []
    table_contents = [
        item for item in table_contents if item['noaaNumber'] in sunspots]
    return table_contents


def how_many_days_between(date1, date2):
    date1_obj = datetime.datetime.strptime(date1, '%Y-%m-%d')
    date2_obj = datetime.datetime.strptime(date2, '%Y-%m-%d')
    diff = date2_obj - date1_obj
    return diff.days
