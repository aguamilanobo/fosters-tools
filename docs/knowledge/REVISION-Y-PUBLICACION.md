# Revisión de la base Fosters — 19/11/2026

## Estado real

Se leyeron los seis documentos V3 activos del Drive compartido. Esta carpeta
contiene sus reemplazos V4. Las instrucciones operativas completas V11 están en
BOTCAKE-INSTRUCCIONES.md, con menos de 15.000 caracteres.

**Los documentos originales del Drive no fueron modificados.** Se obtuvo acceso
público de lectura, pero esta sesión no dispone de conector autenticado de Google
Drive ni de una sesión de navegador controlable para guardar sus cambios. Subir
el código a GitHub o desplegar Render no actualiza Drive ni el índice de Botcake.

## Contradicciones corregidas

| V3 del Drive / información anterior | Versión vigente |
| --- | --- |
| Henley y shorts como únicos productos activos | Henley de lino y Polo de algodón texturizado |
| Ambos productos a 300 Bs / Polo a 300 Bs en backend | Henley 300 Bs; Polo 280 Bs por unidad |
| shorts_lino como producto de anuncios | henley o polo; shorts fuera del catálogo activo |
| El anuncio se impone sobre la elección del cliente | La elección explícita actual prevalece |
| Sin contexto, asumir Henley | Apertura General, sin imágenes, para elegir producto |
| Fotos de shorts y ausencia de fotos Polo | Henley 5 fotos + tabla; Polo 6 fotos + tabla |
| Nunca repetir fotos de forma absoluta | Reenviar por solicitud expresa o fallo anterior |
| Audio automático ante falta de altura/peso | Preguntar solo lo faltante; audio opcional |
| L 78–86/87 y XL 87–110 sin límites exactos | Regla exacta: >77 hasta 86 L; >86 hasta 110 XL, con excepción de altura |
| Medidas históricas S/XXL y shorts en la base activa | Solo M/L/XL; tabla vigente, sin centímetros no verificados |
| Dudas de descuentos de shorts | Tabla existente de ambos productos; 2 Polo=560 sin ahorro |
| Pedir ciudad después de toda consulta general de envío | Preguntarla solo si hace falta resolver o concretar compra |
| Resumen como obligación de cierre | Opcional; no pedir teléfono ni CI para Santa Cruz solo para generarlo |
| Campo/API o texto de instrucciones equivale a enviar fotos | Bloques multimedia reales y comprobación de recepción |

No se confirmó una cantidad exacta de botones Henley ni nuevas medidas físicas.
Se usa la ficha vigente sin inventarlas. La tabla de descuentos y las funciones
compartidas con aguaMILANO se conservan sin cambios.

## Sustitución en Drive conservando los enlaces

Abrir cada documento original, reemplazar su contenido con el archivo indicado y
renombrarlo como V4. Conservar el mismo documento/ID permite mantener sus enlaces.
No dejar una copia V3 contradictoria conectada al bot.

| Documento original | Reemplazo local |
| --- | --- |
| [V3 - 01 INSTRUCCIONES PRINCIPALES BOTCAKE](https://docs.google.com/document/d/1aV1H-VGhcHrvyGgGMGU7-Pbf6gOoV0Ae_0IyaHlO0zk/edit) | 01-INSTRUCCIONES-PRINCIPALES.txt |
| [V3 - 02 PRODUCTOS Y COLORES](https://docs.google.com/document/d/1ZVFNyrjWeWzO74tGL_FAdmeas06TER-qloEEaYdtq5k/edit) | 02-PRODUCTOS-Y-COLORES.txt |
| [V3 - 03 TALLES Y MEDIDAS](https://docs.google.com/document/d/1U9m6xzfS9n74sLVRR9RIarwu88MaY3tcHpgAM8UUjAM/edit) | 03-TALLES-Y-MEDIDAS.txt |
| [V3 - 04 ENVIOS PEDIDOS Y POSTVENTA](https://docs.google.com/document/d/1557P3_CbMJo6DJl6-dIcVsIuf9TVgR-80VW8FrEeBYg/edit) | 04-ENVIOS-PEDIDOS-Y-POSTVENTA.txt |
| [V3 - 05 DESCUENTOS Y CIERRE COMERCIAL](https://docs.google.com/document/d/1peZzgnR6MwAmJ6dAwtEAAc0jasMwtlNPrwpIjMSeAl8/edit) | 05-DESCUENTOS-Y-CIERRE-COMERCIAL.txt |
| [V3 - 06 EJEMPLOS DE ATENCION](https://docs.google.com/document/d/1HyNO_YA_zHSxeDvqo1AbczMYvXiINKIbWo-GykD85y0/edit) | 06-EJEMPLOS-DE-ATENCION.txt |

Después de guardar Drive, actualizar/reimportar las fuentes de conocimiento en
Botcake según su interfaz y comprobar que consulte los textos nuevos. Mantener
ARCHIVO - V1 anterior e INTERNO - pruebas y control fuera de las fuentes activas.
No se modificaron esas carpetas: están expresamente marcadas como no conectables.

## Instrucciones y habilidades de Botcake

Reemplazar el texto maestro por BOTCAKE-INSTRUCCIONES.md V11. Donde aparece
(inserte imagenes), vincular los adjuntos reales. Las seis bases de conocimiento
son documentos de texto: no alojan ni transmiten fotos.

Revisar además el texto fijo de los flujos, las descripciones de habilidades, los
anuncios y respuestas rápidas: si dicen Polo 300/320 Bs, cambiar a 280 Bs. El flujo
Henley sigue a 300 Bs. La consulta GET /discount no requiere cambiarse.

Los precios de ficha, catálogo, apertura y feed Pancake se actualizan desde la
fuente de productos en el backend. Un sistema POS que almacena una copia puede
necesitar ejecutar su sincronización existente; el despliegue no demuestra que
sus datos internos ya se refrescaron.

## Comprobación de imágenes y continuidad pendiente en Botcake

1. Vincular cada archivo al bloque multimedia correcto, con cinco colores Henley
   o seis Polo, más la tabla original. General no envía imágenes.
2. Verificar el disparador del flujo y sus guardas de pago, atención humana y
   compra en curso; no dispararlo ante cualquier cambio de producto sin contexto.
3. Evitar una apertura duplicada de IA y flujo. Si se pausa Botcake AI durante la
   secuencia, reactivarla al final mediante la acción correspondiente.
4. Probar recepción real de las cinco/seis fotos y tabla en WhatsApp. El estado
   de envío del flujo no es por sí solo una confirmación de recepción.
5. Responder “Quiero una negra M” y comprobar que la IA continúe la compra sin
   reiniciar la apertura. Probar también un color específico y reenvío pedido.

Las contradicciones del conocimiento pueden confundir selección de producto y
medios. No se estableció que fueran la causa única de las imágenes ausentes, ni
se verificó desde esta sesión la entrega de fotos en Botcake/WhatsApp.
