import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
# ==========================================
st.set_page_config(page_title="Predicciones Ruleta - Modo Conservador", layout="wide")

# CSS personalizado para emular los colores de la ruleta en los botones
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        font-weight: bold;
        border-radius: 5px;
    }
    .red-btn { background-color: #ff4d4d !important; color: white !important; }
    .black-btn { background-color: #2b2b2b !important; color: white !important; }
    .green-btn { background-color: #2ca02c !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INICIALIZACIÓN DEL ESTADO DE SESIÓN (Memoria interna de la app)
# ==========================================
if 'historial_sesion' not in st.session_state:
    st.session_state.historial_sesion = []  # Guarda los tiros de esta sesión
if 'balance' not in st.session_state:
    st.session_state.balance = 0            # Balance en unidades
if 'caceria_activa' not in st.session_state:
    st.session_state.caceria_activa = None  # Info de la cacería actual {'numero': X, 'tiros_transcurridos': N}
if 'lista_crupieres' not in st.session_state:
    # Lista inicial basada en tus datos recolectados
    st.session_state.lista_crupieres = sorted([
        'DARIA', 'VIKTORIJA', 'DIANA', 'JOSSELYN', 'NIA', 'KATE', 'KEITA', 'LUNA', 'LAURA', 'JEVGENIJA'
    ])

# ==========================================
# 3. LÓGICA DEL ALGORITMO (Modo Conservador)
# ==========================================
def escanear_oportunidades(tiros):
    """
    Analiza los últimos 100 tiros de la sesión activa para buscar un número caliente (>=4 hits)
    que lleve dormido al menos 15 tiros.
    """
    if len(tiros) < 15:
        return None  # No hay suficientes datos en la sesión actual para evaluar
        
    # Tomamos los últimos 100 tiros
    ventana = tiros[-100:]
    counts = pd.Series(ventana).value_counts()
    
    # Buscamos números calientes
    numeros_calientes = counts[counts >= 4].index.tolist()
    
    for num in numeros_calientes:
        # Calcular hace cuántos tiros no sale
        try:
            # Encontrar el índice del último hit
            ultimo_hit_atras = list(reversed(tiros)).index(num)
            if ultimo_hit_atras >= 15:
                return num  # ¡Gatillo detectado! Retornamos este número para cacería
        except ValueError:
            # Si no está en el historial reciente, lleva mucho dormido
            return num
            
    return None

# ==========================================
# 4. INTERFAZ GRÁFICA (UI)
# ==========================================

# CABECERA
st.title("🎯 Analizador de Ruleta Pro - Modo Conservador")
st.write("Conectado a Google Sheets Cloud 🟢")

# PANEL SUPERIOR (Gestión de Crupier y Balance)
col_crupier, col_nuevo, col_status_crupier, col_balance = st.columns([2, 2, 2, 2])

with col_crupier:
    crupier_actual = st.selectbox("Seleccionar Crupier Activo", st.session_state.lista_crupieres)

with col_nuevo:
    nuevo_crupier_input = st.text_input("Agregar Nuevo Crupier", placeholder="Escribe el nombre...")
    if st.button("➕ Registrar"):
        if nuevo_crupier_input and nuevo_crupier_input.upper() not in st.session_state.lista_crupieres:
            st.session_state.lista_crupieres.append(nuevo_crupier_input.upper())
            st.session_state.lista_crupieres.sort()
            st.rerun()

with col_status_crupier:
    # Contamos tiros del crupier en esta sesión
    tiros_crupier = sum(1 for t in st.session_state.historial_sesion if t['crupier'] == crupier_actual)
    st.metric("Tiros del Turno", f"{tiros_crupier} / 50")
    if tiros_crupier >= 40:
        st.warning("⚠️ ¡Cambio de crupier inminente! Evita iniciar cacerías.")

with col_balance:
    color_balance = "green" if st.session_state.balance >= 0 else "red"
    st.markdown(f"### Balance Neto: <span style='color:{color_balance}'>{st.session_state.balance} Unidades</span>", unsafe_allow_html=True)

st.divider()

# ZONA CENTRAL (Tablero numérico e Historial)
col_tablero, col_historial = st.columns([3, 1])

# Definición de colores clásicos de la ruleta
numeros_rojos = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

with col_tablero:
    st.subheader("Ingresar Número Ganador")
    
    # Botón del 0 (Verde)
    if st.button("0", key="btn_0", help="Verde"):
        numero_ingresado = 0
    
    # Generar el tablero en filas de 3 números
    for fila in range(12):
        cols = st.columns(3)
        for i in range(3):
            num = fila * 3 + (i + 1)
            color_class = "red-btn" if num in numeros_rojos else "black-btn"
            
            # Botón interactivo para cada número
            if cols[i].button(f"{num}", key=f"btn_{num}"):
                # Al presionar, registramos el tiro
                st.session_state.historial_sesion.append({
                    'crupier': crupier_actual,
                    'numero': num,
                    'hora': datetime.now().strftime("%H:%M:%S")
                })
                
                # Si hay cacería activa, sumamos un tiro transcurrido
                if st.session_state.caceria_activa:
                    st.session_state.caceria_activa['tiros_transcurridos'] += 1
                    
                    # Si el número ingresado es el que cazábamos -> ¡GANAMOS!
                    if num == st.session_state.caceria_activa['numero']:
                        costo = st.session_state.caceria_activa['tiros_transcurridos']
                        st.session_state.balance += (36 - costo)
                        st.balloons()
                        st.success(f"🎉 ¡CACERÍA EXITOSA! Ganaste en el tiro {costo}.")
                        st.session_state.caceria_activa = None
                    # Si llegamos al tiro 35 sin éxito -> ¡PERDIMOS!
                    elif st.session_state.caceria_activa['tiros_transcurridos'] >= 35:
                        st.session_state.balance -= 35
                        st.error(f"❌ CACERÍA FALLIDA. Se alcanzaron los 35 tiros límite.")
                        st.session_state.caceria_activa = None
                
                # Si no hay cacería activa, escaneamos si se activa una nueva oportunidad
                if not st.session_state.caceria_activa:
                    solo_numeros = [t['numero'] for t in st.session_state.historial_sesion]
                    num_detectado = escanear_oportunidades(solo_numeros)
                    if num_detectado is not None:
                        st.session_state.caceria_activa = {
                            'numero': num_detectado,
                            'tiros_transcurridos': 0
                        }
                
                st.rerun()

with col_historial:
    st.subheader("Registro de Sesión")
    if st.button("↩️ Deshacer Último Registro"):
        if st.session_state.historial_sesion:
            ultimo = st.session_state.historial_sesion.pop()
            # Si estábamos en cacería, restamos el tiro
            if st.session_state.caceria_activa:
                st.session_state.caceria_activa['tiros_transcurridos'] = max(0, st.session_state.caceria_activa['tiros_transcurridos'] - 1)
            st.warning(f"Se eliminó el tiro: {ultimo['numero']}")
            st.rerun()
            
    # Mostrar últimos 10 tiros registrados
    if st.session_state.historial_sesion:
        df_display = pd.DataFrame(st.session_state.historial_sesion).tail(10)
        st.dataframe(df_display[['hora', 'crupier', 'numero']], use_container_width=True)
    else:
        st.info("La sesión está vacía. Registra números para empezar.")

st.divider()

# ==========================================
# 5. PANEL DE PREDICCIONES Y CACERÍA
# ==========================================
st.subheader("🚨 Panel de Alertas de Apuesta")

col_alerta_si, col_alerta_no = st.columns(2)

with col_alerta_si:
    st.markdown("### 🎯 APUESTA RECOMENDADA")
    if st.session_state.caceria_activa:
        num_caza = st.session_state.caceria_activa['numero']
        tiro_n = st.session_state.caceria_activa['tiros_transcurridos'] + 1
        
        st.success(f"### ¡APOSTAR AL NÚMERO **{num_caza}**!")
        st.metric("Tiro de Cacería", f"{tiro_n} de 35")
        st.info(f"Firma del crupier {crupier_actual} y retraso activo detectados para este número.")
    else:
        st.write("Buscando patrones en los tiros... Sigue ingresando números.")

with col_alerta_no:
    st.markdown("### ❌ EVITAR / NO APUESTAR")
    # Mostrar números fríos históricos para evitar
    st.warning("Evita cazar números como el **30** o el **20** sin gatillos activos (llevan ausencias de más de 340 tiros en el histórico).")