from typing import List
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import image_utils
import graphic_utils
import utils
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/solar-monitor/jpeg")
def get_solar_monitor_jpeg_from_date(date: str = Query(None),
                                    download: bool = Query(False),
                                    pre_process: bool = Query(False)):

    days_arr = utils.get_days_arr(date, 0)

    _, images = get_content(days_arr[0], pre_process)

    image_bytes = image_utils.create_image([images])

    if download:
        response = StreamingResponse(image_bytes, media_type="image/jpeg")
        filename = f"solar_monitor_{date}.jpeg"
        response.headers["Content-Disposition"] = 'attachment; filename=' + filename
        return response
    else:
        return StreamingResponse(image_bytes, media_type="image/jpeg")


@app.get("/api/v1/solar-monitor/sunspots/gif")
def get_solar_monitor_spot_info(
        date: str = Query(None),
        sunspots: List[str] = Query(None),
        download: bool = Query(False)
):
    initial_date, final_date, full_content = utils.sunspot_backtracking(
        date, sunspots)
    
    days_arr = list(full_content.keys())
    days_arr.reverse()
    
    gif_bytes = get_images_to_gif(initial_date, utils.how_many_days_between(
            initial_date, final_date), sunspots, True)
    
    if download:
        response = StreamingResponse(gif_bytes, media_type="image/gif")
        response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.gif"'
        return response
    else:
        return StreamingResponse(gif_bytes, media_type="image/gif")

@app.get("/api/v1/solar-monitor/sunspots")
def get_solar_monitor_spot_info(
        date: str = Query(None),
        sunspots: List[str] = Query(None),
        linear_adjustment: bool = Query(True),
        download: bool = Query(False)
):
    initial_date, final_date, full_content = utils.sunspot_backtracking(
        date, sunspots)
    
    days_arr = list(full_content.keys())
    days_arr.reverse()

    full_content = utils.data_equalizer(full_content)

    img_bytes = io.BytesIO()

    graphic_utils.create_graphic(
        full_content, img_bytes, initial_date, final_date, linear_adjustment)
    
    img_bytes.seek(0)

    if download:
        response = StreamingResponse(img_bytes, media_type="image/jpeg")
        response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.jpeg"'
        return response

    return StreamingResponse(img_bytes, media_type="image/jpeg")


def get_content(day, pre_process):
    content, images = utils.save_and_get_solar_monitor_info_from_day(day)
    image = image_utils.image_decode(images)
    if pre_process:
        return content, image_utils.preprocess_image(image, day)
    return content, image

def get_images_to_gif(initial_date, number_of_days, sunspot, pre_process):
    days_arr = utils.get_days_arr(initial_date, number_of_days)
    images = []

    for day in days_arr:
        _, image = get_content(day, pre_process)
        images.append(image)
    #images = image_utils.highlight_text_in_images(images, sunspot)
    gif_bytes = image_utils.create_gif(images)
    return gif_bytes