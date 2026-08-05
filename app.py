import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO RETRO
# ==========================================
st.set_page_config(page_title="Roulette Bot Pro 3.0", layout="wide")

st.markdown("""
    <style>
    /* Fondo general gris estilo software Windows clásico */
    .stApp {
        background-color: #d4d0c8;
        font-family: 'Tahoma', 'Segoe UI', sans-serif;
    }
    
    /* Ocultar espacio vertical de los marcadores HTML */
    [data-testid="stElementContainer"]:has(.marker-red),
    [data-testid="stElementContainer"]:has(.marker-black),
    [data-testid="stElementContainer"]:has(.marker-green),
    [data-testid="stElementContainer"]:has(.green-felt-table) {
        display: none !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* TAPETE VERDE DE FIELTRO COMPLETO */
    [data-testid="stElementContainer"]:has(.green-felt-table) + [data-testid="stHorizontalBlock"] {
        background: linear-gradient(135deg, #0b6623 0%, #064016 100%) !important;
        padding: 25px 20px !important;
        border-radius: 20px !important;
        border: 5px solid #032b0e !important;
        box-shadow: inset 0 0 25px rgba(0,0,0,0.8), 0 8px 16px rgba(0,0,0,0.4) !important;
        margin-bottom: 25px !important;
        align-items: center !important;
    }

    /* BOTÓN VERDE (0) */
    [data-testid="stElementContainer"]:has(.marker-green) + [data-testid="stElementContainer"] button {
        background: linear-gradient(180deg, #2e7d32 0%, #1b5e20 100%) !important;
        border: 2px solid #ffffff !important;
        border-radius: 15px !important;
        height: 160px !important;
        width: 100% !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.6) !important;
    }

    [data-testid="stElementContainer"]:has(.marker-green) + [data-testid="stElementContainer"] button * {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 900 !important;
    }

    /* BOTONES ROJOS (Círculos) */
    [data-testid="stElementContainer"]:has(.marker-red) + [data-testid="stElementContainer"] button {
        background: linear-gradient(180deg, #e53935 0%, #b71c1c 100%) !important;
        border: 2px solid #ffffff !important;
        border-radius: 50% !important;
        height: 48px !important;
        width: 48px !important;
        min-width: 48px !important;
        margin: 4px auto !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stElementContainer"]:has(.marker-red) + [data-testid="stElementContainer"] button * {
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 900 !important;
    }

    /* BOTONES NEGROS (Círculos) */
    [data-testid="stElementContainer"]:has(.marker-black) + [data-testid="stElementContainer"] button {
        background: linear-gradient(180deg, #424242 0%, #111111 100%) !important;
        border: 2px solid #ffffff !important;
        border-radius: 50% !important;
        height: 48px !important;
        width: 48px !important;
        min-width: 48px !important;
        margin: 4px auto !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stElementContainer"]:has(.marker-black) + [data-testid="stElementContainer"] button * {
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 900 !important;
    }

    /* EFECTO HOVER (Al pasar el mouse) */
    [data-testid="stElementContainer"]:has(.marker-red) + [data-testid="stElementContainer"] button:hover,
    [data-testid="stElementContainer"]:has(.marker-black) + [data-testid="stElementContainer"] button:hover,
    [data-testid="stElementContainer"]:has(.marker-green) + [data-testid="stElementContainer"] button:hover {
        transform: scale(1.15) !important;
        border-color: #ffd700 !important;
        box-shadow: 0 0 12px #ffd700 !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Cajas de estado inferiores */
    .status-box {
        background-color: #ffffff;
        border: 2px inset #d4d0c8;
        padding: 12px;
        border-radius: 6px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A GOOGLE SHEETS
# ==========================================
@st.cache_resource
def conectar_google_sheets():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scope
        )
        client = gspread.authorize(creds)
        sheet = client.open("Ruleta_Database").worksheet("Historico_Tiros")
        return sheet
    except Exception:
        return None

sheet = conectar_google_sheets()

def guardar_tiro_en_nube(crupier, numero):
    if sheet:
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")
            sheet.append_row([fecha_actual, hora_actual, crupier, int(numero)])
        except Exception:
            pass

# ==========================================
# 3. MEMORIA DE SESIÓN (Session State)
# ==========================================
if 'historial_sesion' not in st.session_state:
    st.session_state.historial_sesion = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0
if 'caceria_activa' not in st.session_state:
    st.session_state.caceria_activa = None
if 'lista_crupieres' not in st.session_state:
    st.session_state.lista_crupieres = sorted([
        'DARIA', 'VIKTORIJA', 'DIANA', 'JOSSELYN', 'NIA', 'KATE', 'KEITA', 'LUNA', 'LAURA', 'JEVGENIJA'
    ])
if 'balance_history' not in st.session_state:
    st.session_state.balance_history = [0.0]

# Set de Números Rojos para consulta rápida
numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# ==========================================
# 4. FUNCIONES PARA RENDERIZAR BOTONES CON ESTILO
# ==========================================
def render_btn_0(crupier_act):
    st.markdown('<div class="marker-green"></div>', unsafe_allow_html=True)
    if st.button("0", key="btn_0"):
        registrar_tiro(0, crupier_act)
        st.rerun()

def render_btn_num(n, crupier_act):
    if n in numeros_rojos:
        st.markdown('<div class="marker-red"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="marker-black"></div>', unsafe_allow_html=True)
        
    if st.button(f"{n}", key=f"btn_{n}"):
        registrar_tiro(n, crupier_act)
        st.rerun()

# ==========================================
# 5. ALGORITMO ESCÁNER (Modo Conservador)
# ==========================================
def escanear_oportunidades(tiros):
    if len(tiros) < 15:
        return None
        
    ventana = tiros[-100:]
    counts = pd.Series(ventana).value_counts()
    numeros_calientes = counts[counts >= 4].index.tolist()
    
    for num in numeros_calientes:
        try:
            ultimo_hit_atras = list(reversed(tiros)).index(num)
            if ultimo_hit_atras >= 15:
                return num
        except ValueError:
            return num
            
    return None

def registrar_tiro(num, crupier_actual):
    st.session_state.historial_sesion.append({
        'crupier': crupier_actual,
        'numero': num,
        'hora': datetime.now().strftime("%H:%M:%S")
    })
    
    guardar_tiro_en_nube(crupier_actual, num)
    
    if st.session_state.caceria_activa:
        st.session_state.caceria_activa['tiros_transcurridos'] += 1
        
        if num == st.session_state.caceria_activa['numero']:
            costo = st.session_state.caceria_activa['tiros_transcurridos']
            ganancia = 36 - costo
            st.session_state.balance += ganancia
            st.session_state.balance_history.append(st.session_state.balance)
            st.balloons()
            st.session_state.caceria_activa = None
        elif st.session_state.caceria_activa['tiros_transcurridos'] >= 35:
            st.session_state.balance -= 35
            st.session_state.balance_history.append(st.session_state.balance)
            st.session_state.caceria_activa = None
            
    if not st.session_state.caceria_activa:
        solo_numeros = [t['numero'] for t in st.session_state.historial_sesion]
        num_detectado = escanear_oportunidades(solo_numeros)
        if num_detectado is not None:
            st.session_state.caceria_activa = {
                'numero': num_detectado,
                'tiros_transcurridos': 0
            }

# ==========================================
# 6. ESTRUCTURA INTERFAZ "ROULETTE BOT PRO 3.0"
# ==========================================

tab_main, tab_settings, tab_stats, tab_about = st.tabs(["Main", "Settings & Crupieres", "Statistics", "About"])

with tab_main:
    col_left, col_right = st.columns([1, 3])
    
    # PANEL LATERAL IZQUIERDO (Controles)
    with col_left:
        st.markdown("### ⚙️ Controls")
        
        crupier_actual = st.selectbox("-Select Crupier-", st.session_state.lista_crupieres)
        modo_actual = st.selectbox("-Select Mode-", ["Modo Conservador (1 Num)", "Modo Agresivo (Desactivado)"])
        
        tiros_crupier = sum(1 for t in st.session_state.historial_sesion if t['crupier'] == crupier_actual)
        st.caption(f"Turno Crupier: **{tiros_crupier}/50 tiros**")
        if tiros_crupier >= 40:
            st.error("⚠️ Alerta: Cambio de Crupier Cercano")
            
        st.divider()
        
        st.markdown("**Session Performance**")
        df_chart = pd.DataFrame({'Units': st.session_state.balance_history})
        st.line_chart(df_chart, height=120)
        
        st.divider()
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Reset", key="reset_btn"):
                st.session_state.historial_sesion = []
                st.session_state.balance = 0.0
                st.session_state.balance_history = [0.0]
                st.session_state.caceria_activa = None
                st.rerun()
        with col_b2:
            if st.button("Undo ↩️", key="undo_btn"):
                if st.session_state.historial_sesion:
                    st.session_state.historial_sesion.pop()
                    if st.session_state.caceria_activa:
                        st.session_state.caceria_activa['tiros_transcurridos'] = max(0, st.session_state.caceria_activa['tiros_transcurridos'] - 1)
                    st.rerun()

    # TAPETE PRINCIPAL DE LA RULETA (Verde)
    with col_right:
        # Marcador para envolver toda la mesa en el tapete verde
        st.markdown('<div class="green-felt-table"></div>', unsafe_allow_html=True)
        
        c_zero, c_board = st.columns([1, 12])
        
        with c_zero:
            render_btn_0(crupier_actual)
            
        with c_board:
            # Fila 1 (3 a 36)
            cols_f1 = st.columns(12)
            nums_f1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
            for i, n in enumerate(nums_f1):
                with cols_f1[i]:
                    render_btn_num(n, crupier_actual)

            # Fila 2 (2 a 35)
            cols_f2 = st.columns(12)
            nums_f2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
            for i, n in enumerate(nums_f2):
                with cols_f2[i]:
                    render_btn_num(n, crupier_actual)

            # Fila 3 (1 a 34)
            cols_f3 = st.columns(12)
            nums_f3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
            for i, n in enumerate(nums_f3):
                with cols_f3[i]:
                    render_btn_num(n, crupier_actual)
        
        # PANELES INFERIORES DE ESTADO
        st.write("")
        c_bal, c_pred, c_avoid = st.columns([1.5, 2.5, 2])
        
        with c_bal:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.metric("Balance Total", f"{st.session_state.balance:.2f} U")
            st.caption(f"Tiros en sesión: {len(st.session_state.historial_sesion)}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_pred:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.markdown("**🎯 APUESTA RECOMENDADA**")
            if st.session_state.caceria_activa:
                num_caza = st.session_state.caceria_activa['numero']
                tiro_n = st.session_state.caceria_activa['tiros_transcurridos'] + 1
                st.error(f"¡APOSTAR AL NÚMERO [{num_caza}]! (Tiro {tiro_n} de 35)")
            else:
                st.info("Escaneando patrones de mesa...")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_avoid:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.markdown("**❌ EVITAR / FRÍOS**")
            st.warning("Evitar 30, 20 y 3 sin gatillos activos.")
            st.markdown('</div>', unsafe_allow_html=True)

# Pestaña de Configuración y Crupieres
with tab_settings:
    st.subheader("Gestión de Crupieres")
    nuevo_crupier = st.text_input("Añadir Nuevo Crupier")
    if st.button("Guardar Crupier"):
        if nuevo_crupier and nuevo_crupier.upper() not in st.session_state.lista_crupieres:
            st.session_state.lista_crupieres.append(nuevo_crupier.upper())
            st.session_state.lista_crupieres.sort()
            st.success(f"Crupier {nuevo_crupier.upper()} registrado exitosamente.")
            st.rerun()

# Pestaña de Estadísticas
with tab_stats:
    st.subheader("Historial de la Sesión Activa")
    if st.session_state.historial_sesion:
        df_hist = pd.DataFrame(st.session_state.historial_sesion)
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.write("No hay tiradas en esta sesión.")

# Pestaña Acerca de
with tab_about:
    st.markdown("### Roulette Bot Pro 3.0 - Custom Edition")
    st.write("Sistema optimizado para el Modo Conservador con persistencia en Google Sheets Cloud.")
