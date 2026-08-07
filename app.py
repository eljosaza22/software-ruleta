import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO RETRO (ESPAÑOL)
# ==========================================
st.set_page_config(page_title="Bot Ruleta Pro - Ruleta_Data base v4.7", layout="wide")

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

    /* EFECTO HOVER */
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
        
        # Apertura directa de la hoja "Ruleta_Data base"
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

def cargar_datos_historicos_nube():
    """Carga la lista completa de crupieres y retroalimenta el modelo adaptativo con tiradas pasadas."""
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
    
    # 1. Cargar crupieres guardados en la pestaña Lista_Crupieres
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

    # 2. Cargar tiradas históricas para retroalimentar el aprendizaje
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

    crupieres_base = sorted(list(set(crupieres_base)))
    return crupieres_base, aprendizaje_historico

# ==========================================
# 3. MEMORIA Y AUTO-CARGA DESDE LA NUBE
# ==========================================
if 'datos_cargados' not in st.session_state:
    lista_crup_nube, apren_nube = cargar_datos_historicos_nube()
    st.session_state.lista_crupieres = lista_crup_nube
    st.session_state.crupier_aprendizaje = apren_nube
    st.session_state.datos_cargados = True

if 'historial_sesion' not in st.session_state:
    st.session_state.historial_sesion = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0
if 'cacerias_activas' not in st.session_state:
    st.session_state.cacerias_activas = []
if 'balance_history' not in st.session_state:
    st.session_state.balance_history = [0.0]

crupieres_top = {'EMMA', 'NIA', 'KEITA', 'LISA', 'LUNA', 'JEVGENIJA', 'LOLIJA', 'KATE', 'JOSSELYN', 'AMANDA', 'KARALINA', 'ANZELIKA', 'LUIZA', 'ELIYA', 'JASMINE'}
crupieres_toxicos = {'LOLA', 'EMILY', 'VIKTORIJA', 'DARIA', 'LANA', 'INNA', 'LAURA', 'MARGARITA', 'DIANA', 'KSENIIA'}

if 'crupier_anterior_counts' not in st.session_state:
    st.session_state.crupier_anterior_counts = {}
if 's1_hits_tracker' not in st.session_state:
    st.session_state.s1_hits_tracker = {}
if 's2_won_nums' not in st.session_state:
    st.session_state.s2_won_nums = set()

if 'fallos_secos' not in st.session_state:
    st.session_state.fallos_secos = 0
if 'fallos_totales' not in st.session_state:
    st.session_state.fallos_totales = 0

if 'crupier_activo' not in st.session_state:
    st.session_state.crupier_activo = 'DARIA'

numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# ==========================================
# 4. MOTOR ADAPTATIVO CON REGLA DE FALLO FINANCIADO
# ==========================================
def evaluar_permiso_crupier(crupier, modo_filtro):
    if crupier not in st.session_state.crupier_aprendizaje:
        st.session_state.crupier_aprendizaje[crupier] = {'wins': 0, 'losses': 0}
        
    stats = st.session_state.crupier_aprendizaje[crupier]
    total_intentos = stats['wins'] + stats['losses']
    
    if total_intentos >= 2 and (stats['wins'] / total_intentos) < 0.35:
        return False, "Bloqueado por Auto-Optimización (Bajo rendimiento en base histórica)"

    if modo_filtro == "Modo Elite (Top 15 Sniper)":
        if crupier not in crupieres_top:
            return False, "Filtrado (No pertenece al Top Elite)"
    elif modo_filtro == "Filtro Anti-Tóxicos":
        if crupier in crupieres_toxicos:
            return False, "Filtrado (Crupier clasificado como Tóxico)"
            
    return True, "Habilitado"

def escanear_disparos(tiros_shift, crupier_actual, modo_filtro):
    permitido, motivo = evaluar_permiso_crupier(crupier_actual, modo_filtro)
    
    # REGLA DE BLOQUEO ADAPTATIVA:
    # 1. Si ocurrió 1 fallo seco (sin victorias previas en el 1er acierto) -> BLOQUEAR
    # 2. Si ocurrieron 2 fallos totales en el turno -> BLOQUEAR DEFINITIVO
    if not permitido or st.session_state.fallos_secos >= 1 or st.session_state.fallos_totales >= 2:
        return None, None
        
    num_tiros = len(tiros_shift)
    
    # 1. Estrategia 1 (Repetición <= 6 tiros; Ventana 1 a 20 del crupier)
    if 1 <= num_tiros <= 20:
        num_actual = tiros_shift[-1]
        # Regla de Control de Saturación: Máximo 3 salidas en el turno
        if tiros_shift.count(num_actual) < 4:
            prev_occ = [i for i, x in enumerate(tiros_shift[:-1]) if x == num_actual]
            if prev_occ:
                distancia = (num_tiros - 1) - prev_occ[-1]
                if distancia <= 6:
                    if st.session_state.s1_hits_tracker.get(num_actual, 0) < 2:
                        if not any(c['numero'] == num_actual and c['estrategia'] == 1 for c in st.session_state.cacerias_activas):
                            return num_actual, 1

    # 2. Estrategia 2 (3 hits en <= 24 tiros; Ventana 1 a 35; Regla 12 crupier anterior)
    if num_tiros <= 35:
        for num in set(tiros_shift):
            if tiros_shift.count(num) >= 4:
                continue
            if num in st.session_state.s2_won_nums:
                continue
            prev_hits = st.session_state.crupier_anterior_counts.get(num, 0)
            if not (1 <= prev_hits <= 2):
                continue
            occ = [i for i, x in enumerate(tiros_shift) if x == num]
            if len(occ) >= 3:
                if (occ[-1] - occ[-3] + 1) <= 24:
                    if not any(c['numero'] == num for c in st.session_state.cacerias_activas):
                        return num, 2
                        
    return None, None

def registrar_tiro(num, crupier_actual, modo_filtro):
    if st.session_state.crupier_activo != crupier_actual:
        tiros_salientes = [t['numero'] for t in st.session_state.historial_sesion if t['crupier'] == st.session_state.crupier_activo]
        counts_salientes = {}
        for x in tiros_salientes:
            counts_salientes[x] = counts_salientes.get(x, 0) + 1
        st.session_state.crupier_anterior_counts = counts_salientes
        
        st.session_state.crupier_activo = crupier_actual
        st.session_state.s1_hits_tracker = {}
        st.session_state.s2_won_nums = set()
        st.session_state.fallos_secos = 0
        st.session_state.fallos_totales = 0
        st.session_state.cacerias_activas = []

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
            st.session_state.balance += ganancia
            st.session_state.balance_history.append(st.session_state.balance)
            st.session_state.crupier_aprendizaje[crupier_actual]['wins'] += 1
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
                st.session_state.balance -= limite
                st.session_state.balance_history.append(st.session_state.balance)
                st.session_state.crupier_aprendizaje[crupier_actual]['losses'] += 1
                
                st.session_state.fallos_totales += 1
                if not caza.get('es_renovacion_2nd_hit', False):
                    st.session_state.fallos_secos += 1
            else:
                cacerias_restantes.append(caza)
                
    st.session_state.cacerias_activas = cacerias_restantes
    
    tiros_del_crupier = [t['numero'] for t in st.session_state.historial_sesion if t['crupier'] == crupier_actual]
    num_det, strat_det = escanear_disparos(tiros_del_crupier, crupier_actual, modo_filtro)
    if num_det is not None:
        st.session_state.cacerias_activas.append({
            'numero': num_det,
            'estrategia': strat_det,
            'tiros_transcurridos': 0,
            'es_renovacion_2nd_hit': False
        })

# ==========================================
# 5. RENDERIZADO DE BOTONES
# ==========================================
def render_btn_0(crupier_act, modo_f):
    st.markdown('<div class="marker-green"></div>', unsafe_allow_html=True)
    if st.button("0", key="btn_0"):
        registrar_tiro(0, crupier_act, modo_f)
        st.rerun()

def render_btn_num(n, crupier_act, modo_f):
    if n in numeros_rojos:
        st.markdown('<div class="marker-red"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="marker-black"></div>', unsafe_allow_html=True)
        
    if st.button(f"{n}", key=f"btn_{n}"):
        registrar_tiro(n, crupier_act, modo_f)
        st.rerun()

# ==========================================
# 6. INTERFAZ DE USUARIO 100% EN ESPAÑOL
# ==========================================

tab_main, tab_settings, tab_stats, tab_about = st.tabs([
    "Panel Principal (Ruleta_Data base)", 
    "Configuración y Crupieres", 
    "Estadísticas Generales", 
    "Acerca del Sistema"
])

with tab_main:
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.markdown("### ⚙️ Panel de Control")
        
        crupier_actual = st.selectbox("— Seleccionar Crupier Activo —", st.session_state.lista_crupieres)
        
        modo_filtro = st.selectbox(
            "— Estrategia de Selección —", 
            ["🌐 Todos los Crupieres", "🛡️ Filtro Anti-Tóxicos", "🎯 Modo Elite (Top 15 Sniper)"]
        )
        
        permitido, motivo_estado = evaluar_permiso_crupier(crupier_actual, modo_filtro)
        if permitido:
            if crupier_actual in crupieres_top:
                st.success("🌟 Crupier Rítmico (TOP ELITE)")
            else:
                st.info("ℹ️ Crupier Habilitado (Neutro/Estándar)")
        else:
            st.error(f"⛔ {motivo_estado}")
            
        tiros_crupier = sum(1 for t in st.session_state.historial_sesion if t['crupier'] == crupier_actual)
        st.caption(f"Progreso del Crupier: **{tiros_crupier} / 50 tiradas**")
        if tiros_crupier >= 35:
            st.warning("⚠️ Límite de 35 tiros alcanzado (Nuevas entradas bloqueadas)")
        elif tiros_crupier >= 40:
            st.error("⚠️ Alerta: Cambio de Crupier Inminente")
            
        st.divider()

        # FORMULARIO DE NUEVO CRUPIER CON GUARDADO EN GOOGLE SHEETS
        with st.expander("➕ Añadir Nuevo Crupier (Guardado en Nube)"):
            nuevo_nombre = st.text_input("Nombre del Crupier:", key="sidebar_new_dealer")
            if st.button("Guardar en Nube", key="btn_save_dealer"):
                if nuevo_nombre:
                    nombre_clean = nuevo_nombre.strip().upper()
                    if nombre_clean not in st.session_state.lista_crupieres:
                        st.session_state.lista_crupieres.append(nombre_clean)
                        st.session_state.lista_crupieres.sort()
                        guardar_crupier_en_nube(nombre_clean)
                        st.success(f"¡Crupier {nombre_clean} guardado en Ruleta_Data base!")
                        st.rerun()

        st.divider()
        
        st.markdown("**Rendimiento del Día Activo (U)**")
        df_chart = pd.DataFrame({'Unidades': st.session_state.balance_history})
        st.line_chart(df_chart, height=120)
        
        st.divider()
        
        # BOTONES DE GESTIÓN DE SESIÓN
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("☀️ Reiniciar Día", key="reset_day_btn"):
                st.session_state.historial_sesion = []
                st.session_state.balance = 0.0
                st.session_state.balance_history = [0.0]
                st.session_state.cacerias_activas = []
                st.session_state.s1_hits_tracker = {}
                st.session_state.s2_won_nums = set()
                st.session_state.fallos_secos = 0
                st.session_state.fallos_totales = 0
                st.success("¡Nuevo día iniciado! Memoria y crupieres conservados.")
                st.rerun()
        with col_b2:
            if st.button("Deshacer ↩️", key="undo_btn"):
                if st.session_state.historial_sesion:
                    st.session_state.historial_sesion.pop()
                    borrar_ultimo_tiro_en_nube()
                    st.rerun()

    # TAPETE PRINCIPAL
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
        
        st.write("")
        c_bal, c_pred, c_avoid = st.columns([1.5, 2.5, 2])
        
        with c_bal:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.metric("Balance Día Actual", f"{st.session_state.balance:.2f} U")
            st.caption(f"Fallos totales turno: {st.session_state.fallos_totales} / 2 máx")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_pred:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.markdown("**🎯 APUESTAS RECOMENDADAS (Ruleta_Data base)**")
            if not permitido:
                st.warning(f"🔒 Mesa pausada por filtro: {motivo_estado}")
            elif st.session_state.cacerias_activas:
                for caza in st.session_state.cacerias_activas:
                    num_caza = caza['numero']
                    strat = caza['estrategia']
                    tiro_n = caza['tiros_transcurridos'] + 1
                    lim_t = 7 if strat == 1 else 11
                    st.error(f"¡APOSTAR AL NÚMERO [{num_caza}]! (Estrategia {strat} - Tiro {tiro_n} de {lim_t})")
            else:
                if st.session_state.fallos_secos >= 1:
                    st.warning("🔒 Turno bloqueado por 1 fallo seco en 1er intento.")
                elif st.session_state.fallos_totales >= 2:
                    st.warning("🔒 Turno bloqueado por acumulación de 2 fallos totales.")
                else:
                    st.info("Escaneando con aprendizaje retroalimentado desde Ruleta_Data base...")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_avoid:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.markdown("**🤖 PROTECCIÓN DE BALANCE**")
            st.write(f"• Fallos Secos (1er hit): {st.session_state.fallos_secos} / 1 máx")
            st.write(f"• Fallos Totales (Turno): {st.session_state.fallos_totales} / 2 máx")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        st.markdown("### 📜 Verificación e Historial de Tiradas del Día")
        
        if st.session_state.historial_sesion:
            col_tabla_hist, col_stats_resumen = st.columns([2, 1])
            
            with col_tabla_hist:
                df_hist_main = pd.DataFrame(list(reversed(st.session_state.historial_sesion)))
                df_hist_main.index = range(len(df_hist_main), 0, -1)
                df_hist_main.columns = ['Crupier', 'Número', 'Hora']
                
                st.dataframe(
                    df_hist_main[['Hora', 'Crupier', 'Número']], 
                    height=200, 
                    use_container_width=True
                )
                
            with col_stats_resumen:
                total_tiros = len(st.session_state.historial_sesion)
                nums_list = [t['numero'] for t in st.session_state.historial_sesion]
                rojos_cnt = sum(1 for n in nums_list if n in numeros_rojos)
                negros_cnt = sum(1 for n in nums_list if n not in numeros_rojos and n != 0)
                ceros_cnt = sum(1 for n in nums_list if n == 0)
                
                pct_rojo = (rojos_cnt / total_tiros * 100) if total_tiros > 0 else 0
                pct_negro = (negros_cnt / total_tiros * 100) if total_tiros > 0 else 0
                pct_cero = (ceros_cnt / total_tiros * 100) if total_tiros > 0 else 0
                
                st.markdown('<div class="status-box">', unsafe_allow_html=True)
                st.markdown("**📊 Resumen de Tiradas:**")
                st.write(f"• **Total Registrados:** {total_tiros}")
                st.write(f"• 🔴 **Rojos:** {rojos_cnt} ({pct_rojo:.1f}%)")
                st.write(f"• ⬛ **Negros:** {negros_cnt} ({pct_negro:.1f}%)")
                st.write(f"• 🟢 **Ceros (0):** {ceros_cnt} ({pct_cero:.1f}%)")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No hay tiradas en el día activo. Ingresa los números directamente desde el tapete superior.")

with tab_settings:
    st.subheader("Gestión de Crupieres y Aprendizaje Retroalimentado")
    
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
        if st.button("🔄 Sincronizar / Volver a Cargar Datos desde Nube"):
            lista_crup_nube, apren_nube = cargar_datos_historicos_nube()
            st.session_state.lista_crupieres = lista_crup_nube
            st.session_state.crupier_aprendizaje = apren_nube
            st.success("¡Base de datos retroalimentada desde Ruleta_Data base!")
            st.rerun()

    st.divider()
    st.markdown("**Matriz de Aprendizaje Histórico Acumulado por Crupier:**")
    if st.session_state.crupier_aprendizaje:
        df_aprox = pd.DataFrame.from_dict(st.session_state.crupier_aprendizaje, orient='index')
        st.dataframe(df_aprox, use_container_width=True)

with tab_stats:
    st.subheader("Registro Completo de la Sesión Activa")
    if st.session_state.historial_sesion:
        df_hist = pd.DataFrame(st.session_state.historial_sesion)
        st.dataframe(df_hist, use_container_width=True)

with tab_about:
    st.markdown("### Bot Ruleta Pro v4.7 — Conexión Definitiva con Ruleta_Data base")
    st.write("Sistema adaptativo con almacenamiento persistente en 'Ruleta_Data base', aprendizaje histórico y botón de reinicio diario.")
