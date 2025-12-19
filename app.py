import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- BLOQUE DE SEGURIDAD (CONTRASEÑA) ---
def check_password():
    """Retorna `True` si el usuario tiene la contraseña correcta."""

    def password_entered():
        """Chequea si la contraseña ingresada coincide con la secreta."""
        if st.session_state["password"] == "CN-revolution": # <--- CAMBIA TU CONTRASEÑA AQUÍ
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Borra la contraseña del estado por seguridad
        else:
            st.session_state["password_correct"] = False

    # Verifica si la contraseña ya fue validada
    if "password_correct" not in st.session_state:
        # Primera vez que entra, muestra el input
        st.text_input(
            "🔑 Introduce la contraseña del equipo:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Contraseña incorrecta
        st.text_input(
            "🔑 Introduce la contraseña del equipo:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Contraseña incorrecta")
        return False
    else:
        # Contraseña correcta
        return True

if not check_password():
    st.stop() # DETIENE TODA LA EJECUCIÓN SI NO HAY LOGIN

# --- AQUÍ EMPIEZA TU DASHBOARD NORMALMENTE ---
st.title("🚀 Creamos Negocios - Dashboard")
# ... resto del código ...

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Creamos Negocios - Dashboard", layout="wide", page_icon="🚀")
st.title("🚀 Creamos Negocios - Dashboard")

# --- 2. CARGA DE DATOS ---
@st.cache_data(ttl=300) # Se actualiza solo cada 5 minutos para ser rápido
def cargar_datos():
    # TUS LINKS REALES
    url_ventas = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQuXaPCen61slzpr1TElxXoCROIxAgmgWT7pyWvel1dxq_Z_U1yZPrVrTbJfx9MwaL8_cluY3v2ywoB/pub?gid=0&single=true&output=csv"
    url_gastos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGOLgPTDLie5gEbkViCbpebWfN9S_eb2h2GGlpWLjmfVgzfnwR_ncVTs4IqmKgmAFfxZTQHJlMBrIi/pub?gid=0&single=true&output=csv"

    # PROCESAR VENTAS
    try:
        df_v = pd.read_csv(url_ventas)
        df_v['Fecha'] = pd.to_datetime(df_v['Fecha'], dayfirst=True, errors='coerce')
        # Limpiar dinero
        if df_v['Monto ($)'].dtype == 'O': 
            df_v['Monto ($)'] = df_v['Monto ($)'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_v['Monto ($)'] = pd.to_numeric(df_v['Monto ($)'], errors='coerce').fillna(0)
        
        # Rellenar nulos
        df_v['Closer'] = df_v['Closer'].fillna("Sin Asignar")
        df_v['Resultado'] = df_v['Resultado'].fillna("Pendiente")
        
        # Clasificar Estado
        def clasificar_estado(texto):
            texto = str(texto).lower()
            if "venta" in texto: return "✅ Venta"
            if "no show" in texto: return "❌ No Show"
            if "descalificado" in texto: return "🚫 Descalificado"
            if "seguimiento" in texto: return "👀 Seguimiento"
            if "re-agendado" in texto or "reagendado" in texto: return "📅 Re-Agendado"
            return "Otro/Pendiente"
        df_v['Estado_Simple'] = df_v['Resultado'].apply(clasificar_estado)

        # Asistencia Estricta
        def es_asistencia_valida(row):
            res = str(row['Resultado']).lower()
            if "venta" in res: return True
            if "seguimiento" in res: return True 
            if "asistió" in res and "no show" not in res: return True
            return False
        df_v['Es_Asistencia'] = df_v.apply(es_asistencia_valida, axis=1)

    except Exception as e:
        st.error(f"Error cargando Ventas: {e}")
        df_v = pd.DataFrame()

    # PROCESAR GASTOS
    try:
        df_g = pd.read_csv(url_gastos)
        df_g['Fecha'] = pd.to_datetime(df_g['Fecha'], dayfirst=True, errors='coerce')
        if df_g['Gasto'].dtype == 'O':
            df_g['Gasto'] = df_g['Gasto'].astype(str).str.replace(r'[$,]', '', regex=True)
        df_g['Gasto'] = pd.to_numeric(df_g['Gasto'], errors='coerce').fillna(0)
    except Exception as e:
        df_g = pd.DataFrame()

    return df_v, df_g

# Cargar
df_ventas, df_gastos = cargar_datos()

if df_ventas.empty:
    st.warning("Esperando datos... Revisa conexión.")
    st.stop()

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("🎛️ Panel de Control")

# Botón manual para forzar actualización si tienes prisa
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# --- FILTRO DE FECHAS INTELIGENTE ---
filtro_tiempo = st.sidebar.selectbox(
    "Selecciona Período:",
    ["Hoy", "Ayer", "Esta Semana", "Últimos 7 días", "Este Mes", "Últimos 30 días", "Personalizado"]
)

hoy = pd.to_datetime("today").date()

if filtro_tiempo == "Hoy":
    f_inicio, f_fin = hoy, hoy
elif filtro_tiempo == "Ayer":
    f_inicio, f_fin = hoy - timedelta(days=1), hoy - timedelta(days=1)
elif filtro_tiempo == "Esta Semana": # Lunes a Hoy
    f_inicio = hoy - timedelta(days=hoy.weekday())
    f_fin = hoy
elif filtro_tiempo == "Últimos 7 días":
    f_inicio, f_fin = hoy - timedelta(days=7), hoy
elif filtro_tiempo == "Este Mes":
    f_inicio, f_fin = hoy.replace(day=1), hoy
elif filtro_tiempo == "Últimos 30 días":
    f_inicio, f_fin = hoy - timedelta(days=30), hoy
else: # Personalizado
    st.sidebar.markdown("---")
    f_inicio = st.sidebar.date_input("Inicio", hoy)
    f_fin = st.sidebar.date_input("Fin", hoy)

# --- FILTRO CLOSER ---
lista_closers = ["Todos"] + sorted([c for c in df_ventas['Closer'].unique() if c])
closer_sel = st.sidebar.selectbox("Closer", lista_closers)

st.sidebar.info(f"📅 Visualizando: {f_inicio} al {f_fin}")

# --- APLICAR FILTROS ---
mask_v = (df_ventas['Fecha'].dt.date >= f_inicio) & (df_ventas['Fecha'].dt.date <= f_fin)
df_v_filtrado = df_ventas.loc[mask_v].copy()

if not df_gastos.empty:
    mask_g = (df_gastos['Fecha'].dt.date >= f_inicio) & (df_gastos['Fecha'].dt.date <= f_fin)
    df_g_filtrado = df_gastos.loc[mask_g].copy()
else:
    df_g_filtrado = pd.DataFrame(columns=['Fecha', 'Gasto'])

if closer_sel != "Todos":
    df_v_filtrado = df_v_filtrado[df_v_filtrado['Closer'] == closer_sel]

# --- 4. CÁLCULOS KPI ---
total_leads = len(df_v_filtrado)
total_asistencias = df_v_filtrado['Es_Asistencia'].sum()
ventas_cerradas = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])

facturacion = df_v_filtrado['Monto ($)'].sum()
inversion_ads = df_g_filtrado['Gasto'].sum() if closer_sel == "Todos" else 0
profit = facturacion - inversion_ads 
roas = (facturacion / inversion_ads) if inversion_ads > 0 else 0

tasa_asistencia = (total_asistencias / total_leads * 100) if total_leads > 0 else 0
tasa_cierre = (ventas_cerradas / total_asistencias * 100) if total_asistencias > 0 else 0

# --- 5. VISUALIZACIÓN ---

# FILA 1: FINANZAS
st.markdown("### 💰 Estado Financiero")
k1, k2, k3, k4 = st.columns(4)

k1.metric("Facturación", f"${facturacion:,.0f}")

# LÓGICA COLOR PROFIT: Verde si > 0, Rojo si < 0
k2.metric("Profit", f"${profit:,.0f}", delta=profit)

k3.metric("Inversión Ads", f"${inversion_ads:,.0f}")

# LÓGICA COLOR ROAS: Verde si > 1, Rojo si < 1
# Truco: Delta compara contra 0. Restamos 1 al ROAS.
# Si ROAS es 1.5 -> Delta 0.5 (Verde). Si ROAS es 0.8 -> Delta -0.2 (Rojo).
delta_roas = roas - 1
k4.metric("ROAS", f"{roas:.2f}x", delta=f"{delta_roas:.2f} vs Objetivo" if roas > 0 else 0)

st.divider()

# FILA 2: EFICIENCIA
st.markdown("### 📞 Eficiencia Comercial")
e1, e2, e3, e4 = st.columns(4)
e1.metric("Total Leads", total_leads)
e2.metric("Asistencias", total_asistencias, help="Ventas + Seguimiento")
e3.metric("Tasa Asistencia", f"{tasa_asistencia:.1f}%")
e4.metric("Tasa Cierre", f"{tasa_cierre:.1f}%")

# --- WIDGET ---
st.markdown("---")
st.subheader("🔍 Desglose de Leads (Widget)")

# Contadores
c_venta = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "✅ Venta"])
c_noshow = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "❌ No Show"])
c_descalif = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "🚫 Descalificado"])
c_agendado = len(df_v_filtrado[df_v_filtrado['Estado_Simple'].isin(["📅 Re-Agendado", "Otro/Pendiente"])])
c_seguimiento = len(df_v_filtrado[df_v_filtrado['Estado_Simple'] == "👀 Seguimiento"])

w1, w2, w3, w4, w5 = st.columns(5)
w1.metric("✅ Ventas", c_venta)
w2.metric("👀 Seguimiento", c_seguimiento)
w3.metric("❌ No Show", c_noshow)
w4.metric("🚫 Descalif.", c_descalif)
w5.metric("📅 Agend/Otro", c_agendado)

# GRÁFICO BARRAS
if not df_v_filtrado.empty:
    daily_status = df_v_filtrado.groupby(['Fecha', 'Estado_Simple']).size().reset_index(name='Cantidad')
    fig_status = px.bar(
        daily_status, x="Fecha", y="Cantidad", color="Estado_Simple", 
        title="Evolución Diaria de Leads",
        color_discrete_map={
            "✅ Venta": "#00CC96",          # Verde
            "❌ No Show": "#EF553B",        # Rojo
            "🚫 Descalificado": "#FFA15A",  # Naranja
            "👀 Seguimiento": "#636EFA",    # Azul fuerte
            "📅 Re-Agendado": "#AB63FA",    # Morado
            "Otro/Pendiente": "#d3d3d3"
        }
    )
    st.plotly_chart(fig_status, use_container_width=True)

# --- TABLAS ---
tab1, tab2 = st.tabs(["🏆 Ranking Closers", "📊 Facturación vs Ads"])

with tab1:
    if not df_v_filtrado.empty:
        ranking = df_v_filtrado.groupby('Closer').apply(
            lambda x: pd.Series({
                'Facturado': x['Monto ($)'].sum(),
                'Asistencias': x['Es_Asistencia'].sum(),
                'Ventas': x['Estado_Simple'].eq("✅ Venta").sum()
            })
        ).reset_index()
        ranking['% Cierre'] = (ranking['Ventas'] / ranking['Asistencias'] * 100).fillna(0)
        ranking = ranking.sort_values('Facturado', ascending=False)
        st.dataframe(ranking.style.format({'Facturado': '${:,.0f}', '% Cierre': '{:.1f}%'}), use_container_width=True)

with tab2:
    v_dia = df_v_filtrado.groupby('Fecha')['Monto ($)'].sum().reset_index()
    fig_fin = px.bar(v_dia, x='Fecha', y='Monto ($)', title="Ingresos Diarios")
    if closer_sel == "Todos" and not df_g_filtrado.empty:
        g_dia = df_g_filtrado.groupby('Fecha')['Gasto'].sum().reset_index()
        fig_fin.add_scatter(x=g_dia['Fecha'], y=g_dia['Gasto'], mode='lines+markers', name='Gasto Ads', line=dict(color='red'))
    st.plotly_chart(fig_fin, use_container_width=True)