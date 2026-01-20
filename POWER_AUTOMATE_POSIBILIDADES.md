# Integracion con Power Automate para envio de informes

Este documento resume opciones seguras para integrar la salida de la app
con Power Automate (cuenta corporativa) y enviar correos con adjunto Excel
y cuerpo HTML compatible con Outlook. No implica cambios en el codigo;
solo describe posibilidades y una propuesta profesional de implementacion.

---

## Objetivo

- Generar un informe (Excel + HTML) desde la app.
- Crear metadata JSON con datos necesarios para el flujo.
- Disparar un flujo en Power Automate de forma segura.
- Enviar correo corporativo con adjunto Excel y cuerpo HTML responsivo.

---

## Opciones de integracion (seguras)

### Opcion A: GitHub Connector + archivo en repositorio
**Idea:** guardar Excel/HTML/JSON en /informes y usar Power Automate con
GitHub Connector o HTTP + PAT.

**Pros**
- Rapido de implementar (ya existe el flujo base).
- No requiere infraestructura adicional.

**Contras**
- Guardar archivos en repositorio puede ser sensible.
- Depende de PAT y permisos de repo.

**Seguridad recomendada**
- Usar token fine-grained o GitHub App con permisos minimos.
- Restringir acceso al repo y activar retencion corta.

---

### Opcion B: SharePoint / OneDrive for Business
**Idea:** guardar archivos en una biblioteca corporativa y usar
Power Automate con disparador "When a file is created".

**Pros**
- Mejor alineado con entorno corporativo Microsoft.
- Control de acceso (permisos y auditoria).
- No expone archivos en GitHub.

**Contras**
- Requiere modificar la app para guardar en SharePoint/OneDrive.

**Seguridad recomendada**
- Cuenta de servicio con permisos minimos.
- Biblioteca dedicada solo a informes.

---

### Opcion C: HTTP Trigger + almacenamiento externo
**Idea:** la app llama a un flujo HTTP de Power Automate con metadata.
El archivo se guarda en SharePoint/OneDrive/Azure Blob mediante el flujo.

**Pros**
- No se requiere acceso a GitHub desde Power Automate.
- Control total del flujo y registro centralizado.

**Contras**
- Requiere endpoint HTTP protegido.
- La app debe enviar el archivo (o un link seguro) al flujo.

**Seguridad recomendada**
- URL con clave secreta y/o Azure AD.
- Validacion de firma (HMAC) en el flujo.

---

### Opcion D: Power Automate Desktop (RPA)
**Idea:** flujo local que monitorea una carpeta en PC/servidor y envia.

**Pros**
- Simple si no hay conectores disponibles.
- Control total en entorno local.

**Contras**
- Menos escalable, depende de PC encendido.
- Menor robustez en produccion.

---

## Metadata JSON sugerida (profesional)

Se recomienda ampliar la metadata para que el flujo tenga todo lo necesario
sin volver a calcular nada. Ejemplo:

```json
{
  "version": "1.0",
  "fecha_generacion": "2026-01-20T10:30:45.123456",
  "obra": "Caribbean Building Corp",
  "hoja_carga": "1000707875",
  "usuario_origen": "usuario@empresa.com",
  "correo_destino": "destino@empresa.com",
  "enviar_correo": true,
  "kpis": {
    "total_solicitado": 1234,
    "total_cargado": 1200,
    "cumplimiento_general": 0.9724,
    "articulos_pendientes": 4
  },
  "archivos": {
    "excel": "informes/Conciliacion_Obra_HC_20260120.xlsx",
    "html": "informes/Conciliacion_Obra_HC_20260120_email.html"
  },
  "resumen": {
    "pendientes": 4,
    "incompletos": 2,
    "excedentes": 1,
    "sustituciones": 1
  }
}
```

---

## HTML compatible con Outlook (recomendaciones)

- Usar tablas para layout.
- Estilos inline (no CSS externo).
- Colores basicos, sin gradientes complejos.
- Evitar flexbox, grid y JS en el HTML final.
- Tamaños de fuente legibles (12-16px).

---

## Propuesta profesional (recomendada)

**Recomendacion:** Opcion B (SharePoint/OneDrive for Business).

**Flujo sugerido:**
1. App genera Excel + HTML.
2. App guarda archivos en biblioteca corporativa.
3. Power Automate dispara por "file created".
4. Flujo lee metadata JSON.
5. Envia correo con:
   - Subject: Obra + Hoja de Carga.
   - Body: HTML del informe (inline).
   - Attachment: Excel.
6. Limpieza automatica (retencion 7/10 dias).

**Ventajas**
- Seguridad corporativa.
- Control de acceso y auditoria.
- Sin dependencias de GitHub en produccion.

---

## Siguiente paso (si se decide avanzar)

1. Definir opcion elegida.
2. Ajustar el JSON de metadata.
3. Ajustar almacenamiento (GitHub o SharePoint).
4. Implementar el flujo en Power Automate.
5. Probar end-to-end con un informe real.

