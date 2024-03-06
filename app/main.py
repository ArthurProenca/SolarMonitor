from typing import List
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import datetime
import image_utils
import graphic_utils
import utils
from concurrent.futures import ThreadPoolExecutor
import functools
from datetime import datetime
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS middleware
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def download_and_preprocess_image(day):
    day = datetime.strptime(day, "%Y-%m-%d")  # Convert day to datetime object
    images = utils.get_solar_monitor_images(day)
    return image_utils.download_and_preprocess_images(images, [day])[0]

@app.get("/solar-monitor/gif")
def get_solar_monitor_gif_from_days(initial_date: str = Query(None),
                                    number_of_days: int = Query(0),
                                    sunspot: List[str] = Query(None),
                                    download: bool = Query(False)):
    days_arr = utils.get_days_arr(initial_date, number_of_days)

    with ThreadPoolExecutor() as executor:
        download_and_preprocess_partial = functools.partial(download_and_preprocess_image)
        images = list(executor.map(download_and_preprocess_partial, days_arr))

    if sunspot is not None:
        images = image_utils.highlight_text_in_images(images, sunspot)
    
    gif_bytes = image_utils.create_gif(images)

    if download:
        response = StreamingResponse(gif_bytes, media_type="image/gif")
        response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.gif"'
        return response
    else:
        return StreamingResponse(gif_bytes, media_type="image/gif")



@app.get("/solar-monitor")
def get_solar_monitor_info(
        initial_date: str = Query(None),
        number_of_days: int = Query(None),
        sunspot: List[str] = Query(None),
        do_adjustment: bool = Query(True)
):
    days_arr = utils.get_days_arr(initial_date, number_of_days)
    final_date = days_arr[-1]

    solar_monitor_info = utils.get_solar_monitor_info(days_arr)
    table_contents_aux = utils.convert_table_contents_to_json(solar_monitor_info)
    
    result = []

    utils.process_positions(table_contents_aux, result, days_arr)

    if sunspot is not None:
        result = utils.get_by_noaa_number(result, sunspot)

    img_bytes = io.BytesIO()
    
    initial_date = str(initial_date).replace("00:00:00", "")
    final_date = str(final_date).replace("00:00:00", "")
    
    graphic_utils.create_graphic(result, img_bytes, initial_date, final_date, do_adjustment)

    img_bytes.seek(0)
    return StreamingResponse(img_bytes, media_type="image/png")