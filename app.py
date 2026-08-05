import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. ESTILO Y CONFIGURACIÓN "ROULETTE BOT PRO"
# ==========================================
st.set_page_config(page_title="Roulette Bot Pro 3.0", layout="wide")

# Estilos CSS para emular el software clásico (Fieltro verde, botones ovalados y panel retro)
st.markdown("""
    <style>
    /* Fondo general gris tipo software clásico */
    .stApp {
        background-color: #d4d0c8;
        font-family: 'Tahoma', 'Segoe UI', sans-serif;
    }
    
    /* Tapete verde de la ruleta */
    .felt-board {
        background-color: #0b6623;
        border: 4px solid #064016;
        border-radius: 12px;
        padding: 15px;
        box-shadow: inset 0 0 10px #000000;
    }
    
    /* Botones de números en el tapete */
    div.stButton > button {
        border-radius: 50% !important;
        height: 48px !important;
        width: 48px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        color: white !important;
        border: 2px solid #ffd700 !important;
        margin: auto !important;
        display: block !important;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* Estilos por color de botón */
    .red-num > button { background-color: #cc0000 !important; }
    .black-num > button { background-color: #1a1a1a !important; }
    .green-num > button { background-color: #008000 !important; height: 110px !important; border-radius: 20px !important; }
    
    /* Botones de acción lateral */
    .action-btn > button {
        border-radius: 4px !important;
        height: 35px !important;
        width: 100% !important;
        background-color: #e1e1e1 !important;
        color: black !important;
        border: 1px solid #7f9db9 !important;
    }
    
    /* Cajas de Estado e Infecciones */
    .status-box {
        background-color: #ffffff;
        border: 2px inset #ffffff;
        padding: 10px;
        border-radius: 4px;
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
    except Exception as e:
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

# ==========================================
# 4. ALGORITMO ESCÁNER (Modo Conservador)
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
# 5. ESTRUCTURA INTERFAZ "ROULETTE BOT PRO 3.0"
# ==========================================

# Pestañas Superiores Clásicas
tab_main, tab_settings, tab_stats, tab_about = st.tabs(["Main", "Settings & Crupieres", "Statistics", "About"])

with tab_main:
    col_left, col_right = st.columns([1, 3])
    
    # ------------------------------------
    # PANEL LATERAL IZQUIERDO (Controles)
    # ------------------------------------
    with col_left:
        st.markdown("### ⚙️ Controls")
        
        crupier_actual = st.selectbox("-Select Crupier-", st.session_state.lista_crupieres)
        modo_actual = st.selectbox("-Select Mode-", ["Modo Conservador (1 Num)", "Modo Agresivo (Desactivado)"])
        
        # Estado del Turno del Crupier
        tiros_crupier = sum(1 for t in st.session_state.historial_sesion if t['crupier'] == crupier_actual)
        st.caption(f"Turno Crupier: **{tiros_crupier}/50 tiros**")
        if tiros_crupier >= 40:
            st.error("⚠️ Alerta: Cambio de Crupier Cercano")
            
        st.divider()
        
        # Gráfico de Rendimiento Minituara
        st.markdown("**Session Performance**")
        df_chart = pd.DataFrame({'Units': st.session_state.balance_history})
        st.line_chart(df_chart, height=120)
        
        st.divider()
        
        # Botones de Control Lateral
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

    # ------------------------------------
    # TAPETE PRINCIPAL DE LA RULETA (Verde)
    # ------------------------------------
    with col_right:
        st.markdown('<div class="felt-board">', unsafe_allow_html=True)
        
        numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        
        # Fila Superior: Cero + Filas Tradicionales de la Mesa (3 a 36, 2 a 35, 1 a 34)
        c_zero, c_board = st.columns([1, 12])
        
        with c_zero:
            st.markdown('<div class="green-num">', unsafe_allow_html=True)
            if st.button("0", key="btn_0"):
                registrar_tiro(0, crupier_actual)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_board:
            # Fila 1 (Números: 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36)
            cols_f1 = st.columns(12)
            nums_f1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
            for i, n in enumerate(nums_f1):
                cls = "red-num" if n in numeros_rojos else "black-num"
                cols_f1[i].markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                if cols_f1[i].button(f"{n}", key=f"btn_{n}"):
                    registrar_tiro(n, crupier_actual)
                    st.rerun()
                cols_f1[i].markdown('</div>', unsafe_allow_html=True)

            # Fila 2 (Números: 2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35)
            cols_f2 = st.columns(12)
            nums_f2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
            for i, n in enumerate(nums_f2):
                cls = "red-num" if n in numeros_rojos else "black-num"
                cols_f2[i].markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                if cols_f2[i].button(f"{n}", key=f"btn_{n}"):
                    registrar_tiro(n, crupier_actual)
                    st.rerun()
                cols_f2[i].markdown('</div>', unsafe_allow_html=True)

            # Fila 3 (Números: 1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34)
            cols_f3 = st.columns(12)
            nums_f3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
            for i, n in enumerate(nums_f3):
                cls = "red-num" if n in numeros_rojos else "black-num"
                cols_f3[i].markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                if cols_f3[i].button(f"{n}", key=f"btn_{n}"):
                    registrar_tiro(n, crupier_actual)
                    st.rerun()
                cols_f3[i].markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        
        # ------------------------------------
        # PANELES INFERIORES DE ESTADO Y PREDICCIÓN
        # ------------------------------------
        st.write("")
        c_bal, c_pred, c_avoid = st.columns([1.5, 2.5, 2])
        
        with c_bal:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.metric("Balance Total", f"{st.session_state.balance:.2f} U")
            st.caption(f"Tiros registrados en sesión: {len(st.session_state.historial_sesion)}")
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
