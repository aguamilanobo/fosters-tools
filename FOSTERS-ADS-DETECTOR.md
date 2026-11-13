# Detector de producto por anuncio — Fosters

`POST /fosters/ads/resolve` recibe el ID real del anuncio y consulta sus metadatos
en Meta. No requiere mantener una lista manual de IDs. No modifica clientes,
anuncios, campañas, webhooks ni conversaciones. No afecta aguaMILANO.

## Configuración de Render

- `META_ADS_ACCESS_TOKEN`: credencial de Meta con acceso de lectura a los anuncios
  de la cuenta (permiso `ads_read`, o el permiso aplicable autorizado por Meta).
  Introducirla como secreto en las variables de Render, nunca en Git ni en chat.
- `META_GRAPH_API_VERSION`: versión explícita soportada por la aplicación Meta,
  con formato `vNN.0`. Usar la versión indicada en la configuración/documentación
  de esa aplicación; no copiar una versión ficticia de los tests.

La autorización de la cuenta dentro de Botcake no se inyecta automáticamente en
Render. No extraer tokens de sesiones del navegador. Si Botcake ofrece una API
documentada para esos metadatos con una credencial ya disponible, se puede añadir
ese adaptador después de verificarla; este endpoint usa directamente Meta.

Referencia de los campos del anuncio:
https://developers.facebook.com/docs/marketing-api/reference/adgroup/

La consulta es GET a `https://graph.facebook.com/{version}/{ad_id}` con
`fields=id,name,campaign{id,name}`. La credencial viaja en Authorization, no en
la URL. Se mantiene la verificación TLS y se rechazan redirecciones.

## Convención de nombres

Incluir `HENLEY` o `POLO` en el nombre del anuncio o campaña. Ejemplos:

- `FOSTERS | HENLEY | Noviembre`
- `FOSTERS | POLO | Video 01`

Si el anuncio usa un nombre genérico pero la campaña identifica el producto,
se puede resolver por campaña. Si aparecen ambos productos, incluso en nombres
contradictorios de anuncio y campaña, no se elige uno por suposición. Si ninguno
aparece, el detector tampoco puede inferir el producto. No interpreta imágenes.

## Habilidad de Botcake pendiente de configurar

Nombre sugerido: `detect_fosters_ad_product`.

- Tipo: Customize. Método: POST.
- URL: `https://fosters-tools.onrender.com/fosters/ads/resolve`.
- Autenticación: la misma credencial Bearer del backend Fosters.
- Parámetro: `ad_id`, String, sin valor predeterminado. Siempre el ID de anuncio
  recibido realmente por Pancake/Botcake; nunca pedirlo al cliente ni inventarlo.
- Cuerpo: `{"ad_id":"{{ad_id}}"}`.

Descripción sugerida:

> Identifica el producto Fosters del anuncio de origen usando el ad_id real
> disponible en la conversación. Ejecutar antes de la apertura si todavía no hay
> una elección explícita del cliente. Si resolved=true y should_set_product=true,
> usar product para la apertura Henley o Polo. Si no se resuelve, no sobrescribir
> un producto conocido; usar la apertura general si sigue sin producto. No
> repetir la consulta sin cambio de anuncio. No inventar IDs ni inferirlos del
> teléfono, contacto o número de pedido.

Una respuesta resuelta contiene `product=henley` o `polo`, `resolved=true` y
`should_set_product=true`. Después se puede guardar `fosters_producto` y llamar
a `decide_fosters_next_action` con product e is_opening=true, respetando el
historial de aperturas y la prioridad de pagos, reclamos y atención humana.

**No mapear product incondicionalmente al campo persistente:** cuando falla o no
se identifica producto, devuelve null. La integración debe comprobar resolved y
should_set_product antes de guardar. No borrar la elección explícita del cliente
ni reiniciar la apertura por cada mensaje. Los nombres de anuncio pueden quedar
desactualizados respecto de lo que el cliente quiere comprar ahora.

Falta verificar que el campo ad_id mostrado en Pancake se pueda insertar como
valor dinámico en esta petición. Que aparezca en CRM o en el selector de anuncios
no demuestra por sí solo que la IA o una acción HTTP reciban ese campo. Si no se
expone en la habilidad, hace falta una acción/webhook soportado por la plataforma;
no fingir ese enlace ni activar la regla antes de probarlo.

## Resultados sin resolución

Devuelve `resolved=false`, `product=null`, `campaign_key=general`,
`should_set_product=false` y un motivo concreto:

- `missing_ad_id`: sin ID; no consulta Meta.
- `meta_credentials_missing`: falta la variable de credencial.
- `meta_api_version_missing_or_invalid`: falta configurar la versión válida.
- `meta_access_denied`: Meta rechazó la consulta; verificar permiso y vigencia.
- `meta_request_failed`: fallo de red, límite u otro error remoto.
- `product_not_in_ad_names`: los nombres no identifican un producto.
- `ambiguous_ad_product`: aparecen ambos productos.
- `invalid_meta_response`: respuesta inválida o con un ID distinto.

Un ID no numérico devuelve HTTP 400. Sin autenticación del backend devuelve 401.
No se devuelven credenciales, errores crudos de Meta ni información de clientes.

## Verificación

Los tests de `tests/test_ad_source.py` cubren clasificación, conflictos, fallback,
autenticación, errores y construcción de la consulta HTTP. Las respuestas de Meta
en esos tests son simuladas: no demuestran acceso real a la cuenta publicitaria.
Para validar en producción se necesita configurar el acceso y pasar un ID real.
Hasta completar además el paso dinámico de Botcake, no hay detección automática
de extremo a extremo. Mantener las reglas actuales mientras se verifica.
