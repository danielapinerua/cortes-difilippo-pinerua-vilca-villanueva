# Historias de Usuario - Consultora Tech Solutions

Documento consolidado en base al tablero Trello del equipo.

## Historias de Usuario

### US01 - Consultar servicios contratados

Como cliente registrado con al menos un servicio contratado, quiero poder consultar el listado de servicios que tengo contratados con la consultora, para conocer en todo momento qué servicios tengo activos sin tener que comunicarme con un asesor.

 El sistema debe identificar al cliente antes de mostrarle la información, y si no tiene servicios contratados, informárselo claramente en vez de mostrar una pantalla vacía.

### US02 - Solicitar modificación de servicio

Como cliente registrado con al menos un servicio contratado, quiero solicitar una modificación sobre uno de mis servicios contratados, para poder ajustar las condiciones de ese servicio a mis necesidades actuales sin tener que dar de baja y recontratar.

El sistema debe mostrarme primero mis servicios contratados para elegir sobre cuál quiero modificar, pedirme el tipo de modificación, y avisarme si falta algún dato antes de registrar la solicitud con un estado inicial.

### US03 - Adjuntar documentación

Como cliente con una solicitud ya registrada, quiero poder adjuntar documentación o imágenes a esa solicitud, para respaldar el pedido que realicé con la información que la consultora necesite.

 El sistema debe validar que el archivo sea de un formato aceptado antes de asociarlo a la solicitud; si no es válido, debe avisarme y dejarme elegir otro archivo en vez de cortar el proceso.

### US04 - Realizar un reclamo

Como cliente registrado con al menos un servicio contratado, quiero poder registrar un reclamo sobre un servicio contratado, para que la consultora tome conocimiento del problema y le dé seguimiento.

 Debo poder elegir el servicio sobre el que reclamo y describir el motivo; el sistema registra el reclamo, le asigna una prioridad inicial y me confirma que quedó cargado.

### US05 - Consultar estado de una solicitud

Como cliente con al menos una solicitud registrada, quiero consultar en qué estado se encuentra mi solicitud, para saber si ya fue atendida sin tener que esperar a que me contacten.

 El sistema debe mostrarme el estado actual de cada solicitud que tengo activa (pendiente, aprobada, rechazada, etc.), de forma clara y sin tener que pedir ayuda a un administrador para averiguarlo.

### US06 - Gestionar clientes

Como administrador autenticado, quiero poder registrar y actualizar los datos de los clientes, para mantener la base de clientes de la consultora correcta y al día.

El sistema debe mostrarme los clientes ya registrados, permitirme elegir qué operación quiero hacer (alta o modificación), y validar los datos que ingreso antes de guardarlos, avisándome si hay algo mal cargado..

### US07 - Gestionar planes

Como administrador autenticado, quiero poder registrar y actualizar los servicios que ofrece la consultora, para mantener actualizado el catálogo que los clientes pueden contratar.

El sistema debe mostrarme los servicios existentes, dejarme crear uno nuevo o modificar uno existente, y confirmarme cuando la operación se haya realizado correctamente.

### US08 - Gestionar servicios

Como administrador autenticado, quiero poder registrar y actualizar los servicios que ofrece la consultora, para mantener actualizado el catálogo que los clientes pueden contratar.

El sistema debe mostrarme los servicios existentes, dejarme crear uno nuevo o modificar uno existente, y confirmarme cuando la operación se haya realizado correctamente.

### US09 - Atender solicitud

Como administrador autenticado, con al menos una solicitud pendiente, quiero revisar una solicitud y decidir si la apruebo o la rechazo, para darle una resolución a los pedidos que hacen los clientes.

Si rechazo la solicitud, el sistema debe pedirme el motivo del rechazo antes de registrarlo; en cualquiera de los dos casos, el sistema actualiza el estado de la solicitud y notifica al cliente el resultado.

### US10 - Asignar prioridad

Como administrador autenticado, quiero asignar una prioridad a una solicitud según el plan contratado por el cliente, para que las solicitudes se atiendan respetando el nivel de servicio correspondiente.

El sistema debe mostrarme los datos de la solicitud junto con el plan contratado, para que yo pueda determinar la prioridad correcta, y si no puedo determinarla, debe permitirme revisar la información nuevamente en vez de forzar una decisión.

### US11 - Notificar nueva solicitud

Como administrador, quiero recibir una notificación automática cuando se registre una nueva solicitud, para enterarme sin tener que estar revisando el sistema constantemente.

Si la notificación no puede enviarse (por ejemplo, por un problema de conexión), el sistema debe registrar el inconveniente y avisarme igual que hubo una solicitud nueva pendiente de revisión.

### US12 - Notificar cambio de estado de una solicitud

Como cliente con una solicitud registrada, quiero recibir una notificación cuando cambie el estado de mi solicitud, para estar al tanto del avance sin tener que entrar a consultarlo manualmente.

El sistema detecta el cambio de estado, genera la notificación correspondiente y me la envía; si no puede enviarla, debe quedar registrado el inconveniente para que no se pierda el aviso.

### US13 - Solicitar Cambio de Plan

Como cliente con un plan contratado, quiero solicitar un cambio a otro plan, para acceder a condiciones que se ajusten mejor a lo que necesito en este momento.

Antes de registrar la solicitud, el sistema debe validar mi identidad; si no puede validarla, me informa que no puede continuar con el cambio. Si la identidad se valida correctamente, la solicitud queda registrada a la espera de que un administrador la revise.

### US14 - Consultar Solicitudes y Estados

Como administrador autenticado, quiero consultar todas las solicitudes registradas junto con su estado, para tener una visión general de la carga de trabajo pendiente.

El sistema debe mostrarme el listado completo de solicitudes y, si elijo una en particular, sus datos y estado actual en detalle.

### US15 - Consultar Información del Cliente mediante la API

Como sistema externo autorizado, quiero consultar información de un cliente mediante la API del sistema, para utilizar esos datos en mis propios procesos sin intervención manual.

El sistema debe validar que la consulta esté autorizada, buscar al cliente solicitado y devolver la información encontrada; si el cliente no existe, debe informar el error en vez de devolver datos vacíos o incorrectos.

### US16 - Iniciar Sesion

Como usuario ya registrado en el sistema (cliente o administrador), quiero iniciar sesión con mis credenciales, para acceder a las funcionalidades que me corresponden según mi rol.

El sistema debe validar usuario y contraseña, y en caso de que los datos sean incorrectos, informarme el error sin indicar cuál de los dos campos falló, por una cuestión de seguridad.

### US17 - Registrar un nuevo usuario

Como visitante no registrado, quiero crear una cuenta en el sistema, para poder acceder a los servicios que ofrece la consultora.

El sistema debe pedirme los datos necesarios para el alta, validarlos antes de confirmar el registro, y avisarme si algún dato es inválido o si ya existe una cuenta con esos datos.

### US18 - Validar identidad del cliente

Como cliente que solicita un cambio importante (de plan, datos fiscales o un reclamo legal), quiero que el sistema valide mi identidad mediante VeriCheck antes de aplicar el cambio, para garantizar que la operación se haga de forma segura.

Si la validación es correcta, el sistema aprueba el cambio y actualiza mi perfil; si la información resulta incorrecta, el sistema rechaza el cambio y me notifica el motivo.

### US19 - Aprobar o rechazar cambio de plan

Como administrador autenticado, quiero aprobar o rechazar una solicitud de cambio de plan, para controlar qué cambios se hacen efectivos sobre los planes de los clientes.

Si apruebo el cambio, el sistema actualiza el perfil del cliente y prepara la información para facturación; si lo rechazo, el sistema cambia el estado de la solicitud a rechazada sin contactar a los sistemas de facturación.

### US20 - Enviar información de facturación a PagoNet

Como administrador que acaba de aprobar un cambio de plan, quiero que el sistema envíe automáticamente los datos de facturación correspondientes a PagoNet, para que el nuevo plan quede facturado sin que yo tenga que cargarlo manualmente en otro sistema.

Si la conexión con PagoNet falla, el sistema debe guardar la solicitud como aprobada igualmente, marcar el envío como pendiente de reintento y avisarme que la integración falló.

### US21 - Integrar el envio de notifaciones con NotiSys

Como cliente o administrador, quiero recibir las notificaciones del sistema a través de NotiSys, para enterarme de los eventos importantes por el canal que mejor me quede (email o SMS).

Si faltan datos obligatorios del destinatario (como el email o el teléfono), el sistema debe detectarlo y no intentar enviar la notificación por ese canal en particular.

### US22 - Enviar metricas a AnalytixPro

Como administrador, quiero que el sistema envíe diariamente un resumen de métricas de actividad a AnalytixPro, para contar con información actualizada sobre el funcionamiento del sistema sin tener que pedirla manualmente.

El sistema debe calcular los valores del día (clientes totales, nuevos registros, solicitudes nuevas, tiempo promedio de respuesta, cambios de plan y reclamos abiertos), empaquetarlos y enviarlos; si falla la conexión, debe registrar el fallo y programar un reintento automático.

### US23 - Registrar auditoria de integraciones externas

Como administrador, quiero que el sistema registre los envíos, respuestas y errores producidos en las integraciones con sistemas externos (VeriCheck, PagoNet, NotiSys, CRMMax, AnalytixPro), para poder detectar y resolver fallas de comunicación cuando ocurran.

Cada intento de integración, exitoso o fallido, debe quedar registrado con la información suficiente para identificar qué pasó, cuándo y con qué sistema externo.

### US24 - Demo funcional en Python y Flask

**Como** cliente de Consultora Tech Solutions,
**quiero** disponer de una demo funcional desarrollada en Python y Flask sobre funcionalidades seleccionadas del sistema, utilizando IA como apoyo durante el desarrollo,
**para** poder validar mediante un prototipo el funcionamiento de la solución antes de avanzar con versiones posteriores.

### US25 - Tutorial de instalación y ejecución

**Como** cliente de Consultora Tech Solutions,
**quiero** disponer de un videotutorial o documento con las instrucciones necesarias para instalar y ejecutar la demo,
**para** poder correrla y probar sus funcionalidades de manera autónoma.

### US26 - Registro y seguimiento del trabajo del Sprint

**Como** cliente de Consultora Tech Solutions,
**quiero** que el pedido de la demo quede registrado y priorizado dentro del Sprint junto con las horas dedicadas a las tareas realizadas,
**para** poder conocer el esfuerzo invertido y realizar un seguimiento del avance del equipo.

## Sprint 1 - Demo MVP

**Sprint Goal:** desarrollar una Demo MVP funcional en Python y Flask que permita autenticar usuarios, consultar los servicios de un cliente, registrar solicitudes de modificación y permitir que un administrador las consulte y cambie su estado de pendiente a realizado, incluyendo la documentación necesaria para que el cliente pueda ejecutar y probar el sistema.

| Historia | Horas estimadas |
|---|---:|
| US16 - Iniciar Sesion | 4 h |
| US01 - Consultar servicios contratados | 4 h |
| US02 - Solicitar modificación de servicio | 6 h |
| US14 - Consultar Solicitudes y Estados | 4 h |
| US09 - Atender solicitud | 6 h |
| US24 - Demo funcional en Python y Flask | 6 h |
| US25 - Tutorial de instalación y ejecución | 4 h |
| US26 - Registro y seguimiento del trabajo del Sprint | 2 h |
| **Total estimado** | **36 h** |
| **Capacidad máxima** | **40 h** |
| **Margen disponible** | **4 h** |

### Criterio de selección del Sprint 1

El Sprint 1 prioriza el flujo mínimo necesario para demostrar el sistema de punta a punta: autenticación, consulta de servicios, creación de solicitudes, consulta y atención por parte del administrador, preparación de la demo en Python/Flask y documentación para que el cliente pueda ejecutarla de manera autónoma.
