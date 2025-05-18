
from enum import Enum

class SlidesConversionType(str, Enum):
    pdf = "PDF"
    pptx = "PPTX"
    images_zip = "IMAGES_ZIP"

class QualityType(str, Enum):
    sd = "SD"
    hd = "HD"