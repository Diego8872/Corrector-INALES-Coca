"""Lectura de PDFs: texto cuando hay, imágenes cuando el PDF es un escaneo (sin PyMuPDF/OCR externo)."""
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

MAX_CHARS = 14000        # tope de texto enviado al modelo por documento
MAX_PAGINAS_IMG = 4      # tope de páginas escaneadas enviadas como imagen
_MIN_CHARS_TEXTO = 60    # menos que esto en todo el PDF => se trata como escaneo
_RUIDO_COPIA = re.compile(r"\b(original|copia|copy|duplicado|triplicado|cedible|cliente)\b", re.I)


@dataclass
class Doc:
    pages: list = field(default_factory=list)   # texto por página
    scanned: bool = False
    images: list = field(default_factory=list)  # JPEG por página (solo si scanned)

    @property
    def text(self) -> str:
        return "\n\n".join(self.pages)

    @property
    def metodo(self) -> str:
        return "visión (escaneado)" if self.scanned else "texto"


def _limpiar(t: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", t)).strip()


def _sin_copias(pages: list) -> list:
    """Quita páginas que son copias de otra (ORIGINAL / COPIA CEDIBLE...), muy común en facturas."""
    vistos, out = set(), []
    for p in pages:
        clave = re.sub(r"\s+", " ", _RUIDO_COPIA.sub("", p.lower())).strip()
        if clave and clave not in vistos:
            vistos.add(clave)
            out.append(p)
    return out


_LEGAL = re.compile(r"(?i)general\s+terms\s+and\s+conditions|terms\s+and\s+conditions\s+of\s+(sale|supply)|condiciones\s+generales\s+de\s+(venta|suministro)")


def _sin_legales(pages: list) -> list:
    """Quita las páginas de condiciones generales (varias miles de caracteres sin datos), salvo que sean las únicas."""
    utiles = [p for p in pages if not _LEGAL.search(p[:300])]
    return utiles or pages


def read_pdf(data: bytes) -> Doc:
    pdf = fitz.open(stream=data, filetype="pdf")
    pages = [_limpiar(p.get_text("text")) for p in pdf]
    if sum(len(p) for p in pages) >= _MIN_CHARS_TEXTO:
        return Doc(pages=_sin_copias(_sin_legales(pages)))
    # escaneo: se renderizan las páginas para que las lea el modelo de visión
    imgs = []
    for p in list(pdf)[:MAX_PAGINAS_IMG]:
        pix = p.get_pixmap(matrix=fitz.Matrix(2, 2))
        imgs.append(pix.tobytes("jpeg"))
    return Doc(pages=[], scanned=True, images=imgs)
