# Actualización Fosters V6 / instrucciones V13 — 20/11/2026

Sustituye las bases V3/V4/V5 y las instrucciones V11/V12. Henley sigue a 300 Bs, Polo a
280 Bs; colores, descuentos y recomendación de talla sin cambios.

## Comportamiento nuevo

- APERTURA EXCEPTUADA: presentación completa, cinco fotos Henley o seis Polo, tabla y pregunta final incluso ante precio/info inicial. No esperar pedido de fotos.
- Después de la apertura: un párrafo, una frase normalmente, máximo dos y 25 palabras. Sin listas ni
  mensajes de formulario. No repetir datos ni narrar pasos internos.
- Dropshipping: no se exige ni consulta inventario antes de avanzar la venta.
  La gestión operativa posterior queda al equipo. No afirmar reservas hechas,
  stock comprobado, pagos recibidos o plazos inventados.
- Producto, talle y colores elegidos bastan para pasar a destino, sin otra
  confirmación. “L azul y negra” conserva ambos colores y avanza al envío.
- Santa Cruz: ubicación; otros departamentos: solo nombre completo y CI faltantes.
  Después transferir y detener IA, con silencio o un único cierre breve.
- Los bloques multimedia siguen necesarios; no se cambió su vinculación ni se
  verificó la recepción de fotos desde este cambio de código.

## Aplicación en Botcake

Reemplazar el texto maestro por V13 y las seis fuentes de conocimiento por V6.
Los documentos originales del Drive y el panel de Botcake no se modificaron:
no hay herramientas autenticadas de esas aplicaciones en esta sesión. Entregar
archivos Word/TXT directos, sin ZIP. Usar base consolidada o seis documentos,
no ambos formatos duplicados. Refrescar las fuentes conectadas para que deje de
recuperar las instrucciones V4 de verificar inventario en Pancake.

Quitar frases de verificación de stock en descripciones de habilidades, respuestas
rápidas y textos fijos de flujos. Cambiar el cierre largo por “Perfecto, querido.
Enseguida te contacta alguien del equipo.”, o dejar silencio si ya cierra otro
flujo. No recitar al cliente salidas técnicas ni el resumen de impresión.

Descripción sugerida para prepare_fosters_order:
> Prepara la selección real de Henley o Polo sin consulta previa de inventario.
> Producto, talle y colores definidos indican avance al envío; no pedir otra
> confirmación. Conservar cada variante, una unidad por color salvo indicación
> distinta. No pedir teléfono ni datos extra ni afirmar una reserva realizada.

Descripción sugerida para prepare_fosters_shipping:
> Con variante elegida, pedir solo ciudad si falta; Santa Cruz: ubicación; otros
> departamentos: nombre completo y CI faltantes. Con datos completos, transferir
> de inmediato, sin formularios ni nuevas preguntas. No verificar inventario.

Descripción sugerida para notify_fosters_handoff:
> Notificar al equipo con los datos conocidos y ejecutar también la transferencia
> real del chat. No pedir datos extra. Tras éxito, silencio o un solo cierre breve;
> detener IA y no mandar resúmenes, reconfirmaciones ni preguntas adicionales.

## Verificación

Probar “L azul y negra” con producto conocido: pregunta ciudad. Santa Cruz:
pide ubicación. Al recibirla: deriva y no añade requisitos. Otros departamentos:
pide solo documentos faltantes y deriva al completarlos. Probar también pago,
reclamo y fotos explícitas para mantener sus prioridades. Revisar recepción de
imágenes y reanudación de IA por separado, con un contacto de prueba.

AguaMILANO conserva su código y sus instrucciones; estas reglas son solo Fosters.

## Diagnóstico y prueba real de la apertura

No se comprobó la entrega de imágenes desde esta sesión. No se cuenta con acceso
al panel de Botcake ni una sesión controlable del navegador para editar sus
flujos, consultar el registro del contacto o comprobar recepción en WhatsApp.
La cuenta de Botcake configurada en Render no expone por sí sola los adjuntos/IDs
de flujos al proceso de desarrollo. No se enviaron pruebas a contactos reales.

Aplicación mínima: pegar el parche prioritario al inicio de instrucciones sin
borrar los adjuntos existentes; actualizar la descripción de decide_fosters_next_action
para exigir is_opening=true en el primer ingreso comercial, aunque diga precio.
Mantener opening_sent=false hasta terminar los medios. Si Botcake devuelve
send_catalog pero solo manda texto, revisar la acción que consume ese resultado:
debe ejecutar los mismos adjuntos/flujo que ya funciona al pedir “los colores”.
No basta con guardar next_action en un campo sin tener la acción conectada.

La prueba mínima tiene dos casos: primer mensaje “Hola, precio?” con producto
Henley y estado de apertura pendiente → presentación, cinco fotos, tabla y
pregunta; primer mensaje “Hola, quiero las polos” → presentación, seis fotos,
tabla y pregunta. Después responder “L azul y negra”: debe avanzar al envío sin
repetir apertura. Verificar también respuesta de IA después de los medios y
prioridad de humano/pago. Usar un contacto propio de prueba, con estado de
apertura del producto pendiente; no resetear masivamente contactos de clientes.
