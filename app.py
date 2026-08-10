import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from math import sqrt

# ============================================================
# BOT RULETA PRO V5 — MOTOR ESTADÍSTICO / PAPER TRADING
# ============================================================
# Cambios principales:
# - S1 mejorada: repetición <= 5 posiciones.
# - Máximo 2 apariciones previas antes de activar.
# - Cobertura configurable: 8 tiros por defecto.
# - Renovación controlada: máximo 1 renovación.
# - S2 queda SOLO en modo observación/investigación.
# - Se elimina Top 15 / Anti-Tóxicos como filtro fijo.
# - Score dinámico de señal y score estadístico del crupier.
# - Estado: ENTRAR / OBSERVAR / NO APOSTAR.
# - 1 U fija; sin Martingala.
# - Cambio de crupier cierra señales activas como ABANDONADA.
# - Corrección del límite 35/40.
# - Laboratorio de backtesting sobre Historico_Tiros de Google Sheets.
# - Paper trading por defecto: no registra P&L real hasta activarlo.
#
# IMPORTANTE:
# Esta aplicación NO garantiza rentabilidad. Su objetivo es detectar,
# registrar y validar señales antes de arriesgar dinero real.

st.set_page_config(page_title="Bot Ruleta Pro V5 - Edge Detector", layout="wide")

st.markdown("""
<style>
.stApp { background-color:#d4d0c8; font-family:'Tahoma','Segoe UI',sans-serif; }
.status-box { background:#fff; border:2px inset #d4d0c8; padding:12px; border-radius:6px; }
.edge-green { border-left:7px solid #1b5e20; padding:10px; background:#e8f5e9; }
.edge-yellow { border-left:7px solid #f57f17; padding:10px; background:#fff8e1; }
.edge-red { border-left:7px solid #b71c1c; padding:10px; background:#ffebee; }
</style>
""", unsafe_allow_html=True)

# ---------------- CONFIGURACIÓN ----------------
NOMBRE_GOOGLE_SHEET = "Ruleta_Data base"
DEFAULT_S1_DISTANCIA = 5
DEFAULT_S1_LIMITE = 8
DEFAULT_MAX_PREVIAS = 2
MAX_RENOVACIONES = 1
MIN_DEALER_SAMPLE = 50
ENTRY_SCORE = 80
OBSERVE_SCORE = 65
EUROPEAN_P = 1 / 37

numeros_rojos = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}

# ---------------- GOOGLE SHEETS ----------------
@st.cache_resource
def conectar_google_sheets():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)
        try:
            return client.open(NOMBRE_GOOGLE_SHEET)
        except Exception:
            return client.open("Ruleta_Database")
    except Exception:
        return None

spreadsheet = conectar_google_sheets()

def obtener_hoja_tiros():
    if not spreadsheet:
        return None
    try:
        return spreadsheet.worksheet("Historico_Tiros")
    except Exception:
        try:
            ws = spreadsheet.add_worksheet(title="Historico_Tiros", rows="5000", cols="4")
            ws.append_row(["Fecha","Hora","Crupier","Numero"])
            return ws
        except Exception:
            return None

def obtener_hoja_crupieres():
    if not spreadsheet:
        return None
    try:
        return spreadsheet.worksheet("Lista_Crupieres")
    except Exception:
        try:
            ws = spreadsheet.add_worksheet(title="Lista_Crupieres", rows="500", cols="2")
            ws.append_row(["Crupier","Fecha_Registro"])
            return ws
        except Exception:
            return None

def obtener_hoja_balance():
    if not spreadsheet:
        return None
    try:
        return spreadsheet.worksheet("Registro_Ganancias")
    except Exception:
        try:
            ws = spreadsheet.add_worksheet(title="Registro_Ganancias", rows="5000", cols="6")
            ws.append_row(["Fecha","Hora","Crupier","Cambio_U","Balance_Acumulado","Tipo"])
            return ws
        except Exception:
            return None

def guardar_tiro_en_nube(crupier, numero):
    ws = obtener_hoja_tiros()
    if ws:
        try:
            ahora = datetime.now()
            ws.append_row([
                ahora.strftime("%Y-%m-%d"),
                ahora.strftime("%H:%M:%S"),
                str(crupier).strip().upper(),
                int(numero)
            ])
        except Exception:
            pass

def borrar_ultimo_tiro_en_nube():
    ws = obtener_hoja_tiros()
    if ws:
        try:
            rows = ws.get_all_values()
            if len(rows) > 1:
                ws.delete_rows(len(rows))
        except Exception:
            pass

def registrar_movimiento_balance_nube(crupier, cambio_u, nuevo_balance, tipo="PAPER"):
    ws = obtener_hoja_balance()
    if ws:
        try:
            ahora = datetime.now()
            ws.append_row([
                ahora.strftime("%Y-%m-%d"),
                ahora.strftime("%H:%M:%S"),
                str(crupier).strip().upper(),
                float(cambio_u),
                float(nuevo_balance),
                tipo
            ])
        except Exception:
            pass

def borrar_ultimo_movimiento_balance_nube():
    ws = obtener_hoja_balance()
    if ws:
        try:
            rows = ws.get_all_values()
            if len(rows) > 1:
                ws.delete_rows(len(rows))
        except Exception:
            pass

def cargar_tiradas_nube():
    ws = obtener_hoja_tiros()
    if not ws:
        return pd.DataFrame(columns=["Fecha","Hora","Crupier","Numero"])
    try:
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return pd.DataFrame(columns=["Fecha","Hora","Crupier","Numero"])
        df = pd.DataFrame(rows[1:], columns=["Fecha","Hora","Crupier","Numero"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Crupier"] = df["Crupier"].astype(str).str.strip().str.upper()
        df["Numero"] = pd.to_numeric(df["Numero"], errors="coerce")
        df = df.dropna(subset=["Numero"]).copy()
        df["Numero"] = df["Numero"].astype(int)
        df = df[df["Numero"].between(0,36)]
        return df.reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["Fecha","Hora","Crupier","Numero"])

def cargar_crupieres_nube():
    base = {
        'AMANDA','ANASTASIJA','ANZELIKA','AURORA','DARIA','DIANA','ELIYA',
        'ELIZABETH','EMILY','EMMA','EVELINA','GINTA','INNA','JASMINE',
        'JEVGENIJA','JOSSELYN','KARALINA','KATE','KEITA','KSENIIA','LANA',
        'LAURA','LIA','LINA','LISA','LOLA','LOLIJA','LUIZA','LUNA','MADARA',
        'MARGARITA','MARIJA','MERY','NIA','RAYA','STEPHA','SVETLANA',
        'VALERY','VIKTORIJA','XENIA','ZOJA'
    }
    ws = obtener_hoja_crupieres()
    if ws:
        try:
            rows = ws.get_all_values()
            for row in rows[1:]:
                if row and row[0]:
                    base.add(str(row[0]).strip().upper())
        except Exception:
            pass
    return sorted(base)

# ---------------- ESTADÍSTICA ----------------
def wilson_interval(wins, n, z=1.96):
    if n <= 0:
        return 0.0, 0.0
    p = wins / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * sqrt((p*(1-p)/n) + (z*z/(4*n*n))) / den
    return max(0.0, center-half), min(1.0, center+half)

def dealer_stats(df, dealer):
    d = df[df["Crupier"] == dealer].copy()
    n = len(d)
    if n == 0:
        return {"n":0, "repeat_rate":EUROPEAN_P, "excess":0.0, "score":50, "ci_low":0.0}
    nums = d["Numero"].tolist()
    hits = 0
    opportunities = 0
    for i in range(1, len(nums)):
        last = nums[i]
        prev = nums[max(0, i-5):i]
        if last in prev:
            hits += 1
        opportunities += 1
    rate = hits/opportunities if opportunities else EUROPEAN_P
    # Esta métrica NO pretende demostrar ventaja matemática; mide actividad
    # de repetición del patrón que estamos estudiando.
    excess = (rate - (1-(36/37)**5))
    # Estabilizamos el score para evitar que pocas muestras dominen.
    sample_factor = min(1.0, n / MIN_DEALER_SAMPLE)
    base = 50 + 35 * np.tanh(excess * 8)
    score = 50 + (base-50) * sample_factor
    lo, _ = wilson_interval(hits, opportunities)
    return {
        "n":n, "repeat_rate":rate, "excess":excess,
        "score":float(np.clip(score, 0, 100)), "ci_low":lo
    }

def señal_s1(serie, max_dist=5, max_prev=2):
    """Detecta S1: el último número repite una aparición previa a <= max_dist.
    No usa información futura."""
    n = len(serie)
    if n < 2:
        return None
    actual = int(serie[-1])
    prev = [i for i, x in enumerate(serie[:-1]) if int(x) == actual]
    if not prev:
        return None
    distancia = (n-1) - prev[-1]
    apariciones_previas = len(prev)
    if distancia <= max_dist and apariciones_previas <= max_prev:
        return {
            "numero": actual,
            "distancia": distancia,
            "apariciones_previas": apariciones_previas
        }
    return None

def detectar_s2_observacion(serie, ventana=24):
    if len(serie) < 3:
        return None
    actual = int(serie[-1])
    start = max(0, len(serie)-ventana)
    sub = [int(x) for x in serie[start:]]
    if sub.count(actual) >= 3:
        return {"numero":actual, "apariciones":sub.count(actual)}
    return None

def señal_score(s1, df_historico, dealer):
    if not s1:
        return 0, {}
    stats = dealer_stats(df_historico, dealer)
    score = 0
    detalles = {}

    # Cercanía de repetición
    if s1["distancia"] <= 2:
        pts = 30
    elif s1["distancia"] <= 3:
        pts = 25
    elif s1["distancia"] <= 4:
        pts = 20
    else:
        pts = 15
    score += pts
    detalles["distancia"] = pts

    # Menos apariciones previas = señal más limpia
    pts = 20 if s1["apariciones_previas"] == 1 else 10
    score += pts
    detalles["historial_numero"] = pts

    # Crupier
    dealer_pts = int(round((stats["score"] - 50) * 0.35 + 17.5))
    dealer_pts = int(np.clip(dealer_pts, 0, 35))
    score += dealer_pts
    detalles["crupier"] = dealer_pts

    # Muestra suficiente
    sample_pts = 15 if stats["n"] >= 200 else 10 if stats["n"] >= 100 else 5 if stats["n"] >= 50 else 0
    score += sample_pts
    detalles["muestra"] = sample_pts

    # Penalización de muestra pequeña
    if stats["n"] < 50:
        score = min(score, 64)

    return int(np.clip(score,0,100)), {
        "score": int(np.clip(score,0,100)),
        "dealer_score": stats["score"],
        "dealer_n": stats["n"],
        "detalles": detalles
    }

def estado_score(score):
    if score >= ENTRY_SCORE:
        return "🟢 ENTRAR"
    if score >= OBSERVE_SCORE:
        return "🟡 OBSERVAR"
    return "🔴 NO APOSTAR"

# ---------------- BACKTEST ----------------
def simular_estrategia(
    df,
    distancia=5,
    limite=8,
    max_prev=2,
    permitir_s2=False,
    dealer_mode="Todos",
    min_dealer=0
):
    """Backtest limpio, cronológico y sin mirar el futuro.
    Una sola señal activa por vez. 1 U por tiro.
    La ganancia de una apuesta al número en ruleta europea es:
    +35 neto si acierta, -1 por cada tiro apostado.
    """
    if df.empty:
        return pd.DataFrame(), {}

    data = df.sort_values(["Fecha","Hora"], kind="stable").reset_index(drop=True).copy()
    trades = []
    active = None

    # Estadística acumulada por crupier SOLO con datos anteriores.
    dealer_history = {}

    for i, row in data.iterrows():
        dealer = str(row["Crupier"]).upper()
        num = int(row["Numero"])

        # Si hay apuesta activa, se evalúa primero.
        if active is not None:
            active["tiros"] += 1
            if num == active["numero"]:
                costo = active["tiros"]
                pnl = 36 - costo
                trades.append({
                    "indice": i, "Fecha": row["Fecha"], "Hora": row["Hora"],
                    "Crupier": dealer, "Numero": active["numero"],
                    "Estrategia": active["estrategia"],
                    "Distancia": active.get("distancia"),
                    "Score": active.get("score"),
                    "Tiros": costo, "Resultado":"WIN",
                    "PnL": pnl
                })
                active = None
            elif active["tiros"] >= limite:
                trades.append({
                    "indice": i, "Fecha": row["Fecha"], "Hora": row["Hora"],
                    "Crupier": dealer, "Numero": active["numero"],
                    "Estrategia": active["estrategia"],
                    "Distancia": active.get("distancia"),
                    "Score": active.get("score"),
                    "Tiros": active["tiros"], "Resultado":"LOSS",
                    "PnL": -active["tiros"]
                })
                active = None

        # Historial del crupier hasta ANTES de esta tirada.
        prev_df = data.iloc[:i]
        dealer_prev = prev_df[prev_df["Crupier"] == dealer]
        nums = dealer_prev["Numero"].tolist()

        # Si cambió el crupier mientras había una señal, no continuamos la señal.
        # El registro de abandono evita esconder pérdidas/operaciones incompletas.
        if active is not None and active.get("dealer") != dealer:
            trades.append({
                "indice": i, "Fecha": row["Fecha"], "Hora": row["Hora"],
                "Crupier": dealer, "Numero": active["numero"],
                "Estrategia": active["estrategia"],
                "Distancia": active.get("distancia"),
                "Score": active.get("score"),
                "Tiros": active["tiros"], "Resultado":"ABANDONADA_CAMBIO_CRUPIER",
                "PnL": -active["tiros"]
            })
            active = None

        # Detectar nueva señal usando solo las tiradas previas + actual.
        if active is None and len(nums) >= 2:
            s1 = señal_s1(nums + [num], distancia, max_prev)
            if s1:
                ds = dealer_stats(prev_df, dealer)
                if dealer_mode == "Confiables" and ds["n"] < min_dealer:
                    s1 = None
                if s1:
                    sc, meta = señal_score(s1, prev_df, dealer)
                    # Backtest de estrategia: se registra toda señal,
                    # pero para "modo score" se puede filtrar.
                    active = {
                        "numero": s1["numero"],
                        "estrategia":"S1",
                        "distancia":s1["distancia"],
                        "score":sc,
                        "tiros":0,
                        "dealer":dealer
                    }

        # Actualizar el historial conceptual después de la tirada.
        dealer_history.setdefault(dealer, []).append(num)

    tdf = pd.DataFrame(trades)
    if tdf.empty:
        return tdf, {
            "operaciones":0,"wins":0,"losses":0,"pnl":0.0,
            "exposicion":0.0,"roi":0.0,"drawdown":0.0
        }

    wins = int((tdf["Resultado"]=="WIN").sum())
    losses = int((tdf["Resultado"]=="LOSS").sum())
    pnl = float(tdf["PnL"].sum())
    exposicion = float(tdf["Tiros"].sum())
    roi = (pnl/exposicion*100) if exposicion else 0.0
    equity = tdf["PnL"].cumsum()
    peak = equity.cummax()
    drawdown = float((peak-equity).max())
    return tdf, {
        "operaciones":len(tdf),
        "wins":wins,
        "losses":losses,
        "pnl":pnl,
        "exposicion":exposicion,
        "roi":roi,
        "drawdown":drawdown,
        "win_rate": wins/len(tdf)*100 if len(tdf) else 0
    }

# ---------------- SESSION STATE ----------------
if "datos_cargados" not in st.session_state:
    st.session_state.df_nube = cargar_tiradas_nube()
    st.session_state.lista_crupieres = cargar_crupieres_nube()
    st.session_state.datos_cargados = True

if "historial_sesion" not in st.session_state:
    st.session_state.historial_sesion = []
if "balance_dia" not in st.session_state:
    st.session_state.balance_dia = 0.0
if "balance_paper" not in st.session_state:
    st.session_state.balance_paper = 0.0
if "caceria_activa" not in st.session_state:
    st.session_state.caceria_activa = None
if "fallos_secos" not in st.session_state:
    st.session_state.fallos_secos = 0
if "fallos_totales" not in st.session_state:
    st.session_state.fallos_totales = 0
if "paper_mode" not in st.session_state:
    st.session_state.paper_mode = True
if "s1_distancia" not in st.session_state:
    st.session_state.s1_distancia = DEFAULT_S1_DISTANCIA
if "s1_limite" not in st.session_state:
    st.session_state.s1_limite = DEFAULT_S1_LIMITE
if "max_previas" not in st.session_state:
    st.session_state.max_previas = DEFAULT_MAX_PREVIAS

# ---------------- UI ----------------
tab_main, tab_lab, tab_stats, tab_settings = st.tabs([
    "🎯 Panel Principal",
    "🧪 Laboratorio / Backtest",
    "📊 Estadísticas",
    "⚙️ Configuración"
])

with tab_main:
    col_left, col_right = st.columns([1,3])

    with col_left:
        st.markdown("### ⚙️ Control")
        lista = st.session_state.lista_crupieres or ["SIN_CRUPIER"]
        crupier_actual = st.selectbox("Crupier activo", lista)

        st.session_state.paper_mode = st.toggle(
            "🧪 PAPER TRADING (recomendado)",
            value=st.session_state.paper_mode,
            help="Registra resultados de prueba sin considerarlos dinero real."
        )

        modo = st.selectbox(
            "Modo de decisión",
            ["Motor V5 — Score dinámico", "Solo observar señales", "Manual / sin filtro"]
        )

        st.session_state.s1_distancia = st.number_input(
            "Distancia máxima S1", 1, 10, st.session_state.s1_distancia
        )
        st.session_state.s1_limite = st.number_input(
            "Máximo de tiros S1", 4, 12, st.session_state.s1_limite
        )
        st.session_state.max_previas = st.number_input(
            "Máx. apariciones previas", 1, 4, st.session_state.max_previas
        )

        st.info(
            "S2 permanece en OBSERVACIÓN. La V5 no la utiliza para entrar "
            "automáticamente hasta reunir más evidencia."
        )

        if st.button("🔄 Sincronizar histórico"):
            st.session_state.df_nube = cargar_tiradas_nube()
            st.session_state.lista_crupieres = cargar_crupieres_nube()
            st.success(f"Histórico actualizado: {len(st.session_state.df_nube):,} tiradas.")
            st.rerun()

        if st.button("☀️ Reiniciar sesión de prueba"):
            st.session_state.historial_sesion = []
            st.session_state.balance_dia = 0.0
            st.session_state.balance_paper = 0.0
            st.session_state.caceria_activa = None
            st.session_state.fallos_secos = 0
            st.session_state.fallos_totales = 0
            st.rerun()

    with col_right:
        st.markdown("## 🎰 RULETA EDGE V5")
        st.caption(
            "Motor experimental: 1 U fija • sin Martingala • S1 <= 5 por defecto • "
            "S2 solo observación • validación histórica."
        )

        cols = st.columns(12)
        nums = [
            3,6,9,12,15,18,21,24,27,30,33,36,
            2,5,8,11,14,17,20,23,26,29,32,35,
            1,4,7,10,13,16,19,22,25,28,31,34
        ]
        def registrar_numero(n):
            st.session_state.historial_sesion.append({
                "Fecha":datetime.now().strftime("%Y-%m-%d"),
                "Hora":datetime.now().strftime("%H:%M:%S"),
                "Crupier":crupier_actual,
                "Numero":int(n)
            })

        # Botón 0
        if st.button("0", key="btn_zero", use_container_width=True):
            registrar_numero(0)
            st.rerun()

        for idx, n in enumerate(nums):
            with cols[idx % 12]:
                if st.button(str(n), key=f"v5_{n}", use_container_width=True):
                    registrar_numero(n)
                    st.rerun()

        # Construir historial actual
        if st.session_state.historial_sesion:
            hdf = pd.DataFrame(st.session_state.historial_sesion)
            serie = hdf[hdf["Crupier"] == crupier_actual]["Numero"].tolist()
        else:
            hdf = pd.DataFrame(columns=["Fecha","Hora","Crupier","Numero"])
            serie = []

        # Mezcla histórico + sesión para score, sin incluir la tirada actual
        df_hist = st.session_state.df_nube.copy()
        ds = dealer_stats(df_hist, crupier_actual)

        st.divider()
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Balance sesión", f"{st.session_state.balance_dia:.2f} U")
        c2.metric("Paper P&L", f"{st.session_state.balance_paper:.2f} U")
        c3.metric("Score crupier", f"{ds['score']:.0f}/100")
        c4.metric("Muestra crupier", f"{ds['n']:,}")

        # Señal actual
        s1 = señal_s1(serie, st.session_state.s1_distancia, st.session_state.max_previas)
        s2 = detectar_s2_observacion(serie)

        if s1:
            score, meta = señal_score(s1, df_hist, crupier_actual)
            estado = estado_score(score)
            box = "edge-green" if score >= ENTRY_SCORE else "edge-yellow" if score >= OBSERVE_SCORE else "edge-red"
            st.markdown(f'<div class="{box}">', unsafe_allow_html=True)
            st.markdown(f"### {estado}")
            st.write(
                f"**Número:** {s1['numero']} · **S1:** repetición a distancia {s1['distancia']} · "
                f"**Apariciones previas:** {s1['apariciones_previas']} · **Score:** {score}/100"
            )
            st.caption(
                f"Crupier: {crupier_actual} · Score crupier: {meta['dealer_score']:.1f} · "
                f"Muestra: {meta['dealer_n']}"
            )
            if score >= ENTRY_SCORE and modo == "Motor V5 — Score dinámico":
                st.success(
                    f"ENTRADA EXPERIMENTAL: 1 U al {s1['numero']} durante hasta "
                    f"{st.session_state.s1_limite} tiros."
                )
            elif score >= OBSERVE_SCORE:
                st.warning("OBSERVAR: hay señal, pero no supera el umbral de entrada.")
            else:
                st.error("NO APOSTAR: evidencia insuficiente.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No hay señal S1 que supere las condiciones actuales.")

        if s2:
            st.warning(
                f"🔬 S2 EN OBSERVACIÓN: el {s2['numero']} aparece {s2['apariciones']} "
                "veces en la ventana reciente. No genera entrada automática."
            )

        # Historial visible
        st.divider()
        st.markdown("### 📜 Tiradas de la sesión")
        if not hdf.empty:
            st.dataframe(hdf.tail(50).sort_index(ascending=False), use_container_width=True, height=240)
        else:
            st.caption("Aún no hay tiradas registradas en esta sesión.")

with tab_lab:
    st.subheader("🧪 Laboratorio V5 — Backtest")
    st.write(
        "El laboratorio usa el histórico de Google Sheets en orden cronológico. "
        "No usa información futura para generar una señal."
    )

    df_lab = st.session_state.df_nube.copy()
    if df_lab.empty:
        st.warning("No hay datos históricos disponibles.")
    else:
        a,b,c,d = st.columns(4)
        dist = a.slider("Distancia S1", 1, 8, DEFAULT_S1_DISTANCIA)
        limite = b.slider("Límite S1", 4, 12, DEFAULT_S1_LIMITE)
        previas = c.slider("Máx. previas", 1, 4, DEFAULT_MAX_PREVIAS)
        dealer_mode = d.selectbox("Filtro", ["Todos", "Confiables"])

        tdf, res = simular_estrategia(
            df_lab, distancia=dist, limite=limite, max_prev=previas,
            dealer_mode=dealer_mode, min_dealer=MIN_DEALER_SAMPLE
        )

        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Operaciones", res["operaciones"])
        m2.metric("Aciertos", res["wins"])
        m3.metric("Fallos", res["losses"])
        m4.metric("P&L", f"{res['pnl']:.1f} U")
        m5.metric("ROI", f"{res['roi']:.2f}%")

        if not tdf.empty:
            eq = tdf["PnL"].cumsum()
            st.line_chart(pd.DataFrame({"Equity":eq.values}))
            st.dataframe(tdf.tail(100), use_container_width=True)

        st.markdown("### 🔬 Comparación de configuraciones")
        rows = []
        for dd in range(3, 8):
            for ll in range(6, 11):
                t, r = simular_estrategia(df_lab, dd, ll, 2)
                rows.append({
                    "Distancia":dd, "Límite":ll,
                    "Operaciones":r["operaciones"],
                    "Aciertos":r["wins"],
                    "P&L":round(r["pnl"],2),
                    "ROI_%":round(r["roi"],2),
                    "Drawdown":round(r["drawdown"],2)
                })
        comp = pd.DataFrame(rows).sort_values(
            ["ROI_%","Operaciones"], ascending=[False,False]
        )
        st.dataframe(comp.head(15), use_container_width=True)

with tab_stats:
    st.subheader("📊 Estadísticas del sistema")
    df = st.session_state.df_nube
    if df.empty:
        st.info("No hay histórico.")
    else:
        st.write(f"**Tiradas históricas:** {len(df):,}")
        st.write(f"**Crupieres:** {df['Crupier'].nunique()}")
        st.write(f"**Días:** {df['Fecha'].nunique()}")

        dealer_rows = []
        for dealer in sorted(df["Crupier"].dropna().unique()):
            s = dealer_stats(df, dealer)
            dealer_rows.append({
                "Crupier":dealer,
                "Muestra":s["n"],
                "Tasa_repetición_5":round(s["repeat_rate"]*100,2),
                "Score":round(s["score"],1),
                "Estado":"APTO" if s["n"]>=MIN_DEALER_SAMPLE and s["score"]>=ENTRY_SCORE else
                         "OBSERVAR" if s["n"]>=MIN_DEALER_SAMPLE else "MUESTRA BAJA"
            })
        dtable = pd.DataFrame(dealer_rows).sort_values(["Score","Muestra"], ascending=False)
        st.dataframe(dtable, use_container_width=True)

        st.markdown("### Frecuencia de números")
        freq = df["Numero"].value_counts().sort_index()
        freq_df = pd.DataFrame({
            "Número":freq.index,
            "Apariciones":freq.values,
            "Frecuencia_%":(freq.values/len(df)*100).round(3)
        })
        st.dataframe(freq_df, use_container_width=True)

with tab_settings:
    st.subheader("⚙️ Configuración")
    st.markdown("""
    **Reglas V5 activas**

    - S1: repetición a distancia máxima configurable; valor inicial recomendado = **5**.
    - Apariciones previas máximas: **2**.
    - Cobertura inicial: **8 tiros**.
    - Renovación: **máximo 1**.
    - S2: **solo observación**.
    - Apuesta: **1 U fija**.
    - Sin Martingala.
    - Crupier: score dinámico; no se usan listas Top/Tóxicos fijas.
    - Cambio de crupier: las señales abiertas se deben cerrar/registrar como abandono.
    - Objetivo: acumular nuevos datos para validar fuera de muestra.
    """)
    st.warning(
        "No interpretes un ROI histórico positivo como garantía de rentabilidad futura. "
        "La V5 está diseñada para paper trading y validación."
    )

with st.sidebar:
    st.markdown("## RULETA EDGE V5")
    st.write("Modo experimental / paper trading")
    st.write(f"Entrada: **Score ≥ {ENTRY_SCORE}**")
    st.write(f"Observación: **{OBSERVE_SCORE}–{ENTRY_SCORE-1}**")
    st.write("S2: **solo laboratorio**")
    st.write("Stake: **1 U fija**")
