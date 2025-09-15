"""
app.py

Streamlit app principal: UI para hashing de texto y archivos, salt, pepper (st.secrets), HMAC.
Comentarios cortos explican cada bloque.
"""

import streamlit as st
import io
import csv
import base64
from typing import Optional

from hash_utils import (
    hash_text,
    hash_file_chunked,
    with_salt,
    with_pepper,
    hmac_text,
    compare_hashes,
    DEFAULT_ALG,
    CHUNK_SIZE,
)

# --- Configuración de la app ---
st.set_page_config(page_title="Hash Demo", layout="centered", page_icon="🔐")
st.title("🔐 Demo Interactiva de Hashing (SHA / BLAKE2)")

# Información sobre secrets
st.sidebar.header("Secrets (pepper / HMAC_KEY)")
st.sidebar.markdown(
    "- En Streamlit Cloud: `Manage app` → `Secrets`.\n"
    "- Añade `PEPPER` y `HMAC_KEY` (puede ser texto o base64)."
)
st.sidebar.markdown("Si no pones secrets, la app permite usar valores temporales para demo.")

# Obtener secrets (seguro si está en Cloud)
pepper_secret = st.secrets.get("PEPPER") if "PEPPER" in st.secrets else None
hmac_key_secret = st.secrets.get("HMAC_KEY") if "HMAC_KEY" in st.secrets else None

# Si no existen, ofrecer inputs temporales (solo para demo; no guardar)
with st.expander("Pepper / HMAC (demostración)"):
    if pepper_secret is None:
        pepper_demo = st.text_input("Pepper temporal (demo)", value="", type="password",
                                   help="Si no usas secrets, puedes poner aquí un pepper temporal (NO seguro).")
    else:
        st.write("Pepper cargado desde `st.secrets` (oculto).")
        pepper_demo = None

    if hmac_key_secret is None:
        hmac_key_demo = st.text_input("HMAC key temporal (demo)", value="", type="password",
                                     help="Clave HMAC temporal para pruebas.")
    else:
        st.write("HMAC key cargada desde `st.secrets` (oculta).")
        hmac_key_demo = None

# Uso efectivo
pepper_value = pepper_secret if pepper_secret is not None else (pepper_demo or None)
hmac_key_value = hmac_key_secret if hmac_key_secret is not None else (hmac_key_demo or None)
if hmac_key_value is not None:
    # permitir clave en bytes; si el user pegó base64, intentar decodificar
    try:
        # aceptar base64 opcionalmente
        hmac_key_bytes = base64.b64decode(hmac_key_value)
    except Exception:
        hmac_key_bytes = hmac_key_value.encode("utf-8")
else:
    hmac_key_bytes = None

# Selección de algoritmo
algorithms = ["sha256", "sha1", "sha512", "blake2b"]
alg = st.selectbox("Algoritmo", algorithms, index=algorithms.index("sha256"))

st.markdown("---")
st.header("1) Hash de texto")
text_input = st.text_area("Texto a hashear", height=120, placeholder="Escribe algo...")
col1, col2 = st.columns([1,1])
with col1:
    if st.button("Calcular hash (texto)"):
        if not text_input:
            st.warning("Introduce texto primero.")
        else:
            h = hash_text(text_input, algorithm=alg)
            st.code(h, language="text")
            st.write("Longitud (hex):", len(h))
with col2:
    if st.button("Copiar hash al portapapeles (usa navegador)"):
        st.write("Selecciona y copia manualmente el hash mostrado arriba.")

st.markdown("---")
st.header("2) Hash de archivo (chunked)")
uploaded = st.file_uploader("Sube un archivo (máx. ~10 MB por defecto)", type=None)
max_size_bytes = 10 * 1024 * 1024
if uploaded is not None:
    size = uploaded.size
    st.write(f"Tamaño: {size} bytes")
    if size > max_size_bytes:
        st.error(f"Archivo muy grande (> {max_size_bytes} bytes). Ajusta límite en el código si lo necesitas.")
    else:
        if st.button("Calcular hash (archivo)"):
            with st.spinner("Calculando..."):
                # Streamlit proporciona BytesIO
                digest = hash_file_chunked(uploaded, algorithm=alg, chunk_size=CHUNK_SIZE)
                st.code(digest)
                # Botón para descargar resultado CSV
                csv_str = "filename,algorithm,hash\n"
                csv_str += f"{uploaded.name},{alg},{digest}\n"
                st.download_button("Descargar resultado (CSV)", csv_str, file_name="hash_result.csv", mime="text/csv")

st.markdown("---")
st.header("3) Salting")
salt_col1, salt_col2 = st.columns(2)
with salt_col1:
    salt_len = st.number_input("Salt bytes (n)", min_value=4, max_value=64, value=16, step=1)
with salt_col2:
    salt_text = st.text_input("Salt hexadecimal (opcional)", value="")
if st.button("Aplicar salt al texto"):
    if not text_input:
        st.warning("Introduce texto antes.")
    else:
        salt = salt_text if salt_text else None
        salt_hex, salted_hash = with_salt(text_input, salt_hex=salt, algorithm=alg)
        st.write("Salt (hex):", salt_hex)
        st.code(salted_hash)

st.markdown("---")
st.header("4) Pepper (secreto desde st.secrets)")
st.write("Pepper no debe estar en el repo. Debe ponerse en `st.secrets` en Streamlit Cloud.")
if st.button("Aplicar pepper al texto"):
    if not text_input:
        st.warning("Introduce texto antes.")
    elif pepper_value is None:
        st.error("Pepper no proporcionado. Pon `PEPPER` en st.secrets o usa el campo demo en la sidebar.")
    else:
        ph = with_pepper(text_input, pepper_value, algorithm=alg)
        st.code(ph)

st.markdown("---")
st.header("5) HMAC (clave en st.secrets)")
st.write("HMAC garantiza integridad y autenticidad si la clave es secreta.")
if st.button("Calcular HMAC (texto)"):
    if not text_input:
        st.warning("Introduce texto antes.")
    elif hmac_key_bytes is None:
        st.error("Clave HMAC no proporcionada. Pon `HMAC_KEY` en st.secrets o usa el campo demo.")
    else:
        hm = hmac_text(text_input, key=hmac_key_bytes, algorithm=alg)
        st.code(hm)

st.markdown("---")
st.header("6) Comparar hashes / Verificar integridad")
col_a, col_b = st.columns(2)
with col_a:
    h1 = st.text_area("Hash 1", height=80)
with col_b:
    h2 = st.text_area("Hash 2", height=80)
if st.button("Comparar"):
    if not h1 or not h2:
        st.warning("Introduce ambos hashes.")
    else:
        match = compare_hashes(h1.strip(), h2.strip())
        if match:
            st.success("✅ Hashes coinciden")
        else:
            st.error("❌ Hashes diferentes")

st.markdown("---")
st.header("Exportar/Guardar resultados")
st.write("Puedes generar un CSV simple con resultados (nombre, algoritmo, hash).")
# Ejemplo: crear CSV manual
if st.button("Generar CSV de ejemplo"):
    csv_content = "name,algorithm,hash\nexample.txt,sha256,abcd1234...\n"
    st.download_button("Descargar CSV de ejemplo", csv_content, file_name="hashes.csv", mime="text/csv")

st.markdown("---")
st.subheader("Limitaciones y buenas prácticas (resumen)")
st.markdown(
    "- Hash ≠ cifrado. Los hashes son irreversibles en diseño.\n"
    "- Salt: único por valor; no secreto. Pepper: secreto global -> st.secrets.\n"
    "- No reutilizar claves/peppers entre entornos.\n"
    "- Para contraseñas considerar PBKDF2/Argon2 (no cubierto aquí).\n"
    "- SHA-1: no usar en producción (colisiones conocidas)."
)
st.caption("App didáctica — no para gestionar secretos en producción sin controles adicionales.")
