from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, Response
import image_utils
import graphic_utils
import utils
import io
import zipfile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Solaire",
    description="API for Solar Monitor info",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "arthur.proenca@sou.unifal-mg.edu.br"
    },
    license_info={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/api/v1/solar-monitor/jpeg",
    summary="Retrieve a JPEG image from the solar monitor by date",
    description=(
        "Fetch a JPEG image from the solar monitor for a specific date. "
        "The `download` flag allows the image to be downloaded, and the "
        "`pre_process` flag applies preprocessing to the image if set to True."
    ),
)
def get_solar_monitor_jpeg_from_date(
    date: Optional[str] = Query(
        None, 
        description="Date for which the JPEG is to be fetched, in YYYY-MM-DD format."
    ),
    download: bool = Query(
        False, 
        description="Set to True to download the image instead of displaying it in the browser."
    ),
    pre_process: bool = Query(
        False, 
        description="Set to True to apply preprocessing to the image before returning it."
    )
):
    # Get the date array
    days_arr = utils.get_days_arr(date, 0)

    # Retrieve and process images
    _, images = get_content(days_arr[0], pre_process)
    image_bytes = image_utils.create_image([images])

    # Return the image, with download option if selected
    if download:
        response = StreamingResponse(image_bytes, media_type="image/jpeg")
        filename = f"solar_monitor_{date}.jpeg"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return StreamingResponse(image_bytes, media_type="image/jpeg")


@app.get(
    "/api/v1/solar-monitor/sunspots/gif",
    summary="Retrieve a GIF of solar sunspots for a specified date",
    description=(
        "Fetch a GIF image representing solar sunspots information for a given date. "
        "You can specify sunspots to highlight, request to download the GIF, or apply OCR "
        "to extract text data from the image."
    ),
)
def get_solar_monitor_spot_info(
    date: Optional[str] = Query(
        None,
        description="Date for which the sunspots GIF is to be fetched, in YYYY-MM-DD format."
    ),
    sunspots: Optional[List[str]] = Query(
        None,
        description="List of specific NOAA IDs to highlight in the GIF."
    ),
    download: bool = Query(
        False,
        description="Set to True to download the GIF instead of displaying it in the browser."
    ),
    ocr: bool = Query(
        False,
        description="Set to True to perform OCR on the GIF to highlight text data from the image."
    )
):
    initial_date, final_date, full_content = utils.sunspot_backtracking(
        date, sunspots)

    days_arr = list(full_content.keys())
    days_arr.reverse()

    gif_bytes = get_images_to_gif(initial_date, utils.how_many_days_between(
        initial_date, final_date), sunspots, True, ocr)

    if download:
        response = StreamingResponse(gif_bytes, media_type="image/gif")
        response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.gif"'
        return response
    else:
        return StreamingResponse(gif_bytes, media_type="image/gif")


@app.get(
    "/api/v1/solar-monitor/sunspots-amount",
    summary="Retrieve the amount of solar sunspots within a date range",
    description=(
        "Fetch the count of solar sunspots observed within a specified date range. "
        "You can choose to group the data monthly or yearly using the `search_type` parameter."
    ),
)
def get_solar_monitor_sunspots_amount(
    search_type: str = Query(
        "MONTHLY", 
        description="Specify the aggregation type for sunspot count. Options: 'MONTHLY' or 'YEARLY'.",
        regex="^(MONTHLY|YEARLY)$"
    ),
    initial_date: Optional[str] = Query(
        None,
        description="The start date for the data search range, in YYYY-MM-DD format."
    ),
    final_date: Optional[str] = Query(
        None,
        description="The end date for the data search range, in YYYY-MM-DD format."
    )
):
    full_content = {}
    count = 0
    dates = utils.get_days_arr_between_dates(initial_date, final_date, search_type)
    for date in dates:
        full_content[count], _ = utils.cache_and_get_solar_monitor_info_from_day(
            date, data_only=True)
        count += 1

    full_content = utils.data_equalizer(full_content)
    img_bytes = io.BytesIO()
    graphic_utils.create_sunspots_amount_graphic(full_content, img_bytes, initial_date, final_date, search_type)
    full_content = {}
    img_bytes.seek(0)
    return StreamingResponse(img_bytes, media_type="image/jpeg")


@app.get(
    "/api/v1/solar-monitor/sunspots",
    summary="Analyze solar sunspots for a specified date",
    description=(
        "Retrieve and analyze solar sunspots data for a given date. "
        "You can specify sunspot IDs to focus on, apply a linear adjustment "
        "to the data points, and download the result as a file if desired."
    ),
)
def get_solar_monitor_spot_info(
    date: Optional[str] = Query(
        None,
        description="The date for which sunspot analysis is requested, in YYYY-MM-DD format."
    ),
    sunspots: Optional[List[str]] = Query(
        None,
        description="List of specific sunspot IDs to include in the analysis."
    ),
    linear_adjustment: bool = Query(
        True,
        description="Set to True to apply linear adjustment to the sunspot data points in the generated graph."
    ),
    download: bool = Query(
        False,
        description="Set to True to download the analysis result instead of displaying it in the browser."
    ),
    fourier: bool = Query(
        False,
        description="Set to True to generate a Fourier analysis graph of the sunspot data."
    )
):
    initial_date, final_date, full_content = utils.sunspot_backtracking(
        date, sunspots)

    days_arr = list(full_content.keys())
    days_arr.reverse()

    full_content = utils.data_equalizer(full_content)

    img_bytes = io.BytesIO()

    if fourier:
        graphic_utils.create_fourier_graphic(full_content, img_bytes, initial_date, final_date)
    else:
        graphic_utils.create_graphic(full_content, img_bytes, initial_date, final_date, linear_adjustment)

    img_bytes.seek(0)

    if download:
        response = StreamingResponse(img_bytes, media_type="image/jpeg")
        response.headers["Content-Disposition"] = 'attachment; filename="solar_monitor.jpeg"'
        return response

    return StreamingResponse(img_bytes, media_type="image/jpeg")


@app.get("/api/v1/solar-monitor/sunspots/zip", include_in_schema=True)
def get_raw_content(date: str = Query(None), sunspots: List[str] = Query(None)):
    initial_date, final_date, full_content = utils.sunspot_backtracking(
        date, sunspots)

    days_arr = list(full_content.keys())
    days_arr.reverse()

    full_content = utils.data_equalizer(full_content)

    gif_bytes = get_images_to_gif(initial_date, utils.how_many_days_between(
        initial_date, final_date), sunspots, True)

    table_bytes = io.BytesIO()
    csv_bytes = io.BytesIO()
    img_bytes = io.BytesIO()
    fourier_bytes = io.BytesIO()

    graphic_utils.create_fourier_graphic(
        full_content, fourier_bytes, initial_date, final_date)

    graphic_utils.create_graphic(
        full_content, img_bytes, initial_date, final_date, False)

    img_bytes.seek(0)
    utils.create_text_table(full_content, table_bytes)
    utils.create_csv(full_content, csv_bytes)

    # Create a ZIP file to store the bytes
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('gif.gif', gif_bytes.getvalue())
        zip_file.writestr('tabela.txt', table_bytes.getvalue())
        zip_file.writestr('planilha.csv', csv_bytes.getvalue())
        zip_file.writestr('grafico.png', img_bytes.getvalue())
        zip_file.writestr('fourier.png', fourier_bytes.getvalue())

    # Configure the response for the ZIP file
    response = Response(zip_buffer.getvalue(), media_type='application/zip')
    response.headers["Content-Disposition"] = 'attachment; filename="analise.zip"'

    return response


def get_content(day, pre_process):
    content, images = utils.cache_and_get_solar_monitor_info_from_day(day)
    image = image_utils.image_decode(images)
    if pre_process:
        day = graphic_utils.date_format(day, "%d de %b. de %Y")
        return content, image_utils.preprocess_image(image, day)
    return content, image


def get_images_to_gif(initial_date, number_of_days, sunspot, pre_process, ocr = False):
    days_arr = utils.get_days_arr(initial_date, number_of_days)
    images = []

    for day in days_arr:
        _, image = get_content(day, pre_process)
        images.append(image)
    if ocr:
        images = image_utils.highlight_text_in_images(images, sunspot)
    gif_bytes = image_utils.create_gif(images)
    return gif_bytes
