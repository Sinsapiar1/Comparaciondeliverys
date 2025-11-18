# 📧 Guía Completa: Conectar Power Automate con GitHub

## 🎯 Objetivo
Configurar Power Automate para que detecte automáticamente nuevos informes en tu repositorio GitHub y los envíe por correo corporativo con formato profesional.

---

## 📋 Requisitos Previos

✅ Cuenta de Power Automate (Microsoft 365 corporativo)  
✅ Acceso al repositorio GitHub  
✅ Permisos para crear flujos automatizados

---

## 🔧 PASO 1: Preparar GitHub

### 1.1 Crear Personal Access Token (PAT)

1. Ve a GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click en **"Generate new token"** → **"Generate new token (classic)"**
3. Configuración del token:
   - **Note**: `Power Automate - Informes Conciliacion`
   - **Expiration**: Selecciona duración (recomendado: 90 días)
   - **Scopes** (permisos):
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
4. Click **"Generate token"**
5. **⚠️ IMPORTANTE**: Copia el token **AHORA** (solo se muestra una vez)
6. Guárdalo en un lugar seguro (lo necesitarás en Power Automate)

### 1.2 Verificar estructura del repositorio

Tu repositorio debe tener esta estructura:

```
/workspace/
├── informes/                    # Carpeta con informes generados
│   ├── Conciliacion_*.xlsx      # Archivos Excel
│   ├── *_metadata.json          # Metadata de cada informe
│   └── *_email.html             # HTML para correo
├── correos_destino.txt          # Lista de correos autorizados
├── app_conciliador.py           # Aplicación Streamlit
└── .github/workflows/           # GitHub Actions
    ├── limpiar_informes.yml
    └── procesar_informes.yml
```

---

## 🚀 PASO 2: Crear Flujo en Power Automate

### 2.1 Crear nuevo flujo automatizado

1. Ve a **Power Automate** → https://make.powerautomate.com
2. Click en **"+ Crear"** → **"Flujo de nube automatizado"**
3. Nombre: `Enviar Informes de Conciliación desde GitHub`
4. Desencadenador: Buscar **"GitHub"** → Seleccionar **"Cuando se ejecuta un flujo de trabajo"**
   - Si no aparece GitHub, usa **"Recurrence"** (programación) o **"HTTP Request"**

### 2.2 Configuración del Desencadenador

**Opción A: Usando GitHub Connector (Recomendado)**

1. Agregar acción: **"GitHub - Cuando se crea un archivo"**
2. Configuración:
   - **Connection**: Crear nueva conexión
   - **Método de autenticación**: Personal Access Token
   - **Token**: Pega tu PAT de GitHub
   - **Repository**: Selecciona tu repositorio
   - **Branch**: `main`
   - **Folder path**: `/informes`
   - **File name filter**: `*_metadata.json`

**Opción B: Usando HTTP (Si no tienes GitHub Connector)**

1. Agregar acción: **"Recurrence"** (Schedule)
   - **Interval**: 5
   - **Frequency**: Minute
2. Agregar acción: **"HTTP - HTTP"**
   - **Method**: GET
   - **URI**: `https://api.github.com/repos/TU_USUARIO/TU_REPO/contents/informes`
   - **Headers**:
     ```json
     {
       "Authorization": "Bearer TU_PAT_AQUI",
       "Accept": "application/vnd.github.v3+json"
     }
     ```

---

## 🔄 PASO 3: Procesar Archivos JSON (Metadata)

### 3.1 Obtener contenido del metadata JSON

Agregar acción: **"GitHub - Get file content"**
- **Repository**: Tu repositorio
- **Branch**: `main`
- **File path**: `informes/` + (nombre del archivo metadata detectado)

### 3.2 Parsear JSON

Agregar acción: **"Data Operation - Parse JSON"**
- **Content**: Output del paso anterior (contenido del archivo)
- **Schema**: Usa este esquema:

```json
{
  "type": "object",
  "properties": {
    "fecha_generacion": {
      "type": "string"
    },
    "nombre_archivo": {
      "type": "string"
    },
    "ruta_archivo": {
      "type": "string"
    },
    "obra": {
      "type": "string"
    },
    "hoja_carga": {
      "type": "string"
    },
    "correo_destino": {
      "type": "string"
    },
    "enviar_correo": {
      "type": "boolean"
    }
  }
}
```

### 3.3 Agregar condición

Agregar acción: **"Control - Condition"**
- **Condición**: `enviar_correo` (del JSON) **es igual a** `true`

---

## 📎 PASO 4: Obtener Archivos del Repositorio

### 4.1 Obtener archivo Excel

Dentro del **"If yes"** de la condición:

Agregar acción: **"GitHub - Get file content"**
- **Repository**: Tu repositorio
- **Branch**: `main`
- **File path**: `@{body('Parse_JSON')?['ruta_archivo']}`
- **Content format**: Binary

### 4.2 Obtener HTML del correo

Agregar acción: **"GitHub - Get file content"**
- **Repository**: Tu repositorio
- **Branch**: `main`
- **File path**: `informes/` + (nombre del archivo pero reemplazar `.xlsx` por `_email.html`)
- **Content format**: Text

---

## 📧 PASO 5: Enviar Correo con Outlook

### 5.1 Configurar acción de Outlook

Agregar acción: **"Office 365 Outlook - Send an email (V2)"**

Configuración:
- **To**: `@{body('Parse_JSON')?['correo_destino']}`
- **Subject**: `Informe de Conciliación - @{body('Parse_JSON')?['obra']} - Hoja @{body('Parse_JSON')?['hoja_carga']}`
- **Body**: `@{body('Get_file_content_HTML')?['content']}`
- **Is HTML**: `Yes`
- **Attachments**: Click en **"Add new parameter"** → **"Attachments"**
  - **Name**: `@{body('Parse_JSON')?['nombre_archivo']}`
  - **Content**: `@{body('Get_file_content_Excel')?['content']}`

### 5.2 Configuración adicional (opcional)

- **Importance**: High (si es urgente)
- **CC**: Puedes agregar copias
- **From**: Tu correo corporativo (si tienes permisos de delegación)

---

## ✅ PASO 6: Agregar Notificación de Éxito

Agregar acción: **"HTTP - HTTP"** (opcional, para logging)
- **Method**: POST
- **URI**: Webhook de tu elección (Discord, Slack, etc.)
- **Body**: 
```json
{
  "mensaje": "✅ Informe enviado exitosamente",
  "obra": "@{body('Parse_JSON')?['obra']}",
  "destinatario": "@{body('Parse_JSON')?['correo_destino']}",
  "fecha": "@{utcNow()}"
}
```

---

## 🧪 PASO 7: Probar el Flujo

### 7.1 Test manual

1. En Power Automate, click **"Test"** → **"Manual"**
2. Genera un informe desde la app Streamlit con la opción de correo activada
3. Verifica que el flujo se ejecute automáticamente

### 7.2 Verificación

✅ El metadata JSON tiene `"enviar_correo": true`  
✅ El archivo Excel existe en `/informes/`  
✅ El HTML existe en `/informes/`  
✅ El correo destino es válido  
✅ El flujo se ejecuta sin errores

---

## 🎨 PASO 8: Personalizar HTML del Correo (Opcional)

Si quieres personalizar el cuerpo del correo, edita la función `generar_cuerpo_html_outlook()` en `app_conciliador.py`.

**Consideraciones para Outlook:**
- ✅ Usa estilos inline (no `<style>` tags)
- ✅ Usa tablas para layout (no CSS Grid/Flexbox)
- ✅ Colores seguros: hexadecimales básicos
- ❌ Evita: CSS avanzado, JavaScript, `<iframe>`, `<video>`
- ❌ Evita: `position: absolute`, `transform`, `animation`

---

## 🔒 Seguridad y Buenas Prácticas

### Protección del PAT
- ⚠️ **Nunca** compartas tu Personal Access Token
- 🔄 Renueva el token antes de que expire
- 🗑️ Revoca tokens viejos que ya no uses

### Gestión de correos
- ✅ Usa solo correos corporativos autorizados
- ✅ Mantén actualizado `correos_destino.txt`
- ✅ Verifica destinatarios antes de enviar

### Monitoreo
- 📊 Revisa los logs de GitHub Actions regularmente
- 📧 Verifica que los correos lleguen correctamente
- 🧹 La limpieza automática elimina archivos >10 días

---

## 🐛 Solución de Problemas

### Error: "No se puede conectar a GitHub"
**Solución**: Verifica que tu PAT tenga los permisos correctos (`repo`, `workflow`)

### Error: "Archivo no encontrado"
**Solución**: Verifica que los archivos se generen correctamente en `/informes/`

### Error: "Correo no enviado"
**Solución**: 
- Verifica que el destinatario sea un correo válido
- Verifica que tengas permisos de Outlook en Power Automate
- Revisa los logs del flujo en Power Automate

### Los correos llegan sin formato
**Solución**: Asegúrate de marcar **"Is HTML": Yes** en la acción de Outlook

---

## 📞 Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────┐
│  1. STREAMLIT APP                               │
│  Usuario genera informe con opción de correo   │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  2. GITHUB REPOSITORY                           │
│  - Guarda Excel en /informes/                   │
│  - Guarda metadata.json                         │
│  - Guarda HTML del correo                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  3. GITHUB ACTIONS                              │
│  - Detecta nuevos archivos                      │
│  - Crea artefacto                               │
│  - Limpia archivos antiguos (>10 días)         │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  4. POWER AUTOMATE                              │
│  - Detecta metadata con enviar_correo=true     │
│  - Lee archivos desde GitHub                    │
│  - Obtiene Excel + HTML                         │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  5. OUTLOOK / EMAIL                             │
│  - Envía correo corporativo                     │
│  - Cuerpo HTML profesional                      │
│  - Excel adjunto                                │
│  ✅ Llegada garantizada (dominio corporativo)   │
└─────────────────────────────────────────────────┘
```

---

## ✨ Resultado Final

Cuando todo esté configurado:

1. ✅ Usuario genera informe en Streamlit
2. ✅ Marca checkbox "Preparar para envío por correo"
3. ✅ Selecciona destinatario de la lista
4. ✅ Click en "Generar Informe"
5. ✅ Archivo se guarda en repositorio automáticamente
6. ✅ GitHub Actions procesa el archivo
7. ✅ Power Automate detecta el nuevo informe
8. ✅ Correo profesional se envía automáticamente
9. ✅ Destinatario recibe:
   - 📧 Correo con formato HTML elegante
   - 📎 Excel adjunto con datos completos
   - 🎨 Colores y estilos profesionales
   - ✅ Sin problemas de spam/filtros

---

## 📚 Recursos Adicionales

- [Documentación Power Automate](https://learn.microsoft.com/es-es/power-automate/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [HTML Email Best Practices](https://www.campaignmonitor.com/css/)

---

**🎉 ¡Listo! Tu sistema de informes automatizado está configurado.**

¿Preguntas? Consulta los logs de GitHub Actions o el historial de ejecución en Power Automate.
