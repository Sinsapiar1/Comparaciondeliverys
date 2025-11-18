# ⚡ Inicio Rápido - 5 Minutos

## 🎯 Para usar la aplicación AHORA MISMO

### 1️⃣ Ejecutar la app (30 segundos)

```bash
streamlit run app_conciliador.py
```

O doble click en el ejecutable si lo tienes compilado.

---

### 2️⃣ Generar un informe simple (2 minutos)

1. Copia datos del ERP (Ctrl+C)
2. Pega en "Solicitud Inicial" (Ctrl+V)
3. Copia datos de pedido cargado (Ctrl+C)
4. Pega en "Pedido Cargado" (Ctrl+V)
5. Click en **"Generar Informe"**
6. Descarga el Excel

✅ **LISTO** - Ya tienes tu informe profesional

---

### 3️⃣ Configurar envío automático (2 minutos)

#### Paso A: Agregar correos autorizados

Edita `correos_destino.txt`:

```text
# Reemplaza estos correos de ejemplo con los reales
supervisor@tuempresa.com
jefe.obra@tuempresa.com
admin@tuempresa.com
```

Guarda el archivo.

#### Paso B: Generar informe con envío automático

1. Expande **"📧 Opciones de Envío por Correo"**
2. ✅ Activa el checkbox
3. Selecciona destinatario
4. Genera el informe normalmente

✅ **LISTO** - El informe se guardó en `/informes/` listo para Power Automate

---

## 🤖 Para conectar Power Automate (10-15 minutos)

### Quick Steps:

1. **GitHub**: Crear Personal Access Token
   - GitHub → Settings → Developer settings → Tokens
   - Permisos: `repo` + `workflow`
   - Copiar token

2. **Power Automate**: Crear flujo
   - Ir a: https://make.powerautomate.com
   - Crear → Flujo automatizado
   - Desencadenador: "GitHub - When file is created"
   - Carpeta: `/informes/`
   - Filtro: `*_metadata.json`

3. **Configurar acciones**:
   - Leer JSON
   - Condición: `enviar_correo == true`
   - Obtener Excel
   - Obtener HTML
   - Enviar correo (Outlook)

### Guía completa:

👉 Ver [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md) con pasos detallados y screenshots

---

## 📂 Estructura de archivos generados

Cuando generas un informe, se crean 3 archivos en `/informes/`:

```
informes/
├── Conciliacion_Obra_HC123_20241118_153045.xlsx           # Excel profesional
├── Conciliacion_Obra_HC123_20241118_153045_metadata.json # Metadata para Power Automate  
└── Conciliacion_Obra_HC123_20241118_153045_email.html    # HTML del correo
```

Power Automate lee el JSON, obtiene el Excel y el HTML, y envía el correo.

---

## 🧹 Limpieza automática

Los archivos se eliminan automáticamente después de **10 días** via GitHub Actions.

No necesitas hacer nada, el sistema se limpia solo.

---

## ❓ Preguntas Frecuentes

### ¿Puedo usar esto sin Power Automate?

✅ **SÍ** - La app funciona perfectamente sin Power Automate:
- Genera informes Excel profesionales
- Los descarga a tu PC
- Los guarda en el repositorio (opcional)

Power Automate es **opcional** para envío automático por correo.

### ¿Cómo agrego más correos?

Edita `correos_destino.txt` y agrega un correo por línea:

```text
nuevo.correo@empresa.com
otro.correo@empresa.com
```

Aparecerán automáticamente en la app.

### ¿Los informes ocupan mucho espacio?

No. Cada informe son ~100-500 KB (Excel + JSON + HTML).

GitHub Actions elimina automáticamente archivos mayores a 10 días.

### ¿Puedo cambiar los 10 días de retención?

Sí. Edita `.github/workflows/limpiar_informes.yml`:

```yaml
find informes -type f -mtime +10  # <- Cambiar a 20, 30, etc.
```

---

## 🎨 Vista Previa del Correo

Abre `EJEMPLO_CORREO.html` en tu navegador para ver cómo se verá el correo.

---

## 📚 Documentación Completa

- 📖 [`README.md`](./README.md) - Guía completa del sistema
- 🚀 [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md) - Integración detallada
- 🎨 [`EJEMPLO_CORREO.html`](./EJEMPLO_CORREO.html) - Vista previa del correo

---

## 🆘 Ayuda Rápida

### Error: "No hay correos configurados"
→ Edita `correos_destino.txt` y agrega correos válidos

### Error: "No se puede guardar en repositorio"
→ Verifica permisos de escritura en `/informes/`

### Los correos no se envían
→ Verifica configuración de Power Automate (ver guía)

### GitHub Actions no funciona
→ Verifica que `.github/workflows/` tenga los archivos YAML

---

## ✅ Checklist de Implementación

### Implementación Básica (5 min)
- [ ] Ejecutar `streamlit run app_conciliador.py`
- [ ] Probar generar un informe
- [ ] Descargar Excel generado
- [ ] Verificar formato profesional

### Con Guardado Automático (2 min adicionales)
- [ ] Editar `correos_destino.txt` con correos reales
- [ ] Generar informe con opción de correo
- [ ] Verificar archivos en `/informes/`

### Con Power Automate (15 min adicionales)
- [ ] Crear Personal Access Token en GitHub
- [ ] Crear flujo en Power Automate
- [ ] Conectar a repositorio
- [ ] Configurar envío de correo
- [ ] Probar con informe de prueba
- [ ] Verificar recepción del correo

---

## 🎉 ¡Todo Listo!

Tu sistema de informes está configurado y listo para usar.

**¿Dudas?** Consulta la documentación completa en [`README.md`](./README.md)

**¿Power Automate?** Ver [`GUIA_POWER_AUTOMATE.md`](./GUIA_POWER_AUTOMATE.md)

---

**Última actualización**: 2024-11-18  
**Versión**: 2.0
