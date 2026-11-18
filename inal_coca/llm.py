"""Capa de proveedores de IA. Hoy: Groq. Para sumar Anthropic se agrega otra clase y se registra en PROVEEDORES."""
import base64
import json
import re
import time

import requests


class LLMError(Exception):
    pass


def _parse_json(texto: str) -> dict:
    texto = (texto or "").strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.M).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", texto, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    raise LLMError(f"La IA no devolvió un JSON válido: {texto[:200]}")


class Proveedor:
    nombre = "base"

    def extraer_json(self, instrucciones: str, contenido: str = "", imagenes: list | None = None) -> dict:
        """Devuelve un dict. `imagenes` = lista de bytes JPEG (documentos escaneados)."""
        raise NotImplementedError


class Groq(Proveedor):
    nombre = "groq"
    URL = "https://api.groq.com/openai/v1/chat/completions"
    MODELO_TEXTO = "llama-3.3-70b-versatile"
    MODELO_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"

    def __init__(self, api_key: str):
        if not api_key:
            raise LLMError("Falta GROQ_API_KEY")
        self.api_key = api_key

    def _post(self, payload: dict) -> requests.Response:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        for intento in range(4):
            r = requests.post(self.URL, json=payload, headers=headers, timeout=90)
            if r.status_code in (429, 500, 502, 503) and intento < 3:
                espera = min(float(r.headers.get("retry-after", 2 ** (intento + 1))), 25)
                time.sleep(espera)
                continue
            return r
        return r

    def extraer_json(self, instrucciones, contenido="", imagenes=None):
        if imagenes:
            modelo = self.MODELO_VISION
            partes = [{"type": "text", "text": instrucciones}]
            for img in imagenes:
                b64 = base64.b64encode(img).decode()
                partes.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
            mensajes = [{"role": "user", "content": partes}]
        else:
            modelo = self.MODELO_TEXTO
            mensajes = [
                {"role": "system", "content": "Respondés únicamente con un objeto JSON válido, sin texto adicional."},
                {"role": "user", "content": f"{instrucciones}\n\n=== DOCUMENTO ===\n{contenido}"},
            ]
        payload = {"model": modelo, "messages": mensajes, "temperature": 0, "max_tokens": 1500,
                   "response_format": {"type": "json_object"}}
        r = self._post(payload)
        if r.status_code == 400:  # algunos modelos no aceptan json_object: se reintenta sin eso
            payload.pop("response_format")
            r = self._post(payload)
        if r.status_code != 200:
            raise LLMError(f"Groq {r.status_code}: {r.text[:300]}")
        return _parse_json(r.json()["choices"][0]["message"]["content"])


PROVEEDORES = {"groq": Groq}


def get_proveedor(nombre: str, api_key: str) -> Proveedor:
    return PROVEEDORES[nombre](api_key)
