# Casos de uso

## CU1 — Consultar servicios contratados

**Actores:** Cliente

**Precondición:** El cliente debe estar registrado en el sistema.

### Flujo principal
1. El cliente solicita consultar sus servicios contratados.
2. El sistema identifica al cliente.
3. El sistema consulta los servicios asociados al cliente.
4. El sistema muestra al cliente los servicios contratados.

### Flujo alternativo / excepciones

- **2.a — Cliente no identificado**
  1. El sistema informa que no se pudo identificar al cliente.

- **3.a — El cliente no posee servicios contratados**
  1. El sistema informa que el cliente no posee servicios contratados.

**Postcondición:** El cliente visualiza sus servicios contratados.

---

## CU2 — Realizar solicitud de modificación

**Actores:** Cliente

**Precondición:** El cliente debe estar registrado y tener al menos un servicio contratado.

### Flujo principal
1. El cliente solicita realizar una modificación sobre un servicio contratado.
2. El sistema muestra los servicios contratados por el cliente.
3. El cliente selecciona el servicio que desea modificar.
4. El cliente ingresa el tipo de modificación solicitada.
5. El sistema registra la solicitud.
6. El sistema asigna el estado inicial de la solicitud.
7. El sistema informa al cliente que la solicitud fue registrada.

### Flujo alternativo / excepciones

- **3a — El cliente no posee servicios contratados**
  1. El sistema informa que no existen servicios disponibles para modificar.

- **4a — Datos de la solicitud incompletos**
  1. El sistema informa que faltan datos para realizar la solicitud.
  2. El cliente completa los datos requeridos.

**Postcondición:** La solicitud de modificación queda registrada con su estado inicial.

---

## CU03 — Atender solicitud

**Actores:** Administrador

**Precondición:** El administrador debe estar autenticado en el sistema. Debe existir al menos una solicitud pendiente.

### Flujo principal
1. El administrador busca la solicitud pendiente.
2. El sistema muestra los datos de la solicitud.
3. **[Información faltante en la fuente]** No se especifica el paso 3.
4. **[Información faltante en la fuente]** No se especifica el paso 4.
5. El administrador revisa la solicitud y decide su resolución.
6. El sistema actualiza el estado de la solicitud.
7. El sistema notifica al cliente el resultado.

### Flujo alternativo / excepciones

- **1.a — Solicitud no encontrada**
  1. El sistema informa que no se encontró la solicitud.

- **5.a — Solicitud rechazada**
  1. El sistema solicita al administrador el motivo de rechazo.
  2. El administrador ingresa el motivo del rechazo.
  3. El sistema registra el motivo.

**Postcondición:** La solicitud queda con su prioridad y estado actualizados.

---

## CU4 — Adjuntar documentación a una solicitud

**Actores:** Cliente

**Precondición:** El cliente debe tener una solicitud registrada.

### Flujo principal
1. El cliente selecciona una solicitud.
2. El cliente selecciona la opción para adjuntar documentación.
3. El cliente selecciona el archivo o imagen.
4. **[Información faltante en la fuente]** No se especifica la acción del paso 4 del flujo principal.
5. El sistema asocia la documentación a la solicitud.
6. El sistema informa al cliente que la documentación fue adjuntada.

### Flujo alternativo / excepciones

- **3a — Archivo no válido**
  1. El sistema informa que el archivo no es válido.
  2. El cliente selecciona otro archivo.

**Postcondición:** La documentación queda asociada a la solicitud.

---

## CU5 — Gestionar clientes

**Actores:** Administrador

**Precondición:** El administrador debe estar autenticado en el sistema.

### Flujo principal
1. El administrador accede a la gestión de clientes.
2. El sistema muestra los clientes registrados.
3. El administrador selecciona la operación que desea realizar.
4. El administrador ingresa o modifica los datos del cliente.
5. El sistema valida los datos ingresados.

### Flujo alternativo / excepciones

- **5.a — Datos inválidos**
  1. El sistema informa los datos que deben corregirse.
  2. El administrador modifica los datos.

**Postcondición:** Los datos del cliente quedan registrados o actualizados.

---

## CU6 — Gestionar planes y servicios

**Actores:** Administrador

**Precondición:** El administrador debe estar autenticado.

### Flujo principal
1. El administrador accede a la gestión de planes y servicios.
2. El sistema muestra los planes y servicios registrados.
3. El administrador selecciona la operación que desea realizar.
4. El administrador ingresa o modifica los datos.
5. El sistema valida la información.
6. El sistema registra la operación.
7. El sistema informa que la operación fue realizada correctamente.

### Flujo alternativo / excepciones

- **5.a — Datos inválidos**
  1. El sistema informa el error.
  2. El administrador corrige los datos.

**Postcondición:** Los planes y servicios quedan registrados o actualizados.

---

## CU7 — Asignar prioridad a una solicitud

**Actores:** Administrador

**Precondición:** Debe existir una solicitud registrada y el administrador debe estar autenticado.

### Flujo principal
1. El administrador selecciona una solicitud.
2. El sistema muestra los datos de la solicitud y el plan contratado.
3. El administrador determina la prioridad correspondiente.
4. **[Información faltante en la fuente]** No se especifica la acción del paso 4 del flujo principal.

### Flujo alternativo / excepciones

- **3.a — No se puede determinar la prioridad**
  1. El sistema informa que no se puede asignar la prioridad.
  2. El administrador revisa la información de la solicitud.

**Postcondición:** La solicitud queda asociada a una prioridad.

---

## CU8 — Generar Reclamos

**Actores:** Cliente

**Precondición:** El cliente debe estar registrado y tener al menos un servicio contratado.

### Flujo principal
1. El cliente solicita generar un reclamo.
2. El sistema muestra los servicios contratados por el cliente.
3. El cliente selecciona el servicio sobre el que reclama.
4. El cliente describe el motivo del reclamo.
5. El sistema registra el reclamo.
6. El sistema asigna la prioridad inicial del reclamo.
7. El sistema informa al cliente que el reclamo fue registrado.

### Flujo alternativo / excepciones

- **3.a — El cliente no posee servicios contratados**
  1. El sistema informa que no existen servicios disponibles para reclamar.

- **4.a — Datos de la solicitud incompletos**
  1. El sistema informa que faltan datos para realizar el reclamo.
  2. El cliente completa los datos requeridos.

**Postcondición:** El cliente tiene que registrar el reclamo exitosamente.

---

## CU9 — Solicitar cambio de Plan

**Actores:** Cliente

**Precondición:** El cliente tiene que tener un plan contratado.

### Flujo principal
1. El cliente solicita un cambio de plan.
2. El sistema solicita la validación de identidad a VeriCheck.
3. VeriCheck valida la identidad del cliente.
4. El sistema registra la solicitud de cambio de plan.
5. El administrador revisa la solicitud.
6. El administrador aprueba el cambio de plan.

### Flujo alternativo / excepciones

- **2.a — Identidad no validada**
  1. VeriCheck informa que no se pudo validar la identidad.
  2. El sistema informa al cliente que no se puede continuar con el cambio de plan.

- **6.a — Cambio de plan rechazado**
  1. El administrador rechaza la solicitud.
  2. El sistema actualiza el estado de la solicitud.
  3. El sistema informa al cliente que el cambio de plan fue rechazado.

**Postcondición:** El cambio de plan queda aprobado y actualizado, y los datos correspondientes son enviados a PagoNet.

---

## CU10 — Consultar solicitudes y estados

**Actores:** Administrador

**Precondición:** El administrador debe estar autenticado en el sistema. Debe existir al menos una solicitud registrada.

### Flujo principal
1. El administrador solicita consultar las solicitudes.
2. El sistema muestra las solicitudes registradas.
3. El administrador selecciona una solicitud.
4. El sistema muestra los datos y el estado de la solicitud.

### Flujo alternativo / excepciones

- **2.a — Solicitudes no encontradas**
  1. El sistema informa que no existen solicitudes registradas.

**Postcondición:** El administrador visualiza las solicitudes y sus estados.

---

## CU11 — Recibir notificación de nueva solicitud

**Actores:** Administrador

**Precondición:** Debe existir una nueva solicitud registrada.

### Flujo principal
1. El cliente registra una nueva solicitud.
2. El sistema genera una notificación para el administrador.
3. El sistema envía la notificación al administrador.
4. El administrador recibe la notificación.

### Flujo alternativo / excepciones

- **3.a — No se puede enviar la notificación**
  1. El sistema registra el inconveniente.
  2. El sistema informa que la notificación no pudo ser enviada.

**Postcondición:** El administrador recibe la notificación de la nueva solicitud.

---

## CU12 — Recibir notificación sobre el estado de una solicitud

**Actores:** Cliente

**Precondición:** Debe existir una solicitud registrada y haberse producido un cambio en su estado.

### Flujo principal
1. El sistema detecta un cambio en el estado de la solicitud.
2. El sistema genera una notificación para el cliente.
3. El sistema envía la notificación al cliente.
4. El cliente recibe la notificación.

### Flujo alternativo / excepciones

- **3.a — No se puede enviar la notificación**
  1. El sistema registra el inconveniente.
  2. El sistema informa que la notificación no pudo ser enviada.

**Postcondición:** El cliente recibe la información correspondiente al nuevo estado de su solicitud.

---

## CU13 — Consultar información del cliente mediante API

**Actores:** Sistema externo

**Precondición:** El sistema externo debe estar autorizado para realizar la consulta.

### Flujo principal
1. El sistema externo solicita información de un cliente mediante la API.
2. El sistema recibe la solicitud.
3. El sistema consulta la información del cliente.
4. El sistema devuelve la información solicitada al sistema externo.

### Flujo alternativo / excepciones

- **1.a — Cliente no encontrado**
  1. El sistema informa que no se encontró el cliente solicitado.

**Postcondición:** El sistema externo recibe la información solicitada del cliente.

---

## CU14 — Validar información del Cliente

**Actores:** VeriCheck

**Precondición:** El cliente debe efectuar un cambio importante en el sistema (plan, datos fiscales, reclamos legales).

### Flujo principal
1. El cliente realiza una solicitud de cambio importante en el sistema.
2. VeriCheck valida que la información del cliente sea la correcta.
3. **[Información faltante en la fuente]** No se especifica la acción del paso 3 del flujo principal.
4. El sistema aprueba el cambio importante.
5. El cliente ve reflejado el cambio en su perfil.

### Flujo alternativo / excepciones

- **2.1 — VeriCheck verifica que la información no es la correcta**
  - El sistema recibe el rechazo enviado por VeriCheck. En la fuente, esta acción aparece en una fila sin número de paso del flujo principal asociada al flujo alternativo.

**Postcondición:** El cliente tiene que ver reflejado el cambio en su perfil, ya sea cambio de plan, datos fiscales o reclamos legales.

---

## CU15 — Aprobar Plan

**Actores:** Administrador, PagoNet

**Precondición:** Debe existir una solicitud de "cambio de plan" en estado creada previamente por un cliente.

### Flujo principal
1. El sistema muestra el listado de solicitudes.
2. El Administrador selecciona una solicitud de cambio de plan para ver sus detalles (cliente, plan actual, plan solicitado).
3. **[Información faltante en la fuente]** No se especifica la acción del paso 3 del flujo principal.
4. El Administrador aprueba la solicitud.
5. El sistema actualiza internamente el perfil del cliente, asignándole el nuevo plan y cambiando el estado de la solicitud a Aprobada.
6. El sistema recopila la información necesaria para la facturación.
7. El sistema envía esta información automáticamente a PagoNet.

### Flujo alternativo / excepciones

- **2.1 — El Administrador rechaza la solicitud**
  - El sistema cambia el estado de la solicitud a Rechazada y no se contacta a PagoNet.

- **7.1 — Error de conexión con PagoNet**
  - El sistema guarda la solicitud como Aprobada internamente, pero marca el envío a facturación como Pendiente de reintento.
  - El sistema alerta al Administrador de que la integración falló y que se reintentará más tarde.

### Postcondición
- El cliente tiene su nuevo plan activo en el sistema.
- PagoNet cuenta con los datos correctos para emitir la factura y llevar el registro contable correspondiente.

---

## CU16 — Notificar cambio de estado

**Actores:** NotiSys

**Precondición:** Tiene que haber una solicitud creada por el cliente.

### Flujo principal
1. El cliente crea una solicitud.
2. NotiSys envía la notificación “Se ha creado la solicitud XXX”.
3. El cliente realiza una modificación/aprueba la solicitud.
4. NotiSys envía la notificación “Se ha modificado la solicitud XXX” o “Se ha aprobado la solicitud XXX”.
5. El sistema notifica que el cambio de plan fue confirmado.

### Flujo alternativo / excepciones

- **2.1 — Faltan datos obligatorios del destinatario**
  - Si faltan datos obligatorios del destinatario, como email o teléfono, la notificación no puede enviarse por dicho canal.

**Postcondición:** La notificación correspondiente al evento es enviada a NotiSys para su distribución al cliente o administrador.

---

## CU17 — Envío Diario de Métricas a AnalytixPro

**Actores:** AnalytixPro

**Precondición:** El sistema tiene conectividad y credenciales válidas para comunicarse con la API de AnalytixPro.

### Flujo principal
1. El sistema consulta internamente sus bases de datos (clientes, planes, solicitudes) para calcular el resumen de actividad de ese día.
2. El sistema calcula los siguientes valores: la fecha actual, el total de clientes, los nuevos registros, las solicitudes nuevas, el tiempo promedio de respuesta, los cambios de plan y los reclamos abiertos.
3. El sistema empaqueta toda esta información.
4. El sistema envía a AnalytixPro toda la información.
5. **[Información faltante en la fuente]** No se especifica la acción del paso 5 del flujo principal.
6. **[Información faltante en la fuente]** No se especifica la acción del paso 6 del flujo principal.

### Flujo alternativo / excepciones

- **4.1 — Falla de conexión con AnalytixPro**
  1. El sistema registra el fallo en el módulo de auditoría de integraciones.
  2. El sistema programa un reintento automático.

**Postcondición:** La plataforma AnalytixPro cuenta con los datos operativos más recientes para mostrarlos en sus dashboards ejecutivos.

---

## Observaciones sobre la fuente

- En **CU03**, el flujo principal pasa del paso 2 al paso 5; los pasos 3 y 4 no aparecen en la fuente.
- En **CU04**, el paso 4 del flujo principal no contiene una descripción.
- En **CU07**, el paso 4 del flujo principal no contiene una descripción.
- En **CU14**, el paso 3 del flujo principal no contiene una descripción. La acción “VeriCheck envía el rechazo al sistema” aparece en el bloque de excepciones sin un número de paso del flujo principal.
- En **CU15**, el paso 3 del flujo principal no contiene una descripción.
- En **CU17**, los pasos 5 y 6 del flujo principal no contienen una descripción. Las acciones de registrar el fallo y programar un reintento aparecen en el bloque de excepciones asociado a la falla de conexión.
- Se conservaron las denominaciones y la información de la fuente. Las indicaciones entre corchetes señalan datos ausentes y no completan el contenido por inferencia.
