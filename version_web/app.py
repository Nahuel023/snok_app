import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión 3D Web", page_icon="🌐", layout="wide")

# --- BLOQUE DE SEGURIDAD PARA LA NUBE (IMPORTANTE) ---
# Esto permite que la app funcione en Streamlit Cloud sin subir el archivo credenciales.json
if not os.path.exists("credenciales.json"):
    # Si no está el archivo físico, buscamos en los secretos de Streamlit
    if "gcp_service_account" in st.secrets:
        # Creamos el archivo temporalmente para que el backend lo pueda leer
        with open("credenciales.json", "w") as f:
            json.dump(dict(st.secrets["gcp_service_account"]), f)
    else:
        # Si estamos en local y no hay archivo, avisamos (pero no rompemos si ya existe)
        pass

# Importamos el backend DESPUÉS de asegurar que existen credenciales
from backend import BackendGestor 

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    div[data-testid="metric-container"] { background-color: #f0f2f6; padding: 10px; border-radius: 5px; color: black; }
    [data-testid="stMetricValue"] { font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAR BACKEND (Caché) ---
if 'backend' not in st.session_state:
    st.session_state.backend = BackendGestor()

backend = st.session_state.backend
cfg = backend.configuracion

# --- TÍTULO ---
st.title("🌐 Panel Web de Impresión 3D")

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🖨️ Cotizador", "📦 Stock", "📋 Historial", "🔑 Ventas", "⚙️ Config"])

# ==============================================================================
# PESTAÑA 1: COTIZADOR
# ==============================================================================
with tab1:
    col_izq, col_der = st.columns([1, 1])
    
    with col_izq:
        st.subheader("Datos Pieza")
        cli_cliente = st.text_input("Cliente")
        cli_modelo = st.text_input("Modelo")
        
        # Cargar lista de stock
        lista_stock = ["--- Manual ---"]
        datos_stock = {} 
        
        if backend.inventario:
            for item in backend.inventario:
                marca = item.get("Marca") or item.get("marca") or ""
                tipo = item.get("Tipo") or item.get("tipo") or ""
                color = item.get("Color") or item.get("color") or ""
                try:
                    p_act = float(str(item.get("Peso_Actual") or 0).replace(',', '.'))
                except: p_act = 0
                
                label = f"{marca} {tipo} - {color} ({int(p_act)}g)"
                lista_stock.append(label)
                datos_stock[label] = item
            
        seleccion = st.selectbox("Material", lista_stock)
        
        precio_kg_defecto = 0.0
        stock_seleccionado = None
        
        if seleccion != "--- Manual ---":
            item = datos_stock[seleccion]
            stock_seleccionado = item
            try:
                p_rollo = float(str(item.get("Precio_Rollo") or 0).replace(',', '.'))
                p_ini = float(str(item.get("Peso_Inicial") or 1000).replace(',', '.'))
                if p_ini > 0:
                    precio_kg_defecto = (p_rollo / p_ini) * 1000
            except: pass
            
        costo_repo = st.number_input("Costo Reposición ($/kg)", value=float(precio_kg_defecto), step=500.0)

    with col_der:
        st.subheader("Parámetros")
        peso = st.number_input("Peso (g)", min_value=0.0, step=1.0)
        c1, c2 = st.columns(2)
        horas = c1.number_input("Horas", min_value=0, step=1)
        minutos = c2.number_input("Minutos", min_value=0, max_value=59, step=1)
        tiempo_total = horas + (minutos/60)
        cantidad = st.number_input("Cantidad", min_value=1, step=1)
        
        use_margen = st.checkbox("Fallo 10%", value=True)
        margen = 0.10 if use_margen else 0.0
        
        use_diseno = st.checkbox("Diseño 3D")
        hs_diseno = st.number_input("Hs Diseño", disabled=not use_diseno) if use_diseno else 0

    if st.button("CALCULAR 🧮", type="primary"):
        peso_real = peso * (1 + margen)
        costo_mat = (peso_real / 1000) * costo_repo
        costo_luz = tiempo_total * cfg.get("consumo_kw", 0.2) * cfg.get("precio_kwh", 150)
        costo_maq = tiempo_total * cfg.get("precio_desgaste_hora", 200)
        
        subtotal = costo_mat + costo_luz + costo_maq
        precio_venta_unit = subtotal * (1 + cfg.get("margen_ganancia", 100)/100)
        costo_diseno = hs_diseno * cfg.get("precio_hora_diseno", 8000)
        
        total_lote = (precio_venta_unit * cantidad) + costo_diseno
        unitario = total_lote / cantidad
        
        st.success(f"💰 TOTAL: ${total_lote:,.2f}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Unitario", f"${unitario:,.2f}")
        c2.metric("Costo Puro", f"${subtotal:,.2f}")
        c3.metric("Material Total", f"{peso_real*cantidad:.0f}g")

        st.session_state.calc = {
            "total": total_lote, "unit": unitario, "peso": peso, 
            "cant": cantidad, "stock": stock_seleccionado, 
            "cli": cli_cliente, "mod": cli_modelo, "peso_real": peso_real,
            "horas": horas, "min": minutos, "diseno": hs_diseno, "mat_nom": seleccion
        }

    if 'calc' in st.session_state:
        if st.button("💾 GUARDAR"):
            d = st.session_state.calc
            if not d['cli']:
                st.error("Falta Cliente")
            else:
                if d['stock']:
                    id_rollo = d['stock'].get("ID")
                    if id_rollo:
                        backend.descontar_stock(id_rollo, d['peso_real']*d['cant'])
                
                fila = [
                    datetime.now().strftime("%d/%m/%Y"), "Web", d['cli'], d['mod'],
                    "Impresión", d['mat_nom'], "-", d['peso'], f"{d['horas']}h {d['min']}m",
                    d['cant'], f"{d['diseno']}h", f"${d['total']:.2f}", f"${d['unit']:.2f}"
                ]
                if backend.guardar_fila_historial(fila):
                    st.toast("✅ Guardado en Drive!")
                    del st.session_state.calc
                else:
                    st.error("Error de conexión con Drive")

# ==============================================================================
# PESTAÑA 2: STOCK
# ==============================================================================
with tab2:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("#### Nuevo Rollo")
        with st.form("stock_add"):
            marca = st.selectbox("Marca", ["Generic", "Elegoo", "Grilon", "Printalot", "BambuLab"])
            tipo = st.selectbox("Tipo", ["PLA", "PETG", "ABS", "TPU"])
            color = st.text_input("Color")
            peso = st.number_input("Peso (g)", 1000)
            precio = st.number_input("Precio ($)", 20000)
            if st.form_submit_button("Agregar"):
                fila = [datetime.now().strftime("%d/%m/%Y"), marca, tipo, color, "Std", peso, peso, precio]
                backend.agregar_stock_nube(fila)
                st.rerun()
                
    with col2:
        st.markdown("#### Inventario Nube")
        if st.button("🔄 Refrescar"):
            backend.forzar_descarga_inventario()
            st.rerun()
            
        if backend.inventario:
            df = pd.DataFrame(backend.inventario)
            cols = [c for c in ["Marca", "Tipo", "Color", "Peso_Actual"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True)

# ==============================================================================
# PESTAÑA 3: HISTORIAL
# ==============================================================================
with tab3:
    if st.button("🔄 Actualizar Tabla"):
        st.rerun()
    data = backend.obtener_historial_completo()
    if data:
        st.dataframe(pd.DataFrame(data[1:], columns=data[0]), use_container_width=True)

# ==============================================================================
# PESTAÑA 4: VENTAS RÁPIDAS
# ==============================================================================
with tab4:
    st.info("Ventas de mostrador (Llaveros, impresiones stock)")
    with st.form("ventas"):
        v_cli = st.text_input("Cliente")
        v_prod = st.text_input("Producto")
        v_cant = st.number_input("Cantidad", 1)
        v_pre = st.number_input("Precio Unitario", 500)
        if st.form_submit_button("Registrar Venta"):
            tot = v_cant * v_pre
            fila = [datetime.now().strftime("%d/%m/%Y"), "Web", v_cli, v_prod, "Directa", "-", "-", 0, "-", v_cant, "-", f"${tot}", f"${v_pre}"]
            backend.guardar_fila_historial(fila)
            st.success("Venta guardada")

# ==============================================================================
# PESTAÑA 5: CONFIGURACIÓN
# ==============================================================================
with tab5:
    with st.form("conf"):
        st.write("Ajustes Locales (Web)")
        nkwh = st.number_input("Precio KWh", value=float(cfg.get("precio_kwh", 150)))
        ncon = st.number_input("Consumo kW", value=float(cfg.get("consumo_kw", 0.2)))
        ngan = st.number_input("Ganancia %", value=int(cfg.get("margen_ganancia", 100)))
        ndes = st.number_input("Desgaste $/h", value=int(cfg.get("precio_desgaste_hora", 200)))
        
        if st.form_submit_button("Guardar"):
            backend.configuracion.update({"precio_kwh": nkwh, "consumo_kw": ncon, "margen_ganancia": ngan, "precio_desgaste_hora": ndes})
            backend.save_local_config()
            st.success("Guardado temporalmente")