import io, os
import qrcode
from PIL import Image
from app.utils.settings import settings

EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../export"))

def make_qr_png(url: str, save: bool = False, filename: str = "qr.png") -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    if save:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        path = os.path.join(EXPORT_DIR, filename)
        with open(path, "wb") as f:
            f.write(data)

    return data
