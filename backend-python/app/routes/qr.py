# backend-python/app/routes/qr.py

from fastapi import APIRouter, Response, Query
from app.utils.qrgen import make_qr_png
from app.utils.settings import settings

router = APIRouter()


@router.get("/{product_id}.png", response_class=Response)
def qr_png(
    product_id: str,
    save: int = Query(0, description="Save PNG to /export if save=1"),
):
    # Prefer PUBLIC_VERIFY_BASE_URL (public frontend) over backend_base_url
    public_base = (
        getattr(settings, "public_verify_base_url", None)
        or settings.backend_base_url
    )

    # For public customer verification we deep-link to the frontend root with ?id=
    verify_url = f"{public_base}/?id={product_id}"

    png = make_qr_png(
        url=verify_url,
        save=bool(save),
        filename=f"{product_id}.png",
    )
    return Response(content=png, media_type="image/png")
