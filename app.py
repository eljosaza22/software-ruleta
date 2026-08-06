import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO RETRO (ESPAÑOL)
# ==========================================
st.set_page_config(page_title="Bot Ruleta Pro - Auto-Optimizado v4.2", layout="wide")

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

def borrar_ultimo_tiro_en_nube():
    if sheet:
        try:
            filas = sheet.get_all_values()
            if len(filas) > 1:
                sheet.delete_rows(len(filas))
        except Exception:
            pass

# ==========================================
# 3. MEMORIA DE SESIÓN Y AUTO-OPTIMIZACIÓN
# ==========================================
if 'historial_sesion' not in st.session_state:
    st.session_state.historial_sesion = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0
if 'cacerias_activas' not in st.session_state:
    st.session_state.cacerias_activas = []
if 'lista_crupieres' not in st.session_state:
    st.session_state.lista_crupieres = [
        'AMANDA', 'ANASTASIJA', 'ANZELIKA', 'AURORA', 'DARIA', 'DIANA', 
        'ELIYA', 'ELIZABETH', 'EMILY', 'EMMA', 'EVELINA', 'GINTA', 
        'INNA', 'JASMINE', 'JEVGENIJA', 'JOSSELYN', 'KARALINA', 'KATE', 
        'KEITA', 'KSENIIA', 'LANA', 'LAURA', 'LIA', 'LINA', 'LISA', 
        'LOLA', 'LOLIJA', 'LUIZA', 'LUNA', 'MADARA', 'MARGARITA', 'MARIJA', 
        'MERY', 'NIA', 'RAYA', 'STEPHA', 'SVETLANA', 'VALERY', 'VIKTORIJA', 
        'XENIA', 'ZOJA'
    ]
if 'balance_history' not in st.session_state:
    st.session_state.balance_history = [0.0]

# Listas de Perfil
crupieres_top = {'EMMA', 'NIA', 'KEITA', 'LISA', 'LUNA', 'JEVGENIJA', 'LOLIJA', 'KATE', 'JOSSELYN', 'AMANDA', 'KARALINA', 'ANZELIKA', 'LUIZA', 'ELIYA', 'JASMINE'}
crupieres_toxicos = {'LOLA', 'EMILY', 'VIKTORIJA', 'DARIA', 'LANA', 'INNA', 'LAURA', 'MARGARITA', 'DIANA', 'KSENIIA'}

# Diccionario de Aprendizaje Dinámico por Crupier (Auto-Optimización)
if 'crupier_aprendizaje' not in st.session_state:
    st.session_state.crupier_aprendizaje = {} # crupier -> {'wins': 0, 'losses': 0}

if 'crupier_anterior_counts' not in st.session_state:
    st.session_state.crupier_anterior_counts = {}
if 's1_hits_tracker' not in st.session_state:
    st.session_state.s1_hits_tracker = {}
if 's2_won_nums' not in st.session_state:
    st.session_state.s2_won_nums = set()
if 'shift_losses' not in st.session_state:
    st.session_state.shift_losses = 0
if 'crupier_activo' not in st.session_state:
    st.session_state.crupier_activo = 'DARIA'

numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# ==========================================
# 4. RENDERIZADO DE BOTONES
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
# 5. MOTOR ADAPTATIVO CON AUTO-OPTIMIZACIÓN
# ==========================================
def evaluar_permiso_crupier(crupier, modo_filtro):
    # Inicializar registro de aprendizaje si no existe
    if crupier not in st.session_state.crupier_aprendizaje:
        st.session_state.crupier_aprendizaje[crupier] = {'wins': 0, 'losses': 0}
        
    stats = st.session_state.crupier_aprendizaje[crupier]
    total_intentos = stats['wins'] + stats['losses']
    
    # Auto-Optimización Dinámica: Si en esta sesión el crupier acumula más derrotas que victorias, se bloquea automáticamente
    if total_intentos >= 2 and (stats['wins'] / total_intentos) < 0.35:
        return False, "Bloqueado por Auto-Optimización (Bajo rendimiento en sesión)"

    if modo_filtro == "Modo Elite (Top 15 Sniper)":
        if crupier not in crupieres_top:
            return False, "Filtrado (No pertenece al Top Elite)"
    elif modo_filtro == "Filtro Anti-Tóxicos":
        if crupier in crupieres_toxicos:
            return False, "Filtrado (Crupier clasificado como Tóxico/Disperso)"
            
    return True, "Habilitado"

def escanear_disparos(tiros_shift, crupier_actual, modo_filtro):
    permitido, motivo = evaluar_permiso_crupier(crupier_actual, modo_filtro)
    if not permitido or st.session_state.shift_losses >= 1:
        return None, None
        
    num_tiros = len(tiros_shift)
    
    # Estrategia 1 (Tiros 1 a 20)
    if 1 <= num_tiros <= 20:
        num_actual = tiros_shift[-1]
        prev_occ = [i for i, x in enumerate(tiros_shift[:-1]) if x == num_actual]
        if prev_occ:
            distancia = (num_tiros - 1) - prev_occ[-1]
            if distancia <= 6:
                if st.session_state.s1_hits_tracker.get(num_actual, 0) < 2:
                    if not any(c['numero'] == num_actual and c['estrategia'] == 1 for c in st.session_state.cacerias_activas):
                        return num_actual, 1

    # Estrategia 2 (Tiros 1 a 35)
    if num_tiros <= 35:
        for num in set(tiros_shift):
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
        st.session_state.shift_losses = 0
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
            st.session_state.crupier_aprendizaje[crupier_actual]['wins'] += 1 # Auto-Optimización: Registra acierto
            st.balloons()
            
            if caza['estrategia'] == 1:
                st.session_state.s1_hits_tracker[num] = st.session_state.s1_hits_tracker.get(num, 0) + 1
                if st.session_state.s1_hits_tracker[num] < 2:
                    caza['tiros_transcurridos'] = 0
                    cacerias_restantes.append(caza)
            else:
                st.session_state.s2_won_nums.add(num)
        else:
            limite = 7 if caza['estrategia'] == 1 else 11
            if caza['tiros_transcurridos'] >= limite:
                st.session_state.balance -= limite
                st.session_state.balance_history.append(st.session_state.balance)
                st.session_state.shift_losses += 1
                st.session_state.crupier_aprendizaje[crupier_actual]['losses'] += 1 # Auto-Optimización: Registra fallo
            else:
                cacerias_restantes.append(caza)
                
    st.session_state.cacerias_activas = cacerias_restantes
    
    tiros_del_crupier = [t['numero'] for t in st.session_state.historial_sesion if t['crupier'] == crupier_actual]
    num_det, strat_det = escanear_disparos(tiros_del_crupier, crupier_actual, modo_filtro)
    if num_det is not None:
        st.session_state.cacerias_activas.append({
            'numero': num_det,
            'estrategia': strat_det,
            'tiros_transcurridos': 0
        })

# ==========================================
# 6. INTERFAZ DE USUARIO 100% EN ESPAÑOL
# ==========================================

tab_main, tab_settings, tab_stats, tab_about = st.tabs([
    "Panel Principal (Auto-Optimizado)", 
    "Configuración y Crupieres", 
    "Estadísticas Generales", 
    "Acerca del Sistema"
])

with tab_main:
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.markdown("### ⚙️ Panel de Control")
        
        crupier_actual = st.selectbox("— Seleccionar Crupier Activo —", st.session_state.lista_crupieres)
        
        # Selector de Filtro de Crupieres solicitado
        modo_filtro = st.selectbox(
            "— Estrategia de Selección —", 
            ["🌐 Todos los Crupieres", "🛡️ Filtro Anti-Tóxicos", "🎯 Modo Elite (Top 15 Sniper)"]
        )
        
        # Validación de Estado del Crupier actual según filtro y auto-optimización
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
        
        st.markdown("**Rendimiento del Sistema Adaptativo (U)**")
        df_chart = pd.DataFrame({'Unidades': st.session_state.balance_history})
        st.line_chart(df_chart, height=120)
        
        st.divider()
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Reiniciar", key="reset_btn"):
                st.session_state.historial_sesion = []
                st.session_state.balance = 0.0
                st.session_state.balance_history = [0.0]
                st.session_state.cacerias_activas = []
                st.session_state.crupier_anterior_counts = {}
                st.session_state.s1_hits_tracker = {}
                st.session_state.s2_won_nums = set()
                st.session_state.shift_losses = 0
                st.session_state.crupier_aprendizaje = {}
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
            render_btn_0(crupier_act=crupier_actual)
            
        with c_board:
            cols_f1 = st.columns(12)
            nums_f1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
            for i, n in enumerate(nums_f1):
                with cols_f1[i]:
                    render_btn_num(n, crupier_actual)

            cols_f2 = st.columns(12)
            nums_f2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
            for i, n in enumerate(nums_f2):
                with cols_f2[i]:
                    render_btn_num(n, crupier_actual)

            cols_f3 = st.columns(12)
            nums_f3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
            for i, n in enumerate(nums_f3):
                with cols_f3[i]:
                    render_btn_num(n, crupier_actual)
        
        st.write("")
        c_bal, c_pred, c_avoid = st.columns([1.5, 2.5, 2])
        
        with c_bal:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.metric("Balance Total", f"{st.session_state.balance:.2f} U")
            st.caption(f"Fallos en este turno: {st.session_state.shift_losses} / 1 máx")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_pred:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.markdown("**🎯 APUESTAS RECOMENDADAS (AUTO-ADAPTATIVO)**")
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
                if st.session_state.shift_losses >= 1:
                    st.warning("🔒 Turno bloqueado por 1 fallo previo. Esperando cambio de crupier.")
                else:
                    st.info("Escaneando con aprendizaje dinámico activo...")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_avoid:
            st.markdown('<div class="status-box">', unsafe_allow_html=True)
            st.markdown("**🤖 ESTADO DE APRENDIZAJE**")
            stats_actuales = st.session_state.crupier_aprendizaje.get(crupier_actual, {'wins': 0, 'losses': 0})
            st.write(f"• Crupier: **{crupier_actual}**")
            st.write(f"• Aciertos Registrados: {stats_actuales['wins']}")
            st.write(f"• Fallos Registrados: {stats_actuales['losses']}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        st.markdown("### 📜 Verificación e Historial de Tiradas en Vivo")
        
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
            st.info("No hay tiradas registradas. Ingresa los números directamente desde el tapete superior.")

with tab_settings:
    st.subheader("Gestión de Crupieres y Pesos de Aprendizaje")
    st.markdown("**Matriz de Auto-Optimización Activa por Crupier:**")
    if st.session_state.crupier_aprendizaje:
        df_aprox = pd.DataFrame.from_dict(st.session_state.crupier_aprendizaje, orient='index')
        st.dataframe(df_aprox, use_container_width=True)
    else:
        st.info("Aún no hay registros de aprendizaje en esta sesión. Empieza a registrar tiros.")

with tab_stats:
    st.subheader("Registro Completo de la Sesión")
    if st.session_state.historial_sesion:
        df_hist = pd.DataFrame(st.session_state.historial_sesion)
        st.dataframe(df_hist, use_container_width=True)

with tab_about:
    st.markdown("### Bot Ruleta Pro v4.2 — Auto-Optimizado")
    st.write("Sistema cuántico adaptativo con aprendizaje dinámico por crupier y filtros de selección personalizados.")
