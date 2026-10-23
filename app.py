
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, date
import uuid

st.set_page_config(
    page_title="Planning Livraisons",
    page_icon="\U0001f69b",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.main { background: #f4f6f9; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: white; padding: 8px; border-radius: 10px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; font-weight: 500; }
.stTabs [aria-selected="true"] { background: #1a2340 !important; color: white !important; }
.app-header {
    background: linear-gradient(135deg, #1a2340 0%, #2d3a5e 100%);
    color: white; padding: 18px 28px; border-radius: 12px; margin-bottom: 20px;
}
.app-header h1 { margin: 0; font-size: 1.4rem; font-weight: 700; }
.app-header p  { margin: 4px 0 0 0; font-size: 0.85rem; opacity: 0.75; }
.stat-card {
    background: white; border-radius: 10px; padding: 16px 20px;
    text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.stat-num   { font-size: 2rem; font-weight: 700; color: #1a2340; }
.stat-label { font-size: 0.8rem; color: #888; margin-top: 2px; }
.card {
    background: white; border-radius: 10px; padding: 12px 14px;
    margin-bottom: 8px; border-left: 5px solid #ccc;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.card-livraison  { border-left-color: #1a2340; }
.card-enlevement { border-left-color: #7c3aed; }
.card-autre      { border-left-color: #ea580c; }
.card-divers     { border-left-color: #6b7280; }
.card-titre { font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }
.card-detail { font-size: 0.82rem; color: #555; line-height: 1.7; }
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; margin-right: 6px;
}
.badge-planifie  { background: #dbeafe; color: #1d4ed8; }
.badge-livre     { background: #dcfce7; color: #16a34a; }
.badge-reporte   { background: #fee2e2; color: #dc2626; }
.badge-tl { background: #e0e7ff; color: #1a2340; }
.badge-te { background: #ede9fe; color: #7c3aed; }
.badge-ta { background: #ffedd5; color: #ea580c; }
.badge-td { background: #f3f4f6; color: #6b7280; }
.col-jour {
    background: white; border-radius: 10px; padding: 10px;
    min-height: 120px; box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    margin-bottom: 8px;
}
.col-jour-today { border: 2px solid #1a2340; }
.col-jour-header {
    text-align: center; font-weight: 700; font-size: 0.85rem;
    color: #1a2340; padding: 4px 0 8px 0;
    border-bottom: 2px solid #e5e7eb; margin-bottom: 8px;
}
.day-num { font-size: 1.6rem; font-weight: 700; display: block; }
.day-vide { text-align:center; color:#ccc; font-size:0.8rem; padding:16px 0; }
.bandeau-jour {
    background: #1a2340; color: white; padding: 10px 16px;
    border-radius: 8px; margin: 12px 0 8px 0; font-weight: 600;
}
@media print {
    header, footer, [data-testid="stToolbar"],
    [data-testid="stSidebar"], .stTabs { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_URL   = "https://docs.google.com/spreadsheets/d/1KbS5fA33r6o1isdXdT_dWZMDIgtbAG17t0TKa9bdDpw"
MOT_DE_PASSE = "atelier2026"

TYPES_TRAJET = ["Livraison ouvrage", "Enlevement / Collecte", "Livraison autre", "Trajet divers"]
DESTINATIONS = ["Peinture", "Galvanisation", "Chantier", "Autre"]
CAMIONS      = ["Camion 1", "Camion 2", "Camion 3", "Vehicule leger"]
STATUTS      = ["Planifie", "Livre", "Reporte"]
JOURS_FR     = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

TYPE_CARD = {
    "Livraison ouvrage":    "card-livraison",
    "Enlevement / Collecte":"card-enlevement",
    "Livraison autre":      "card-autre",
    "Trajet divers":        "card-divers",
}
TYPE_BADGE = {
    "Livraison ouvrage":    "badge-tl",
    "Enlevement / Collecte":"badge-te",
    "Livraison autre":      "badge-ta",
    "Trajet divers":        "badge-td",
}
TYPE_EMOJI = {
    "Livraison ouvrage":    "\U0001f535",
    "Enlevement / Collecte":"\U0001f7e3",
    "Livraison autre":      "\U0001f7e0",
    "Trajet divers":        "\u26ab",
}
STATUT_BADGE = {
    "Planifie":"badge-planifie",
    "Livre":   "badge-livre",
    "Reporte": "badge-reporte",
}

HEADER_LIVRAISONS = [
    "id_trajet","type_trajet","id_tache","affaire","ouvrage",
    "destination","nom_chantier","description","adresse",
    "contact_nom","contact_tel","date_livraison","semaine",
    "heure_debut","heure_fin","camion","statut","commentaire"
]

@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def open_sheet():
    return get_client().open_by_url(SHEET_URL)

def get_ws(name):
    try:
        return open_sheet().worksheet(name)
    except gspread.WorksheetNotFound:
        return None

def init_livraisons():
    sh = open_sheet()
    try:
        ws = sh.worksheet("livraisons")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet("livraisons", rows=1000, cols=20)
    if ws.row_values(1) != HEADER_LIVRAISONS:
        ws.clear()
        ws.append_row(HEADER_LIVRAISONS)
    return ws

def load_livraisons():
    ws = get_ws("livraisons")
    if ws is None:
        return pd.DataFrame()
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if "date_livraison" in df.columns:
        df["date_livraison"] = pd.to_datetime(df["date_livraison"], errors="coerce")
    return df

def load_taches_terminees():
    ws = get_ws("taches")
    if ws is None:
        return pd.DataFrame()
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df.columns = [c.lower().strip() for c in df.columns]
    col_s = next((c for c in df.columns if "statut" in c), None)
    if col_s is None:
        return pd.DataFrame()
    return df[df[col_s].str.strip().str.lower() == "termine"].copy()

def save_trajet(row_data):
    ws = get_ws("livraisons") or init_livraisons()
    ws.append_row(row_data)

def do_update_statut(ws, row_idx, new_statut):
    ws.update_cell(row_idx + 2, HEADER_LIVRAISONS.index("statut") + 1, new_statut)

def do_delete_trajet(ws, row_idx):
    ws.delete_rows(row_idx + 2)

def get_semaines(n=12):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    result = []
    for i in range(-2, n):
        d = monday + timedelta(weeks=i)
        iso = d.isocalendar()
        result.append(f"S{iso[1]:02d}-{iso[0]}")
    return result

def semaine_to_dates(s):
    try:
        parts = s.replace("S","").split("-")
        week, year = int(parts[0]), int(parts[1])
        monday = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w").date()
        return [monday + timedelta(days=i) for i in range(5)]
    except Exception:
        return []

def heures_list():
    h = []
    for hh in range(5, 22):
        for mm in [0, 15, 30, 45]:
            h.append(f"{hh:02d}:{mm:02d}")
    return h

def card_html(row):
    typ  = str(row.get("type_trajet",""))
    desc = str(row.get("description","") or row.get("ouvrage","") or "")
    hd   = str(row.get("heure_debut",""))
    hf   = str(row.get("heure_fin",""))
    adr  = str(row.get("adresse",""))
    cnt  = str(row.get("contact_nom",""))
    cam  = str(row.get("camion",""))
    stat = str(row.get("statut","Planifie"))
    dest = str(row.get("destination",""))

    cc = TYPE_CARD.get(typ, "card-divers")
    bc = TYPE_BADGE.get(typ, "badge-td")
    sc = STATUT_BADGE.get(stat, "badge-planifie")

    parts = []
    if hd and hf:
        parts.append(f"\u23f1 {hd} - {hf}")
    if dest:
        parts.append(f"\u2192 {dest}")
    if adr:
        parts.append(f"\U0001f4cd {adr}")
    if cnt:
        parts.append(f"\U0001f464 {cnt}")
    if cam:
        parts.append(f"\U0001f69a {cam}")

    detail = "<br>".join(parts)

    return f"""<div class="card {cc}">
  <div class="card-titre">
    <span class="badge {bc}">{typ}</span>
    <span class="badge {sc}">{stat}</span>
    {desc}
  </div>
  <div class="card-detail">{detail}</div>
</div>"""

def check_auth():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("""
        <div style='max-width:360px;margin:80px auto;background:white;
             border-radius:14px;padding:36px;box-shadow:0 4px 20px rgba(0,0,0,0.1);
             text-align:center;'>
          <div style='font-size:2.5rem;'>\U0001f69b</div>
          <h2 style='color:#1a2340;margin:8px 0 4px;'>Planning Livraisons</h2>
          <p style='color:#888;font-size:0.85rem;margin-bottom:24px;'>Acces securise</p>
        </div>""", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("Mot de passe", type="password",
                                label_visibility="collapsed",
                                placeholder="Mot de passe")
            if st.button("Connexion", use_container_width=True, type="primary"):
                if pwd == MOT_DE_PASSE:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        st.stop()

def onglet_dashboard(df):
    today = date.today()
    iso   = today.isocalendar()
    sem   = f"S{iso[1]:02d}-{iso[0]}"

    df_sem = df[df["semaine"] == sem] if not df.empty and "semaine" in df.columns else pd.DataFrame()

    total     = len(df) if not df.empty else 0
    planifies = int((df["statut"] == "Planifie").sum()) if not df.empty and "statut" in df.columns else 0
    livres    = int((df["statut"] == "Livre").sum())    if not df.empty and "statut" in df.columns else 0
    cette_sem = len(df_sem)

    c1, c2, c3, c4 = st.columns(4)
    for col, num, label in [
        (c1, total,     "Trajets total"),
        (c2, cette_sem, "Cette semaine"),
        (c3, planifies, "Planifies"),
        (c4, livres,    "Livres"),
    ]:
        with col:
            st.markdown(f"""<div class="stat-card">
              <div class="stat-num">{num}</div>
              <div class="stat-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    if df.empty:
        st.info("Aucun trajet enregistre pour le moment.")
        return

    st.markdown("### \U0001f4c5 Prochains trajets")
    if "date_livraison" in df.columns:
        df_f = df[
            df["date_livraison"].notna() &
            (df["date_livraison"].dt.date >= today) &
            (df["statut"] != "Livre")
        ].sort_values("date_livraison")
    else:
        df_f = pd.DataFrame()

    if df_f.empty:
        st.info("Aucun trajet a venir.")
    else:
        prev_date = None
        for _, row in df_f.head(8).iterrows():
            d = row["date_livraison"]
            if pd.notna(d):
                d_str = d.strftime("%A %d/%m/%Y").capitalize()
                if d_str != prev_date:
                    st.markdown(f"**{d_str}**")
                    prev_date = d_str
            st.markdown(card_html(row), unsafe_allow_html=True)

    st.markdown("### \U0001f4ca Repartition par type")
    if "type_trajet" in df.columns:
        counts = df["type_trajet"].value_counts()
        cols = st.columns(max(len(counts), 1))
        for i, (typ, cnt) in enumerate(counts.items()):
            with cols[i]:
                emoji = TYPE_EMOJI.get(typ, "\u26ab")
                st.markdown(f"""<div class="stat-card">
                  <div style='font-size:1.5rem;'>{emoji}</div>
                  <div class="stat-num" style='font-size:1.5rem;'>{cnt}</div>
                  <div class="stat-label">{typ}</div>
                </div>""", unsafe_allow_html=True)

def onglet_ajouter():
    st.markdown("### \u2795 Nouveau trajet")

    with st.form("form_trajet", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            type_trajet = st.selectbox("Type de trajet *", TYPES_TRAJET)
        with c2:
            semaines = get_semaines()
            today = date.today()
            iso   = today.isocalendar()
            sem_def = f"S{iso[1]:02d}-{iso[0]}"
            idx_s = semaines.index(sem_def) if sem_def in semaines else 2
            semaine = st.selectbox("Semaine *", semaines, index=idx_s)

        dates_sem = semaine_to_dates(semaine)
        opts_dates = [d.strftime("%A %d/%m/%Y").capitalize() for d in dates_sem]

        c3, c4 = st.columns(2)
        with c3:
            date_str = st.selectbox("Jour *", opts_dates) if opts_dates else st.text_input("Date")
        with c4:
            camion = st.selectbox("Vehicule *", CAMIONS)

        heures = heures_list()
        idx_8  = heures.index("08:00") if "08:00" in heures else 0
        idx_10 = heures.index("10:00") if "10:00" in heures else 4
        c5, c6 = st.columns(2)
        with c5:
            heure_debut = st.selectbox("Heure debut", heures, index=idx_8)
        with c6:
            heure_fin = st.selectbox("Heure fin", heures, index=idx_10)

        affaire = ouvrage = id_tache = ""
        if type_trajet == "Livraison ouvrage":
            taches_df = load_taches_terminees()
            if not taches_df.empty:
                opts_t = taches_df.apply(
                    lambda r: f"{r.get('affaire','')} - {r.get('ouvrage', r.get('designation',''))}",
                    axis=1
                ).tolist()
                choix = st.selectbox("Ouvrage termine *", opts_t)
                idx_t = opts_t.index(choix)
                rt = taches_df.iloc[idx_t]
                affaire  = str(rt.get("affaire",""))
                ouvrage  = str(rt.get("ouvrage", rt.get("designation","")))
                id_tache = str(rt.get("id", rt.get("id_tache","")))
            else:
                st.warning("Aucun ouvrage marque Termine dans le planning atelier.")
                affaire = st.text_input("Affaire")
                ouvrage = st.text_input("Ouvrage")

        description = st.text_input("Description / Objet du trajet *")
        adresse     = st.text_input("Adresse")

        c7, c8 = st.columns(2)
        with c7:
            contact_nom = st.text_input("Contact sur place")
        with c8:
            contact_tel = st.text_input("Telephone")

        destination = nom_chantier = ""
        if type_trajet in ["Livraison ouvrage", "Livraison autre"]:
            c9, c10 = st.columns(2)
            with c9:
                destination = st.selectbox("Destination", DESTINATIONS)
            with c10:
                if destination == "Chantier":
                    nom_chantier = st.text_input("Nom du chantier")

        commentaire = st.text_area("Commentaire", height=70)
        submitted   = st.form_submit_button("Enregistrer", type="primary",
                                            use_container_width=True)

    if submitted:
        if not description:
            st.error("La description est obligatoire.")
            return
        date_liv = ""
        if dates_sem and date_str:
            try:
                idx_d = opts_dates.index(date_str)
                date_liv = dates_sem[idx_d].strftime("%Y-%m-%d")
            except Exception:
                date_liv = ""
        row = [
            str(uuid.uuid4())[:8], type_trajet, id_tache, affaire, ouvrage,
            destination, nom_chantier, description, adresse,
            contact_nom, contact_tel, date_liv, semaine,
            heure_debut, heure_fin, camion, "Planifie", commentaire
        ]
        try:
            save_trajet(row)
            st.success(f"Trajet enregistre : {description} — {date_str}")
            st.balloons()
        except Exception as e:
            st.error(f"Erreur : {e}")

def onglet_calendrier(df):
    st.markdown("### \U0001f4c5 Calendrier de la semaine")

    semaines = get_semaines()
    today    = date.today()
    iso      = today.isocalendar()
    sem_def  = f"S{iso[1]:02d}-{iso[0]}"
    idx_def  = semaines.index(sem_def) if sem_def in semaines else 2

    col_sel, col_btn = st.columns([4, 1])
    with col_sel:
        semaine = st.selectbox("Semaine", semaines, index=idx_def,
                               label_visibility="collapsed")
    with col_btn:
        if st.button("\U0001f5a8 Imprimer", use_container_width=True):
            st.markdown("<script>window.print()</script>", unsafe_allow_html=True)

    dates_sem = semaine_to_dates(semaine)
    if not dates_sem:
        st.error("Semaine invalide.")
        return

    if df.empty or "semaine" not in df.columns:
        df_sem = pd.DataFrame()
    else:
        df_sem = df[df["semaine"] == semaine].copy()

    nb = len(df_sem)
    d0 = dates_sem[0].strftime("%d/%m/%Y")
    d4 = dates_sem[4].strftime("%d/%m/%Y")
    st.markdown(f"""<div style='background:white;border-radius:10px;
        padding:12px 18px;margin-bottom:16px;border-left:5px solid #1a2340;'>
        <strong>Semaine {semaine}</strong> &nbsp;|&nbsp;
        {d0} au {d4} &nbsp;|&nbsp; <strong>{nb} trajet(s)</strong>
    </div>""", unsafe_allow_html=True)

    # ── Grille 5 colonnes ──────────────────────────────────────────────────────
    cols = st.columns(5)
    for i, (col, d) in enumerate(zip(cols, dates_sem)):
        is_today  = (d == today)
        today_cls = "col-jour-today" if is_today else ""

        if not df_sem.empty and "date_livraison" in df_sem.columns:
            df_jour = df_sem[
                df_sem["date_livraison"].dt.date == d
            ].sort_values("heure_debut")
        else:
            df_jour = pd.DataFrame()

        with col:
            st.markdown(f"""<div class="col-jour {today_cls}">
              <div class="col-jour-header">
                {JOURS_FR[i]}<br>
                <span class="day-num">{d.day}</span>
                <span style='font-size:0.75rem;color:#888;'>{d.strftime("%b").capitalize()}</span>
              </div>
              {"".join(card_html(r) for _, r in df_jour.iterrows())
                if not df_jour.empty
                else "<div class=\"day-vide\">—</div>"}
            </div>""", unsafe_allow_html=True)

    # ── Detail liste ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### \U0001f4cb Detail de la semaine")

    if df_sem.empty:
        st.info("Aucun trajet cette semaine.")
        return

    ws       = get_ws("livraisons")
    all_rows = ws.get_all_records() if ws else []

    for i, d in enumerate(dates_sem):
        if not df_sem.empty and "date_livraison" in df_sem.columns:
            df_jour = df_sem[
                df_sem["date_livraison"].dt.date == d
            ].sort_values("heure_debut")
        else:
            df_jour = pd.DataFrame()

        if df_jour.empty:
            continue

        st.markdown(f"""<div class="bandeau-jour">
            {JOURS_FR[i]} {d.strftime("%d/%m/%Y")} &nbsp;—&nbsp; {len(df_jour)} trajet(s)
        </div>""", unsafe_allow_html=True)

        for _, row in df_jour.iterrows():
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            with c1:
                st.markdown(card_html(row), unsafe_allow_html=True)
            with c2:
                hd = str(row.get("heure_debut",""))
                hf = str(row.get("heure_fin",""))
                if hd:
                    st.markdown(f"**\u23f1 {hd} \u2192 {hf}**")
                st.markdown(f"\U0001f69a {row.get('camion','')}")
            with c3:
                id_t = str(row.get("id_trajet",""))
                stat_actuel = str(row.get("statut","Planifie"))
                new_stat = st.selectbox(
                    "Statut", STATUTS,
                    index=STATUTS.index(stat_actuel) if stat_actuel in STATUTS else 0,
                    key=f"stat_{id_t}",
                    label_visibility="collapsed"
                )
                if new_stat != stat_actuel:
                    for ri, r in enumerate(all_rows):
                        if str(r.get("id_trajet","")) == id_t:
                            do_update_statut(ws, ri, new_stat)
                            st.success("Mis a jour !")
                            st.rerun()
                            break
            with c4:
                if st.button("\U0001f5d1", key=f"del_{id_t}", help="Supprimer"):
                    for ri, r in enumerate(all_rows):
                        if str(r.get("id_trajet","")) == id_t:
                            do_delete_trajet(ws, ri)
                            st.success("Supprime !")
                            st.rerun()
                            break

def main():
    check_auth()
    st.markdown("""<div class="app-header">
        <h1>\U0001f69b Planning Livraisons & Tournees</h1>
        <p>Rollin Metallerie — Gestion des livraisons et tournees</p>
    </div>""", unsafe_allow_html=True)

    init_livraisons()
    df = load_livraisons()

    tab1, tab2, tab3 = st.tabs([
        "\U0001f3e0 Tableau de bord",
        "\u2795 Ajouter un trajet",
        "\U0001f4c5 Calendrier"
    ])
    with tab1:
        onglet_dashboard(df)
    with tab2:
        onglet_ajouter()
    with tab3:
        onglet_calendrier(df)

if __name__ == "__main__":
    main()
