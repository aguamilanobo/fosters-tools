# FOSTERS — Lanzamiento camisa de lino brasilero (11-oct-2026)

## Productos
### Activo — Camisa lino brasilero
- 300 Bs.
- Lino brasilero (nombre comercial; NO afirmar composición exacta sin ficha técnica).
- Botones a lo largo de todo el frente.
- Colores: negro, blanco, azul, celeste, plomo y beige.
- Talles de referencia M, L y XL. Confirmar stock y si XXL corresponde a alguna variante antes de prometerlo.
- Misma guía de talle/horma de la Henley: M 65–77 kg, L 78–87 kg, XL 87–110 kg aprox. La altura también influye en largo.
- Stock por color/talle: **sin confirmar**; verificar en Pancake POS.
- Fotos nuevas: **pendientes de cargar**; nunca usar fotos de Henley para la nueva camisa.
### Pausado — Henley
- 300 Bs; composición 55 % lino / 45 % algodón; botones únicamente en el pecho.
- Pausada temporalmente por falta de stock; no promover hasta confirmar reposición.
- Colores activos del portafolio: negro, blanco, azul, celeste y beige. **No verde ni marrón**.

## Backend en GitHub / Render
- `GET /fosters/products`: ambos productos y estado.
- `GET /fosters/product?product=camisa-lino-brasilero&color=plomo`: ficha de nueva camisa.
- `GET /fosters/campaign-reply?product=camisa-lino-brasilero`: respuesta sugerida para anuncios.
- `GET /catalog`: ahora usa la ficha principal, acepta `product` y `color`.
- `GET /products`: catálogo de sincronización de producto **nuevo**; imágenes vacías y cantidades no verificadas. NO activar sincronización automática de Pancake POS antes de verificar mapeo y stock, para evitar duplicados o sobrescritura del catálogo real.
- `POST /fosters/payment-summary`: dejó de anteponer "Henley" a todo.
- `GET /recommend-size` sigue con misma lógica anterior.
- Dispatch/Printer/aguaMILANO no fueron modificados.

## Botcake — tareas manuales
1. En productos/etiquetas de conversación, crear `FOSTERS_LINO_BRASILERO`, dejar `FOSTERS_HENLEY` como pausado.
2. En la nueva campaña Click-to-WhatsApp, identificar la procedencia con ref del anuncio, palabra clave o un flujo específico, según lo que esté habilitado en tu Botcake/Meta. Probar con WhatsApp personal antes de lanzar.
3. Activar un flujo específico **Camisa lino brasilero**; usar la respuesta de abajo, imágenes reales de los seis colores y pregunta por talle/color. Deshabilitar o pausar el flujo de Henley para nuevas conversaciones; no cambiar conversaciones que ya están atendiendo un pedido antiguo.
4. Si Botcake AI usa instrucciones fijas, actualizar base de conocimiento y prioridad comercial: nueva camisa principal, Henley pausada, colores retirados no disponibles, no confundir lino brasilero con mezcla 55/45.
5. Verificar stock real de todas las variantes, incluidos talles. Actualizar catálogo de Pancake POS manualmente primero; no suponer que GitHub lo modifica.
6. Hacer prueba de un mensaje de anuncio a WhatsApp desde otro teléfono: verificar origen, fotos, precio, talles, derivación humana, cierre.

## Mensaje inicial recomendado (copia Botcake)
¡Hola! 👋 Bienvenido a FOSTERS.

Nuestra nueva **camisa de lino brasilero** tiene botones completos y cuesta **300 Bs**. Disponible en **negro, blanco, azul, celeste, plomo y beige**. Manejamos la misma horma de siempre.

¿Qué talla y color buscás? Si tenés dudas con la talla, pasanos altura y peso y te ayudamos.

## Respuesta si preguntan por Henley
Las Henley están temporalmente pausadas por reposición. Por ahora tenemos la nueva camisa Fosters de lino brasilero a 300 Bs, con botones en todo el frente. ¿Querés ver los colores?

## Pendientes antes de campaña real
- Cargar URLs de 6 fotos reales nuevas, sin inventar imágenes.
- Validar existencias de cada talle/color.
- Comprobar cómo Botcake recibe atribución del anuncio; un commit no modifica automáticamente sus flujos.
- Confirmar si XXL está disponible en algún color.
- No asumir que `/products` es el catálogo real de Pancake POS o que las existencias están sincronizadas.
