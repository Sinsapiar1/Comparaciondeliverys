# 🔗 Conectar Power Automate con GitHub - Paso a Paso Visual

## 📸 Según las imágenes que compartiste

Este documento te guía para conectar Power Automate con tu repositorio GitHub de forma específica para tu entorno corporativo.

---

## 🎯 MÉTODO 1: Usando GitHub Connector (Recomendado)

### Paso 1: Crear Personal Access Token en GitHub

1. Ve a GitHub.com e inicia sesión
2. Click en tu foto de perfil (arriba derecha) → **Settings**
3. Scroll down → **Developer settings** (última opción del menú izquierdo)
4. Click en **Personal access tokens** → **Tokens (classic)**
5. Click en **"Generate new token"** → **"Generate new token (classic)"**

#### Configuración del Token:

| Campo | Valor |
|-------|-------|
| **Note** | `Power Automate - Informes Conciliacion` |
| **Expiration** | 90 days (o la duración que prefieras) |
| **Scopes (permisos)** | ✅ Marca estos: |
| | ☑️ **repo** (todos los sub-permisos) |
| | ☑️ **workflow** |
| | ☑️ **admin:repo_hook** (si vas a usar webhooks) |

6. Scroll down y click **"Generate token"**
7. **⚠️ MUY IMPORTANTE**: Copia el token AHORA (ejemplo: `ghp_xxxxxxxxxxxxxxxxxxxx`)
   - Guárdalo en un lugar seguro (Notepad, password manager)
   - Solo se muestra una vez

---

### Paso 2: Crear Flujo en Power Automate

#### 2.1 Acceder a Power Automate

1. Ve a: **https://make.powerautomate.com**
2. Inicia sesión con tu cuenta corporativa Microsoft 365
3. Asegúrate de estar en el entorno correcto (arriba derecha)

#### 2.2 Crear Nuevo Flujo

1. Click en **"+ Create"** (o **"+ Crear"** en español)
2. Selecciona **"Automated cloud flow"** (o **"Flujo de nube automatizado"**)
3. Nombre del flujo: `Enviar Informes de Conciliación`
4. En "Choose your flow's trigger":
   - Busca: `GitHub`
   - **NO selecciones nada aún**, click **"Skip"** o **"Create"**

---

### Paso 3: Configurar el Desencadenador (Trigger)

#### 3.1 Agregar Trigger de GitHub

1. En el canvas, click en **"+ New step"**
2. Busca: `GitHub`
3. Si GitHub aparece en conectores:
   - Selecciona: **"GitHub - List repository issues"** o cualquier acción de GitHub
   - Esto te permitirá crear la conexión primero

#### 3.2 Crear Conexión a GitHub

Cuando te pida conectar:

1. **Connection Name**: `GitHub - Informes`
2. **Authentication Type**: `Personal Access Token` (PAT)
3. **Token**: Pega tu token de GitHub (el que copiaste antes)
4. Click **"Create"** o **"Crear"**

✅ **Conexión establecida**

---

### Paso 4: Configurar Webhook de GitHub (Trigger Real)

#### Opción A: Using Recurrence (Polling - Más simple)

Si no puedes configurar webhooks, usa este método:

1. **Elimina** la acción de GitHub que agregaste
2. Click **"+ New step"**
3. Busca: `Recurrence`
4. Configura:
   - **Interval**: `5`
   - **Frequency**: `Minute`

#### Opción B: Using HTTP Request (Webhook - Más eficiente)

1. En GitHub, ve a tu repositorio
2. **Settings** → **Webhooks** → **Add webhook**
3. Configuración:
   - **Payload URL**: (lo obtendrás de Power Automate después)
   - **Content type**: `application/json`
   - **Which events**: Just the **push** event
   - **Active**: ✅ Marcado

En Power Automate:
1. Elimina la acción anterior
2. **+ New step** → Busca: `When a HTTP request is received`
3. Guarda el flujo (esto generará la URL)
4. Copia la **HTTP POST URL** que aparece
5. Pega esa URL en GitHub Webhook (Payload URL)

---

## 🔄 PASO 5: Obtener Archivos del Repositorio

### 5.1 Listar Archivos de la Carpeta Informes

**Método 1: Usando GitHub Connector (Si tienes el conector)**

1. **+ New step** → Busca: `GitHub - Get file content`
2. Configuración:
   - **Repository**: Selecciona tu repositorio de la lista
   - **Branch**: `main`
   - **File path**: `informes/` (dejar así por ahora)

**Método 2: Usando HTTP Request (Universal)**

1. **+ New step** → Busca: `HTTP - HTTP`
2. Configuración:

```json
Method: GET
URI: https://api.github.com/repos/TU_USUARIO/TU_REPO/contents/informes
Headers:
{
  "Authorization": "token TU_PAT_AQUI",
  "Accept": "application/vnd.github.v3+json",
  "User-Agent": "PowerAutomate"
}
```

Reemplaza:
- `TU_USUARIO`: Tu usuario de GitHub
- `TU_REPO`: Nombre de tu repositorio
- `TU_PAT_AQUI`: Tu Personal Access Token

---

### 5.2 Parsear Lista de Archivos

1. **+ New step** → Busca: `Parse JSON`
2. **Content**: Output del paso anterior
3. **Schema**: Click en **"Generate from sample"**
4. Pega este JSON de ejemplo:

```json
[
  {
    "name": "Conciliacion_Obra_HC123_20241118_153045_metadata.json",
    "path": "informes/Conciliacion_Obra_HC123_20241118_153045_metadata.json",
    "sha": "abc123",
    "size": 256,
    "url": "https://api.github.com/repos/user/repo/contents/informes/file.json",
    "html_url": "https://github.com/user/repo/blob/main/informes/file.json",
    "git_url": "https://api.github.com/repos/user/repo/git/blobs/abc123",
    "download_url": "https://raw.githubusercontent.com/user/repo/main/informes/file.json",
    "type": "file"
  }
]
```

---

### 5.3 Filtrar Solo Metadata JSON con Correo

1. **+ New step** → Busca: `Filter array`
2. **From**: Output del Parse JSON (el array de archivos)
3. **Condición**: 
   - Campo: `name` (del array)
   - Operador: `ends with`
   - Valor: `_metadata.json`

---

### 5.4 Loop por Cada Archivo Metadata

1. **+ New step** → Busca: `Apply to each`
2. **Select an output from previous steps**: Selecciona el output del **Filter array**

Dentro del loop:

#### A. Obtener Contenido del Metadata JSON

**+ Add an action** → HTTP Request:

```json
Method: GET
URI: @{items('Apply_to_each')?['download_url']}
Headers:
{
  "Authorization": "token TU_PAT",
  "Accept": "application/json"
}
```

#### B. Parsear Metadata JSON

**+ Add an action** → Parse JSON:

- **Content**: Body del HTTP anterior
- **Schema**:

```json
{
  "type": "object",
  "properties": {
    "fecha_generacion": {"type": "string"},
    "nombre_archivo": {"type": "string"},
    "ruta_archivo": {"type": "string"},
    "obra": {"type": "string"},
    "hoja_carga": {"type": "string"},
    "correo_destino": {"type": ["string", "null"]},
    "enviar_correo": {"type": "boolean"}
  }
}
```

#### C. Condición: Solo si debe enviar correo

**+ Add an action** → Condition:

- **Value**: `@{body('Parse_JSON_Metadata')?['enviar_correo']}`
- **is equal to**: `true`

---

### 5.5 Obtener Archivo Excel (Dentro de "If yes")

**+ Add an action** → HTTP Request:

```json
Method: GET
URI: https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/@{body('Parse_JSON_Metadata')?['ruta_archivo']}
Headers:
{
  "Authorization": "token TU_PAT"
}
```

**Importante**: Después de esta acción:

**+ Add an action** → `Compose`:
- **Inputs**: `@base64(body('HTTP_Get_Excel'))`

Esto convierte el Excel a Base64 para el adjunto.

---

### 5.6 Obtener HTML del Correo

**+ Add an action** → HTTP Request:

```json
Method: GET
URI: https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/informes/@{replace(body('Parse_JSON_Metadata')?['nombre_archivo'], '.xlsx', '_email.html')}
Headers:
{
  "Authorization": "token TU_PAT",
  "Accept": "text/html"
}
```

---

## 📧 PASO 6: Enviar Correo con Outlook

**+ Add an action** → Busca: `Send an email (V2)` (Office 365 Outlook)

### Configuración del Correo:

| Campo | Valor (usar Dynamic Content) |
|-------|------------------------------|
| **To** | `@{body('Parse_JSON_Metadata')?['correo_destino']}` |
| **Subject** | `Informe de Conciliación - @{body('Parse_JSON_Metadata')?['obra']} - HC @{body('Parse_JSON_Metadata')?['hoja_carga']}` |
| **Body** | `@{body('HTTP_Get_HTML')}` |
| **Is HTML** | `Yes` (marcar checkbox) |

### Agregar Adjunto:

1. Click en **"Show advanced options"**
2. En **"Attachments"**, click **"Switch to input entire array"**
3. Pega esto:

```json
[
  {
    "Name": "@{body('Parse_JSON_Metadata')?['nombre_archivo']}",
    "ContentBytes": "@{outputs('Compose_Excel_Base64')}"
  }
]
```

---

## ✅ PASO 7: Guardar y Probar

### 7.1 Guardar el Flujo

1. Click en **"Save"** (arriba derecha)
2. Espera confirmación de guardado

### 7.2 Probar el Flujo

**Opción A: Test Manual**

1. Click en **"Test"** (arriba derecha)
2. Selecciona **"Manually"**
3. Click **"Test"**
4. Genera un informe desde Streamlit con opción de correo
5. Espera 5 minutos (si usas Recurrence)
6. Verifica que el flujo se ejecute

**Opción B: Test con Datos de Prueba**

1. Click en **"Test"**
2. Selecciona **"Automatically"** o **"With data from previous runs"**
3. Si no hay datos previos, haz push manualmente a `/informes/`

### 7.3 Verificar Ejecución

1. Ve a **"28-day run history"** (en el flujo)
2. Verifica que aparezcan ejecuciones
3. Click en una ejecución para ver detalles
4. Si hay errores:
   - Lee el mensaje de error
   - Verifica las URLs y tokens
   - Verifica que los archivos existan en GitHub

---

## 🎨 PASO 8: Personalización Avanzada (Opcional)

### Agregar Logo Corporativo

En el HTML del correo (archivo `app_conciliador.py`):

```python
# En la función generar_cuerpo_html_outlook()
html = f"""
<div style="...">
    <img src="https://tuempresa.com/logo.png" style="max-width: 200px; margin-bottom: 20px;">
    <h1>Informe de Conciliación</h1>
</div>
"""
```

### Agregar Múltiples Destinatarios

En la metadata JSON, cambia a array:

```json
"correos_destino": ["correo1@empresa.com", "correo2@empresa.com"]
```

En Power Automate (Outlook):
- **To**: `@{join(body('Parse_JSON_Metadata')?['correos_destino'], ';')}`

### Agregar Copia (CC) Fija

En Outlook action:
- **CC**: `admin@empresa.com;supervisor@empresa.com`

---

## 🔒 Seguridad - Mejores Prácticas

### Proteger el PAT

❌ **NUNCA hagas esto:**
- Compartir el PAT por correo
- Guardarlo en texto plano compartido
- Subirlo a un repositorio público
- Dejarlo en un post-it

✅ **SÍ haz esto:**
- Guardar en password manager (1Password, LastPass, etc.)
- Renovar antes de expiración (90 días)
- Usar permisos mínimos necesarios
- Revocar tokens viejos

### En Power Automate

✅ El PAT se guarda encriptado en la conexión
✅ Solo tú y admins de Power Platform pueden verlo
✅ Usa variables de entorno para producción

---

## 📊 Monitoreo y Logs

### Ver Historial de Ejecuciones

1. En Power Automate, abre tu flujo
2. Click en **"28-day run history"**
3. Verás todas las ejecuciones con estado:
   - ✅ **Succeeded**: Correcto
   - ⚠️ **Failed**: Error (click para ver detalles)
   - 🔄 **Running**: En proceso

### Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `401 Unauthorized` | Token inválido | Verificar PAT, regenerar si expiró |
| `404 Not Found` | Archivo no existe | Verificar ruta del archivo en GitHub |
| `403 Forbidden` | Sin permisos | Verificar scopes del PAT (`repo`, `workflow`) |
| `Rate limit exceeded` | Muchas peticiones | Aumentar intervalo de Recurrence a 10-15 min |
| `Invalid JSON` | JSON malformado | Verificar que el metadata.json sea válido |

---

## 🎯 Diagrama de Flujo Completo

```
┌──────────────────────────────────────┐
│ 1. TRIGGER (Cada 5 minutos)         │
│    - Recurrence o HTTP Request       │
└─────────────┬────────────────────────┘
              │
              ↓
┌──────────────────────────────────────┐
│ 2. GET - Listar archivos /informes/ │
│    - HTTP Request a GitHub API       │
└─────────────┬────────────────────────┘
              │
              ↓
┌──────────────────────────────────────┐
│ 3. PARSE JSON - Lista de archivos   │
└─────────────┬────────────────────────┘
              │
              ↓
┌──────────────────────────────────────┐
│ 4. FILTER - Solo *_metadata.json    │
└─────────────┬────────────────────────┘
              │
              ↓
┌──────────────────────────────────────┐
│ 5. APPLY TO EACH - Loop archivos    │
│    ┌───────────────────────────┐    │
│    │ 5.1 GET Metadata JSON     │    │
│    │ 5.2 PARSE Metadata        │    │
│    │ 5.3 CONDITION             │    │
│    │     enviar_correo == true │    │
│    │       ↓ IF YES            │    │
│    │     5.4 GET Excel         │    │
│    │     5.5 GET HTML          │    │
│    │     5.6 SEND EMAIL        │    │
│    └───────────────────────────┘    │
└──────────────────────────────────────┘
```

---

## 🆘 Soporte y Ayuda

### Recursos Oficiales

- **Power Automate Docs**: https://learn.microsoft.com/en-us/power-automate/
- **GitHub API Docs**: https://docs.github.com/en/rest
- **Community Forums**: https://powerusers.microsoft.com/t5/Power-Automate-Community/ct-p/MPACommunity

### Troubleshooting Paso a Paso

1. **Verificar GitHub**:
   ```bash
   # En terminal, probar la API
   curl -H "Authorization: token TU_PAT" \
        https://api.github.com/repos/TU_USUARIO/TU_REPO/contents/informes
   ```

2. **Verificar Archivos**:
   - Ve a GitHub.com
   - Navega a tu repositorio
   - Entra a carpeta `/informes/`
   - Verifica que existan archivos `*_metadata.json`

3. **Verificar Metadata**:
   - Abre un `*_metadata.json` en GitHub
   - Verifica que tenga `"enviar_correo": true`
   - Verifica que `"correo_destino"` no sea null

4. **Test Power Automate**:
   - Crea un flujo simple solo con GET a GitHub
   - Verifica que devuelva datos
   - Agrega pasos incrementalmente

---

## ✨ Resultado Final Esperado

Cuando todo funcione correctamente:

1. ✅ Usuario genera informe en Streamlit
2. ✅ Marca "Enviar por correo" y selecciona destinatario
3. ✅ Click en "Generar Informe"
4. ✅ Archivos se guardan en `/informes/` del repo
5. ✅ Power Automate (cada 5 min) revisa carpeta
6. ✅ Detecta nuevo metadata con `enviar_correo: true`
7. ✅ Obtiene Excel y HTML
8. ✅ Envía correo profesional con adjunto
9. ✅ Destinatario recibe:
   - 📧 Correo HTML hermoso
   - 📎 Excel profesional adjunto
   - 🎨 Formato perfecto en Outlook
   - ✅ Sin problemas de spam

**Tiempo total de entrega**: 5-10 minutos desde generación

---

## 🎉 ¡Listo para Producción!

Tu sistema está completamente configurado y listo para uso corporativo.

**¿Preguntas?**
- Consulta [`README.md`](./README.md) para uso general
- Consulta [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md) para más detalles
- Abre `EJEMPLO_CORREO.html` para ver vista previa

---

**Última actualización**: 2024-11-18  
**Versión**: 2.0 - Sistema Completo Automatizado
