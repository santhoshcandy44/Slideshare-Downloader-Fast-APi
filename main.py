from fastapi import FastAPI,  Request, Query
from fastapi.responses import JSONResponse
from slide_share_dl import get_slides_download_link
from exceptions import CustomAPIException
from utils import SlidesConversionType, QualityType

from ftplib import FTP

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



@app.get("/")
def root():
    # ftp_host = "82.25.120.208"
    # ftp_user = "u979883547.admin"
    # ftp_pass = "a*58cSG%x5Y4*Tn62e&zp7pT"
    # ftp_port = 21  # FTP port
    #
    # ftp = FTP()
    # ftp.set_pasv(False)
    # ftp.connect(host=ftp_host, port=ftp_port)
    # ftp.login(user=ftp_user, passwd=ftp_pass)
    #
    # print("✅ Connected to Hostinger FTP")
    # files = ftp.nlst()
    # print("📄 Files:", files)
    # ftp.quit()
    return {"message": "API entry"}

@app.get("/convert")
async def convert_slideshare_to_pdf(
    url: str = Query(..., description="Slideshare presentation URL"),
   conversion_type: SlidesConversionType = Query(..., description="Conversion type: PDF, PPTX, IMAGES_ZIP"),
    quality: QualityType = Query(QualityType.hd, description="Preferred image resolution")):
    try:
        if not url.strip():
            raise CustomAPIException(status_code=400, detail='Url can\'t be empty')
        return await get_slides_download_link(url = url, conversion_type = conversion_type, quality_type = quality)
    except Exception as e:
        if isinstance(e, CustomAPIException):
            raise  e
        return {"success":False, 'error':True, 'detail': 'Something went wrong' }
