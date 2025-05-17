from fastapi import FastAPI,  Request, Query
from fastapi.responses import JSONResponse
from slide_share_dl import get_slides_pdf_download_link
from CustomAPIException import CustomAPIException
from enum import Enum

app = FastAPI()


@app.exception_handler(CustomAPIException)
async def custom_http_exception_handler(request: Request, exc: CustomAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": True,
            "detail": exc.detail
        }
    )

class ConversionType(str, Enum):
    pdf = "PDF"
    pptx = "PPTX"
    images_zip = "IMAGES_ZIP"

@app.get("/")
def root():
    return {"message": "API entry"}

@app.get("/convert")
async def convert_slideshare_to_pdf(
    url: str = Query(..., description="Slideshare presentation URL"),
    resolution: int = Query(2048, description="Preferred image resolution"),
    conversion_type: ConversionType = Query(..., description="Conversion type: PDF, PPTX, IMAGES_ZIP")

):
    try:
        if not url.strip():
            raise CustomAPIException(status_code=400, detail='Url can\'t be empty')
        return await get_slides_pdf_download_link(url = url, quality = resolution)
    except Exception as e:
        if isinstance(e, CustomAPIException):
            raise  e
        return {"success":False, 'error':True, 'detail': 'Something went wrong' }
