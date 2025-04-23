import streamlit as st
import pandas as pd
from io import BytesIO
import re
import json
import os
import urllib.parse # Importar para codificar texto para URL

st.set_page_config(page_title="Tienda Natural", layout="wide")

# --- CONFIG ---
PASSWORD = "mipassword123" # Considera usar st.secrets para más seguridad si despliegas la app
MAX_PRODUCTOS = 20
PRODUCTOS_FILE = "productos.json" # Nombre del archivo donde guardaremos los productos
# --- NUEVO: Número de WhatsApp para pedidos ---
WHATSAPP_PHONE_NUMBER = "5493516507867" # Reemplaza con el número de WhatsApp (incluye código de país sin el signo +)
# Ejemplo para Argentina: 5491112345678 (54 país, 9 para indicar móvil, 11 código de área, resto el número)


# --- Funciones para cargar y guardar productos ---
def cargar_productos(filename=PRODUCTOS_FILE):
    """Carga los productos desde un archivo JSON."""
    if os.path.exists(filename):
        with open(filename, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Devuelve una lista vacía si el archivo está vacío o mal formateado
    return [] # Devuelve una lista vacía si el archivo no existe

def guardar_productos(productos, filename=PRODUCTOS_FILE):
    """Guarda la lista de productos en un archivo JSON."""
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)

# --- SESSION STATE ---
if 'productos' not in st.session_state:
    st.session_state.productos = cargar_productos()

st.title("🛍️ COTIZADOR NEWRBAN")

# --- Modo de uso ---
modo = st.radio("Seleccioná el modo de acceso:", ["Cliente", "Admin 🔐"], horizontal=True)

if modo == "Admin 🔐":
    clave = st.text_input("Ingresá la clave para editar productos", type="password")
    if clave == PASSWORD:
        st.success("🔓 Acceso concedido")

        st.markdown("Ingresá hasta 20 productos con nombre, descripción, precio y un link a una imagen pública (de Imgur, Google Drive, etc.):")

        productos_editados = []
        productos_actuales = st.session_state.productos[:]

        for i in range(max(MAX_PRODUCTOS, len(productos_actuales) + 1)):
            datos_actuales = productos_actuales[i] if i < len(productos_actuales) else {}
            nombre_actual = datos_actuales.get("nombre", "")
            descripcion_actual = datos_actuales.get("descripcion", "")
            precio_actual = datos_actuales.get("precio", 0.0)
            imagen_actual = datos_actuales.get("imagen", "")

            if i < len(productos_actuales) or i == len(productos_actuales):
                 with st.expander(f"Producto {i + 1}", expanded= (nombre_actual !="") or i == len(productos_actuales) ):
                    nombre = st.text_input("Nombre del producto", value=nombre_actual, key=f"nombre_{i}")
                    descripcion = st.text_area("Descripción del producto", value=descripcion_actual, key=f"descripcion_{i}", height=100)
                    precio = st.number_input("Precio ($)", value=precio_actual, min_value=0.0, step=0.1, key=f"precio_{i}")

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

                    if nombre and precio > 0 and imagen_url_input:
                        productos_editados.append({
                            "nombre": nombre,
                            "descripcion": descripcion,
                            "precio": precio,
                            "imagen": imagen_url_para_mostrar
                        })
                    elif nombre or descripcion or precio > 0 or imagen_url_input:
                         pass

        if productos_editados:
            if st.button("💾 Guardar Cambios"):
                productos_finales = [p for p in productos_editados if p["nombre"] and p["precio"] > 0 and p["imagen"]]
                guardar_productos(productos_finales)
                st.session_state.productos = productos_finales
                st.success(f"✅ ¡{len(productos_finales)} Productos guardados para los clientes!")
                st.rerun()

    elif clave != "" :
        st.error("🔑 Clave incorrecta.")
    else:
        st.warning("🔒 Ingresá la clave para editar productos.")


# --- MODO CLIENTE ---
elif modo == "Cliente":
    if not st.session_state.productos:
        st.info("Todavía no hay productos cargados. Vuelve más tarde.")
    else:
        st.markdown("### 🧴 Productos disponibles:")
        cantidades = {}
        productos_disponibles = st.session_state.productos
        column_count = 3
        columns = st.columns(column_count)

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
             pedido_texto = "¡Hola! Quiero hacer el siguiente pedido:\n\n" # Inicio del mensaje para WhatsApp
             pedido_items = []
             for idx, cant in cantidades.items():
                  producto = productos_disponibles[idx]
                  subtotal = cant * producto["precio"]
                  total += subtotal
                  item_linea = f"- {cant} x {producto['nombre']} (${producto['precio']:.2f} c/u) = ${subtotal:.2f}"
                  pedido_items.append(item_linea)
                  pedido_texto += item_linea + "\n" # Añadir al texto de WhatsApp

             st.markdown("\n".join(pedido_items))
             st.markdown(f"**Total del Pedido: ${total:.2f}**")
             st.markdown("---")

             st.markdown("### 🧾 Tus datos para el pedido:")
             nombre_cliente = st.text_input("🧍 Tu nombre")
             email_cliente = st.text_input("📧 Tu email")

             # Añadir datos del cliente al texto de WhatsApp si se ingresaron
             if nombre_cliente:
                 pedido_texto += f"\nDatos del cliente:\nNombre: {nombre_cliente}"
             if email_cliente:
                 pedido_texto += f"\nEmail: {email_cliente}"

             # --- NUEVO: Botón de enviar a WhatsApp ---
             if st.button("📲 Enviar Pedido por WhatsApp"):
                 if nombre_cliente and email_cliente: # Opcional: validar que ingresó nombre y email antes de enviar
                     # Codificar el texto del pedido para la URL de WhatsApp
                     mensaje_codificado = urllib.parse.quote(pedido_texto)

                     # Construir el enlace de WhatsApp
                     whatsapp_url = f"https://wa.me/{WHATSAPP_PHONE_NUMBER}?text={mensaje_codificado}"

                     # Usar st.link_button para crear el botón que abre el enlace
                     st.markdown(
                         f'<a href="{whatsapp_url}" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #25D366; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px; margin-top: 10px;">📲 Enviar Pedido por WhatsApp</a>',
                         unsafe_allow_html=True
                     )
                     st.success("¡Haz clic en el botón de WhatsApp para enviar el pedido!")
                     st.info("Se abrirá tu aplicación de WhatsApp con el mensaje listo para enviar.")

                 else:
                     st.warning("⚠️ Por favor, ingresa tu nombre y email para poder generar el mensaje de pedido.")

             # --- ELIMINAR O COMENTAR la sección del botón de Excel ---
             # if st.button("✅ Generar Excel del Pedido"):
             #    ... (código anterior para generar Excel) ...
             # --- FIN ELIMINAR O COMENTAR ---


        else:
             st.info("Selecciona la cantidad de los productos que deseas comprar.")





