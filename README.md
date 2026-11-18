# Corrector INAL Coca

Controla el PD de INAL (**345**, **Autorización**, **Aviso**) contra factura, BL/guía/CRT, COA, packing list y el listado de importación. Devuelve un Excel `Campo / PD / Documento fuente / Resultado` con ✅ / ❌ (con motivo) / ⚠️ (no se pudo verificar).

## Cómo funciona
- **PD y listado de importación**: se leen con código (sin IA).
- **Factura, BL/guía/CRT, COA y packing list**: la IA extrae los datos (Groq, `llama-3.3-70b-versatile`). Si un PDF es un escaneo (sin texto) se lee con visión (`llama-4-scout`).
- **Material del listado**: primero por código (columna A). Si el código de la factura es del proveedor y no está en el listado, se buscan candidatos por posición arancelaria y palabras, y la IA elige entre ellos (el Excel indica que fue "por descripción/arancel").
- **Comparación y Excel**: código determinista.

## Deploy (Streamlit Cloud)
1. Subir el repo a GitHub y crear la app con `app.py`.
2. En *Secrets*: `GROQ_API_KEY = "gsk_..."`
3. No hace falta `packages.txt`.

## Portal Grupo 8
Copiar la carpeta `inal_coca/` a la raíz del Portal y `portal/20_Corrector_INAL_Coca.py` a `pages/` (ajustar el número), y agregar la tarjeta en `projects` de `app.py`.

## Agregar o cambiar un tipo de control
Datos fijos (RNE, domicilio) y campos propios de cada tipo: `inal_coca/config.py`.

## Agregar Anthropic
Crear una clase `Anthropic(Proveedor)` en `inal_coca/llm.py` con el método `extraer_json` y registrarla en `PROVEEDORES`.
