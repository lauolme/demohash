# Pruebas manuales (ejemplos) — test_hash_utils.md

1. Hash de texto:
   - Input: "hola"
   - Algoritmo: sha256
   - Esperado (ejemplo calculado localmente): `2c0e...` (puedes verificar en la app)

2. Salt:
   - Texto: "password"
   - Salt: "a1b2" (hex)
   - Resultado: hash de "a1b2password"

3. HMAC:
   - Texto: "mensaje"
   - Key: "clave" (utf-8)
   - Algoritmo: sha256
   - Ejecuta en la app: debe mostrar un hex de 64 chars.

Nota: estos son ejemplos para verificar manualmente la app desplegada.
