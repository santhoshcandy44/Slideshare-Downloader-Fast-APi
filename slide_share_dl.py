import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PIL import Image
import requests
from io import BytesIO

from exceptions import CustomAPIException
import httpx
import asyncio



def validate_url(url):
    domain = urlparse(url).netloc
    if domain != "www.slideshare.net":
        raise CustomAPIException(status_code=400, detail="Invalid SlideShare URL.")
    return True


def fetch_slide_images_all_resolutions(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise CustomAPIException(status_code=500, detail="Failed to fetch the presentation page.")

    soup = BeautifulSoup(response.text, "html.parser")
    image_tags = soup.find_all("img", {"data-testid": "vertical-slide-image"})

    if not image_tags:
        raise CustomAPIException(status_code=404, detail="No slide images found.")

    all_slide_images = []
    for tag in image_tags:
        srcset = tag.get("srcset")
        if not srcset:
            continue

        slide_resolutions = {}
        sources = [s.strip().split(" ") for s in srcset.split(",")]

        for src in sources:
            if len(src) == 2:
                url_part, res = src
                if res.endswith("w"):
                    resolution = int(res[:-1])
                    slide_resolutions[resolution] = url_part

        if slide_resolutions:
            all_slide_images.append(slide_resolutions)

    return all_slide_images



async def fetch_image(client: httpx.AsyncClient, url: str):
    try:
        response = await client.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return img
    except Exception as e:
        raise CustomAPIException(status_code=500, detail=f"Failed to fetch image: {url}, Error: {str(e)}")

async def convert_urls_to_pdf_async(image_urls, output_pdf="slides.pdf"):
    images = []

    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [fetch_image(client, url) for url in image_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                raise result
            images.append(result)

    if not images:
        raise CustomAPIException(status_code=500, detail="No images to convert to PDF.")

    first_image, *rest = images
    first_image.save(output_pdf, save_all=True, append_images=rest)
    return output_pdf


from pptx import Presentation
from pptx.util import Inches


async def convert_urls_to_pptx_async(image_urls, output_pptx="slides.pptx"):
    prs = Presentation()
    blank_slide_layout = prs.slide_layouts[6]  # No title/content

    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [fetch_image(client, url) for url in image_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                raise result

            img_byte_arr = BytesIO()
            result.convert("RGB").save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)

            slide = prs.slides.add_slide(blank_slide_layout)
            slide.shapes.add_picture(img_byte_arr, Inches(0), Inches(0),
                                     width=prs.slide_width, height=prs.slide_height)

    prs.save(output_pptx)
    return output_pptx


import zipfile


async def convert_urls_to_zip_async(image_urls, output_zip_path="slides.zip"):
    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [fetch_image(client, url) for url in image_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    memory_zip = BytesIO()

    with zipfile.ZipFile(memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                raise result

            img_byte_arr = BytesIO()
            result.convert("RGB").save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            zf.writestr(f"slide_{idx}.jpg", img_byte_arr.read())

    with open(output_zip_path, "wb") as f:
        f.write(memory_zip.getvalue())

    return output_zip_path

from utils import SlidesConversionType

async  def get_slides_pdf_download_link(url: str, conversion_type:SlidesConversionType, quality: int = 2048):
    validate_url(url)

    path_parts = urlparse(url).path.strip("/").split("/")
    if len(path_parts) >= 2:
        doc_short = path_parts[-2]
    else:
        raise CustomAPIException(status_code=400, detail="Invalid SlideShare URL format.")

    date_str = datetime.today().strftime("%d%m%Y")

    output_dir = os.path.join("Slide_DL", date_str)
    output_pdf_path = os.path.join(output_dir, f"{doc_short}.pdf")
    output_pptx_path = os.path.join(output_dir, f"{doc_short}.pptx")
    output_zip_path = os.path.join(output_dir, f"{doc_short}.zip")

    os.makedirs(output_dir, exist_ok=True)

    slide_images = fetch_slide_images_all_resolutions(url)

    high_res_images = [slide[quality] for slide in slide_images if quality in slide]

    if not high_res_images:
        raise CustomAPIException(status_code=404, detail=f"No {quality}px resolution slides found.")


    if conversion_type == SlidesConversionType.pdf:
        path = await convert_urls_to_pdf_async(high_res_images, output_pdf_path)
        message = "PDF generated successfully."
    elif conversion_type == SlidesConversionType.pptx:
        path = await convert_urls_to_pptx_async(high_res_images, output_pptx_path)
        message = "PPTX generated successfully."
    elif conversion_type == SlidesConversionType.images_zip:
        path = await convert_urls_to_zip_async(high_res_images, output_zip_path)
        message = "IMAGES ZIP generated successfully."
    else:
        raise CustomAPIException(status_code=400, detail="Unsupported conversion type.")

    return {
        "success": True,
        "message": message,
        "slides_download_link": path,
    }
