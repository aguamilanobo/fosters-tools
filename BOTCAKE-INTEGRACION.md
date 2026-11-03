# Aplicación de la V8 en Botcake

La V8 de BOTCAKE-INSTRUCCIONES.md reemplaza las instrucciones maestras V7; no agregarla debajo de la V7. Este cambio en Git no modifica el agente remoto. Conservar los adjuntos originales y las acciones, credenciales y asignaciones reales existentes al reemplazar el texto.

## Correspondencia con el backend

| Herramienta Botcake | Ruta de este repositorio |
| --- | --- |
| decide_fosters_next_action | POST /decide-next-action |
| classify_fosters_lead | POST /classify-lead |
| recommend_fosters_size | GET /recommend-size |
| prepare_fosters_order | POST /prepare-order |
| prepare_fosters_shipping | POST /prepare-shipping |
| get_fosters_discount | GET /discount |
| fosters_upsell_offer | POST /fosters/upsell/offer |
| fosters_upsell_decision | POST /fosters/upsell/decision |

Esta tabla describe la correspondencia esperada, no acredita que el agente esté conectado a estas rutas. Preservar la autenticación existente. Consultar /openapi.json desplegado para el esquema exacto.

En decide_fosters_next_action exponer asks_for_store_location y asks_for_photos como booleanos opcionales, false por defecto; conservar el resto de los parámetros. Mapear answer_store_location a mostrar message sin texto adicional. Mapear send_catalog a una acción multimedia real usando product y color. La API no envía adjuntos por sí misma.

En fosters_upsell_offer exponer customer_requested_upsell, booleano false por defecto. Solo activarlo por solicitud explícita. Las llamadas antiguas que envíen solo buying_intent ahora omiten el upsell intencionalmente.

prepare_fosters_order ya no exige nombre para preparar una compra de Santa Cruz. No crea órdenes ni comprueba stock. prepare_fosters_shipping pide destino antes de pedir documentos y no pide CI cuando reconoce Santa Cruz; el cliente debe compartir ciudad/departamento para aplicar esa regla.

marcar_pedido_pagado y cancelar_pedido no están implementadas en este repositorio. Conservar sus conexiones Shopify externas si existen y verificar sus esquemas reales. No apuntarlas a rutas inventadas ni simular confirmaciones. Si no existen, la V8 exige derivar.

## Adjuntos y contradicciones resueltas

- El texto V7 enumera adjuntos de Botcake; eso no permite descargar ni verificar su existencia o sus IDs. No borrar los adjuntos al reemplazar las instrucciones.
- El catálogo API tiene image_urls vacías. Eso no impide usar adjuntos internos de Botcake, pero no demuestra que el flujo de envío esté conectado.
- Asociar las nueve fotos por producto/color según la tabla V8. Conservar los IDs reales. Los nombres truncados de tabla, audio y PDF no son identificadores utilizables; seleccionar sus adjuntos existentes en el editor.
- Se eliminan repeticiones de “SIEMPRE”: fotos una vez al abrir el producto; tabla al necesitarla; audio y PDF opcionales. Solicitudes explícitas permiten reenviar.
- Shorts: precio normal confirmado por el negocio 280 Bs, upsell 250 y ahorro 30. Backend y V8 usan esos valores. No cambiar precios Shopify existentes.
- Cantidad de botones: V7 decía cuatro y backend tres. Sin ficha comprobada, ambos quedan como “botones en el pecho”.

## Validación pendiente en el agente real

1. “¿Dónde están?”: solo la respuesta fija, sin apertura ni contactos.
2. “Quiero ver el short perla”: recibir la imagen Short Blanco.jpg como archivo real, identificada como Perla.
3. Elegir Henley, color y talle: avanzar a entrega sin upsell automático; con ubicación SCZ, derivar sin pedir CI o nombre.
4. Pedido web con número, nombre, CI y destino ya incluidos: conservar todo, no reconstruir ni repetir datos.
5. Pago/cancelación web: confirmar únicamente tras resultado explícito de la herramienta real; fallo implica derivación.

La verificación local del backend no sustituye estos casos de Botcake/WhatsApp. Render tampoco actualiza automáticamente las instrucciones ni los adjuntos de Botcake.
