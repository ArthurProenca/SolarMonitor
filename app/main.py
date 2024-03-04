from typing import List
from fastapi import FastAPI, Query, Response
from fastapi.responses import StreamingResponse
import datetime
import image_utils
import graphic_utils
import utils
import imageio
from concurrent.futures import ThreadPoolExecutor
import functools
from datetime import datetime
import zipfile
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS middleware
origins = ["*"]  # You can replace "*" with your allowed origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can replace "*" with your allowed methods
    allow_headers=["*"],  # You can replace "*" with your allowed headers
)

def download_and_preprocess_image(day):
    day = datetime.strptime(day, "%Y-%m-%d")  # Convert day to datetime object
    images = utils.get_solar_monitor_images(day)
    return image_utils.download_and_preprocess_images(images, [day])[0]

@app.get("/solar-monitor/{initial_date}/{number_of_days}/gif")
def get_solar_monitor_gif_from_days(initial_date: str, 
                                    number_of_days: int, 
                                    sunspot_numbers: List[str] = Query(None)):
    days_arr = utils.get_days_arr(initial_date, number_of_days)

    with ThreadPoolExecutor() as executor:
        download_and_preprocess_partial = functools.partial(download_and_preprocess_image)
        images = list(executor.map(download_and_preprocess_partial, days_arr))

    if sunspot_numbers is not None:
        images = image_utils.highlight_text_in_images(images, sunspot_numbers)

    return StreamingResponse(image_utils.create_gif(images), media_type="image/gif")



@app.get("/solar-monitor/{initial_date}/{number_of_days}")
def get_solar_monitor_info(
        initial_date: str,
        number_of_days: int,
        sunspot_numbers: List[str] = Query(None),
        do_adjustment: bool = Query(True)
):
    days_arr = utils.get_days_arr(initial_date, number_of_days)
    final_date = days_arr[-1]

    solar_monitor_info = utils.get_solar_monitor_info(days_arr)
    table_contents_aux = utils.convert_table_contents_to_json(solar_monitor_info)
    
    result = []

    utils.process_positions(table_contents_aux, result, days_arr)

    if sunspot_numbers is not None:
        result = utils.get_by_noaa_number(result, sunspot_numbers)

    img_bytes = io.BytesIO()
    
    initial_date = str(initial_date).replace("00:00:00", "")
    final_date = str(final_date).replace("00:00:00", "")
    
    graphic_utils.create_graphic(result, img_bytes, initial_date, final_date, do_adjustment)

    img_bytes.seek(0)
    return StreamingResponse(img_bytes, media_type="image/png")

@app.get("/solar-monitor/{initial_date}/{number_of_days}/zip")
def get_solar_monitor_info(
        initial_date: str,
        number_of_days: int,
        sunspot_numbers: List[str] = Query(None, description="Sunspot number")
):
    days_arr = utils.get_days_arr(initial_date, number_of_days)

    table_contents = utils.get_solar_monitor_info(days_arr)

    table_contents_aux = utils.convert_table_contents_to_json(table_contents)
    result = []

    utils.process_positions(table_contents_aux, result, days_arr)

    if sunspot_numbers is not None:
        result = utils.get_by_noaa_number(result, sunspot_numbers)

    # Use ThreadPoolExecutor to download and preprocess images concurrently
    with ThreadPoolExecutor() as executor:
        download_and_preprocess_partial = functools.partial(download_and_preprocess_image)
        images = list(executor.map(download_and_preprocess_partial, days_arr))

    gif_bytes = io.BytesIO()
    imageio.mimsave(gif_bytes, images, format='gif', fps=1, loop=0)
    gif_bytes.seek(0)

    zip_buffer = io.BytesIO()

    # Create a ZipFile object to write to the buffer
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        # Create a CSV file in memory
        csv_buffer = io.StringIO()
        utils.convert_to_csv(result, csv_buffer)


        # Add the CSV file to the zip archive
        zip_file.writestr('data.csv', csv_buffer.getvalue())

        # Add the GIF file to the zip archive
        zip_file.writestr('days.gif', gif_bytes.read())

    # Seek to the beginning of the buffer
    zip_buffer.seek(0)

    # Set the response headers for the zip file
    headers = {
        "Content-Disposition": "attachment; filename=result.zip",
        "Content-Type": "application/zip",
    }

    # Return the zip file as a response
    return Response(content=zip_buffer.getvalue(), headers=headers)