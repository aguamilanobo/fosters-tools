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
