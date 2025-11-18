# Script actualizado para usarlo con python3 extraído y modificado de ExploitDB.
-------------
**Uso del script:**
```bash
usage: enum_users_p3.py [-h] -t TARGET [-p PORT] [-u USERNAME]

SSH User Enumeration by Leap Security (@LeapSecurity)

options:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        IP address of the target system
  -p PORT, --port PORT  Set port of SSH service
  -u USERNAME, --username USERNAME
                        Username to check for validity.
```
**Estructura basica:**

**Probar un usuario**
```bash
python3 enum_users_p3.py 172.17.0.2  --username <username>
```
**Probar multiples usuarios en una lista**
```bash
cat dic.txt | while read line; do python3 enum_users_p3.py 172.17.0.2 --username $line ;done
```
-----------------
# Enumeración de Usuarios en OpenSSH 7.7

## Descripción Detallada de la Vulnerabilidad

La vulnerabilidad de enumeración de usuarios en **OpenSSH 7.7** se basa en diferencias sutiles en las respuestas del servicio SSH al procesar intentos de autenticación. Aunque SSH está diseñado para ofrecer un comportamiento uniforme tanto para usuarios válidos como inválidos, ciertas versiones —incluyendo la 7.7— presentan **variaciones detectables**, lo que permite a un atacante identificar qué cuentas de usuario existen realmente en el sistema.

En sistemas vulnerables, cuando un cliente intenta autenticarse usando un nombre de usuario inexistente, OpenSSH responde con un conjunto de mensajes y tiempos de respuesta ligeramente diferentes respecto al intento de autenticación con un usuario legítimo. Estas diferencias se originan principalmente durante la fase de negociación de métodos de autenticación y están relacionadas con la lógica interna del módulo `auth2.c`, encargado del proceso de validación.

### ¿Por qué ocurre la vulneración de anonimato?

Cuando OpenSSH recibe un intento de autenticación, sigue un flujo que incluye:

1. **Validar si el usuario existe en el sistema.**
    
2. **Determinar qué métodos de autenticación tiene permitidos ese usuario.**
    
3. **Responder al cliente indicando qué métodos están disponibles.**
    

El problema aparece porque el servidor SSH, al validar la existencia del usuario, debe consultar varias fuentes del sistema (como `/etc/passwd`, PAM, LDAP, etc.). Durante esta validación, el servidor puede tardar más en responder si el usuario existe, o puede devolver un conjunto de métodos disponible diferente.

Por ejemplo:

- Para un usuario inexistente, el servidor puede responder inmediatamente con un mensaje de rechazo estándar.
    
- Para un usuario existente, el servidor continúa con pasos posteriores de autenticación, incluso si la contraseña enviada es incorrecta. Esto genera un **tiempo de respuesta distinto**, o un **paquete SSH ligeramente diferente** (por ejemplo: incluir `keyboard-interactive`, `password`, `publickey` como métodos válidos).
    

Estos patrones pueden ser analizados por un atacante mediante herramientas automatizadas o scripts que miden milisegundos de diferencia o comparan los mensajes de los paquetes SSH. Esta técnica es conocida como **side-channel enumeration**.

### Impacto de la vulnerabilidad

La enumeración de usuarios no permite un acceso directo al sistema, pero sí proporciona información crítica que puede ser usada en ataques posteriores, tales como:

- **Ataques de fuerza bruta más eficientes.**  
    Saber qué usuarios existen reduce drásticamente el espacio de búsqueda.
    
- **Ataques dirigidos a cuentas específicas** (por ejemplo: `root`, `admin`, `backup`, `developer`, etc.).
    
- **Reconocimiento previo a ataques más avanzados**, como exploiting de servicios específicos del usuario.
    

En entornos corporativos, la revelación de nombres de usuarios puede permitir a un atacante descubrir convenciones internas (como iniciales, nombres abreviados o numeraciones), lo que facilita ataques contra otros sistemas dentro de la misma organización.

### Cómo se explota

Los atacantes pueden usar herramientas o scripts que:

1. Intentan autenticarse repetidamente con diferentes nombres de usuario.
    
2. Registran el **tiempo entre solicitud y respuesta**.
    
3. Analizan qué métodos de autenticación fueron ofrecidos por el servidor.
    
4. Comparan los resultados para identificar los usuarios que realmente existen.
    

Ejemplos de herramientas conocidas para este tipo de ataque incluyen:

- `ssh-user-enum`
    
- `hydra` con módulo SSH personalizado
    
- Scripts en Python que analizan tiempos de respuesta usando `paramiko`
    

Con suficientes mediciones, la probabilidad de falsos positivos es extremadamente baja, especialmente si la latencia en la red es estable.

