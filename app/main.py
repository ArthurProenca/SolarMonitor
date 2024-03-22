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

@app.get("/solar-monitor/jpeg")
def get_solar_monitor_gif_from_days(date: str = Query(None),
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


@app.get("/solar-monitor/gif")
def get_solar_monitor_gif_from_days(initial_date: str = Query(None),
                                    number_of_days: int = Query(0),
                                    sunspot: List[str] = Query(None),
                                    download: bool = Query(False),
                                    pre_process: bool = Query(False)):
    gif_bytes = get_images_to_gif(
        initial_date, number_of_days, sunspot, pre_process)

    if download:
        response = StreamingResponse(gif_bytes, media_type="image/gif")
        response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.gif"'
        return response
    else:
        return StreamingResponse(gif_bytes, media_type="image/gif")


@app.get("/solar-monitor/spot")
def get_solar_monitor_spot_info(
        date: str = Query(None),
        sunspots: List[str] = Query(None),
        do_adjustment: bool = Query(True),
        make_gif: bool = Query(False),
        pre_process: bool = Query(False),
        download: bool = Query(False)
):
    initial_date, final_date, full_content = utils.sunspot_backtracking(
        date, sunspots)
    
    days_arr = list(full_content.keys())
    days_arr.reverse()

    full_content = utils.data_equalizer(full_content)

    img_bytes = io.BytesIO()
    
    if make_gif:
        gif_bytes = get_images_to_gif(initial_date, utils.how_many_days_between(
            initial_date, final_date), sunspots, pre_process)
        if download:
            response = StreamingResponse(gif_bytes, media_type="image/gif")
            response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.gif"'
            return response
        else:
            return StreamingResponse(gif_bytes, media_type="image/gif")

    graphic_utils.create_graphic(
        full_content, img_bytes, initial_date, final_date, do_adjustment)

    img_bytes.seek(0)
    return StreamingResponse(img_bytes, media_type="image/png")


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

    gif_bytes = image_utils.create_gif(images)
    return gif_bytes