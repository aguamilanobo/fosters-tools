# Fosters Dispatch (v0.1, modo seguro)

Módulo FastAPI `dispatch.py` montado desde `main.py`.

## Estado
- Recibe imágenes en un bot Telegram independiente.
- Deduplicación SHA-256.
- Guarda imágenes y metadatos en SQLite.
- Extracción por visión opcional (OpenAI API).
- Bandeja Telegram Mini App en `/dispatch`.
- Revisión manual del destinatario + referencia de pedido.
- Endpoint de vista previa protegida y búsqueda orientativa sobre contactos importados.
- **NO envía WhatsApps. No hace matching real contra Pancake todavía.**
- No hay QR.

## Requisitos Render
Añadir variables de entorno (**no copiar secretos a GitHub**):
- `DISPATCH_TELEGRAM_BOT_TOKEN` nuevo token de bot de BotFather.
- `DISPATCH_TELEGRAM_WEBHOOK_SECRET` cadena aleatoria de caracteres válidos Telegram (A-Z, a-z, 0-9, _, -).
- `DISPATCH_ALLOWED_USER_IDS` IDs numéricos autorizados, separados con coma.
- `DISPATCH_TELEGRAM_CHAT_ID` opcional: grupo destino, recomendado restringirlo a un grupo operativo.
- `DISPATCH_ADMIN_KEY` token secreto largo distinto de los anteriores.
- `OPENAI_API_KEY` para reconocimiento de imágenes.
- `DISPATCH_VISION_MODEL` opcional, default `gpt-4.1-mini`.
- `DISPATCH_DATA_DIR` ruta persistente, por ejemplo `/var/data/fosters-dispatch`, con disco persistente Render configurado.

**IMPORTANTE:** la ruta predeterminada actual es `/tmp/fosters-dispatch`: en Render se pierde al reiniciar/desplegar. **No usar tickets reales sin disco persistente o almacenamiento externo.** Si Render free no admite disco persistente, mover almacenamiento a Postgres + object storage antes de producción.

## Activar webhook
Una vez que Render esté Live, realizar POST autenticado:

`POST https://fosters-tools.onrender.com/dispatch/admin/setup`

Header `X-Dispatch-Admin-Key: <DISPATCH_ADMIN_KEY>`, body `{}`.

Configurará webhook en Telegram del bot nuevo, usando la secret header definida.

## API de revisión
- `POST /dispatch/api/list`
- `POST /dispatch/api/image/{id}`
- `POST /dispatch/api/suggestions/{id}`
- `POST /dispatch/api/review/{id}`
- `POST /dispatch/api/send/{id}` -> HTTP 501, por seguridad.
- `POST /dispatch/admin/import-contacts` permite cargar contactos en JSON, protegido por clave; por ahora no hay sync Pancake.
- `GET /dispatch` dashboard Mini App dentro de Telegram.

Los endpoints de revisión aceptan `X-Telegram-Init-Data` válido y usuario en `DISPATCH_ALLOWED_USER_IDS` o `X-Dispatch-Admin-Key`; el dashboard solo usa sesión Telegram.

## Pendiente para producción
- Autenticación real / documentación de API de Pancake para consultar clientes, pedidos y enviar imágenes mediante WhatsApp autorizado.
- Configurar un bot dedicado y sus secretos.
- Almacenamiento persistente seguro.
- Verificar extracción con tickets de varios transportes, manejo de nombre remitente/destinatario, privacidad y consistencia.
- Implementar cola de envíos con idempotencia y comprobantes, aprobación humana y registro delivery.
- Configurar el botón Mini App en BotFather con `https://fosters-tools.onrender.com/dispatch` (HTTPS).


## Actualización operativa 2026-10-09
Se añadió `dispatch_ops.py` a main, con rutas autenticadas:
- POST `/dispatch/ops/lookup/{id}`: toma el teléfono del ticket, normaliza a dígitos, consulta historial mediante PSID `wa_...` (solo lectura). **Un historial existente no verifica nombre ni pedido.**
- POST `/dispatch/ops/confirm/{id}`: exige teléfono, nombre y referencia de pedido, consulta que Botcake acepte PSID, guarda aprobación/auditoría sin enviar.
- POST `/dispatch/ops/retry-vision/{id}`: nueva extracción con IA para fotos existentes, excepto tickets aprobados o procesándose.
- POST `/dispatch/ops/health`: muestra ruta y avisa si es almacenamiento temporal.
- POST `/dispatch/ops/audit/{id}`: historial de acciones.
- POST `/dispatch/ops/summary`: resumen limitado a 100 tickets.
Panel Telegram incorpora ver foto, buscar Botcake, confirmar, reintentar IA y estado.

**NO habilitar envíos de WhatsApp aún.** `/dispatch/api/send/{id}` sigue devolviendo HTTP 501. Falta confirmar payload multimedia Botcake, ventana WhatsApp, pruebas de extremo a extremo y durabilidad del almacenamiento. Mover fotos a almacenamiento persistente privado con estrategia de backups y retención antes de producción. No guardar secretos en git.

## Prueba de envío multimedia Botcake (2026-10)
El envío de prueba usa `POST /api/public_api/v1/pages/{page_id}/flows/send_content` con mensaje `image` y URL HTTPS de una imagen genérica. **No manda ningún ticket ni datos de clientes**.

Configurar `DISPATCH_TEST_WHATSAPP` en Render: **solo el número personal autorizado** con código país, dígitos únicamente (no el número de empresa). No se necesita enviar ese número por el chat.

La imagen es un patrón público sin información sensible en `/dispatch/test-image.png`. Opcionalmente `DISPATCH_TEST_IMAGE_URL` permite sustituirla por otra URL de PNG/JPG pública sin parámetros.

En la Mini App se hace `Preparar envío de prueba` y luego `CONFIRMAR Y ENVIAR UNA IMAGEN DE PRUEBA`. El servidor restringe el destinatario al número configurado, la aprobación dura 5 minutos y solo permite un intento por aprobación. La aprobación y resultado se registran en la base de datos persistente.

**Precaución:** respuesta `success: true` solo significa que Botcake aceptó la solicitud; debe comprobarse la recepción real en WhatsApp. Si hay timeout o error ambiguo NO repetir antes de verificar recepción. Hay que verificar ventana de atención WhatsApp y restricciones de plantillas. No hay envíos de tickets ni por lotes habilitados.

La verificación previa del cliente con historial no confirma identidad ni titularidad del número. El operador debe confirmar que el número de prueba le pertenece y asumir el envío con consentimiento explícito.
