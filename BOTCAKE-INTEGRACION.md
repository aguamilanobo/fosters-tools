# FOSTERS — Henley + Polo por WhatsApp

## Backend

Dos productos activos, M/L/XL: Henley a 300 Bs y Polo a 280 Bs por unidad.

| product | Material | Colores |
| --- | --- | --- |
| henley | 55% lino / 45% algodón | Negro, Blanco, Azul, Celeste, Beige |
| polo | Algodón texturizado | Negro, Blanco, Azul, Celeste, Beige, Gris |

Polo reconoce Plomo/Gris claro como Gris; Beige claro como Beige. /products incluye Henley (15 variantes) y Polo (18). El stock sigue sin verificar. AguaMILANO, la tabla de descuentos y la fórmula de recomendación de talla permanecen sin cambios. Se actualizó exclusivamente el precio individual de Polo a 280 Bs; las variantes del feed Pancake usan ese valor.

## Aperturas y herramientas existentes

No hace falta una nueva habilidad de descuentos ni tallas. Actualizar únicamente el esquema y las instrucciones de las herramientas Fosters existentes:

| Herramienta | Endpoint | Ajuste |
| --- | --- | --- |
| Catálogo Fosters | GET /fosters/products | Ahora devuelve ambos productos |
| Ficha Fosters | GET /fosters/product | product=henley o polo; color opcional |
| Apertura/campaña Fosters | GET /fosters/campaign-reply | product vacío → general; henley → cinco fotos; polo → seis |
| decide_fosters_next_action | POST /decide-next-action | Conservar parámetros; exponer product, message opcional, web_order, is_opening y opening_sent |
| prepare_fosters_order | POST /prepare-order | Pasar product explícito; Polo ya no se convierte en Henley; web_order bloquea pedidos web |
| Resumen de pago | POST /fosters/payment-summary | Conserva Polo en el texto; web_order bloquea pedidos web |
| prepare_fosters_shipping | POST /prepare-shipping | Sin cambios |
| recommend_fosters_size | GET /recommend-size | Sin cambios |
| get_fosters_discount | GET /discount | Sin cambios |
| classify_fosters_lead | POST /classify-lead | Sin cambios |

Mantener autenticación y asignaciones reales existentes. El esquema exacto está en /openapi.json. Ejemplos de decide_fosters_next_action:

```json
{"is_opening": true}
```
→ ask_product, campaign_key=general, sin fotos.

```json
{"product": "henley", "is_opening": true}
```
→ send_catalog, cinco fotos Henley, send_size_chart=true.

```json
{"message": "Hola, estoy interesado en las polos", "is_opening": true}
```
→ send_catalog, product=polo, seis fotos, send_size_chart=true.

```json
{"product": "polo", "color": "plomo", "asks_for_photos": true, "opening_sent": true}
```
→ una foto Polo Gris; puede reenviarse por solicitud expresa.

La presentación general no cuenta como apertura del producto; tras elegirlo, ejecutar la apertura correspondiente. Mantener el estado por producto en el contexto de Botcake. Cambiar de producto no debe heredar el estado de apertura del anterior.

## Acciones multimedia reales de Botcake

Henley conserva negra.png, blanca.png, navy.png, celeste.png y crema.png. Polo requiere vincular las seis imágenes provistas por el responsable:

| Clave lógica | Color | Identificación visual de la foto |
| --- | --- | --- |
| polo_negro | Negro | Polo negra, rótulo Negro |
| polo_blanco | Blanco | Polo blanca, rótulo Blanco |
| polo_azul | Azul | Polo azul, rótulo Azul |
| polo_celeste | Celeste | Polo celeste, rótulo Celeste |
| polo_beige | Beige | Rótulo Beige claro |
| polo_gris | Gris | Rótulo Gris claro |

Las claves no son nombres de archivo ni IDs reales. filename=null y binding_required=true señalan que el backend desconoce el vínculo en Botcake. No sustituirlo por fotos Henley. La tabla usa clave fosters_size_chart y debe vincularse a la tabla original existente. La API no ejecuta el envío. media_sent=false no confirma entrega.

## Pedidos web desactivados y conservados

La lógica histórica y sus instrucciones completas se conservan en docs/archive/BOTCAKE-V8-DESACTIVADO.md; no cargar ese archivo. El catálogo declara sales_channel=whatsapp y web_orders_enabled=false. Los endpoints Fosters de decisión, preparación y resumen bloquean web_order=true. Decisión y preparación también detectan el texto típico “Hola Fosters, quiero hacer este pedido” o referencias a Shopify/fostersbolivia.shop. Derivan a revisión sin crear, modificar, cobrar ni cancelar pedidos web.

Las herramientas reales de Shopify viven fuera del repositorio: el despliegue en Render NO las desactiva en Botcake. Allí hay que desactivar (no borrar) sus habilidades, disparadores y reglas web. Mantener los webhooks de aguaMILANO intactos; no son pedidos web Fosters.

Las rutas históricas /fosters/upsell/* continúan HTTP 410. Mantener desactivadas sus habilidades y los productos retirados.

## Instrucciones activas y comprobación

Usar BOTCAKE-INSTRUCCIONES.md como nuevo texto maestro exclusivo de Fosters. Antes de declarar listo el bot real, verificar en Botcake: elección general, Henley con cinco fotos, Polo con seis, Polo Gris/Plomo con una foto, tabla original, continuidad sin repetir apertura, descuento solo bajo consulta y derivación al cerrar. Las pruebas del backend no comprueban envío en WhatsApp ni cambios en Botcake.

## Base de conocimiento vigente

Usar los seis documentos V4 de docs/knowledge y BOTCAKE-INSTRUCCIONES.md (V11). Los seis documentos V3 del Drive aún requieren sustitución manual en los originales y actualización de la fuente de Botcake; este repositorio no los modifica remotamente. Ver docs/knowledge/REVISION-Y-PUBLICACION.md. Dos Polo a 560 Bs equivalen a dos unidades de 280 Bs: no anunciar ahorro para esa cantidad.
