# -*- coding: utf-8 -*-
# app_conciliador.py - VERSIÓN ESTABLE SIN WHATSAPP

import streamlit as st
import pandas as pd
import numpy as np
import io
import sys
import os
import json
import re
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path

# Configuración para el ejecutable
if hasattr(sys, '_MEIPASS'):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

def normalizar_codigo(valor):
    """Normaliza codigos para evitar mismatches (ej: 67284.0 -> 67284)."""
    if pd.isna(valor):
        return ''
    texto = str(valor).strip()
    if not texto:
        return ''
    if texto.lower() in {'nan', 'none'}:
        return ''
    if re.fullmatch(r'\d+\.0+', texto):
        return texto.split('.')[0]
    return texto

def formatear_cantidad(valor):
    """Convierte cantidades a texto legible sin decimales innecesarios."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if np.isnan(numero):
        return "0"
    if numero.is_integer():
        return f"{int(numero):,}"
    return f"{numero:,.2f}".rstrip('0').rstrip('.')

def extraer_metadatos_carga(cargado_df):
    """Extrae el nombre de la obra y hoja de carga de los datos"""
    metadata = {"nombre": "Sin_Nombre", "hoja_carga": "Sin_Hoja"}
    
    try:
        if 'Nombre' in cargado_df.columns:
            nombres = cargado_df['Nombre'].dropna().unique()
            if len(nombres) > 0:
                metadata["nombre"] = str(nombres[0]).strip()
        
        if 'Hoja de carga' in cargado_df.columns:
            hojas = cargado_df['Hoja de carga'].dropna().unique()
            if len(hojas) > 0:
                metadata["hoja_carga"] = str(hojas[0]).strip()
    except Exception:
        pass
    
    return metadata

def procesar_datos(texto_solicitud, texto_cargado):
    try:
        solicitud_df = pd.read_csv(io.StringIO(texto_solicitud), sep='\t')
        cargado_df = pd.read_csv(io.StringIO(texto_cargado), sep='\t')

        metadata = extraer_metadatos_carga(cargado_df)

        solicitud_df.columns = solicitud_df.columns.str.strip()
        cargado_df.columns = cargado_df.columns.str.strip()
        solicitud_df['Cantidad'] = pd.to_numeric(solicitud_df['Cantidad'], errors='coerce').fillna(0)
        cargado_df['Cantidad'] = pd.to_numeric(cargado_df['Cantidad'], errors='coerce').fillna(0)
        
        solicitud_df['Código de artículo'] = solicitud_df['Código de artículo'].apply(normalizar_codigo)
        cargado_df['Código de artículo'] = cargado_df['Código de artículo'].apply(normalizar_codigo)

        if 'Artículo original' in cargado_df.columns:
            cargado_df['Artículo original'] = cargado_df['Artículo original'].apply(normalizar_codigo)
        
        solicitud_final = solicitud_df.groupby(['Código de artículo', 'Nombre del producto'])['Cantidad'].sum().reset_index()
        solicitud_final = solicitud_final.rename(columns={'Cantidad': 'Cantidad Solicitada'})

        cargado_filtrado_df = cargado_df[cargado_df['Estado de la emisión'].astype(str).str.strip() == 'Seleccionado'].copy()
        
        cargado_filtrado_df['Código de artículo'] = cargado_filtrado_df['Código de artículo'].apply(normalizar_codigo)

        sustituciones = {}
        sustituciones_totales = {}

        if 'Artículo original' in cargado_filtrado_df.columns:
            cargado_filtrado_df['Artículo original'] = cargado_filtrado_df['Artículo original'].apply(normalizar_codigo)

            sustitutos_df = cargado_filtrado_df[
                (cargado_filtrado_df['Artículo original'] != '') &
                (cargado_filtrado_df['Artículo original'] != '0') &
                (cargado_filtrado_df['Artículo original'] != cargado_filtrado_df['Código de artículo'])
            ].copy()

            if not sustitutos_df.empty:
                resumen_sustituciones = (
                    sustitutos_df.groupby(['Artículo original', 'Código de artículo'])['Cantidad']
                    .sum()
                    .reset_index()
                )
                sustituciones_totales = (
                    resumen_sustituciones.groupby('Artículo original')['Cantidad']
                    .sum()
                    .to_dict()
                )
                for original, grupo in resumen_sustituciones.groupby('Artículo original'):
                    detalles = []
                    for _, fila in grupo.iterrows():
                        cantidad_txt = formatear_cantidad(fila['Cantidad'])
                        detalles.append(f"{fila['Código de artículo']} ({cantidad_txt})")
                    sustituciones[original] = ", ".join(detalles)
        
        if 'Artículo original' in cargado_filtrado_df.columns:
            cargado_filtrado_df['Artículo original'] = cargado_filtrado_df['Artículo original'].apply(normalizar_codigo)
            
            cargado_filtrado_df['Código de Agrupación'] = np.where(
                (cargado_filtrado_df['Artículo original'] != '') &
                (cargado_filtrado_df['Artículo original'] != '0'),
                cargado_filtrado_df['Artículo original'],
                cargado_filtrado_df['Código de artículo']
            )
        else:
            cargado_filtrado_df['Código de Agrupación'] = cargado_filtrado_df['Código de artículo']

        cargado_agrupado = cargado_filtrado_df.groupby('Código de Agrupación').agg(
            Cantidad_Cargada=('Cantidad', 'sum'),
            Pallets=('Id de pallet', lambda x: ', '.join(x.dropna().astype(str).unique()))
        ).reset_index()

        informe_df = pd.merge(
            solicitud_final,
            cargado_agrupado,
            left_on='Código de artículo',
            right_on='Código de Agrupación',
            how='outer'
        )
        
        informe_df['Código de artículo'] = informe_df['Código de artículo'].fillna(informe_df['Código de Agrupación'])
        informe_df['Código de artículo'] = informe_df['Código de artículo'].apply(normalizar_codigo)

        if informe_df['Nombre del producto'].isna().any():
            name_map = solicitud_final.drop_duplicates('Código de artículo').set_index('Código de artículo')['Nombre del producto']
            informe_df['Nombre del producto'] = informe_df['Nombre del producto'].fillna(
                informe_df['Código de artículo'].map(name_map)
            )
            informe_df['Nombre del producto'] = informe_df['Nombre del producto'].fillna('Artículo no en la solicitud original')

        informe_df = informe_df.drop(columns=['Código de Agrupación'], errors='ignore')
        
        informe_df['Cantidad Solicitada'] = informe_df['Cantidad Solicitada'].fillna(0).astype(int)
        informe_df['Cantidad_Cargada'] = informe_df['Cantidad_Cargada'].fillna(0).astype(int)
        informe_df['Pallets'] = informe_df['Pallets'].fillna('---')
        informe_df['Diferencia'] = informe_df['Cantidad_Cargada'] - informe_df['Cantidad Solicitada']

        def resumen_sustitucion(row):
            codigo = row['Código de artículo']
            detalle = sustituciones.get(codigo)
            if not detalle:
                return '---'
            total_sustituido = sustituciones_totales.get(codigo, 0)
            if row['Cantidad Solicitada'] > 0:
                estado = 'Parcial' if total_sustituido < row['Cantidad Solicitada'] else 'Total'
                return f"{estado}: {detalle}"
            return detalle

        informe_df['Sustituido por'] = informe_df.apply(resumen_sustitucion, axis=1)
        
        informe_df['% Cumplimiento'] = informe_df.apply(
            lambda row: (row['Cantidad_Cargada'] / row['Cantidad Solicitada']) if row['Cantidad Solicitada'] > 0 else 0, axis=1)
        
        conditions = [
            (informe_df['Cantidad_Cargada'] == 0) & (informe_df['Cantidad Solicitada'] > 0),
            (informe_df['Diferencia'] < 0),
            (informe_df['Diferencia'] > 0),
            (informe_df['Cantidad Solicitada'] == 0) & (informe_df['Cantidad_Cargada'] > 0),
            (informe_df['Diferencia'] == 0) & (informe_df['Cantidad Solicitada'] > 0)
        ]
        choices = ['Pendiente', 'Incompleto', 'Excedente', 'No Solicitado', 'Completo']
        informe_df['Estado'] = np.select(conditions, choices, default='Revisar')
        
        informe_df = informe_df[['Código de artículo', 'Nombre del producto', 'Estado', 'Sustituido por', 'Cantidad Solicitada', 'Cantidad_Cargada', 'Diferencia', '% Cumplimiento', 'Pallets']]
        
        return informe_df, metadata

    except KeyError as e:
        st.error(f"Falta una columna necesaria en los datos pegados: {e}")
        st.error("Por favor, asegúrate de que las columnas 'Código de artículo', 'Nombre del producto', 'Cantidad' y 'Estado de la emisión' están presentes.")
        return None, None
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los datos: {e}")
        st.error("Verifica que los datos estén en el formato correcto (separados por tabulaciones)")
        return None, None

def crear_excel_profesional(df, kpis, metadata):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    sheet_name = 'Informe de Conciliacion'
    df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=10)
    
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
    percent_format = workbook.add_format({'num_format': '0.0%'})
    title_format = workbook.add_format({'bold': True, 'font_size': 20, 'font_color': '#1F497D'})
    subtitle_format = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1F497D'})
    metadata_format = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2F5496'})
    kpi_format = workbook.add_format({'bold': True, 'font_size': 12})
    kpi_value_format = workbook.add_format({'font_size': 12, 'num_format': '#,##0.00'})
    pendiente_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    incompleto_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
    completo_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
    excedente_format = workbook.add_format({'bg_color': '#D9E1F2', 'font_color': '#2F5496'})

    worksheet.merge_range('B2:I2', 'Informe de Conciliación de Carga', title_format)
    
    worksheet.write('B3', 'Obra:', metadata_format)
    worksheet.write('C3', metadata['nombre'], metadata_format)
    worksheet.write('E3', 'Hoja de Carga:', metadata_format)
    worksheet.write('F3', metadata['hoja_carga'], metadata_format)
    
    worksheet.merge_range('B5:I5', 'Resumen Ejecutivo', subtitle_format)
    worksheet.write('B6', 'Unidades Solicitadas:', kpi_format); worksheet.write('C6', kpis['total_solicitado'], kpi_value_format)
    worksheet.write('B7', 'Unidades Cargadas:', kpi_format); worksheet.write('C7', kpis['total_cargado'], kpi_value_format)
    worksheet.write('E6', '% Cumplimiento General:', kpi_format); worksheet.write('F6', kpis['cumplimiento_general'], percent_format)
    worksheet.write('E7', 'Artículos Pendientes:', kpi_format); worksheet.write('F7', kpis['articulos_pendientes'], kpi_value_format)

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(10, col_num, value, header_format)
    
    worksheet.set_column('A:A', 15); worksheet.set_column('B:B', 50)
    worksheet.set_column('C:C', 15); worksheet.set_column('D:D', 30)
    worksheet.set_column('E:G', 20); worksheet.set_column('H:H', 18, percent_format)
    worksheet.set_column('I:I', 40)
    
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Pendiente"', 'format': pendiente_format})
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Incompleto"', 'format': incompleto_format})
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Completo"', 'format': completo_format})
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Excedente"', 'format': excedente_format})

    writer.close()
    return output.getvalue()

def generar_nombre_archivo(metadata):
    """Genera un nombre de archivo basado en obra, hoja de carga y fecha"""
    fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    nombre_limpio = metadata['nombre'].replace(' ', '_').replace('/', '-').replace('\\', '-')
    hoja_limpia = metadata['hoja_carga'].replace(' ', '_').replace('/', '-').replace('\\', '-')
    
    nombre_archivo = f"Conciliacion_{nombre_limpio}_{hoja_limpia}_{fecha_actual}.xlsx"
    
    return nombre_archivo

def leer_correos_permitidos():
    """Lee la lista de correos autorizados desde el archivo correos_destino.txt"""
    correos = []
    archivo_correos = Path('correos_destino.txt')
    
    try:
        if archivo_correos.exists():
            with open(archivo_correos, 'r', encoding='utf-8') as f:
                for linea in f:
                    linea = linea.strip()
                    if linea and not linea.startswith('#') and '@' in linea:
                        correos.append(linea)
    except Exception as e:
        st.warning(f"No se pudo leer el archivo de correos: {e}")
    
    return correos

def guardar_informe_en_repositorio(excel_bytes, nombre_archivo, metadata, correo_destino=None):
    """Guarda el informe Excel y metadata en la carpeta /informes/"""
    try:
        # Crear carpeta si no existe
        carpeta_informes = Path('informes')
        carpeta_informes.mkdir(exist_ok=True)
        
        # Guardar archivo Excel
        ruta_excel = carpeta_informes / nombre_archivo
        with open(ruta_excel, 'wb') as f:
            f.write(excel_bytes)
        
        # Crear metadata JSON
        metadata_completa = {
            'fecha_generacion': datetime.now().isoformat(),
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': f'informes/{nombre_archivo}',
            'obra': metadata['nombre'],
            'hoja_carga': metadata['hoja_carga'],
            'correo_destino': correo_destino,
            'enviar_correo': correo_destino is not None
        }
        
        # Guardar metadata
        nombre_metadata = nombre_archivo.replace('.xlsx', '_metadata.json')
        ruta_metadata = carpeta_informes / nombre_metadata
        with open(ruta_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata_completa, f, indent=2, ensure_ascii=False)
        
        return True, ruta_excel, ruta_metadata
    
    except Exception as e:
        return False, None, None

def generar_cuerpo_html_outlook(informe_df, kpis, metadata):
    """Genera HTML profesional compatible con Outlook para el cuerpo del correo"""
    # Colores corporativos y estilos inline (Outlook solo soporta inline CSS)
    html = f"""
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            
            <!-- Encabezado -->
            <div style="background: linear-gradient(135deg, #1F497D 0%, #4F81BD 100%); padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold;">📊 Informe de Conciliación de Carga</h1>
            </div>
            
            <!-- Información de la Obra -->
            <div style="padding: 20px 30px; background-color: #f8f9fa; border-bottom: 3px solid #4F81BD;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; width: 50%;">
                            <strong style="color: #1F497D; font-size: 14px;">🏗️ Obra:</strong><br>
                            <span style="font-size: 18px; color: #333; font-weight: bold;">{metadata['nombre']}</span>
                        </td>
                        <td style="padding: 10px; width: 50%; text-align: right;">
                            <strong style="color: #1F497D; font-size: 14px;">📋 Hoja de Carga:</strong><br>
                            <span style="font-size: 18px; color: #333; font-weight: bold;">{metadata['hoja_carga']}</span>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- KPIs -->
            <div style="padding: 30px;">
                <h2 style="color: #1F497D; font-size: 20px; margin-bottom: 20px; border-bottom: 2px solid #4F81BD; padding-bottom: 10px;">📈 Resumen Ejecutivo</h2>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="width: 50%; padding: 15px; background-color: #E8F0FE; border-radius: 8px; margin-right: 10px;">
                            <div style="text-align: center;">
                                <div style="color: #666; font-size: 13px; margin-bottom: 5px;">Unidades Solicitadas</div>
                                <div style="color: #1F497D; font-size: 32px; font-weight: bold;">{kpis['total_solicitado']:,.0f}</div>
                            </div>
                        </td>
                        <td style="width: 50%; padding: 15px; background-color: #E8F5E9; border-radius: 8px;">
                            <div style="text-align: center;">
                                <div style="color: #666; font-size: 13px; margin-bottom: 5px;">Unidades Cargadas</div>
                                <div style="color: #2E7D32; font-size: 32px; font-weight: bold;">{kpis['total_cargado']:,.0f}</div>
                            </div>
                        </td>
                    </tr>
                </table>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 50%; padding: 15px; background-color: #FFF8E1; border-radius: 8px; margin-right: 10px;">
                            <div style="text-align: center;">
                                <div style="color: #666; font-size: 13px; margin-bottom: 5px;">% Cumplimiento General</div>
                                <div style="color: #F57C00; font-size: 32px; font-weight: bold;">{kpis['cumplimiento_general']:.1%}</div>
                            </div>
                        </td>
                        <td style="width: 50%; padding: 15px; background-color: #FFEBEE; border-radius: 8px;">
                            <div style="text-align: center;">
                                <div style="color: #666; font-size: 13px; margin-bottom: 5px;">Artículos Pendientes</div>
                                <div style="color: #C62828; font-size: 32px; font-weight: bold;">{kpis['articulos_pendientes']}</div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Tabla de Detalle -->
            <div style="padding: 0 30px 30px 30px;">
                <h2 style="color: #1F497D; font-size: 20px; margin-bottom: 20px; border-bottom: 2px solid #4F81BD; padding-bottom: 10px;">📦 Detalle de Artículos</h2>
                
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead>
                            <tr style="background-color: #1F497D;">
                                <th style="padding: 12px 8px; text-align: left; color: white; border: 1px solid #ddd;">Código</th>
                                <th style="padding: 12px 8px; text-align: left; color: white; border: 1px solid #ddd;">Producto</th>
                                <th style="padding: 12px 8px; text-align: center; color: white; border: 1px solid #ddd;">Estado</th>
                                <th style="padding: 12px 8px; text-align: left; color: white; border: 1px solid #ddd;">Sustituido por</th>
                                <th style="padding: 12px 8px; text-align: right; color: white; border: 1px solid #ddd;">Solicitado</th>
                                <th style="padding: 12px 8px; text-align: right; color: white; border: 1px solid #ddd;">Cargado</th>
                                <th style="padding: 12px 8px; text-align: right; color: white; border: 1px solid #ddd;">Diferencia</th>
                            </tr>
                        </thead>
                        <tbody>
"""
    
    # Agregar filas de la tabla
    for idx, row in informe_df.iterrows():
        # Colores según estado (compatibles con Outlook)
        if row['Estado'] == 'Pendiente':
            bg_color = '#FFCDD2'
            text_color = '#B71C1C'
        elif row['Estado'] == 'Incompleto':
            bg_color = '#FFF9C4'
            text_color = '#F57F17'
        elif row['Estado'] == 'Completo':
            bg_color = '#C8E6C9'
            text_color = '#1B5E20'
        elif row['Estado'] in ['Excedente', 'No Solicitado']:
            bg_color = '#BBDEFB'
            text_color = '#0D47A1'
        else:
            bg_color = '#FFFFFF'
            text_color = '#000000'
        
        html += f"""
                            <tr style="background-color: {bg_color};">
                                <td style="padding: 10px 8px; border: 1px solid #ddd; color: {text_color};">{row['Código de artículo']}</td>
                                <td style="padding: 10px 8px; border: 1px solid #ddd; color: {text_color};">{row['Nombre del producto']}</td>
                                <td style="padding: 10px 8px; text-align: center; border: 1px solid #ddd; font-weight: bold; color: {text_color};">{row['Estado']}</td>
                                <td style="padding: 10px 8px; text-align: left; border: 1px solid #ddd; color: {text_color};">{row['Sustituido por']}</td>
                                <td style="padding: 10px 8px; text-align: right; border: 1px solid #ddd; color: {text_color};">{int(row['Cantidad Solicitada']):,}</td>
                                <td style="padding: 10px 8px; text-align: right; border: 1px solid #ddd; color: {text_color};">{int(row['Cantidad_Cargada']):,}</td>
                                <td style="padding: 10px 8px; text-align: right; border: 1px solid #ddd; color: {text_color};">{int(row['Diferencia']):,}</td>
                            </tr>
"""
    
    html += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Pie de página -->
            <div style="padding: 20px 30px; background-color: #f8f9fa; border-top: 3px solid #4F81BD; text-align: center;">
                <p style="margin: 0; color: #666; font-size: 12px;">📧 Informe generado automáticamente</p>
                <p style="margin: 5px 0 0 0; color: #999; font-size: 11px;">Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    return html

def generar_resumen_whatsapp(informe_df, kpis, metadata):
    """Genera un resumen simple para copiar y pegar en WhatsApp."""
    fecha = datetime.now().strftime('%d/%m/%Y')
    lineas = [
        "📦 Conciliacion de carga",
        f"Obra: {metadata['nombre']}",
        f"Orden: {metadata['hoja_carga']}",
        f"Fecha: {fecha}",
        "---------------------------",
        "Productos:"
    ]

    productos_df = informe_df[informe_df['Cantidad Solicitada'] > 0].copy()
    emojis_estado = {
        'Completo': '✅',
        'Pendiente': '🔴',
        'Incompleto': '🟡',
        'Excedente': '🔵',
        'No Solicitado': '⚪'
    }
    for _, row in productos_df.iterrows():
        codigo = row['Código de artículo']
        nombre = row['Nombre del producto']
        solicitado = formatear_cantidad(row['Cantidad Solicitada'])
        cargado = formatear_cantidad(row['Cantidad_Cargada'])
        diferencia = row['Diferencia']
        estado = row['Estado']
        emoji_estado = emojis_estado.get(estado, 'ℹ️')
        lineas.append(f"{emoji_estado} {codigo} {nombre}")
        detalle_partes = [f"Pedido: {solicitado}", f"Envio: {cargado}"]
        if diferencia < 0:
            detalle_partes.append(f"Faltan: {formatear_cantidad(abs(diferencia))}")
        elif diferencia > 0:
            detalle_partes.append(f"Excedente: {formatear_cantidad(diferencia)}")
        lineas.append(f"   " + " | ".join(detalle_partes))
        if row['Sustituido por'] != '---':
            lineas.append(f"   -> Sustituido por: {row['Sustituido por']}")

    lineas.append("")
    lineas.append(f"Totalidad de envio: {kpis['cumplimiento_general']:.1%}")
    lineas.append("")
    lineas.append("ATTE, sistema de delivery")

    return "\n".join(lineas)

def main():
    st.set_page_config(
        page_title="Conciliador de Cargas", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("Generador de Informes de Conciliación de Cargas")
    st.write("Copia los datos de tu ERP (Ctrl+C) y pégalos (Ctrl+V) en las áreas correspondientes. Asegúrate de incluir la fila de encabezados.")

    col1, col2 = st.columns(2)
    with col1:
        st.header("1. Pegar Tabla de Solicitud Inicial")
        texto_solicitud = st.text_area("Datos de la solicitud:", height=300, key="solicitud")
    with col2:
        st.header("2. Pegar Tabla del Pedido Cargado")
        texto_cargado = st.text_area("Datos del pedido cargado:", height=300, key="cargado")

    # Opciones de envío de correo (colapsable)
    with st.expander("📧 Opciones de Envío por Correo (Opcional)", expanded=False):
        enviar_correo = st.checkbox("Preparar informe para envío automático por correo", value=False)
        
        correo_seleccionado = None
        if enviar_correo:
            correos_disponibles = leer_correos_permitidos()
            
            if correos_disponibles:
                correo_seleccionado = st.selectbox(
                    "Seleccionar destinatario:",
                    options=correos_disponibles,
                    help="Correos autorizados desde correos_destino.txt"
                )
                st.info(f"📬 El informe se preparará para envío a: **{correo_seleccionado}**")
            else:
                st.warning("⚠️ No hay correos configurados. Edita el archivo `correos_destino.txt` para agregar destinatarios.")
                enviar_correo = False

    if st.button("Generar Informe de Conciliación", type="primary"):
        if texto_solicitud and texto_cargado:
            resultado = procesar_datos(texto_solicitud, texto_cargado)
            
            if resultado[0] is not None:
                informe_final, metadata = resultado
                
                st.header("Resultados del Análisis")
                
                col_meta1, col_meta2 = st.columns(2)
                with col_meta1:
                    st.info(f"**Obra:** {metadata['nombre']}")
                with col_meta2:
                    st.info(f"**Hoja de Carga:** {metadata['hoja_carga']}")

                total_solicitado = informe_final['Cantidad Solicitada'].sum()
                total_cargado = informe_final['Cantidad_Cargada'].sum()
                cumplimiento_general = total_cargado / total_solicitado if total_solicitado > 0 else 0
                articulos_pendientes = informe_final[informe_final['Estado'] == 'Pendiente'].shape[0]

                kpis = { 
                    "total_solicitado": total_solicitado, 
                    "total_cargado": total_cargado,
                    "cumplimiento_general": cumplimiento_general, 
                    "articulos_pendientes": articulos_pendientes
                }

                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric(label="Uds. Solicitadas", value=f"{total_solicitado:,.0f}")
                kpi2.metric(label="Uds. Cargadas", value=f"{total_cargado:,.0f}")
                kpi3.metric(label="% Cumplimiento", value=f"{cumplimiento_general:.2%}")
                kpi4.metric(label="Artículos Pendientes", value=f"{articulos_pendientes}", delta=f"-{articulos_pendientes}", delta_color="inverse")
                
                def highlight_status(row):
                    style = ''
                    if row.Estado == 'Pendiente': 
                        style = 'background-color: #FFC7CE; color: #9C0006;'
                    elif row.Estado == 'Incompleto': 
                        style = 'background-color: #FFEB9C; color: #9C6500;'
                    elif row.Estado == 'Completo': 
                        style = 'background-color: #C6EFCE; color: #006100;'
                    elif row.Estado == 'Excedente' or row.Estado == 'No Solicitado': 
                        style = 'background-color: #D9E1F2; color: #2F5496;'
                    return [style] * len(row)

                st.dataframe(informe_final.style.apply(highlight_status, axis=1))
                
                excel_bytes = crear_excel_profesional(informe_final, kpis, metadata)
                nombre_archivo = generar_nombre_archivo(metadata)
                
                # Guardar en repositorio SOLO si se marcó la opción de correo
                if enviar_correo and correo_seleccionado:
                    exito, ruta_excel, ruta_metadata = guardar_informe_en_repositorio(
                        excel_bytes, 
                        nombre_archivo, 
                        metadata,
                        correo_seleccionado
                    )
                    
                    if exito:
                        st.success(f"✅ Informe guardado en repositorio: `{ruta_excel}`")
                        
                        # Generar HTML para el correo
                        html_correo = generar_cuerpo_html_outlook(informe_final, kpis, metadata)
                        
                        # Guardar HTML también
                        nombre_html = nombre_archivo.replace('.xlsx', '_email.html')
                        ruta_html = Path('informes') / nombre_html
                        with open(ruta_html, 'w', encoding='utf-8') as f:
                            f.write(html_correo)
                        
                        st.success(f"📧 Preparado para envío a: **{correo_seleccionado}**")
                        st.info("💡 **Power Automate** detectará automáticamente este informe y lo enviará por correo.")
                    else:
                        st.error("❌ Error al guardar el informe en el repositorio")
                else:
                    # Solo descarga, sin guardar en repositorio
                    st.info("ℹ️ Informe generado solo para descarga (no se guardó en repositorio)")
                
                # Botón de descarga
                st.download_button(
                    label="⬇️ Descargar Informe en Excel", 
                    data=excel_bytes,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.caption(f"📄 Archivo: {nombre_archivo}")

                resumen_whatsapp = generar_resumen_whatsapp(informe_final, kpis, metadata)
                with st.expander("📲 Resumen para WhatsApp", expanded=False):
                    st.text_area("Mensaje listo para copiar", value=resumen_whatsapp, height=220)
                    st.caption("Copia y pega este resumen en WhatsApp.")
                    mensaje_normalizado = unicodedata.normalize('NFC', resumen_whatsapp)
                    mensaje_json = json.dumps(mensaje_normalizado)
                    components.html(
                        f"""
                        <div style="margin-top: 6px;">
                          <button onclick="abrirWhatsapp()"
                            style="background-color:#22c55e;border:none;color:white;padding:8px 14px;border-radius:6px;cursor:pointer;font-weight:600;">
                            Abrir WhatsApp Web
                          </button>
                        </div>
                        <script>
                          const mensajeWhatsapp = {mensaje_json};
                          function abrirWhatsapp() {{
                            const url = 'https://wa.me/?text=' + encodeURIComponent(mensajeWhatsapp);
                            window.open(url, '_blank');
                          }}
                        </script>
                        """,
                        height=64
                    )
                    st.caption("Se abrira WhatsApp Web para elegir el chat.")
                
                # Información adicional
                with st.expander("ℹ️ Información del Informe", expanded=False):
                    st.markdown("""
                    **Informe generado exitosamente**
                    - ✅ Archivo Excel con formato profesional
                    - ✅ Resumen ejecutivo con KPIs
                    - ✅ Tabla detallada con colores por estado
                    - ✅ Disponible para descarga inmediata
                    """)
                    
                    if enviar_correo and correo_seleccionado:
                        st.markdown("""
                        **Configurado para envío por correo**
                        - 📧 Cuerpo HTML profesional generado
                        - 📎 Excel adjunto preparado
                        - 💾 Guardado en `/informes/` del repositorio
                        - 🤖 Power Automate procesará automáticamente
                        """)
                    else:
                        st.markdown("""
                        **Modo descarga únicamente**
                        - 📥 Solo descarga local
                        - 🚫 No se guardó en repositorio
                        - 🚫 No se enviará por correo
                        """)
                
        else:
            st.warning("Por favor, pega los datos en ambas tablas antes de generar el informe.")

if __name__ == "__main__":
    main()