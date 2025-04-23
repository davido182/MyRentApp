import streamlit as st
import sqlite3
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter # Corrected import statement
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from werkzeug.utils import secure_filename
import base64
import re
from PIL import Image
from datetime import datetime
import pandas as pd
import altair as alt

# Configuración de la aplicación Streamlit
st.set_page_config(page_title="Control de rentas-inquilinos", page_icon=":house:", layout="wide")

# Configuración de la base de datos
DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads'

# Asegurar que la carpeta 'uploads' exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Funciones para la base de datos
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        results = cursor.fetchall()
        return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        return cursor.lastrowid

# Inicialización de la base de datos al iniciar la aplicación
def setup_database():
    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS propiedades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                propiedad_id INTEGER UNIQUE,
                valor_renta REAL,
                arrendatario TEXT,
                fecha_inicio DATE,
                garantia INTEGER,
                monto_deposito REAL,
                comprobante_garantia TEXT,
                comprobante_contrato TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comprobantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                propiedad_id INTEGER,
                nombre TEXT,
                mes TEXT,
                anio INTEGER,
                FOREIGN KEY (propiedad_id) REFERENCES propiedades (propiedad_id)
            )
        ''')
        existing_properties = query_db("SELECT propiedad_id FROM propiedades")
        existing_ids = [prop['propiedad_id'] for prop in existing_properties]
        for i in range(1, 10):
            if i not in existing_ids:
                try:
                    cursor.execute("INSERT INTO propiedades (propiedad_id) VALUES (?)", (i,))
                except sqlite3.IntegrityError:
                    pass
        db.commit()

setup_database()

class ReportGenerator:
    def __init__(self, database):
        self.database = database

    def generate_tenant_report(self):
        """Generate a comprehensive tenant report"""
        propiedades = query_db('SELECT * FROM propiedades ORDER BY propiedad_id')
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Informe de Inquilinos", styles['Title']))
        story.append(Spacer(1, 0.2*inch))

        for propiedad in propiedades:
            story.append(Paragraph(f"Propiedad {propiedad['propiedad_id']}", styles['h2']))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"Valor Renta: {propiedad['valor_renta'] if propiedad['valor_renta'] is not None else 'N/A'}", styles['Normal']))
            story.append(Paragraph(f"Arrendatario: {propiedad['arrendatario'] if propiedad['arrendatario'] else 'Vacante'}", styles['Normal']))
            story.append(Paragraph(f"Fecha Inicio: {propiedad['fecha_inicio'] if propiedad['fecha_inicio'] else 'N/A'}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

        doc.build(story)
        output.seek(0)
        return output


# Función principal de la aplicación
def main():
    if st.session_state.get('selected_propiedad') is not None:
        if st.sidebar.button("Página principal"):
            st.session_state['selected_propiedad'] = None
            st.rerun()

    if 'selected_propiedad' not in st.session_state:
        st.session_state['selected_propiedad'] = None

    if st.session_state['selected_propiedad'] is None:
        st.title("Control rentas - inquilinos")

        propiedades = query_db('SELECT * FROM propiedades ORDER BY propiedad_id')

        cols = st.columns(3)
        for i, propiedad in enumerate(propiedades):
            with cols[i % 3]:
                st.subheader(f"Propiedad {propiedad['propiedad_id']}")

                ocupada = propiedad['arrendatario'] is not None and propiedad['arrendatario'] != ''

                if ocupada:
                    st.markdown(f'<p style="margin-top: -10px; margin-bottom: 10px; color:red;">Ocupada</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p style="margin-top: -10px; margin-bottom: 10px; color:green;">Disponible</p>', unsafe_allow_html=True)

                if st.button("Ver Detalles", key=f"propiedad_{propiedad['propiedad_id']}"):
                    st.session_state['selected_propiedad'] = propiedad['propiedad_id']
                    st.rerun()

        st.subheader("Informes")
        if st.button("Generar Informe de Inquilinos"):
            report_generator = ReportGenerator(DATABASE)
            pdf_bytes = report_generator.generate_tenant_report().getvalue()
            st.download_button(
                label="Descargar Informe",
                data=pdf_bytes,
                file_name='informe_inquilinos.pdf',
                mime='application/pdf',
            )
        st.subheader("Gráfico de Valores de Renta")
        propiedades_data = query_db('SELECT propiedad_id, valor_renta FROM propiedades ORDER BY propiedad_id')
        chart_data = []
        for propiedad in propiedades_data:
            if propiedad['valor_renta'] is not None and propiedad['valor_renta'] > 0:
                chart_data.append({"Propiedad": str(propiedad['propiedad_id']), "Valor Renta": propiedad['valor_renta']})
            else:
                chart_data.append({"Propiedad": str(propiedad['propiedad_id']), "Valor Renta": 0, "Estado": "Disponible"})
        df = pd.DataFrame(chart_data)
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Propiedad:O', title='Propiedad'),
            y=alt.Y('Valor Renta:Q',
                    title='Valor Renta (USD)'),
            tooltip=['Propiedad', 'Valor Renta'],
            text=alt.Text('Valor Renta:Q', format='.0f')
        ).properties(
            title='Valores de Renta por propiedad'
        )
        st.altair_chart(chart, use_container_width=True)
        st.markdown("---")

        st.subheader("Eliminar propiedad")
        propiedades = query_db('SELECT propiedad_id FROM propiedades ORDER BY propiedad_id')
        propiedad_ids = [s['propiedad_id'] for s in propiedades] if propiedades else []
        propiedad_to_delete = st.selectbox("Seleccione la propiedad a eliminar:", propiedad_ids, key="delete_propiedad_selectbox")

        if st.button("Eliminar propiedad"):
            if propiedad_to_delete is not None:
                if st.session_state.get('confirm_delete') != propiedad_to_delete:
                    st.warning(f"¿Está seguro de que desea eliminar la propiedad {propiedad_to_delete}? Confirme nuevamente.")
                    st.session_state['confirm_delete'] = propiedad_to_delete
                else:
                    associated_comprobantes = query_db("SELECT id, nombre FROM comprobantes WHERE propiedad_id = ?", (propiedad_to_delete,))
                    for comp in associated_comprobantes:
                        filepath_to_delete = os.path.join(UPLOAD_FOLDER, comp['nombre'])
                        if os.path.exists(filepath_to_delete):
                            try:
                                os.remove(filepath_to_delete)
                            except Exception as e:
                                st.error(f"Error al eliminar archivo asociado {comp['nombre']}: {e}")
                    execute_db("DELETE FROM comprobantes WHERE propiedad_id = ?", (propiedad_to_delete,))

                    propiedad_data_to_delete = query_db("SELECT comprobante_contrato FROM propiedades WHERE propiedad_id = ?", (propiedad_to_delete,), one=True)
                    if propiedad_data_to_delete and propiedad_data_to_delete['comprobante_contrato']:
                         contract_filepath_to_delete = os.path.join(UPLOAD_FOLDER, propiedad_data_to_delete['comprobante_contrato'])
                         if os.path.exists(contract_filepath_to_delete):
                              try:
                                   os.remove(contract_filepath_to_delete)
                              except Exception as e:
                                   st.error(f"Error al eliminar archivo de contrato asociado {propiedad_data_to_delete['comprobante_contrato']}: {e}")


                    execute_db("DELETE FROM propiedades WHERE propiedad_id = ?", (propiedad_to_delete,))
                    st.success(f"Propiedad {propiedad_to_delete} y sus registros asociados eliminados.")
                    st.session_state['confirm_delete'] = None
                    st.session_state['selected_propiedad'] = None
                    st.rerun()
            else:
                st.info("No hay propiedades para eliminar.")


        st.subheader("Agregar propiedad")
        if st.button("Agregar propiedad"):
            max_propiedad = query_db("SELECT MAX(propiedad_id) as max_id FROM propiedades", one=True)
            new_propiedad_id = (max_propiedad['max_id'] or 0) + 1
            execute_db("INSERT INTO propiedades (propiedad_id) VALUES (?)", (new_propiedad_id,))
            st.success(f"Propiedad {new_propiedad_id} agregada")
            st.rerun()
    else:
        propiedad_id = st.session_state['selected_propiedad']
        propiedad_data = query_db('SELECT * FROM propiedades WHERE propiedad_id = ?', (propiedad_id,), one=True)

        st.header(f"Detalles de la propiedad {propiedad_id}")

        if 'confirm_edit' not in st.session_state:
            st.session_state['confirm_edit'] = False
        if 'comprobante_delete_id_to_confirm' not in st.session_state:
             st.session_state['comprobante_delete_id_to_confirm'] = None


        if propiedad_data:
            st.subheader("Datos del Inquilino:")
            st.write(f"Valor Renta: {propiedad_data['valor_renta'] if propiedad_data['valor_renta'] is not None else 'N/A'}")
            st.write(f"Arrendatario: {propiedad_data['arrendatario'] if propiedad_data['arrendatario'] else 'Vacante'}")
            st.write(f"Fecha Inicio: {propiedad_data['fecha_inicio'] if propiedad_data['fecha_inicio'] else 'N/A'}")
            st.write(f"Garantía: {'Sí' if propiedad_data['garantia'] else 'No'}")
            st.write(f"Monto Depósito: {propiedad_data['monto_deposito'] if propiedad_data['monto_deposito'] is not None else 'N/A'}")

            st.subheader("Contrato:")
            if propiedad_data['comprobante_contrato']:
                contract_filename = propiedad_data['comprobante_contrato']
                contract_filepath = os.path.join(UPLOAD_FOLDER, contract_filename)
                if os.path.exists(contract_filepath):
                    with open(contract_filepath, "rb") as f:
                        contract_bytes = f.read()
                    st.download_button(
                        label="Descargar Contrato",
                        data=contract_bytes,
                        file_name=contract_filename,
                        mime="application/octet-stream",
                        key=f"download_contract_{propiedad_id}"
                    )
                else:
                    st.write("Archivo de contrato no encontrado.")
            else:
                st.write("No se ha subido ningún contrato.")

            if st.button("Modificar Datos del Inquilino"):
                st.session_state['confirm_edit'] = not st.session_state['confirm_edit']
                if st.session_state['confirm_edit']:
                     st.warning("¡Está a punto de modificar los datos del arrendatario actual! ¿Está seguro?")


            if st.session_state['confirm_edit']:
                 with st.form(key=f"form_propiedad_{propiedad_id}"):
                    valor_renta = st.number_input("Valor Renta", value=propiedad_data['valor_renta'] if propiedad_data['valor_renta'] is not None else 0.0, min_value=0.0)
                    arrendatario = st.text_input("Arrendatario", value=propiedad_data['arrendatario'] if propiedad_data['arrendatario'] else '')
                    fecha_inicio_str = propiedad_data['fecha_inicio']
                    fecha_inicio_date = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else None
                    fecha_inicio = st.date_input("Fecha Inicio", value=fecha_inicio_date if fecha_inicio_date else datetime.now().date())
                    garantia = st.checkbox("Garantía", value=bool(propiedad_data['garantia']))
                    monto_deposito = st.number_input("Monto Deposito", value=propiedad_data['monto_deposito'] if propiedad_data['monto_deposito'] is not None else 0.0, min_value=0.0)

                    uploaded_contract_file = st.file_uploader("Subir Contrato (Opcional)", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"], key=f"uploader_contract_{propiedad_id}")


                    submit_button = st.form_submit_button(label="Guardar Cambios")

                    if submit_button:
                        if arrendatario and not re.match('^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]+$', arrendatario):
                            st.error('Solo letras y espacios en el nombre del arrendatario.')
                        else:
                            contract_filename = propiedad_data['comprobante_contrato']
                            if uploaded_contract_file is not None:
                                try:
                                    filename = secure_filename(uploaded_contract_file.name)
                                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(uploaded_contract_file.getbuffer())
                                    contract_filename = filename
                                    st.success("Archivo de contrato subido exitosamente.")
                                except Exception as e:
                                    st.error(f"Error al subir el archivo de contrato: {e}")
                                    contract_filename = propiedad_data['comprobante_contrato']


                            execute_db('''
                                UPDATE propiedades
                                SET valor_renta = ?,
                                    arrendatario = ?,
                                    fecha_inicio = ?,
                                    garantia = ?,
                                    monto_deposito = ?,
                                    comprobante_contrato = ?
                                WHERE propiedad_id = ?
                            ''', (valor_renta, arrendatario, fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else None, int(garantia), monto_deposito, contract_filename, propiedad_id))
                            st.success("Datos de la propiedad actualizados")
                            st.session_state['confirm_edit'] = False
                            st.rerun()


        st.subheader("Control de Pagos y Comprobantes")

        st.write("Subir nuevo comprobante:")
        # --- MODIFIED: File uploader and separate save button ---
        uploaded_file = st.file_uploader("Seleccionar archivo", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_{propiedad_id}")
        mes_pago = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], key=f"mes_{propiedad_id}")
        anio_pago = st.number_input("Año", min_value=2000, max_value=2030, value=datetime.now().year, key=f"anio_{propiedad_id}")

        # Only show save button if a file is uploaded
        if uploaded_file is not None:
            if st.button("Guardar Comprobante", key=f"save_comprobante_{propiedad_id}"):
                try:
                    filename = secure_filename(uploaded_file.name)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    existing_comprobante = query_db("SELECT id FROM comprobantes WHERE propiedad_id = ? AND nombre = ? AND mes = ? AND anio = ?", (propiedad_id, filename, mes_pago, anio_pago), one=True)

                    if existing_comprobante is None:
                        with open(filepath, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        execute_db('INSERT INTO comprobantes (propiedad_id, nombre, mes, anio) VALUES (?, ?, ?, ?)', (propiedad_id, filename, mes_pago, anio_pago))
                        st.success("Comprobante guardado")

                        # --- No explicit state clearing needed here with the button approach ---
                        st.rerun()
                    else:
                        st.info(f"Un comprobante con el nombre '{filename}' para {mes_pago} {anio_pago} ya existe para esta propiedad.")
                        # --- No explicit state clearing needed here ---
                        st.rerun()


                except Exception as e:
                    st.error(f"Error al guardar el comprobante: {e}")
                    # --- No explicit state clearing needed here ---
                    st.rerun()


        comprobantes = query_db('''
            SELECT * FROM comprobantes
            WHERE propiedad_id = ?
            ORDER BY anio DESC,
                     CASE mes
                         WHEN "Enero" THEN 1
                         WHEN "Febrero" THEN 2
                         WHEN "Marzo" THEN 3
                         WHEN "Abril" THEN 4
                         WHEN "Mayo" THEN 5
                         WHEN "Junio" THEN 6
                         WHEN "Julio" THEN 7
                         WHEN "Agosto" THEN 8
                         WHEN "Septiembre" THEN 9
                         WHEN "Octubre" THEN 10
                         WHEN "Noviembre" THEN 11
                         WHEN "Diciembre" THEN 12
                     END DESC
        ''', (propiedad_id,))

        data = []

        if comprobantes:
            st.subheader("Comprobantes Subidos")
            for comprobante in comprobantes:
                filepath = os.path.join(UPLOAD_FOLDER, comprobante['nombre'])

                if os.path.exists(filepath):
                    file_extension = os.path.splitext(comprobante['nombre'])[1].lower()
                    if file_extension in ['.png', '.jpg', '.jpeg']:
                        with open(filepath, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode()
                        file_preview_html = f'<img src="data:image/png;base64,{encoded_string}" width="100">'
                        download_link_html = f'<a href="data:image/png;base64,{encoded_string}" download="{comprobante["nombre"]}">Descargar</a>'
                    elif file_extension == '.pdf':
                        with open(filepath, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        file_preview_html = "PDF"
                        download_link_html = f'<a href="data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}" download="{comprobante["nombre"]}">Descargar PDF</a>'
                    else:
                         file_preview_html = "Tipo de archivo no soportado"
                         download_link_html = "Descargar Archivo"

                    data.append({
                        "ID": comprobante['id'],
                        "Mes / Año": f"{comprobante['mes']} {comprobante['anio']}",
                        "Previsualización": file_preview_html,
                        "Descargar": download_link_html
                    })
                else:
                    data.append({
                         "ID": comprobante['id'],
                        "Mes / Año": f"{comprobante['mes']} {comprobante['anio']}",
                        "Previsualización": "Archivo no encontrado",
                        "Descargar": "Archivo no encontrado"
                    })

            df_comprobantes = pd.DataFrame(data)
            st.write(df_comprobantes[['ID', 'Mes / Año', 'Previsualización', 'Descargar']].to_html(escape=False, index=False), unsafe_allow_html=True)


            st.subheader("Eliminar Comprobante por ID")
            comprobante_ids = [c['id'] for c in comprobantes] if comprobantes else []
            comprobante_to_delete_id = st.selectbox("Seleccione el ID del comprobante a eliminar:", comprobante_ids, key="delete_comprobante_selectbox")

            if st.button("Confirmar Eliminación"):
                if comprobante_to_delete_id is not None:
                    comprobante_data_to_delete = query_db("SELECT nombre FROM comprobantes WHERE id = ?", (comprobante_to_delete_id,), one=True)
                    if comprobante_data_to_delete and comprobante_data_to_delete['nombre']:
                        filepath_to_delete = os.path.join(UPLOAD_FOLDER, comprobante_data_to_delete['nombre'])
                        if os.path.exists(filepath_to_delete):
                            try:
                                os.remove(filepath_to_delete)
                            except Exception as e:
                                st.error(f"Error al eliminar el archivo {comprobante_data_to_delete['nombre']}: {e}")

                    execute_db("DELETE FROM comprobantes WHERE id = ?", (comprobante_to_delete_id,))
                    st.success(f"Comprobante con ID {comprobante_to_delete_id} eliminado de la base de datos.")
                    st.rerun()
                else:
                    st.info("Seleccione un comprobante para eliminar.")
        else:
            st.info("No hay comprobantes subidos para esta propiedad.")


if __name__ == "__main__":
    main()