# -*- coding: utf-8 -*-
# app_conciliador.py - VERSIÓN ESTABLE SIN WHATSAPP

import streamlit as st
import pandas as pd
import numpy as np
import io
import sys
import os
from datetime import datetime

# Configuración para el ejecutable
if hasattr(sys, '_MEIPASS'):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

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
        
        solicitud_df['Código de artículo'] = solicitud_df['Código de artículo'].astype(str).str.strip()
        cargado_df['Código de artículo'] = cargado_df['Código de artículo'].astype(str).str.strip()
        
        solicitud_final = solicitud_df.groupby(['Código de artículo', 'Nombre del producto'])['Cantidad'].sum().reset_index()
        solicitud_final = solicitud_final.rename(columns={'Cantidad': 'Cantidad Solicitada'})

        cargado_filtrado_df = cargado_df[cargado_df['Estado de la emisión'].str.strip() == 'Seleccionado'].copy()
        
        cargado_filtrado_df['Código de artículo'] = cargado_filtrado_df['Código de artículo'].astype(str).str.strip()
        
        if 'Artículo original' in cargado_filtrado_df.columns:
            cargado_filtrado_df['Artículo original'] = cargado_filtrado_df['Artículo original'].astype(str).str.strip()
            
            cargado_filtrado_df['Código de Agrupación'] = np.where(
                (cargado_filtrado_df['Artículo original'].notna()) & 
                (cargado_filtrado_df['Artículo original'] != '') & 
                (cargado_filtrado_df['Artículo original'] != 'nan') &
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
        
        informe_df = informe_df[['Código de artículo', 'Nombre del producto', 'Estado', 'Cantidad Solicitada', 'Cantidad_Cargada', 'Diferencia', '% Cumplimiento', 'Pallets']]
        
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

    worksheet.merge_range('B2:G2', 'Informe de Conciliación de Carga', title_format)
    
    worksheet.write('B3', 'Obra:', metadata_format)
    worksheet.write('C3', metadata['nombre'], metadata_format)
    worksheet.write('E3', 'Hoja de Carga:', metadata_format)
    worksheet.write('F3', metadata['hoja_carga'], metadata_format)
    
    worksheet.merge_range('B5:G5', 'Resumen Ejecutivo', subtitle_format)
    worksheet.write('B6', 'Unidades Solicitadas:', kpi_format); worksheet.write('C6', kpis['total_solicitado'], kpi_value_format)
    worksheet.write('B7', 'Unidades Cargadas:', kpi_format); worksheet.write('C7', kpis['total_cargado'], kpi_value_format)
    worksheet.write('E6', '% Cumplimiento General:', kpi_format); worksheet.write('F6', kpis['cumplimiento_general'], percent_format)
    worksheet.write('E7', 'Artículos Pendientes:', kpi_format); worksheet.write('F7', kpis['articulos_pendientes'], kpi_value_format)

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(10, col_num, value, header_format)
    
    worksheet.set_column('A:A', 15); worksheet.set_column('B:B', 50)
    worksheet.set_column('C:C', 15); worksheet.set_column('D:F', 20)
    worksheet.set_column('G:G', 18, percent_format); worksheet.set_column('H:H', 40)
    
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Pendiente"', 'format': pendiente_format})
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Incompleto"', 'format': incompleto_format})
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Completo"', 'format': completo_format})
    worksheet.conditional_format('C12:C1000', {'type': 'cell', 'criteria': 'equal to', 'value': '"Excedente"', 'format': excedente_format})

    writer.close()
    return output.getvalue()

def generar_nombre_archivo(metadata):
    """Genera un nombre de archivo basado en obra, hoja de carga y fecha"""
    fecha_actual = datetime.now().strftime("%Y%m%d")
    
    nombre_limpio = metadata['nombre'].replace(' ', '_').replace('/', '-').replace('\\', '-')
    hoja_limpia = metadata['hoja_carga'].replace(' ', '_').replace('/', '-').replace('\\', '-')
    
    nombre_archivo = f"Conciliacion_{nombre_limpio}_{hoja_limpia}_{fecha_actual}.xlsx"
    
    return nombre_archivo

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
                
                # Solo botón de descarga - 100% funcional
                st.download_button(
                    label="Descargar Informe en Excel", 
                    data=excel_bytes,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.caption(f"Archivo Excel: {nombre_archivo}")
                
                # Información adicional para el usuario
                st.info("""
                **Informe generado exitosamente**
                - El archivo Excel incluye toda la información de la obra y hoja de carga
                - Contiene el resumen ejecutivo con todos los KPIs
                - Tabla detallada con formato condicional por colores
                - Listo para compartir o archivar
                """)
                
        else:
            st.warning("Por favor, pega los datos en ambas tablas antes de generar el informe.")

if __name__ == "__main__":
    main()