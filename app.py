import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO MEJORADO (ESPAÑOL)
# ==========================================
st.set_page_config(page_title="Bot Ruleta Pro - v5.8 Alertas Precisas", layout="wide")

st.markdown("""
    <style>
    /* Estilo General de Fondo y Tipografía */
    .stApp {
        background-color: #d8d4cb;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.2rem !important;
        max-width: 98% !important;
    }

    /* Pestañas Superiores Claras y Visibles */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 700 !important;
        color: #2c3e50 !important;
        background-color: #c8c3b8 !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 8px 16px !important;
        margin-right: 4px !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0b6623 !important;
        color: #ffffff !important;
        border-bottom: 3px solid #ffd700 !important;
    }

    /* Ocultar Marcadores de CSS Estándar */
    [data-testid="stElementContainer"]:has(.marker-red),
    [data-testid="stElementContainer"]:has(.marker-black),
    [data-testid="stElementContainer"]:has(.marker-green),
    [data-testid="stElementContainer"]:has(.green-felt-table) {
        display: none !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* Tapete Verde Ajustado */
    [data-testid="stElementContainer"]:has(.green-felt-table) + [data-testid="stHorizontalBlock"] {
        background: linear-gradient(135deg, #0b6623 0%, #053311 100%) !important;
        padding: 14px 12px !important;
        border-radius: 12px !important;
        border: 4px solid #032b0e !important;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.8), 0 4px 8px rgba(0,0,0,0.3) !important;
        margin-bottom: 12px !important;
        align-items: center !important;
    }

    /* Botón Cero (0) */
    [data-testid="stElementContainer"]:has(.marker-green) + [data-testid="stElementContainer"] button {
        background: linear-gradient(180deg, #2e7d32 0%, #1b5e20 100%) !important;
        border: 2px solid #ffffff !important;
        border-radius: 10px !important;
        height: 138px !important;
        width: 100% !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.5) !important;
    }

    [data-testid="stElementContainer"]:has(.marker-green) + [data-testid="stElementContainer"] button * {
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    /* Botones Rojos - Texto en Una Sola Línea Impecable */
    [data-testid="stElementContainer"]:has(.marker-red) + [data-testid="stElementContainer"] button {
        background: linear-gradient(180deg, #e53935 0%, #b71c1c 100%) !important;
        border: 2px solid #ffffff !important;
        border-radius: 50% !important;
        height: 42px !important;
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        margin: 2px auto !important;
        padding: 0px !important;
        box-shadow: 0 3px 5px rgba(0,0,0,0.4) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stElementContainer"]:has(.marker-red) + [data-testid="stElementContainer"] button * {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    /* Botones Negros - Texto en Una Sola Línea Impecable */
    [data-testid="stElementContainer"]:has(.marker-black) + [data-testid="stElementContainer"] button {
        background: linear-gradient(180deg, #37474f 0%, #111111 100%) !important;
        border: 2px solid #ffffff !important;
        border-radius: 50% !important;
        height: 42px !important;
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        margin: 2px auto !important;
        padding: 0px !important;
        box-shadow: 0 3px 5px rgba(0,0,0,0.4) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stElementContainer"]:has(.marker-black) + [data-testid="stElementContainer"] button * {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    [data-testid="stElementContainer"]:has(.marker-red) + [data-testid="stElementContainer"] button:hover,
    [data-testid="stElementContainer"]:has(.marker-black) + [data-testid="stElementContainer"] button:hover,
    [data-testid="stElementContainer"]:has(.marker-green) + [data-testid="stElementContainer"] button:hover {
        transform: scale(1.15) !important;
        border-color: #ffd700 !important;
        box-shadow: 0 0 12px #ffd700 !important;
        transition: all 0.12s ease-in-out !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. PERSISTENCIA CON GOOGLE SHEETS ("Ruleta_Data base")
# ==========================================
NOMBRE_GOOGLE_SHEET = "Ruleta_Data base"

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
        
        try:
            spreadsheet = client.open(NOMBRE_GOOGLE_SHEET)
        except Exception:
            spreadsheet = client.open("Ruleta_Database")
            
        return spreadsheet
    except Exception:
        return None

spreadsheet = conectar_google_sheets()

def obtener_hoja_tiros():
    if spreadsheet:
        try:
            return spreadsheet.worksheet("Historico_Tiros")
        except Exception:
            try:
                ws = spreadsheet.add_worksheet(title="Historico_Tiros", rows="1000", cols="4")
                ws.append_row(["Fecha", "Hora", "Crupier", "Numero"])
                return ws
            except Exception:
                return None
    return None

def obtener_hoja_crupieres():
    if spreadsheet:
        try:
            return spreadsheet.worksheet("Lista_Crupieres")
        except Exception:
            try:
                ws = spreadsheet.add_worksheet(title="Lista_Crupieres", rows="200", cols="2")
                ws.append_row(["Crupier", "Fecha_Registro"])
                return ws
            except Exception:
                return None
    return None

def obtener_hoja_balance():
    if spreadsheet:
        try:
            return spreadsheet.worksheet("Registro_Ganancias")
        except Exception:
            try:
                ws = spreadsheet.add_worksheet(title="Registro_Ganancias", rows="1000", cols="5")
                ws.append_row(["Fecha", "Hora", "Crupier", "Cambio_U", "Balance_Acumulado"])
                return ws
            except Exception:
                return None
    return None

def guardar_tiro_en_nube(crupier, numero):
    sheet_tiros = obtener_hoja_tiros()
    if sheet_tiros:
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")
            sheet_tiros.append_row([fecha_actual, hora_actual, str(crupier).strip().upper(), int(numero)])
        except Exception:
            pass

def borrar_ultimo_tiro_en_nube():
    sheet_tiros = obtener_hoja_tiros()
    if sheet_tiros:
        try:
            filas = sheet_tiros.get_all_values()
            if len(filas) > 1:
                sheet_tiros.delete_rows(len(filas))
        except Exception:
            pass

def guardar_crupier_en_nube(nombre_crupier):
    sheet_crup = obtener_hoja_crupieres()
    if sheet_crup:
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            sheet_crup.append_row([nombre_crupier.strip().upper(), fecha_actual])
        except Exception:
            pass

def registrar_movimiento_balance_nube(crupier, cambio_u, nuevo_balance):
    sheet_bal = obtener_hoja_balance()
    if sheet_bal:
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")
            sheet_bal.append_row([fecha_actual, hora_actual, str(crupier).strip().upper(), float(cambio_u), float(nuevo_balance)])
        except Exception:
            pass

def borrar_ultimo_movimiento_balance_nube():
    sheet_bal = obtener_hoja_balance()
    if sheet_bal:
        try:
            filas = sheet_bal.get_all_values()
            if len(filas) > 1:
                sheet_bal.delete_rows(len(filas))
        except Exception:
            pass

def reiniciar_balance_historico_nube():
    sheet_bal = obtener_hoja_balance()
    if sheet_bal:
        try:
            sheet_bal.clear()
            sheet_bal.append_row(["Fecha", "Hora", "Crupier", "Cambio_U", "Balance_Acumulado"])
        except Exception:
            pass

def cargar_datos_historicos_nube():
    crupieres_base = [
        'AMANDA', 'ANASTASIJA', 'ANZELIKA', 'AURORA', 'DARIA', 'DIANA', 
        'ELIYA', 'ELIZABETH', 'EMILY', 'EMMA', 'EVELINA', 'GINTA', 
        'INNA', 'JASMINE', 'JEVGENIJA', 'JOSSELYN', 'KARALINA', 'KATE', 
        'KEITA', 'KSENIIA', 'LANA', 'LAURA', 'LIA', 'LINA', 'LISA', 
        'LOLA', 'LOLIJA', 'LUIZA', 'LUNA', 'MADARA', 'MARGARITA', 'MARIJA', 
        'MERY', 'NIA', 'RAYA', 'STEPHA', 'SVETLANA', 'VALERY', 'VIKTORIJA', 
        'XENIA', 'ZOJA'
    ]
    aprendizaje_historico = {}
    balance_historico_ultimo = 0.0
    historial_balance_lista = [0.0]
    
    sheet_crup = obtener_hoja_crupieres()
    if sheet_crup:
        try:
            registros = sheet_crup.get_all_values()
            if len(registros) > 1:
                for row in registros[1:]:
                    if row and row[0]:
                        nombre = str(row[0]).strip().upper()
                        if nombre and nombre not in crupieres_base:
                            crupieres_base.append(nombre)
        except Exception:
            pass

    sheet_tiros = obtener_hoja_tiros()
    if sheet_tiros:
        try:
            rows = sheet_tiros.get_all_values()
            if len(rows) > 1:
                df_past = pd.DataFrame(rows[1:], columns=['Fecha', 'Hora', 'Crupier', 'Numero'])
                df_past['Crupier'] = df_past['Crupier'].astype(str).str.strip().str.upper()
                df_past['Numero'] = pd.to_numeric(df_past['Numero'], errors='coerce')
                
                for cu in df_past['Crupier'].unique():
                    if cu and cu not in crupieres_base:
                        crupieres_base.append(cu)
                        
                for crup, group in df_past.groupby('Crupier'):
                    nums = group['Numero'].dropna().tolist()
                    wins = 0
                    losses = 0
                    for idx, n in enumerate(nums):
                        sub = nums[max(0, idx-6):idx]
                        if n in sub:
                            wins += 1
                        elif idx >= 7 and n not in nums[idx-7:idx]:
                            losses += 0.2
                    aprendizaje_historico[crup] = {'wins': int(wins), 'losses': int(losses)}
        except Exception:
            pass

    sheet_bal = obtener_hoja_balance()
    if sheet_bal:
        try:
            b_rows = sheet_bal.get_all_values()
            if len(b_rows) > 1:
                b_list = []
                for br in b_rows[1:]:
                    if len(br) >= 5:
                        try:
                            val = float(br[4])
                            b_list.append(val)
                        except Exception:
                            pass
                if b_list:
                    balance_historico_ultimo = b_list[-1]
                    historial_balance_lista = [0.0] + b_list
        except Exception:
            pass

    crupieres_base = sorted(list(set(crupieres_base)))
    return crupieres_base, aprendizaje_historico, balance_historico_ultimo, historial_balance_lista

# ==========================================
# 3. MEMORIA Y VARIABLES DE ESTADO
# ==========================================
if 'datos_cargados' not in st.session_state:
    lista_crup_nube, apren_nube, bal_hist_nube, bh_lista_nube = cargar_datos_historicos_nube()
    st.session_state.lista_crupieres = lista_crup_nube
    st.session_state.crupier_aprendizaje = apren_nube
    st.session_state.balance_acumulado_historico = bal_hist_nube
    st.session_state.balance_history_acumulado = bh_lista_nube
    st.session_state.datos_cargados = True

if 'historial_sesion' not in st.session_state:
    st.session_state.historial_sesion = []
if 'balance_dia' not in st.session_state:
    st.session_state.balance_dia = 0.0
if 'cacerias_activas' not in st.session_state:
    st.session_state.cacerias_activas = []
if 'balance_history_dia' not in st.session_state:
    st.session_state.balance_history_dia = [0.0]

crupieres_top = {'EMMA', 'NIA', 'KEITA', 'LISA', 'LUNA', 'JEVGENIJA', 'LOLIJA', 'KATE', 'JOSSELYN', 'AMANDA', 'KARALINA', 'ANZELIKA', 'LUIZA', 'ELIYA', 'JASMINE'}
crupieres_toxicos = {'LOLA', 'EMILY', 'VIKTORIJA', 'DARIA', 'LANA', 'INNA', 'LAURA', 'MARGARITA', 'DIANA', 'KSENIIA'}

if 'crupier_anterior_counts' not in st.session_state:
    st.session_state.crupier_anterior_counts = {}
if 's1_hits_tracker' not in st.session_state:
    st.session_state.s1_hits_tracker = {}
if 's2_won_nums' not in st.session_state:
    st.session_state.s2_won_nums = set()

if 'crupier_activo' not in st.session_state:
    st.session_state.crupier_activo = 'DARIA'

if 'tiros_turno_actual' not in st.session_state:
    st.session_state.tiros_turno_actual = []

if 'apuestas_pausadas_manualmente' not in st.session_state:
    st.session_state.apuestas_pausadas_manualmente = False

# CONTADORES PRECISOS PARA ALERTAS ANTIRRETROCESO
if 'fallos_turno_crupier' not in st.session_state:
    st.session_state.fallos_turno_crupier = 0

if 'fallos_consecutivos_globales' not in st.session_state:
    st.session_state.fallos_consecutivos_globales = 0

numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# ==========================================
# 4. GESTIÓN INMEDIATA DE CAMBIO DE TURNO (SINCRONIZACIÓN)
# ==========================================
def cambiar_turno_crupier(nuevo_crupier):
    """Sincroniza y reinicia de inmediato las variables del turno activo."""
    if st.session_state.tiros_turno_actual:
        counts = {}
        for x in st.session_state.tiros_turno_actual:
            counts[x] = counts.get(x, 0) + 1
        st.session_state.crupier_anterior_counts = counts
    
    st.session_state.crupier_activo = nuevo_crupier
    st.session_state.s1_hits_tracker = {}
    st.session_state.s2_won_nums = set()
    st.session_state.fallos_turno_crupier = 0
    st.session_state.cacerias_activas = []
    st.session_state.tiros_turno_actual = []

# ==========================================
# 5. MOTOR ADAPTATIVO OPTIMIZADO (v5.8)
# ==========================================
def evaluar_permiso_crupier(crupier, modo_filtro):
    if modo_filtro == "Modo Elite (Top 15 Sniper)":
        if crupier not in crupieres_top:
            return False, "Filtrado (No pertenece al Top Elite)"
    elif modo_filtro == "Filtro Anti-Tóxicos":
        if crupier in crupieres_toxicos:
            return False, "Filtrado (Crupier clasificado como Tóxico)"
            
    return True, "Habilitado"

def escanear_disparos(tiros_shift, crupier_actual, modo_filtro):
    if st.session_state.apuestas_pausadas_manualmente:
        return None, None

    permitido, motivo = evaluar_permiso_crupier(crupier_actual, modo_filtro)
    
    if not permitido:
        return None, None
        
    num_tiros = len(tiros_shift)
    
    if num_tiros > 35:
        return None, None
    
    # 1. EVALUAR PRIMERO ESTRATEGIA 2 (3 hits en <= 24 tiros; Ventana Tiros 1 a 35)
    if num_tiros <= 35:
        for num in set(tiros_shift):
            if tiros_shift.count(num) >= 4 or num in st.session_state.s2_won_nums:
                continue
            prev_hits = st.session_state.crupier_anterior_counts.get(num, 0)
            if not (1 <= prev_hits <= 2):
                continue
            occ = [i for i, x in enumerate(tiros_shift) if x == num]
            if len(occ) >= 3 and (occ[-1] - occ[-3] + 1) <= 24:
                if not any(c['numero'] == num for c in st.session_state.cacerias_activas):
                    return num, 2

    # 2. EVALUAR ESTRATEGIA 1 (Repetición <= 6 tiros; Ventana Tiros 1 a 25)
    if 1 <= num_tiros <= 25:
        num_actual = tiros_shift[-1]
        if tiros_shift.count(num_actual) < 4:
            prev_occ = [i for i, x in enumerate(tiros_shift[:-1]) if x == num_actual]
            if prev_occ:
                distancia = (num_tiros - 1) - prev_occ[-1]
                if distancia <= 6:
                    if st.session_state.s1_hits_tracker.get(num_actual, 0) < 2:
                        if not any(c['numero'] == num_actual for c in st.session_state.cacerias_activas):
                            return num_actual, 1

    return None, None

def registrar_tiro(num, crupier_actual, modo_filtro):
    if st.session_state.crupier_activo != crupier_actual:
        cambiar_turno_crupier(crupier_actual)

    st.session_state.tiros_turno_actual.append(num)

    st.session_state.historial_sesion.append({
        'crupier': crupier_actual,
        'numero': num,
        'hora': datetime.now().strftime("%H:%M:%S")
    })
    
    guardar_tiro_en_nube(crupier_actual, num)
    
    if crupier_actual not in st.session_state.crupier_aprendizaje:
        st.session_state.crupier_aprendizaje[crupier_actual] = {'wins': 0, 'losses': 0}

    cacerias_restantes = []
    
    for caza in st.session_state.cacerias_activas:
        caza['tiros_transcurridos'] += 1
        
        if num == caza['numero']:
            costo = caza['tiros_transcurridos']
            ganancia = 36 - costo
            
            st.session_state.balance_dia += ganancia
            st.session_state.balance_acumulado_historico += ganancia
            
            st.session_state.balance_history_dia.append(st.session_state.balance_dia)
            st.session_state.balance_history_acumulado.append(st.session_state.balance_acumulado_historico)
            
            st.session_state.crupier_aprendizaje[crupier_actual]['wins'] += 1
            
            # REINICIO EXACTO DE FALLOS TRAS VICTORIA
            st.session_state.fallos_turno_crupier = 0
            st.session_state.fallos_consecutivos_globales = 0
            
            registrar_movimiento_balance_nube(crupier_actual, ganancia, st.session_state.balance_acumulado_historico)
            st.balloons()
            
            if caza['estrategia'] == 1:
                st.session_state.s1_hits_tracker[num] = st.session_state.s1_hits_tracker.get(num, 0) + 1
                if st.session_state.s1_hits_tracker[num] < 2:
                    caza_renovada = dict(caza)
                    caza_renovada['tiros_transcurridos'] = 0
                    caza_renovada['es_renovacion_2nd_hit'] = True
                    cacerias_restantes.append(caza_renovada)
            else:
                st.session_state.s2_won_nums.add(num)
        else:
            limite = 7 if caza['estrategia'] == 1 else 11
            if caza['tiros_transcurridos'] >= limite:
                pérdida = -limite
                st.session_state.balance_dia += pérdida
                st.session_state.balance_acumulado_historico += pérdida
                
                st.session_state.balance_history_dia.append(st.session_state.balance_dia)
                st.session_state.balance_history_acumulado.append(st.session_state.balance_acumulado_historico)
                
                st.session_state.crupier_aprendizaje[crupier_actual]['losses'] += 1
                st.session_state.fallos_turno_crupier += 1
                st.session_state.fallos_consecutivos_globales += 1
                registrar_movimiento_balance_nube(crupier_actual, pérdida, st.session_state.balance_acumulado_historico)
            else:
                cacerias_restantes.append(caza)
                
    st.session_state.cacerias_activas = cacerias_restantes
    
    num_det, strat_det = escanear_disparos(st.session_state.tiros_turno_actual, crupier_actual, modo_filtro)
    if num_det is not None:
        st.session_state.cacerias_activas.append({
            'numero': num_det,
            'estrategia': strat_det,
            'tiros_transcurridos': 0,
            'es_renovacion_2nd_hit': False
        })

# ==========================================
# 6. RENDERIZADO DE BOTONES DE LA RULETA (HD)
# ==========================================
def render_btn_0(crupier_act, modo_filtro):
    st.markdown('<div class="marker-green"></div>', unsafe_allow_html=True)
    if st.button("0", key="btn_0"):
        registrar_tiro(0, crupier_act, modo_filtro)
        st.rerun()

def render_btn_num(n, crupier_act, modo_filtro):
    if n in numeros_rojos:
        st.markdown('<div class="marker-red"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="marker-black"></div>', unsafe_allow_html=True)
        
    if st.button(f"{n}", key=f"btn_{n}"):
        registrar_tiro(n, crupier_act, modo_filtro)
        st.rerun()

# ==========================================
# 7. INTERFAZ DE USUARIO V5.8
# ==========================================

tab_main, tab_settings, tab_stats, tab_about = st.tabs([
    "🎯 Panel Principal (Ruleta_Data base)", 
    "⚙️ Configuración y Crupieres", 
    "📊 Histórico de Ganancias/Pérdidas", 
    "ℹ️ Acerca del Sistema"
])

with tab_main:
    col_left, col_right = st.columns([1, 3.2])
    
    with col_left:
        st.markdown("### ⚙️ Control de Mesa")
        
        # Selección de Crupier sincronizada
        crupier_seleccionado = st.selectbox(
            "— Crupier Activo —", 
            st.session_state.lista_crupieres,
            index=st.session_state.lista_crupieres.index(st.session_state.crupier_activo) if st.session_state.crupier_activo in st.session_state.lista_crupieres else 0
        )
        
        if crupier_seleccionado != st.session_state.crupier_activo:
            cambiar_turno_crupier(crupier_seleccionado)
            st.rerun()

        crupier_actual = st.session_state.crupier_activo
        
        modo_filtro = st.selectbox("— Modo de Juego —", ["🌐 Todos los Crupieres", "🛡️ Filtro Anti-Tóxicos", "🎯 Modo Elite (Top 15 Sniper)"])
        
        permitido, motivo_estado = evaluar_permiso_crupier(crupier_actual, modo_filtro)
        if permitido:
            if crupier_actual in crupieres_top:
                st.success("🌟 Crupier TOP ELITE")
            else:
                st.info("ℹ️ Crupier Habilitado")
        else:
            st.error(f"⛔ {motivo_estado}")
            
        tiros_crupier = len(st.session_state.tiros_turno_actual)
        
        if tiros_crupier <= 10:
            st.caption(f"Turno: **{tiros_crupier}/50** | 🌟 ZONA ORO (1-10)")
        elif tiros_crupier <= 25:
            st.caption(f"Turno: **{tiros_crupier}/50** | 🟢 ZONA ALTA (11-25)")
        elif tiros_crupier <= 35:
            st.caption(f"Turno: **{tiros_crupier}/50** | 🟡 ZONA MEDIA (26-35)")
        else:
            st.caption(f"Turno: **{tiros_crupier}/50** | 🔴 FATIGA (>35)")

        # Botón para iniciar un nuevo turno limpio si el crupier repite tanda
        if st.button("🔄 Iniciar Nuevo Turno Crupier", key="btn_new_shift_current", use_container_width=True):
            cambiar_turno_crupier(crupier_actual)
            st.success(f"¡Nuevo turno de 50 tiradas iniciado para {crupier_actual}!")
            st.rerun()

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("☀️ Reiniciar Día", key="reset_day_btn", use_container_width=True):
                st.session_state.historial_sesion = []
                st.session_state.tiros_turno_actual = []
                st.session_state.balance_dia = 0.0
                st.session_state.balance_history_dia = [0.0]
                st.session_state.cacerias_activas = []
                st.session_state.s1_hits_tracker = {}
                st.session_state.s2_won_nums = set()
                st.session_state.fallos_turno_crupier = 0
                st.session_state.fallos_consecutivos_globales = 0
                st.session_state.apuestas_pausadas_manualmente = False
                st.rerun()
        with col_b2:
            if st.button("Deshacer ↩️", key="undo_btn", use_container_width=True):
                if st.session_state.historial_sesion:
                    st.session_state.historial_sesion.pop()
                    if st.session_state.tiros_turno_actual:
                        st.session_state.tiros_turno_actual.pop()
                    borrar_ultimo_tiro_en_nube()
                    borrar_ultimo_movimiento_balance_nube()
                    st.rerun()

        st.markdown("**Tendencia de Balance (Sesión)**")
        df_chart_dia = pd.DataFrame({'Día': st.session_state.balance_history_dia})
        st.line_chart(df_chart_dia, height=90)

    # TAPETE PRINCIPAL Y SECCIÓN DE APUESTAS
    with col_right:
        st.markdown('<div class="green-felt-table"></div>', unsafe_allow_html=True)
        
        c_zero, c_board = st.columns([1, 12])
        
        with c_zero:
            render_btn_0(crupier_actual, modo_filtro)
            
        with c_board:
            cols_f1 = st.columns(12)
            nums_f1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
            for i, n in enumerate(nums_f1):
                with cols_f1[i]:
                    render_btn_num(n, crupier_actual, modo_filtro)

            cols_f2 = st.columns(12)
            nums_f2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
            for i, n in enumerate(nums_f2):
                with cols_f2[i]:
                    render_btn_num(n, crupier_actual, modo_filtro)

            cols_f3 = st.columns(12)
            nums_f3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
            for i, n in enumerate(nums_f3):
                with cols_f3[i]:
                    render_btn_num(n, crupier_actual, modo_filtro)
        
        # FILA DE MÉTRICAS Y RECOMENDADOR
        c_m1, c_m2, c_ctrl, c_rec = st.columns([1.1, 1.1, 1.5, 2.5])
        
        with c_m1:
            st.metric("Balance Día", f"{st.session_state.balance_dia:.1f} U")
            
        with c_m2:
            st.metric("Balance Total", f"{st.session_state.balance_acumulado_historico:.1f} U")
            
        with c_ctrl:
            if st.session_state.apuestas_pausadas_manualmente:
                if st.button("▶️ REANUDAR", key="btn_resume_betting", use_container_width=True):
                    st.session_state.apuestas_pausadas_manualmente = False
                    st.rerun()
            else:
                if st.button("⏸️ PARAR APUESTAS", key="btn_stop_betting", use_container_width=True):
                    st.session_state.apuestas_pausadas_manualmente = True
                    st.rerun()
                    
        with c_rec:
            if st.session_state.apuestas_pausadas_manualmente:
                st.warning("⏸️ APUESTAS PAUSADAS MANUALMENTE")
            elif not permitido:
                st.warning(f"🔒 Mesa pausada: {motivo_estado}")
            elif st.session_state.cacerias_activas:
                for caza in st.session_state.cacerias_activas:
                    num_caza = caza['numero']
                    strat = caza['estrategia']
                    tiro_n = caza['tiros_transcurridos'] + 1
                    lim_t = 7 if strat == 1 else 11
                    
                    if caza.get('es_renovacion_2nd_hit', False):
                        st.error(f"🎯 APOSTAR [{num_caza}] (E{strat} - 2º HIT - {tiro_n}/{lim_t})")
                    else:
                        st.error(f"🎯 APOSTAR [{num_caza}] (E{strat} - {tiro_n}/{lim_t})")
            else:
                if tiros_crupier > 35:
                    st.error("🔒 Fatiga (>35 tiros). Esperando cambio.")
                else:
                    st.info("Escaneando patrones...")

        # AVISOS ANTIRRETROCESO PRECISOS
        alertas_generadas = False
        
        # REGLA 1: Freno por Operador (2 fallos acumulados en su turno SIN victorias)
        if st.session_state.fallos_turno_crupier >= 2:
            st.warning(f"🛑 **ALERTA REGLA 1 (Freno por Operador):** El crupier **{crupier_actual}** suma {st.session_state.fallos_turno_crupier} fallos activos en este turno.")
            alertas_generadas = True

        # REGLA 2: Stop-Loss Diario Rígido (-35 U)
        if st.session_state.balance_dia <= -35.0:
            st.error(f"🔴 **ALERTA REGLA 2 (Stop-Loss Diario):** Balance diario cayó a `{st.session_state.balance_dia:.1f} U`. Se sugiere cerrar la sesión por hoy.")
            alertas_generadas = True

        # REGLA 3: Pausa de Marea (2 fallos consecutivos globales sin victorias)
        if st.session_state.fallos_consecutivos_globales >= 2:
            st.warning(f"🌊 **ALERTA REGLA 3 (Pausa de Marea):** {st.session_state.fallos_consecutivos_globales} fallos consecutivos globales. Se sugiere pausar 15 min.")
            alertas_generadas = True

        # REGLA 4: Crupieres Tóxicos en Día Negativo
        if st.session_state.balance_dia < 0 and crupier_actual in crupieres_toxicos:
            st.warning(f"🛡️ **ALERTA REGLA 4 (Mesa Fría / Crupier Tóxico):** Día en negativo (`{st.session_state.balance_dia:.1f} U`) y {crupier_actual} es tóxica. Activar Filtro Anti-Tóxicos.")
            alertas_generadas = True

        # REGLA 5: Take-Profit Diario (+100 U)
        if st.session_state.balance_dia >= 100.0:
            st.success(f"🏆 **ALERTA REGLA 5 (Take-Profit):** Meta alcanzada (`{st.session_state.balance_dia:.1f} U`). Se sugiere retirar ganancias.")
            alertas_generadas = True

        if not alertas_generadas:
            st.success("✅ **Parámetros de Riesgo Normales:** Sin alertas activas. Ritmo y banca óptimos.")

        # HISTORIAL DE TIRADAS DEL DÍA (COMPACTO Y LEGIBLE)
        st.markdown("#### 📜 Números Registrados en la Sesión")
        if st.session_state.historial_sesion:
            col_t1, col_t2 = st.columns([2.3, 1])
            with col_t1:
                df_hist_main = pd.DataFrame(list(reversed(st.session_state.historial_sesion)))
                df_hist_main.index = range(len(df_hist_main), 0, -1)
                df_hist_main.columns = ['Crupier', 'Número', 'Hora']
                st.dataframe(df_hist_main[['Hora', 'Crupier', 'Número']], height=160, use_container_width=True)
            with col_t2:
                total_tiros = len(st.session_state.historial_sesion)
                nums_list = [t['numero'] for t in st.session_state.historial_sesion]
                rojos_cnt = sum(1 for n in nums_list if n in numeros_rojos)
                negros_cnt = sum(1 for n in nums_list if n not in numeros_rojos and n != 0)
                ceros_cnt = sum(1 for n in nums_list if n == 0)
                st.caption(f"**Total Tiradas:** {total_tiros}")
                st.caption(f"🔴 **Rojos:** {rojos_cnt} | ⬛ **Negros:** {negros_cnt} | 🟢 **0:** {ceros_cnt}")
        else:
            st.caption("No hay tiradas registradas aún en la sesión.")

with tab_settings:
    st.subheader("Gestión de Crupieres")
    col_set1, col_set2 = st.columns(2)
    with col_set1:
        nuevo_crupier_settings = st.text_input("Añadir Crupier a Ruleta_Data base:")
        if st.button("Guardar Crupier en Nube"):
            if nuevo_crupier_settings:
                nombre_clean2 = nuevo_crupier_settings.strip().upper()
                if nombre_clean2 not in st.session_state.lista_crupieres:
                    st.session_state.lista_crupieres.append(nombre_clean2)
                    st.session_state.lista_crupieres.sort()
                    guardar_crupier_en_nube(nombre_clean2)
                    st.success(f"¡Crupier {nombre_clean2} guardado permanentemente!")
                    st.rerun()
    with col_set2:
        if st.button("🔄 Sincronizar desde Nube"):
            lista_crup_nube, apren_nube, bal_hist_nube, bh_lista_nube = cargar_datos_historicos_nube()
            st.session_state.lista_crupieres = lista_crup_nube
            st.session_state.crupier_aprendizaje = apren_nube
            st.session_state.balance_acumulado_historico = bal_hist_nube
            st.session_state.balance_history_acumulado = bh_lista_nube
            st.success("¡Base de datos sincronizada!")
            st.rerun()

    st.divider()
    st.markdown("**Lista de Crupieres Registrados:**")
    st.write(", ".join(st.session_state.lista_crupieres))

with tab_stats:
    st.subheader("Registro Histórico de Ganancias/Pérdidas")
    st.markdown(f"**Balance Acumulado Total Actual:** `{st.session_state.balance_acumulado_historico:.2f} U`")
    if st.session_state.balance_history_acumulado:
        df_hist_bal = pd.DataFrame({'Balance Acumulado (U)': st.session_state.balance_history_acumulado})
        st.line_chart(df_hist_bal, height=200)
    st.divider()
    st.warning("⚠️ Zona de Reinicio del Registro Financiero")
    if st.button("🗑️ Reiniciar Registro Histórico de Ganancias/Pérdidas (A Cero)", key="reset_hist_financial_btn"):
        reiniciar_balance_historico_nube()
        st.session_state.balance_acumulado_historico = 0.0
        st.session_state.balance_history_acumulado = [0.0]
        st.success("¡Registro histórico de ganancias y pérdidas reiniciado a 0.00 U en Google Sheets!")
        st.rerun()

with tab_about:
    st.markdown("### Bot Ruleta Pro v5.8 — Alertas y Turnos Precisos")
    st.write("Sincronización instantánea de cambio de crupier, reinicio de fallos tras victoria y gestión independiente de turnos repetidos.")
