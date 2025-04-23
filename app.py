import streamlit as st
import pandas as pd
from io import BytesIO
import re # <--- Añadido para procesar las URLs de Google Drive

st.set_page_config(page_title="Tienda Natural", layout="wide")

# --- CONFIG ---
PASSWORD = "mipassword123" # Considera usar st.secrets para más seguridad si despliegas la app
MAX_PRODUCTOS = 20

# --- SESSION STATE ---
if 'productos' not in st.session_state:
    st.session_state.productos = []

st.title("🛍️ COTIZADOR NEWRBAN")

# --- Modo de uso ---
modo = st.radio("Seleccioná el modo de acceso:", ["Cliente", "Admin 🔐"], horizontal=True)

if modo == "Admin 🔐":
    clave = st.text_input("Ingresá la clave para editar productos", type="password")
    if clave == PASSWORD:
        st.success("🔓 Acceso concedido")

        st.markdown("Ingresá hasta 20 productos con nombre, descripción, precio y un link a una imagen pública (de Imgur, Google Drive, etc.):")

        # Usaremos una lista temporal para recolectar los productos en esta sesión de edición
        productos_editados = []
        # Cargamos los productos existentes para pre-llenar los campos si los hay
        productos_actuales = st.session_state.productos[:] # Copia para no modificar el state directamente aún

        for i in range(MAX_PRODUCTOS):
            # Pre-llenar con datos existentes si el índice es válido
            datos_actuales = productos_actuales[i] if i < len(productos_actuales) else {}
            nombre_actual = datos_actuales.get("nombre", "")
            descripcion_actual = datos_actuales.get("descripcion", "")
            precio_actual = datos_actuales.get("precio", 0.0)
            imagen_actual = datos_actuales.get("imagen", "") # Esta será la URL ya procesada o la original si no es de GDrive


            with st.expander(f"Producto {i + 1}", expanded= (nombre_actual !="") ): # Expandir si ya tiene nombre
                nombre = st.text_input("Nombre del producto", value=nombre_actual, key=f"nombre_{i}")
                descripcion = st.text_area("Descripción del producto", value=descripcion_actual, key=f"descripcion_{i}", height=100)
                precio = st.number_input("Precio ($)", value=precio_actual, min_value=0.0, step=0.1, key=f"precio_{i}")

                # --- INICIO: MODIFICACIÓN MANEJO DE IMAGEN ---
                # Usamos la imagen 'actual' (ya procesada si es de GDrive) como valor por defecto
                # Pero permitimos al admin pegar una nueva URL (que podría ser un link de compartición de GDrive)
                imagen_url_input = st.text_input(
                    "Link de imagen pública (Imgur, Drive)",
                    value=imagen_actual,  # Mostramos la URL actual (procesada o no)
                    key=f"imagen_url_{i}"
                )

                imagen_url_para_mostrar = imagen_url_input # Por defecto, usamos la URL ingresada/actual

                if imagen_url_input:
                    # Si la URL ingresada parece ser un link de compartición de Google Drive, procesarlo
                    if 'drive.google.com' in imagen_url_input and '/file/d/' in imagen_url_input:
                        # Intenta extraer el ID del archivo usando una expresión regular
                        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', imagen_url_input)
                        if match:
                            file_id = match.group(1)
                            # Construye la URL directa para visualización
                            imagen_url_para_mostrar = f'https://drive.google.com/uc?export=view&id={file_id}'
                            # Opcional: Mostrar una nota si la URL fue transformada
                            # st.caption(f"URL de GDrive transformada a: {imagen_url_para_mostrar}")
                        else:
                             # Si tiene 'drive.google.com' pero no '/file/d/', podría ser ya 'uc?' u otro formato.
                             # Advertimos pero intentamos usarla tal cual.
                             if 'uc?id=' not in imagen_url_input and 'uc?export=view&id=' not in imagen_url_input:
                                 st.warning(f"Formato del link de Google Drive no reconocido para transformar ({imagen_url_input}). Se usará como está. Verifica los permisos.", icon="⚠️")
                             imagen_url_para_mostrar = imagen_url_input # Usar como está si no se pudo procesar

                    # Si no es de Google Drive o ya está en formato 'uc?', usamos la URL tal cual
                    # (imagen_url_para_mostrar ya tiene el valor de imagen_url_input por defecto)

                    # Previsualizar la imagen usando la URL final (procesada o no)
                    try:
                        st.image(imagen_url_para_mostrar, use_container_width=True)
                    except Exception as e:
                        st.error(f"No se pudo cargar la previsualización. Verifica el link y los permisos ('Cualquier persona con el enlace'). Error: {e}", icon="🖼️")

                # Añadir a la lista si tiene los datos básicos (nombre, precio y una URL de imagen ingresada)
                if nombre and precio > 0 and imagen_url_input: # Asegurarse que el precio sea mayor a 0 también
                    productos_editados.append({
                        "nombre": nombre,
                        "descripcion": descripcion,
                        "precio": precio,
                        "imagen": imagen_url_para_mostrar # Guardar la URL que se usa para mostrar
                    })
                elif nombre or descripcion or precio > 0 or imagen_url_input:
                     # Si el usuario ingresó algo pero falta un campo esencial (ej. precio 0 o sin imagen/nombre),
                     # podríamos querer añadir una advertencia dentro del expander.
                     # Por ahora, simplemente no se añade si falta algo esencial.
                     pass
                 # --- FIN: MODIFICACIÓN MANEJO DE IMAGEN ---

        if st.button("💾 Guardar Cambios"):
            # Filtrar productos vacíos (si el admin borró todos los datos de un slot)
            productos_finales = [p for p in productos_editados if p["nombre"] and p["precio"] > 0 and p["imagen"]]
            st.session_state.productos = productos_finales
            st.success(f"✅ ¡{len(productos_finales)} Productos guardados para los clientes!")
            st.rerun() # Refrescar para reflejar los cambios guardados

    elif clave != "" : # Si ingresó algo pero no es la clave correcta
        st.error("🔑 Clave incorrecta.")
    else: # Si no ingresó clave aún
        st.warning("🔒 Ingresá la clave para editar productos.")


# --- MODO CLIENTE ---
elif modo == "Cliente":
    if not st.session_state.productos:
        st.info("Todavía no hay productos cargados. Vuelve más tarde.")
    else:
        st.markdown("### 🧴 Productos disponibles:")
        cantidades = {} # Usar diccionario para asociar cantidad con índice de producto

        productos_disponibles = st.session_state.productos
        column_count = 3 # Puedes ajustar cuántas columnas quieres (2, 3, 4...)
        columns = st.columns(column_count)

        for idx, producto in enumerate(productos_disponibles):
            col = columns[idx % column_count] # Asignar producto a columna de forma cíclica
            with col:
                st.image(producto["imagen"], use_container_width=True, caption=f"{producto['nombre']} (${producto['precio']:.2f})")
                # Usar st.expander para la descripción si es larga
                with st.expander("Descripción"):
                     st.markdown(
                         f"<div style='font-size: 14px; color: #444'>{producto['descripcion']}</div>",
                         unsafe_allow_html=True
                     )
                # st.markdown(f"<div style='font-size: 16px; font-weight: bold; margin-top: 5px;'>💰 Precio: ${producto['precio']:.2f}</div>",
                #             unsafe_allow_html=True) # Precio ya está en el caption de la imagen

                cantidad = st.number_input(
                    f"Cantidad",# ({producto['nombre']})", # Label más corto
                    min_value=0,
                    step=1,
                    key=f"cantidad_cliente_{idx}", # Usar índice como parte de la key
                    value=0 # Asegurar que empieza en 0
                )
                if cantidad > 0:
                    cantidades[idx] = cantidad # Guardar cantidad si es mayor a 0

        st.markdown("---")

        # Solo mostrar sección de datos y botón si hay algo seleccionado
        if cantidades:
             st.markdown("### 🛒 Tu Pedido:")
             total = 0
             pedido_items = []
             for idx, cant in cantidades.items():
                 producto = productos_disponibles[idx]
                 subtotal = cant * producto["precio"]
                 total += subtotal
                 pedido_items.append(f"- {cant} x {producto['nombre']} (${producto['precio']:.2f} c/u) = ${subtotal:.2f}")
                 # Añadir datos para el DataFrame
                 # (Se generará después al presionar "Comprar")

             # Mostrar resumen del pedido antes de pedir datos
             st.markdown("\n".join(pedido_items))
             st.markdown(f"**Total del Pedido: ${total:.2f}**")
             st.markdown("---")

             st.markdown("### 🧾 Tus datos para generar el Excel:")
             nombre_cliente = st.text_input("🧍 Tu nombre")
             email_cliente = st.text_input("📧 Tu email")

             if st.button("✅ Generar Excel del Pedido"):
                 if nombre_cliente and email_cliente: # Validar que ingresó nombre y email
                     data = []
                     total_final = 0 # Recalcular por seguridad
                     for idx, cant in cantidades.items():
                         producto = productos_disponibles[idx]
                         subtotal = cant * producto["precio"]
                         total_final += subtotal
                         data.append({
                             "Producto": producto["nombre"],
                             "Descripción": producto["descripcion"],
                             "Precio Unitario": f"${producto['precio']:.2f}", # Formatear como texto para Excel
                             "Cantidad": cant,
                             "Subtotal": f"${subtotal:.2f}" # Formatear como texto para Excel
                         })

                     df = pd.DataFrame(data)
                     # Añadir fila de TOTAL al final
                     df.loc[len(df.index)] = ["", "", "", "TOTAL", f"${total_final:.2f}"]

                     output = BytesIO()
                     with pd.ExcelWriter(output, engine="openpyxl") as writer:
                         df.to_excel(writer, index=False, sheet_name="Pedido")
                         # Añadir hoja con datos del cliente
                         pd.DataFrame({"Cliente": [nombre_cliente], "Email": [email_cliente]}).to_excel(writer, index=False, sheet_name="Datos Cliente")

                     st.success("✅ ¡Archivo Excel generado!")
                     st.download_button(
                         label="📥 Descargar pedido en Excel",
                         data=output.getvalue(),
                         file_name=f"pedido_{nombre_cliente.replace(' ', '_')}.xlsx", # Nombre de archivo más descriptivo
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                     )
                 else:
                     st.warning("⚠️ Por favor, ingresa tu nombre y email para generar el archivo.")
        else:
             st.info("Selecciona la cantidad de los productos que deseas comprar.")




