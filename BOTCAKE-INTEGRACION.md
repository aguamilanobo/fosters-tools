# FOSTERS — integración actual: solo Henley

El backend FOSTERS publica exclusivamente Henley a 300 Bs, en Negro, Blanco, Azul, Celeste y Beige, talles M, L y XL.

## Catálogo y funciones retiradas

- /fosters/products, /fosters/product, /catalog y /products solo publican Henley.
- Las consultas explícitas por productos retirados devuelven found=false y send_product_photos=false. No se convierten silenciosamente a Henley.
- El módulo de ofertas adicionales y su manifiesto de fotos fueron eliminados.
- Las antiguas rutas /fosters/upsell/* devuelven HTTP 410, sin precios, artículos ni ofertas, con should_offer=false, accepted=false y send_product_photos=false. No se publican en OpenAPI.
- En Botcake retirar las herramientas fosters_upsell_offer y fosters_upsell_decision, sus automatizaciones y los adjuntos de productos retirados. Un despliegue de Render no borra la configuración propia de Botcake.
- La preparación de órdenes no acepta productos retirados ni mezclas que los incluyan. Tampoco se genera resumen de pago o impresión de esos productos.

## Apertura y fotos Henley

GET /fosters/campaign-reply devuelve la apertura Henley y el plan de cinco imágenes originales. POST /decide-next-action admite:

- is_opening=true para una apertura comercial real.
- opening_sent=true si esa apertura ya se completó; no repetirla automáticamente. Guardar este estado con los mecanismos existentes de Botcake, solo tras completar la apertura y sus medios. No marcarla enviada si fallan los adjuntos.
- asks_for_photos=true o asks_for_catalog=true para una solicitud explícita, aunque la apertura ya se haya enviado.
- color opcional: limita los adjuntos al color solicitado y admite aliases navy/Azul marino, crema, negra y blanca.

Una apertura general devuelve next_action=send_catalog, send_product_photos=true, photo_count=5 y photo_attachments con estos pares:

| Color API | Adjunto original Botcake |
| --- | --- |
| Negro | negra.png |
| Blanco | blanca.png |
| Azul | navy.png |
| Celeste | celeste.png |
| Beige | crema.png |

Conectar send_catalog con una acción multimedia real de Botcake usando los IDs de esos adjuntos. Los nombres anteriores permiten identificar los archivos; no son IDs de medios ni URLs. Los originales y sus IDs no están disponibles en el repositorio.

media_delivery=botcake_flow_required y media_sent=false indican que la API preparó la selección, no que envió archivos. image_urls sigue vacío: no inventar URLs ni usar imágenes de otros productos. La confirmación de envío pertenece a Botcake. Recargar y vincular los cinco originales si el flujo no los encuentra.

Exponer los nuevos parámetros is_opening y opening_sent en el esquema real de decide_fosters_next_action. Los clientes existentes pueden usar asks_for_catalog o asks_for_photos y reciben el mismo plan. El endpoint de campaña siempre devuelve el plan, pero Botcake debe evitar invocarlo como apertura en cada turno.

La apertura no desplaza consultas de ubicación, pago, humano, reclamos o un cierre ya iniciado. Las herramientas de Shopify conservan su conexión externa: no están implementadas en este repositorio. No usar herramientas comerciales para recrear pedidos web existentes.

## Correspondencias que siguen activas

| Herramienta Botcake | Ruta backend |
| --- | --- |
| decide_fosters_next_action | POST /decide-next-action |
| classify_fosters_lead | POST /classify-lead |
| recommend_fosters_size | GET /recommend-size |
| prepare_fosters_order | POST /prepare-order |
| prepare_fosters_shipping | POST /prepare-shipping |
| get_fosters_discount | GET /discount |

Conservar la autenticación y las asignaciones reales existentes. Consultar /openapi.json para parámetros exactos.

## Pendiente antes de declarar arreglado el bot activo

Actualizar las instrucciones maestras con el texto que entregue el responsable; la V8 anterior quedó desactualizada y no debe cargarse. Verificar el despliegue en Render y probar en WhatsApp: apertura con cinco imágenes reales, un color específico, reenvío solicitado y ausencia de ofertas retiradas. Las pruebas locales del backend no confirman la entrega real de medios.
