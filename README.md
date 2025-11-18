# 📊 Sistema de Conciliación de Cargas

Sistema automatizado de generación y envío de informes de conciliación con integración GitHub + Power Automate.

## 🎯 Características

✅ **Generación Profesional de Informes**
- Informes Excel con formato ejecutivo
- KPIs automáticos (cumplimiento, pendientes, diferencias)
- Colores condicionales por estado
- Metadata completa para trazabilidad

✅ **Guardado Automático en Repositorio**
- Almacenamiento en `/informes/`
- Generación de metadata JSON
- HTML profesional para correos
- Limpieza automática (>10 días)

✅ **Envío Automatizado por Correo**
- Integración con Power Automate
- Correos corporativos sin problemas de spam
- HTML compatible con Outlook
- Lista de destinatarios autorizada

✅ **GitHub Actions**
- Detección automática de nuevos informes
- Limpieza programada de archivos antiguos
- Artefactos para integración
- Logs y reportes automáticos

---

## 🚀 Inicio Rápido

### 1. Clonar repositorio

```bash
git clone [tu-repositorio]
cd [carpeta-del-proyecto]
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar correos autorizados

Edita `correos_destino.txt`:

```text
# Lista de correos corporativos autorizados
juan.perez@empresa.com
maria.lopez@empresa.com
admin@empresa.com
```

### 4. Ejecutar aplicación

```bash
streamlit run app_conciliador.py
```

O usando el launcher:

```bash
python run.py
```

---

## 📖 Uso

### Generar Informe Simple (solo descarga)

1. Abre la aplicación en tu navegador
2. Pega datos de **Solicitud Inicial** (Ctrl+C desde ERP)
3. Pega datos de **Pedido Cargado** (Ctrl+C desde ERP)
4. Click en **"Generar Informe de Conciliación"**
5. Descarga el Excel generado

### Generar Informe con Envío Automático

1. Expande **"📧 Opciones de Envío por Correo"**
2. Activa checkbox **"Preparar informe para envío automático"**
3. Selecciona destinatario de la lista
4. Genera el informe normalmente
5. El sistema guardará automáticamente:
   - `Conciliacion_[Obra]_[Hoja]_[Fecha].xlsx`
   - `Conciliacion_[Obra]_[Hoja]_[Fecha]_metadata.json`
   - `Conciliacion_[Obra]_[Hoja]_[Fecha]_email.html`
6. Power Automate detectará y enviará el correo automáticamente

---

## 🗂️ Estructura del Proyecto

```
/workspace/
├── app_conciliador.py           # Aplicación principal Streamlit
├── run.py                       # Launcher para ejecutable
├── requirements.txt             # Dependencias Python
├── correos_destino.txt          # Lista de correos autorizados
├── informes/                    # Carpeta de informes generados
│   ├── .gitkeep
│   ├── Conciliacion_*.xlsx      # Archivos Excel
│   ├── *_metadata.json          # Metadata de cada informe
│   └── *_email.html             # HTML para correos
├── .github/workflows/           # GitHub Actions
│   ├── limpiar_informes.yml     # Limpieza automática
│   └── procesar_informes.yml    # Procesamiento de informes
├── GUIA_POWER_AUTOMATE.md       # Guía de integración
└── README.md                    # Este archivo
```

---

## 🔧 Configuración Avanzada

### Agregar nuevos correos autorizados

1. Abre `correos_destino.txt`
2. Agrega un correo por línea
3. Guarda el archivo
4. Los correos aparecerán automáticamente en la app

### Personalizar HTML del correo

Edita la función `generar_cuerpo_html_outlook()` en `app_conciliador.py`:

```python
def generar_cuerpo_html_outlook(informe_df, kpis, metadata):
    # Personaliza colores, textos, logos, etc.
    html = """
    <html>
    ...tu HTML personalizado...
    </html>
    """
    return html
```

**⚠️ Importante**: Usa solo estilos inline para compatibilidad con Outlook.

### Cambiar período de retención de archivos

Edita `.github/workflows/limpiar_informes.yml`:

```yaml
# Cambiar de 10 a N días
find informes -type f -mtime +10  # <- Cambiar este número
```

---

## 🤖 Integración con Power Automate

**Ver guía completa**: [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md)

### Resumen rápido:

1. **Crear Personal Access Token en GitHub**
   - Settings → Developer settings → Tokens
   - Permisos: `repo`, `workflow`

2. **Crear flujo en Power Automate**
   - Desencadenador: "When a file is created" (GitHub)
   - Ruta: `/informes/*_metadata.json`
   - Condición: `enviar_correo == true`

3. **Obtener archivos**
   - Leer metadata JSON
   - Obtener Excel desde ruta en metadata
   - Obtener HTML del correo

4. **Enviar correo**
   - Acción: "Send an email (V2)" (Outlook)
   - Destinatario: del metadata JSON
   - Cuerpo: HTML del archivo
   - Adjunto: Excel

---

## 📊 Formato del Informe Excel

El informe generado incluye:

### Sección 1: Encabezado
- Título del informe
- Nombre de la obra
- Número de hoja de carga
- Fecha de generación

### Sección 2: KPIs
- **Unidades Solicitadas**: Total de productos pedidos
- **Unidades Cargadas**: Total efectivamente cargado
- **% Cumplimiento General**: Porcentaje de cumplimiento
- **Artículos Pendientes**: Cantidad de productos sin cargar

### Sección 3: Tabla Detallada
Columnas:
- Código de artículo
- Nombre del producto
- Estado (Completo/Incompleto/Pendiente/Excedente)
- Cantidad Solicitada
- Cantidad Cargada
- Diferencia
- % Cumplimiento
- Pallets

**Estados posibles:**
- 🟢 **Completo**: Cantidad cargada = solicitada
- 🟡 **Incompleto**: Cargado menos de lo solicitado
- 🔴 **Pendiente**: Nada cargado
- 🔵 **Excedente**: Cargado más de lo solicitado
- ⚪ **No Solicitado**: Producto no estaba en solicitud

---

## 🔄 GitHub Actions

### Workflow: Procesar Informes

**Archivo**: `.github/workflows/procesar_informes.yml`

**Se activa cuando:**
- Se hace push a la carpeta `/informes/`

**Acciones:**
1. Lista todos los informes con `enviar_correo: true`
2. Crea resumen en GitHub Actions
3. Genera artefacto con informes pendientes
4. Facilita integración con Power Automate

### Workflow: Limpiar Informes

**Archivo**: `.github/workflows/limpiar_informes.yml`

**Se activa:**
- Diariamente a las 2 AM UTC
- Manualmente desde GitHub Actions
- Cuando hay cambios en `/informes/`

**Acciones:**
1. Busca archivos mayores a 10 días
2. Elimina Excel, JSON, HTML antiguos
3. Genera reporte de limpieza
4. Hace commit de los cambios

---

## 📋 Formato de Metadata JSON

Cada informe genera un archivo `*_metadata.json`:

```json
{
  "fecha_generacion": "2024-11-18T10:30:45.123456",
  "nombre_archivo": "Conciliacion_Obra123_HC456_20241118_103045.xlsx",
  "ruta_archivo": "informes/Conciliacion_Obra123_HC456_20241118_103045.xlsx",
  "obra": "Obra Principal Centro",
  "hoja_carga": "HC-2024-456",
  "correo_destino": "supervisor@empresa.com",
  "enviar_correo": true
}
```

Power Automate usa este archivo para:
- Saber qué informes enviar
- Obtener la ruta del Excel
- Conocer el destinatario
- Personalizar el asunto del correo

---

## 🔒 Seguridad

### Correos Autorizados
- Solo se pueden seleccionar correos de `correos_destino.txt`
- No se pueden enviar correos a dominios no autorizados
- Lista editable manualmente por administradores

### Personal Access Token (PAT)
- Necesario solo para Power Automate
- No se almacena en el repositorio
- Configurado directamente en Power Automate
- Permisos mínimos necesarios: `repo`, `workflow`

### Datos Sensibles
- Los informes se almacenan temporalmente (10 días)
- Limpieza automática de archivos antiguos
- Metadata no incluye información sensible más allá de nombres de obra

---

## 🐛 Solución de Problemas

### "No hay correos configurados"
**Solución**: Edita `correos_destino.txt` y agrega correos válidos (uno por línea)

### "Error al guardar el informe en el repositorio"
**Solución**: Verifica permisos de escritura en la carpeta `/informes/`

### Los correos no se envían automáticamente
**Solución**: 
1. Verifica que Power Automate esté configurado correctamente
2. Revisa logs en GitHub Actions
3. Verifica que el metadata tenga `"enviar_correo": true`
4. Consulta [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md)

### GitHub Actions no se ejecuta
**Solución**:
1. Verifica que los workflows estén en `.github/workflows/`
2. Haz push a la carpeta `informes/` para activar el workflow
3. Revisa permisos de GitHub Actions en configuración del repo

---

## 📈 Roadmap Futuro

Posibles mejoras:
- [ ] Soporte para múltiples destinatarios por informe
- [ ] Dashboard de métricas históricas
- [ ] Notificaciones por Slack/Discord
- [ ] Integración con base de datos
- [ ] API REST para consultas
- [ ] Generación de PDFs adicionales
- [ ] Firma digital de informes

---

## 👥 Contribuir

Para contribuir al proyecto:

1. Crea un branch para tu feature
2. Haz tus cambios
3. Crea un Pull Request con descripción clara

---

## 📄 Licencia

Este proyecto es de uso interno corporativo.

---

## 📞 Soporte

Para dudas o problemas:
1. Revisa esta documentación
2. Consulta [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md)
3. Revisa logs de GitHub Actions
4. Contacta al administrador del sistema

---

**Última actualización**: 2024-11-18  
**Versión**: 2.0 - Sistema Automatizado con Power Automate
