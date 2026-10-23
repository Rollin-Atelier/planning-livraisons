
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, timedelta, datetime

# ── Configuration ──────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KbS5fA33r6o1isdXdT_dWZMDIgtbAG17t0TKa9bdDpw"
APP_PASSWORD = "atelier2026"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TYPES_TRAJET = [
    "Livraison ouvrage",
    "Enlevement / Collecte",
    "Livraison autre",
    "Trajet divers",
]

DESTINATIONS_OUVRAGE = ["Peinture", "Galvanisation", "Chantier"]

CAMIONS = ["Camion 1", "Camion 2", "Camion 3", "Vehicule leger"]

COLORS = {
    "Livraison ouvrage":    "#0f3460",
    "Enlevement / Collecte": "#8E44AD",
    "Livraison autre":      "#E67E22",
    "Trajet divers":        "#7F8C8D",
}

STATUTS = ["Planifie", "Livre", "Reporte"]

HEURES = [f"{h:02d}:{m:02d}" for h in range(5, 22) for m in (0, 15, 30, 45)]

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
        ws = sh.add_worksheet(title=tab_name, rows=500, cols=25)
        ws.append_row([
            "id_trajet", "type_trajet", "id_tache", "affaire", "ouvrage",
            "destination", "nom_chantier", "description",
            "adresse", "contact_nom", "contact_tel",
            "date_livraison", "semaine", "heure_debut", "heure_fin",
            "camion", "statut", "commentaire",
        ])
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

# ── Lecture / ecriture des trajets ────────────────────────────
@st.cache_data(ttl=30)
def load_trajets(_client):
    ws = get_sheet(_client, "livraisons")
    data = ws.get_all_records()
    cols = ["id_trajet", "type_trajet", "id_tache", "affaire", "ouvrage",
            "destination", "nom_chantier", "description",
            "adresse", "contact_nom", "contact_tel",
            "date_livraison", "semaine", "heure_debut", "heure_fin",
            "camion", "statut", "commentaire"]
    if not data:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(data)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def save_trajet(client, row_dict):
    ws = get_sheet(client, "livraisons")
    ws.append_row([
        row_dict.get("id_trajet", ""),
        row_dict.get("type_trajet", ""),
        row_dict.get("id_tache", ""),
        row_dict.get("affaire", ""),
        row_dict.get("ouvrage", ""),
        row_dict.get("destination", ""),
        row_dict.get("nom_chantier", ""),
        row_dict.get("description", ""),
        row_dict.get("adresse", ""),
        row_dict.get("contact_nom", ""),
        row_dict.get("contact_tel", ""),
        row_dict.get("date_livraison", ""),
        row_dict.get("semaine", ""),
        row_dict.get("heure_debut", ""),
        row_dict.get("heure_fin", ""),
        row_dict.get("camion", ""),
        row_dict.get("statut", "Planifie"),
        row_dict.get("commentaire", ""),
    ])
    st.cache_data.clear()

def update_trajet_statut(client, id_trajet, new_statut):
    ws = get_sheet(client, "livraisons")
    data = ws.get_all_records()
    for i, row in enumerate(data):
        if str(row.get("id_trajet", "")) == str(id_trajet):
            ws.update_cell(i + 2, 17, new_statut)
            break
    st.cache_data.clear()

def delete_trajet(client, id_trajet):
    ws = get_sheet(client, "livraisons")
    data = ws.get_all_records()
    for i, row in enumerate(data):
        if str(row.get("id_trajet", "")) == str(id_trajet):
            ws.delete_rows(i + 2)
            break
    st.cache_data.clear()

def gen_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

# ── Utilitaires semaine / date ─────────────────────────────────
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

def jours_semaine(semaine_label: str):
    lundi, _ = semaine_to_dates(semaine_label)
    if not lundi:
        return []
    jours = []
    noms = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    for i, nom in enumerate(noms):
        d = lundi + timedelta(days=i)
        jours.append((nom, d))
    return jours

def heure_to_min(h: str) -> int:
    try:
        parts = h.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

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
        padding: 0.9rem 1.2rem;
        margin: 0.4rem 0;
        border-left: 5px solid #4A90D9;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
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
    .jour-header {
        background: #1a1a2e;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 1.2rem 0 0.5rem;
        font-weight: 700;
        font-size: 1rem;
    }
    .semaine-header {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 1rem 0 0.5rem;
        font-weight: 700;
        color: #1a1a2e;
        border-left: 4px solid #0f3460;
    }
    .heure-badge {
        background: #f0f4f8;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-right: 6px;
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
        <p>Planning de livraison et tournees</p>
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

# ── Composant carte trajet ─────────────────────────────────────
def render_card(row):
    type_t = row.get("type_trajet", "")
    color = COLORS.get(type_t, "#888")
    statut = row.get("statut", "Planifie")
    badge_class = f"badge-{statut.lower()}" if statut.lower() in ("planifie", "livre", "reporte") else "badge-planifie"

    titre = row.get("description") or row.get("ouvrage") or type_t
    sous_titre = row.get("affaire", "")

    heure_debut = row.get("heure_debut", "")
    heure_fin   = row.get("heure_fin", "")
    plage = f"{heure_debut} - {heure_fin}" if heure_debut and heure_fin else (heure_debut or "")

    adresse = row.get("adresse", "")
    contact_nom = row.get("contact_nom", "")
    contact_tel = row.get("contact_tel", "")
    commentaire = row.get("commentaire", "")
    destination = row.get("destination", "")
    nom_chantier = row.get("nom_chantier", "")

    dest_label = ""
    if destination:
        dest_label = destination
        if destination == "Chantier" and nom_chantier:
            dest_label = f"Chantier : {nom_chantier}"

    lines = []
    if plage:
        lines.append(f"<span class='heure-badge'>⏱ {plage}</span>")
    if dest_label:
        lines.append(f"<span style='color:{color};font-weight:600'>{dest_label}</span>")
    lines.append(f"<span class='badge {badge_class}'>{statut}</span>")

    detail_lines = []
    if adresse:
        detail_lines.append(f"📍 {adresse}")
    if contact_nom or contact_tel:
        contact_str = " ".join(filter(None, [contact_nom, contact_tel]))
        detail_lines.append(f"👤 {contact_str}")
    if commentaire:
        detail_lines.append(f"💬 {commentaire}")

    detail_html = ""
    if detail_lines:
        detail_html = "<br>" + "<br>".join(
            [f"<span style='font-size:0.85rem;color:#555'>{l}</span>" for l in detail_lines]
        )

    type_badge = f"<span style='background:{color};color:white;border-radius:4px;padding:1px 7px;font-size:0.75rem;font-weight:600;margin-right:6px'>{type_t}</span>"

    st.markdown(f"""
    <div class="card" style="border-left-color:{color}">
        {type_badge}
        <strong>{titre}</strong>
        {f"&nbsp;<span style='color:#666;font-size:0.9rem'>{sous_titre}</span>" if sous_titre else ""}
        <br>
        {"&nbsp;&nbsp;".join(lines)}
        {detail_html}
    </div>
    """, unsafe_allow_html=True)

# ── Page : Ajouter un trajet ───────────────────────────────────
def page_ajouter(client):
    st.subheader("Ajouter un trajet")

    type_trajet = st.selectbox("Type de trajet", TYPES_TRAJET)

    with st.form("form_trajet"):

        # -- Champs specifiques selon le type
        id_tache   = ""
        affaire    = ""
        ouvrage    = ""
        destination = ""
        nom_chantier = ""
        description  = ""

        if type_trajet == "Livraison ouvrage":
            taches = load_taches_terminees(client)
            trajets = load_trajets(client)
            ids_planifies = set(trajets[trajets["type_trajet"] == "Livraison ouvrage"]["id_tache"].astype(str).tolist()) if not trajets.empty else set()
            taches_dispo = taches[~taches["id"].astype(str).isin(ids_planifies)].copy()

            if taches_dispo.empty:
                st.info("Aucun ouvrage termine en attente de planification.")
                st.form_submit_button("Ajouter", disabled=True)
                return

            options = [
                f"{r['affaire']} -- {r['ouvrage']} (id: {r['id']})"
                for _, r in taches_dispo.iterrows()
            ]
            choix = st.selectbox("Ouvrage a livrer", options)
            idx = options.index(choix)
            tache_sel = taches_dispo.iloc[idx]
            id_tache  = str(tache_sel["id"])
            affaire   = str(tache_sel["affaire"])
            ouvrage   = str(tache_sel["ouvrage"])

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                destination = st.selectbox("Destination", DESTINATIONS_OUVRAGE)
            with col_d2:
                nom_chantier = st.text_input("Nom du chantier (si Chantier)")

        else:
            description = st.text_input("Description du trajet *", placeholder="Ex: Recuperer profiles chez fournisseur X")

        st.markdown("---")
        st.markdown("**Quand ?**")
        col1, col2, col3 = st.columns(3)
        with col1:
            date_liv = st.date_input("Date", value=date.today())
        with col2:
            heure_debut = st.selectbox("Heure de depart", HEURES,
                                       index=HEURES.index("08:00") if "08:00" in HEURES else 0)
        with col3:
            heure_fin = st.selectbox("Heure de fin", HEURES,
                                     index=HEURES.index("10:00") if "10:00" in HEURES else 4)

        st.markdown("**Vehicule**")
        camion = st.selectbox("Camion / Vehicule", CAMIONS)

        st.markdown("**Lieu**")
        adresse = st.text_input("Adresse", placeholder="Ex: 12 rue de la Paix, 75001 Paris")

        st.markdown("**Contact sur place**")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            contact_nom = st.text_input("Nom du contact")
        with col_c2:
            contact_tel = st.text_input("Telephone")

        commentaire = st.text_area("Commentaire (optionnel)", height=70)

        submitted = st.form_submit_button("Ajouter le trajet", type="primary")
        if submitted:
            if type_trajet != "Livraison ouvrage" and not description.strip():
                st.error("Veuillez saisir une description.")
            elif heure_to_min(heure_fin) <= heure_to_min(heure_debut):
                st.error("L'heure de fin doit etre apres l'heure de depart.")
            else:
                semaine = get_semaine_label(date_liv)
                save_trajet(client, {
                    "id_trajet":      gen_id(),
                    "type_trajet":    type_trajet,
                    "id_tache":       id_tache,
                    "affaire":        affaire,
                    "ouvrage":        ouvrage,
                    "destination":    destination,
                    "nom_chantier":   nom_chantier.strip(),
                    "description":    description.strip(),
                    "adresse":        adresse.strip(),
                    "contact_nom":    contact_nom.strip(),
                    "contact_tel":    contact_tel.strip(),
                    "date_livraison": str(date_liv),
                    "semaine":        semaine,
                    "heure_debut":    heure_debut,
                    "heure_fin":      heure_fin,
                    "camion":         camion,
                    "statut":         "Planifie",
                    "commentaire":    commentaire.strip(),
                })
                label = description.strip() if description.strip() else ouvrage
                st.success(f"Trajet ajoute : {label} le {date_liv.strftime('%d/%m/%Y')} ({heure_debut} - {heure_fin})")

# ── Page : Planning par semaine ────────────────────────────────
def page_planning(client):
    st.subheader("Planning par semaine")
    trajets = load_trajets(client)

    if trajets.empty:
        st.info("Aucun trajet planifie pour l'instant.")
        return

    semaines_dispo = sorted(trajets["semaine"].unique().tolist())
    semaine_sel = st.selectbox("Semaine", semaines_dispo)

    df_sem = trajets[trajets["semaine"] == semaine_sel].copy()
    lundi, vendredi = semaine_to_dates(semaine_sel)
    if lundi:
        st.markdown(f"""
        <div class="semaine-header">
            Semaine {semaine_sel} &nbsp;|&nbsp;
            {lundi.strftime('%d/%m/%Y')} au {vendredi.strftime('%d/%m/%Y')}
            &nbsp;|&nbsp; {len(df_sem)} trajet(s)
        </div>
        """, unsafe_allow_html=True)

    # Vue par jour
    jours = jours_semaine(semaine_sel)
    for nom_jour, d in jours:
        d_str = str(d)
        df_jour = df_sem[df_sem["date_livraison"] == d_str].copy()
        if df_jour.empty:
            continue

        # Trier par heure de debut
        df_jour["_min"] = df_jour["heure_debut"].apply(heure_to_min)
        df_jour = df_jour.sort_values("_min")

        st.markdown(f"""
        <div class="jour-header">
            {nom_jour} {d.strftime('%d/%m/%Y')} &nbsp;—&nbsp; {len(df_jour)} trajet(s)
        </div>
        """, unsafe_allow_html=True)

        for _, row in df_jour.iterrows():
            render_card(row)

    # Mise a jour statuts
    st.markdown("---")
    with st.expander("Mettre a jour les statuts / supprimer"):
        for _, row in df_sem.iterrows():
            col_a, col_b, col_c = st.columns([4, 2, 1])
            label = row.get("description") or row.get("ouvrage") or row.get("type_trajet", "")
            with col_a:
                st.write(f"{row.get('date_livraison','')} | {row.get('heure_debut','')} | {label}")
            with col_b:
                statut_actuel = row.get("statut", "Planifie")
                if statut_actuel not in STATUTS:
                    statut_actuel = "Planifie"
                new_statut = st.selectbox(
                    "Statut",
                    STATUTS,
                    index=STATUTS.index(statut_actuel),
                    key=f"st_{row.get('id_trajet','')}",
                )
                if st.button("OK", key=f"ok_{row.get('id_trajet','')}"):
                    update_trajet_statut(client, row.get("id_trajet", ""), new_statut)
                    st.success("Mis a jour !")
                    st.rerun()
            with col_c:
                if st.button("🗑", key=f"del_{row.get('id_trajet','')}"):
                    delete_trajet(client, row.get("id_trajet", ""))
                    st.success("Supprime !")
                    st.rerun()

# ── Page : Tableau de bord ─────────────────────────────────────
def page_dashboard(client):
    st.subheader("Tableau de bord")
    trajets = load_trajets(client)
    taches  = load_taches_terminees(client)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ouvrages termines", len(taches))
    with col2:
        n_planif = len(trajets[trajets["statut"] == "Planifie"]) if not trajets.empty else 0
        st.metric("Trajets planifies", n_planif)
    with col3:
        n_livre = len(trajets[trajets["statut"] == "Livre"]) if not trajets.empty else 0
        st.metric("Trajets effectues", n_livre)
    with col4:
        n_att = len(taches) - len(trajets[trajets["type_trajet"] == "Livraison ouvrage"]) if not trajets.empty else len(taches)
        st.metric("Ouvrages en attente", max(n_att, 0))

    if not trajets.empty:
        st.markdown("---")
        st.markdown("**Repartition par type de trajet**")
        type_counts = trajets["type_trajet"].value_counts()
        cols = st.columns(len(TYPES_TRAJET))
        for col, t in zip(cols, TYPES_TRAJET):
            with col:
                count = int(type_counts.get(t, 0))
                color = COLORS.get(t, "#888")
                st.markdown(f"""
                <div style="background:{color};color:white;border-radius:10px;
                            padding:1rem;text-align:center;">
                    <div style="font-size:1.8rem;font-weight:700">{count}</div>
                    <div style="font-size:0.8rem">{t}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Prochains trajets**")
        today_str = str(date.today())
        df_next = trajets[
            (trajets["date_livraison"] >= today_str) &
            (trajets["statut"] == "Planifie")
        ].copy()
        df_next["_min"] = df_next["heure_debut"].apply(heure_to_min)
        df_next = df_next.sort_values(["date_livraison", "_min"]).head(5)
        for _, row in df_next.iterrows():
            render_card(row)

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
        <p>Planning de livraison et tournees</p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Tableau de bord", "Ajouter un trajet", "Planning par semaine"])
    with tabs[0]:
        page_dashboard(client)
    with tabs[1]:
        page_ajouter(client)
    with tabs[2]:
        page_planning(client)

if __name__ == "__main__":
    main()
