
from enum import Enum

class SlidesConversionType(str, Enum):
    pdf = "PDF"
    pptx = "PPTX"
    images_zip = "IMAGES_ZIP"