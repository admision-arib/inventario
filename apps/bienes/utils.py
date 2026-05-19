import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
from pathlib import Path


def generar_qr_bien(bien):
    """Genera imagen QR para el bien y la guarda en su campo qr_imagen."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    data = f"{bien.codigo_patrimonial}\n{bien.denominacion[:100]}"
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar en memoria
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    nombre_archivo = f"{bien.codigo_patrimonial}.png"
    bien.qr_imagen.save(nombre_archivo, File(buffer), save=False)
    bien.codigo_qr_generado = True