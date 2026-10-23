
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, timedelta

# ── Configuration ──────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KbS5fA33r6o1isdXdT_dWZMDIgtbAG17t0TKa9bdDpw"
APP_PASSWORD = "atelier2026"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DESTINATIONS = ["Peinture", "Galvanisation", "Chantier"]
CAMIONS = ["Camion 1", "Camion 2", "Camion 3"]

COLORS = {
    "Peinture":      "#4A90D9",
    "Galvanisation": "#E67E22",
    "Chantier":      "#27AE60",
}

# ── Connexion Google Sheets ─────────────────────────────────────
@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(client, tab_name):
    sh = client.open_by_url(SHEET_URL)
    try:
        return sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=500, cols=20)
        ws.append_row(["id_tache", "affaire", "ouvrage", "destination",
                       "nom_chantier", "semaine", "camion", "date_livraison",
                       "statut", "commentaire"])
        return ws

# ── Lecture des taches terminees ───────────────────────────────
@st.cache_data(ttl=60)
def load_taches_terminees(_client):
    sh = _client.open_by_url(SHEET_URL)
    ws = sh.worksheet("taches")
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame(columns=["id", "affaire", "ouvrage", "statut"])
    col_statut = None
    for c in df.columns:
        if c.lower() in ("statut", "status", "etat", "etat_tache"):
            col_statut = c
            break
    if col_statut is None:
        return pd.DataFrame(columns=["id", "affaire", "ouvrage", "statut"])
    df_term = df[df[col_statut].str.strip().str.lower() == "termine"].copy()
    cols_map = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ("id", "id_tache", "identifiant"):
            cols_map["id"] = c
        elif cl in ("affaire", "chantier", "projet"):
            cols_map["affaire"] = c
        elif cl in ("ouvrage", "tache", "designation", "libelle"):
            cols_map["ouvrage"] = c
    rename = {v: k for k, v in cols_map.items()}
    rename[col_statut] = "statut"
    df_term = df_term.rename(columns=rename)
    for col in ["id", "affaire", "ouvrage"]:
        if col not in df_term.columns:
            df_term[col] = ""
    return df_term[["id", "affaire", "ouvrage", "statut"]]

# ── Lecture des livraisons ─────────────────────────────────────
@st.cache_data(ttl=30)
def load_livraisons(_client):
    ws = get_sheet(_client, "livraisons")
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=["id_tache", "affaire", "ouvrage",
                                     "destination", "nom_chantier", "semaine",
                                     "camion", "date_livraison", "statut",
                                     "commentaire"])
    return pd.DataFrame(data)

def save_livraison(client, row_dict):
    ws = get_sheet(client, "livraisons")
    ws.append_row([
        row_dict.get("id_tache", ""),
        row_dict.get("affaire", ""),
        row_dict.get("ouvrage", ""),
        row_dict.get("destination", ""),
        row_dict.get("nom_chantier", ""),
        row_dict.get("semaine", ""),
        row_dict.get("camion", ""),
        row_dict.get("date_livraison", ""),
        row_dict.get("statut", "Planifie"),
        row_dict.get("commentaire", ""),
    ])
    st.cache_data.clear()

def update_livraison_statut(client, id_tache, new_statut):
    ws = get_sheet(client, "livraisons")
    data = ws.get_all_records()
    for i, row in enumerate(data):
        if str(row.get("id_tache", "")) == str(id_tache):
            ws.update_cell(i + 2, 9, new_statut)
            break
    st.cache_data.clear()

# ── Utilitaires semaine ────────────────────────────────────────
def get_semaine_label(d: date) -> str:
    iso = d.isocalendar()
    return f"S{iso[1]:02d}-{iso[0]}"

def semaine_to_dates(semaine_label: str):
    try:
        parts = semaine_label.replace("S", "").split("-")
        week = int(parts[0])
        year = int(parts[1])
        lundi = date.fromisocalendar(year, week, 1)
        vendredi = lundi + timedelta(days=4)
        return lundi, vendredi
    except Exception:
        return None, None

def get_next_semaines(n=16):
    today = date.today()
    semaines = []
    d = today - timedelta(days=today.weekday())
    for _ in range(n):
        semaines.append(get_semaine_label(d))
        d += timedelta(weeks=1)
    return semaines

# ── CSS ────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.8; font-size: 0.95rem; }
    .card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.4rem 0;
        border-left: 5px solid #4A90D9;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .card-peinture      { border-left-color: #4A90D9; }
    .card-galvanisation { border-left-color: #E67E22; }
    .card-chantier      { border-left-color: #27AE60; }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        color: white;
    }
    .badge-planifie { background: #4A90D9; }
    .badge-livre    { background: #27AE60; }
    .badge-reporte  { background: #E74C3C; }
    .semaine-header {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 1rem 0 0.5rem;
        font-weight: 700;
        color: #1a1a2e;
        border-left: 4px solid #0f3460;
    }
    </style>
    """, unsafe_allow_html=True)

# ── Authentification ───────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="main-header">
        <h1>Livraisons Atelier</h1>
        <p>Planning de livraison des ouvrages finis</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Connexion")
        if submitted:
            if pwd == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    return False

# ── Page : Planifier ───────────────────────────────────────────
def page_planifier(client):
    st.subheader("Planifier une livraison")
    taches = load_taches_terminees(client)
    livraisons = load_livraisons(client)

    ids_planifies = set(livraisons["id_tache"].astype(str).tolist()) if not livraisons.empty else set()
    taches_dispo = taches[~taches["id"].astype(str).isin(ids_planifies)].copy()

    if taches_dispo.empty:
        st.info("Aucun ouvrage termine en attente de planification.")
        return

    with st.form("form_livraison"):
        st.markdown("**Ouvrage a livrer**")
        options = [
            f"{r['affaire']} -- {r['ouvrage']} (id: {r['id']})"
            for _, r in taches_dispo.iterrows()
        ]
        choix = st.selectbox("Selectionner l'ouvrage", options)
        idx = options.index(choix)
        tache_sel = taches_dispo.iloc[idx]

        col1, col2 = st.columns(2)
        with col1:
            destination = st.selectbox("Destination", DESTINATIONS)
        with col2:
            semaines = get_next_semaines(16)
            semaine = st.selectbox("Semaine de livraison", semaines)

        nom_chantier = st.text_input("Nom du chantier (si destination = Chantier)")

        col3, col4 = st.columns(2)
        with col3:
            camion = st.selectbox("Camion", CAMIONS)
        with col4:
            date_liv = st.date_input("Date prevue", value=date.today())

        commentaire = st.text_area("Commentaire (optionnel)", height=80)

        submitted = st.form_submit_button("Planifier la livraison", type="primary")
        if submitted:
            if destination == "Chantier" and not nom_chantier.strip():
                st.error("Veuillez saisir le nom du chantier.")
            else:
                save_livraison(client, {
                    "id_tache":       str(tache_sel["id"]),
                    "affaire":        str(tache_sel["affaire"]),
                    "ouvrage":        str(tache_sel["ouvrage"]),
                    "destination":    destination,
                    "nom_chantier":   nom_chantier.strip(),
                    "semaine":        semaine,
                    "camion":         camion,
                    "date_livraison": str(date_liv),
                    "statut":         "Planifie",
                    "commentaire":    commentaire.strip(),
                })
                st.success(f"Livraison planifiee : {tache_sel['ouvrage']} -> {destination} ({semaine})")

# ── Page : Planning par semaine ────────────────────────────────
def page_planning(client):
    st.subheader("Planning de livraison")
    livraisons = load_livraisons(client)

    if livraisons.empty:
        st.info("Aucune livraison planifiee pour l'instant.")
        return

    semaines_dispo = sorted(livraisons["semaine"].unique().tolist())
    semaine_sel = st.selectbox("Semaine", semaines_dispo)

    df_sem = livraisons[livraisons["semaine"] == semaine_sel].copy()
    lundi, vendredi = semaine_to_dates(semaine_sel)
    if lundi:
        st.markdown(f"""
        <div class="semaine-header">
            Semaine {semaine_sel} &nbsp;|&nbsp;
            {lundi.strftime('%d/%m/%Y')} au {vendredi.strftime('%d/%m/%Y')}
            &nbsp;|&nbsp; {len(df_sem)} livraison(s)
        </div>
        """, unsafe_allow_html=True)

    if df_sem.empty:
        st.info("Aucune livraison cette semaine.")
        return

    for camion in CAMIONS:
        df_cam = df_sem[df_sem["camion"] == camion]
        if df_cam.empty:
            continue
        st.markdown(f"**{camion}** ({len(df_cam)} livraison(s))")
        for _, row in df_cam.iterrows():
            dest = row.get("destination", "")
            css_class = f"card-{dest.lower()}" if dest.lower() in ("peinture", "galvanisation", "chantier") else ""
            color = COLORS.get(dest, "#888")
            label_dest = dest
            if dest == "Chantier" and row.get("nom_chantier"):
                label_dest = f"Chantier : {row['nom_chantier']}"
            statut = row.get("statut", "Planifie")
            badge_class = f"badge-{statut.lower()}" if statut.lower() in ("planifie", "livre", "reporte") else "badge-planifie"
            commentaire_html = f"<br><em style='font-size:0.85rem;color:#666'>{row.get('commentaire','')}</em>" if row.get("commentaire") else ""
            st.markdown(f"""
            <div class="card {css_class}">
                <strong>{row.get('ouvrage','')}</strong>
                &nbsp;<span style="color:#666;font-size:0.9rem">{row.get('affaire','')}</span><br>
                <span style="color:{color};font-weight:600">{label_dest}</span>
                &nbsp;&nbsp;
                <span class="badge {badge_class}">{statut}</span>
                &nbsp;&nbsp;
                <span style="color:#888;font-size:0.85rem">{row.get('date_livraison','')}</span>
                {commentaire_html}
            </div>
            """, unsafe_allow_html=True)

        with st.expander(f"Mettre a jour le statut ({camion})"):
            for _, row in df_cam.iterrows():
                col_a, col_b = st.columns([3, 2])
                with col_a:
                    st.write(f"{row.get('ouvrage','')} -- {row.get('affaire','')}")
                with col_b:
                    statut_actuel = row.get("statut", "Planifie")
                    if statut_actuel not in ["Planifie", "Livre", "Reporte"]:
                        statut_actuel = "Planifie"
                    new_statut = st.selectbox(
                        "Statut",
                        ["Planifie", "Livre", "Reporte"],
                        index=["Planifie", "Livre", "Reporte"].index(statut_actuel),
                        key=f"statut_{row.get('id_tache','')}_{camion}",
                    )
                    if st.button("Sauvegarder", key=f"btn_{row.get('id_tache','')}_{camion}"):
                        update_livraison_statut(client, row.get("id_tache", ""), new_statut)
                        st.success("Statut mis a jour !")
                        st.rerun()

# ── Page : Tableau de bord ─────────────────────────────────────
def page_dashboard(client):
    st.subheader("Tableau de bord")
    livraisons = load_livraisons(client)
    taches = load_taches_terminees(client)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ouvrages termines", len(taches))
    with col2:
        n_planif = len(livraisons[livraisons["statut"] == "Planifie"]) if not livraisons.empty else 0
        st.metric("Livraisons planifiees", n_planif)
    with col3:
        n_livre = len(livraisons[livraisons["statut"] == "Livre"]) if not livraisons.empty else 0
        st.metric("Livraisons effectuees", n_livre)
    with col4:
        n_att = len(taches) - len(livraisons) if not livraisons.empty else len(taches)
        st.metric("En attente de planification", max(n_att, 0))

    if not livraisons.empty:
        st.markdown("---")
        st.markdown("**Repartition par destination**")
        dest_counts = livraisons["destination"].value_counts()
        col_a, col_b, col_c = st.columns(3)
        for col, dest in zip([col_a, col_b, col_c], DESTINATIONS):
            with col:
                count = int(dest_counts.get(dest, 0))
                color = COLORS.get(dest, "#888")
                st.markdown(f"""
                <div style="background:{color};color:white;border-radius:10px;
                            padding:1rem;text-align:center;">
                    <div style="font-size:2rem;font-weight:700">{count}</div>
                    <div style="font-size:0.9rem">{dest}</div>
                </div>
                """, unsafe_allow_html=True)

# ── Main ───────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Livraisons Atelier",
        page_icon="🚚",
        layout="wide",
    )
    inject_css()

    if not check_password():
        return

    client = get_client()

    st.markdown("""
    <div class="main-header">
        <h1>🚚 Livraisons Atelier</h1>
        <p>Planning de livraison des ouvrages finis</p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Tableau de bord", "Planifier une livraison", "Planning par semaine"])
    with tabs[0]:
        page_dashboard(client)
    with tabs[1]:
        page_planifier(client)
    with tabs[2]:
        page_planning(client)

if __name__ == "__main__":
    main()
