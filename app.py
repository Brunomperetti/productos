import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Tienda Natural", layout="wide")

# --- CONFIG ---
PASSWORD = "mipassword123"
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

        st.markdown("Ingresá hasta 20 productos con nombre, descripción, precio y un link a una imagen (de Imgur, Google Drive, etc.):")
        productos = []
        for i in range(MAX_PRODUCTOS):
            with st.expander(f"Producto {i + 1}", expanded=False):
                nombre = st.text_input("Nombre del producto", key=f"nombre_{i}")
                descripcion = st.text_area("Descripción del producto", key=f"descripcion_{i}", height=100)
                precio = st.number_input("Precio ($)", min_value=0.0, step=0.1, key=f"precio_{i}")
                imagen_url = st.text_input("Link de imagen pública (Imgur, Drive)", key=f"imagen_url_{i}")
                
                if imagen_url:
                    st.image(image, use_container_width=True)
                
                if nombre and precio and imagen_url:
                    productos.append({
                        "nombre": nombre,
                        "descripcion": descripcion,
                        "precio": precio,
                        "imagen": imagen_url
                    })

        if st.button("Guardar productos"):
            st.session_state.productos = productos
            st.success("✅ Productos guardados para los clientes")
    else:
        st.warning("🔒 Ingresá la clave para editar productos.")

# --- MODO CLIENTE ---
elif modo == "Cliente":
    if not st.session_state.productos:
        st.info("Todavía no hay productos cargados. Vuelve más tarde.")
    else:
        st.markdown("### 🧴 Productos disponibles:")
        cantidades = []

        productos = st.session_state.productos
        for i in range(0, len(productos), 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(productos):
                    with cols[j]:
                        producto = productos[idx]
                        st.image(producto["imagen"], use_column_width=True, caption=producto["nombre"])
                        st.markdown(
                            f"<div style='margin-bottom: 10px; font-size: 14px; color: #444'>{producto['descripcion']}</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(f"<div style='font-size: 16px; font-weight: bold;'>💰 Precio: ${producto['precio']}</div>",
                                    unsafe_allow_html=True)
                        cantidad = st.number_input(
                            f"Cantidad ({producto['nombre']})",
                            min_value=0,
                            step=1,
                            key=f"cantidad_cliente_{idx}",
                        )
                        cantidades.append(cantidad)

        st.markdown("---")
        st.markdown("### 🧾 Tus datos:")
        nombre_cliente = st.text_input("🧍 Tu nombre")
        email_cliente = st.text_input("📧 Tu email")

        if st.button("✅ Comprar"):
            data = []
            total = 0
            for i, cant in enumerate(cantidades):
                if cant > 0:
                    subtotal = cant * productos[i]["precio"]
                    total += subtotal
                    data.append({
                        "Producto": productos[i]["nombre"],
                        "Descripción": productos[i]["descripcion"],
                        "Precio Unitario": productos[i]["precio"],
                        "Cantidad": cant,
                        "Subtotal": subtotal
                    })

            df = pd.DataFrame(data)
            df.loc[len(df.index)] = ["", "", "", "TOTAL", total]

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Pedido")
                pd.DataFrame({"Cliente": [nombre_cliente], "Email": [email_cliente]}).to_excel(writer, sheet_name="Datos")

            st.success("✅ ¡Pedido generado!")
            st.download_button("📥 Descargar pedido en Excel", data=output.getvalue(), file_name="pedido.xlsx")


