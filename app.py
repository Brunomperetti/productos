import streamlit as st
import pandas as pd
from io import BytesIO
import re
import json # Importar la librería para trabajar con JSON
import os # Importar para verificar si el archivo existe

st.set_page_config(page_title="Productos para Mascotas", layout="wide")

# --- CONFIG ---
PASSWORD = "mipassword123" # Considera usar st.secrets para más seguridad si despliegas la app
MAX_PRODUCTOS = 20
PRODUCTOS_FILE = "productos.json" # Nombre del archivo donde guardaremos los productos

# --- Funciones para cargar y guardar productos ---
def cargar_productos(filename=PRODUCTOS_FILE):
    """Carga los productos desde un archivo JSON."""
    if os.path.exists(filename):
        with open(filename, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Manejar el caso de que el archivo esté vacío o mal formateado
                return []
    return [] # Devuelve una lista vacía si el archivo no existe

def guardar_productos(productos, filename=PRODUCTOS_FILE):
    """Guarda la lista de productos en un archivo JSON."""
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)

# --- SESSION STATE ---
# Intentar cargar productos del archivo al inicio de la aplicación/sesión
if 'productos' not in st.session_state:
    st.session_state.productos = cargar_productos()

st.title("🛍️ Novedades Millex")

# --- Modo de uso ---
modo = st.radio("Seleccioná el modo de acceso:", ["Cliente", "Admin 🔐"], horizontal=True)

if modo == "Admin 🔐":
    clave = st.text_input("Ingresá la clave para editar productos", type="password")
    if clave == PASSWORD:
        st.success("🔓 Acceso concedido")

        st.markdown("Ingresá hasta 20 productos con nombre, descripción, precio y un link a una imagen pública (de Imgur, Google Drive, etc.):")

        # Usaremos una lista temporal para recolectar los productos en esta sesión de edición
        productos_editados = []
        # Cargamos los productos existentes directamente del session_state (que ya se llenó desde el archivo)
        productos_actuales = st.session_state.productos[:] # Copia para no modificar el state directamente aún

        # Asegurarse de tener suficientes slots si hay menos de MAX_PRODUCTOS guardados
        for i in range(max(MAX_PRODUCTOS, len(productos_actuales) + 1)): # Mostrar al menos un slot vacío si hay productos
            # Pre-llenar con datos existentes si el índice es válido
            datos_actuales = productos_actuales[i] if i < len(productos_actuales) else {}
            nombre_actual = datos_actuales.get("nombre", "")
            descripcion_actual = datos_actuales.get("descripcion", "")
            precio_actual = datos_actuales.get("precio", 0.0)
            imagen_actual = datos_actuales.get("imagen", "")

            # Solo mostrar expander si hay datos o es el primer slot vacío
            if i < len(productos_actuales) or i == len(productos_actuales): # Mostrar slots existentes y el siguiente vacío
                 with st.expander(f"Producto {i + 1}", expanded= (nombre_actual !="") or i == len(productos_actuales) ): # Expandir si ya tiene nombre o es el primer slot vacío
                    nombre = st.text_input("Nombre del producto", value=nombre_actual, key=f"nombre_{i}")
                    descripcion = st.text_area("Descripción del producto", value=descripcion_actual, key=f"descripcion_{i}", height=100)
                    precio = st.number_input("Precio ($)", value=precio_actual, min_value=0.0, step=0.1, key=f"precio_{i}")

                    # --- INICIO: MODIFICACIÓN MANEJO DE IMAGEN ---
                    imagen_url_input = st.text_input(
                        "Link de imagen pública (Imgur, Drive)",
                        value=imagen_actual,
                        key=f"imagen_url_{i}"
                    )

                    imagen_url_para_mostrar = imagen_url_input

                    if imagen_url_input:
                        if 'drive.google.com' in imagen_url_input and '/file/d/' in imagen_url_input:
                            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', imagen_url_input)
                            if match:
                                file_id = match.group(1)
                                imagen_url_para_mostrar = f'https://drive.google.com/uc?export=view&id={file_id}'
                            else:
                                if 'uc?id=' not in imagen_url_input and 'uc?export=view&id=' not in imagen_url_input:
                                     st.warning(f"Formato del link de Google Drive no reconocido para transformar ({imagen_url_input}). Se usará como está. Verifica los permisos.", icon="⚠️")
                                imagen_url_para_mostrar = imagen_url_input

                        try:
                            st.image(imagen_url_para_mostrar, use_container_width=True)
                        except Exception as e:
                            st.error(f"No se pudo cargar la previsualización. Verifica el link y los permisos ('Cualquier persona con el enlace'). Error: {e}", icon="🖼️")

                    # Añadir a la lista si tiene los datos básicos (nombre, precio > 0, y una URL de imagen ingresada)
                    if nombre and precio > 0 and imagen_url_input:
                        productos_editados.append({
                            "nombre": nombre,
                            "descripcion": descripcion,
                            "precio": precio,
                            "imagen": imagen_url_para_mostrar # Guardar la URL que se usa para mostrar
                        })
                    elif nombre or descripcion or precio > 0 or imagen_url_input:
                         pass # Ignorar si hay campos incompletos pero algo se ingresó
                    # --- FIN: MODIFICACIÓN MANEJO DE IMAGEN ---

        # Solo mostrar el botón Guardar si hay al menos un producto editado con datos
        if productos_editados:
            if st.button("💾 Guardar Cambios"):
                # Filtrar productos vacíos (si el admin borró todos los datos de un slot que antes tenía)
                productos_finales = [p for p in productos_editados if p["nombre"] and p["precio"] > 0 and p["imagen"]]

                # --- Paso crucial: Guardar los productos en el archivo ---
                guardar_productos(productos_finales)

                # Actualizar el session state con los productos guardados para reflejar en la vista actual del admin
                st.session_state.productos = productos_finales

                st.success(f"✅ ¡{len(productos_finales)} Productos guardados para los clientes!")
                st.rerun() # Refrescar para que el modo cliente cargue desde el archivo actualizado

    elif clave != "" :
        st.error("🔑 Clave incorrecta.")
    else:
        st.warning("🔒 Ingresá la clave para editar productos.")


# --- MODO CLIENTE ---
elif modo == "Cliente":
    # El session_state.productos ya contiene los productos cargados desde el archivo al inicio
    if not st.session_state.productos:
        st.info("Todavía no hay productos cargados. Vuelve más tarde.")
    else:
        st.markdown("### 🧴 Productos disponibles:")
        cantidades = {}
        productos_disponibles = st.session_state.productos
        column_count = 3
        columns = st.columns(column_count)

        # Usar enumerate con el rango de productos_disponibles
        for idx, producto in enumerate(productos_disponibles):
             col = columns[idx % column_count]
             with col:
                 st.image(producto["imagen"], use_container_width=True, caption=f"{producto['nombre']} (${producto['precio']:.2f})")
                 with st.expander("Descripción"):
                     st.markdown(
                         f"<div style='font-size: 14px; color: #444'>{producto['descripcion']}</div>",
                         unsafe_allow_html=True
                     )

                 cantidad = st.number_input(
                     f"Cantidad",
                     min_value=0,
                     step=1,
                     key=f"cantidad_cliente_{idx}",
                     value=0
                 )
                 if cantidad > 0:
                     cantidades[idx] = cantidad

        st.markdown("---")

        if cantidades:
             st.markdown("### 🛒 Tu Pedido:")
             total = 0
             pedido_items = []
             for idx, cant in cantidades.items():
                  producto = productos_disponibles[idx]
                  subtotal = cant * producto["precio"]
                  total += subtotal
                  pedido_items.append(f"- {cant} x {producto['nombre']} (${producto['precio']:.2f} c/u) = ${subtotal:.2f}")

             st.markdown("\n".join(pedido_items))
             st.markdown(f"**Total del Pedido: ${total:.2f}**")
             st.markdown("---")

             st.markdown("### 🧾 Tus datos para generar el Excel:")
             nombre_cliente = st.text_input("🧍 Tu nombre")
             email_cliente = st.text_input("📧 Tu email")

             if st.button("✅ Generar Excel del Pedido"):
                  if nombre_cliente and email_cliente:
                      data = []
                      total_final = 0
                      for idx, cant in cantidades.items():
                           producto = productos_disponibles[idx]
                           subtotal = cant * producto["precio"]
                           total_final += subtotal
                           data.append({
                               "Producto": producto["nombre"],
                               "Descripción": producto["descripcion"],
                               "Precio Unitario": f"${producto['precio']:.2f}",
                               "Cantidad": cant,
                               "Subtotal": f"${subtotal:.2f}"
                           })

                      df = pd.DataFrame(data)
                      df.loc[len(df.index)] = ["", "", "", "TOTAL", f"${total_final:.2f}"]

                      output = BytesIO()
                      with pd.ExcelWriter(output, engine="openpyxl") as writer:
                           df.to_excel(writer, index=False, sheet_name="Pedido")
                           pd.DataFrame({"Cliente": [nombre_cliente], "Email": [email_cliente]}).to_excel(writer, index=False, sheet_name="Datos Cliente")

                      st.success("✅ ¡Archivo Excel generado!")
                      st.download_button(
                           label="📥 Descargar pedido en Excel",
                           data=output.getvalue(),
                           file_name=f"pedido_{nombre_cliente.replace(' ', '_')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                      )
                  else:
                      st.warning("⚠️ Por favor, ingresa tu nombre y email para generar el archivo.")
        else:
             st.info("Selecciona la cantidad de los productos que deseas comprar.")





