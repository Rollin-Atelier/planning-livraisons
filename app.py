import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, date
import uuid
import streamlit.components.v1 as components

st.set_page_config(page_title="Planning Livraisons", page_icon="\U0001f69b", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.main { background: #f4f6f9; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: white; padding: 8px; border-radius: 10px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; font-weight: 500; }
.stTabs [aria-selected="true"] { background: #1a2340 !important; color: white !important; }
.app-header { background: linear-gradient(135deg, #1c1c1c 0%, #2d2d2d 60%, #3a3a3a 100%); border-left: 5px solid #f97316; color: white; padding: 18px 28px; border-radius: 12px; margin-bottom: 20px; display: flex; align-items: center; gap: 16px; }
.app-header-logo { font-size: 2rem; font-weight: 900; color: #f97316; letter-spacing: -0.04em; line-height: 1; }
.app-header-sub-logo { font-size: 0.6rem; color: #888; letter-spacing: 0.15em; text-transform: uppercase; }
.app-header h1 { margin: 0; font-size: 1.3rem; font-weight: 700; }
.app-header p  { margin: 4px 0 0 0; font-size: 0.82rem; opacity: 0.65; }
.stat-card { background: white; border-radius: 10px; padding: 16px 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
.stat-num { font-size: 2rem; font-weight: 700; color: #1a2340; }
.stat-label { font-size: 0.8rem; color: #888; margin-top: 2px; }
.card { background: white; border-radius: 10px; padding: 12px 14px; margin-bottom: 4px; border-left: 5px solid #ccc; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
.card-livraison { border-left-color: #1a2340; }
.card-enlevement { border-left-color: #7c3aed; }
.card-autre { border-left-color: #ea580c; }
.card-divers { border-left-color: #6b7280; }
.card-titre { font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }
.card-detail { font-size: 0.82rem; color: #555; line-height: 1.7; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; margin-right: 6px; }
.badge-planifie { background: #dbeafe; color: #1d4ed8; }
.badge-livre { background: #dcfce7; color: #16a34a; }
.badge-reporte { background: #fee2e2; color: #dc2626; }
.badge-archive { background: #f3f4f6; color: #6b7280; }
.badge-tl { background: #e0e7ff; color: #1a2340; }
.badge-te { background: #ede9fe; color: #7c3aed; }
.badge-ta { background: #ffedd5; color: #ea580c; }
.badge-td { background: #f3f4f6; color: #6b7280; }
.badge-cam { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; margin-right: 4px; color: white; }
.ouvrage-card { background: white; border-radius: 10px; padding: 12px 16px; margin-bottom: 6px; border-left: 5px solid #16a34a; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
.ouvrage-label { font-weight: 600; font-size: 0.9rem; color: #1a2340; }
.ouvrage-sub { font-size: 0.78rem; color: #888; margin-top: 2px; }
.col-jour { background: white; border-radius: 10px; padding: 10px; min-height: 120px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); margin-bottom: 8px; }
.col-jour-today { border: 2px solid #f97316; }
.col-jour-header { text-align: center; font-weight: 700; font-size: 0.85rem; color: #1a2340; padding: 4px 0 8px 0; border-bottom: 2px solid #e5e7eb; margin-bottom: 8px; }
.day-num { font-size: 1.6rem; font-weight: 700; display: block; }
.day-vide { text-align:center; color:#ccc; font-size:0.8rem; padding:16px 0; }
.bandeau-jour { background: #1c1c1c; border-left: 4px solid #f97316; color: white; padding: 10px 16px; border-radius: 8px; margin: 12px 0 8px 0; font-weight: 600; }
.archive-card { background: #f9fafb; border-radius: 10px; padding: 10px 14px; margin-bottom: 4px; border-left: 5px solid #9ca3af; box-shadow: 0 1px 3px rgba(0,0,0,0.05); opacity: 0.85; }
.legende-cam { display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 16px 0; }
.legende-item { display:flex; align-items:center; gap:6px; font-size:0.8rem; font-weight:600; }
.legende-dot { width:14px; height:14px; border-radius:50%; display:inline-block; }
@media print { header, footer, [data-testid="stToolbar"], [data-testid="stSidebar"], .stTabs, [data-testid="stForm"], button { display: none !important; } }
</style>
""", unsafe_allow_html=True)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
SHEET_URL    = "https://docs.google.com/spreadsheets/d/1KbS5fA33r6o1isdXdT_dWZMDIgtbAG17t0TKa9bdDpw"
MOT_DE_PASSE = "atelier2026"
TYPES_TRAJET  = ["Livraison ouvrage","Enlevement / Collecte","Livraison autre","Trajet divers"]
DESTINATIONS  = ["Peinture","Galvanisation","Chantier","Autre"]
LIEUX_DEPART  = ["Atelier","Peinture","Galvanisation","Chantier","Autre"]
LIEUX_ARRIVEE = ["Atelier","Peinture","Galvanisation","Chantier","Autre"]
CAMIONS       = ["Camion Denjean","Camion poseur","Camion Agenov","Camion autre Semi","Camion Kangoo"]
STATUTS       = ["Planifie","Livre","Reporte"]
JOURS_FR      = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi"]

# Couleurs par camion (dark pour badge/PDF, light pour fond carte)
CAMION_COLORS = {
    "Camion Denjean":    {"dark": "#1a2340", "light": "#e0e7ff", "hex": "#1a2340"},
    "Camion poseur":     {"dark": "#15803d", "light": "#dcfce7", "hex": "#15803d"},
    "Camion Agenov":     {"dark": "#b45309", "light": "#fef3c7", "hex": "#b45309"},
    "Camion autre Semi": {"dark": "#7c3aed", "light": "#ede9fe", "hex": "#7c3aed"},
    "Camion Kangoo":     {"dark": "#dc2626", "light": "#fee2e2", "hex": "#dc2626"},
}
CAMION_DEFAULT = {"dark": "#6b7280", "light": "#f3f4f6", "hex": "#6b7280"}

TYPE_CARD  = {"Livraison ouvrage":"card-livraison","Enlevement / Collecte":"card-enlevement","Livraison autre":"card-autre","Trajet divers":"card-divers"}
TYPE_BADGE = {"Livraison ouvrage":"badge-tl","Enlevement / Collecte":"badge-te","Livraison autre":"badge-ta","Trajet divers":"badge-td"}
TYPE_EMOJI = {"Livraison ouvrage":"\U0001f535","Enlevement / Collecte":"\U0001f7e3","Livraison autre":"\U0001f7e0","Trajet divers":"\u26ab"}
STATUT_BADGE = {"Planifie":"badge-planifie","Livre":"badge-livre","Reporte":"badge-reporte"}
HEADER_LIVRAISONS = ["id_trajet","type_trajet","id_tache","affaire","ouvrage","lieu_depart","lieu_depart_autre","lieu_arrivee","lieu_arrivee_autre","destination","nom_chantier","description","adresse","contact_nom","contact_tel","date_livraison","semaine","heure_debut","heure_fin","camion","statut","commentaire"]

def cam_color(cam, key="dark"):
    return CAMION_COLORS.get(cam, CAMION_DEFAULT)[key]

@st.cache_resource
def get_client():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n","\n")
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_resource
def open_sheet():
    return get_client().open_by_url(SHEET_URL)

def get_ws(name):
    try:    return open_sheet().worksheet(name)
    except gspread.WorksheetNotFound: return None

def init_livraisons():
    if st.session_state.get("livraisons_init_done"):
        return get_ws("livraisons")
    try:
        sh = open_sheet()
        try:    ws = sh.worksheet("livraisons")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("livraisons", rows=1000, cols=25)
        try:
            header = ws.row_values(1)
            if header != HEADER_LIVRAISONS:
                ws.clear(); ws.append_row(HEADER_LIVRAISONS)
        except Exception:
            pass
        st.session_state["livraisons_init_done"] = True
        return ws
    except Exception as e:
        st.warning(f"Connexion Google Sheets en cours... ({e})")
        return None

@st.cache_data(ttl=30)
def load_livraisons():
    ws = get_ws("livraisons")
    if ws is None: return pd.DataFrame()
    data = ws.get_all_records()
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    if "date_livraison" in df.columns:
        df["date_livraison"] = pd.to_datetime(df["date_livraison"], errors="coerce")
    for col in ["heure_debut","lieu_depart","lieu_depart_autre","lieu_arrivee","lieu_arrivee_autre"]:
        if col not in df.columns: df[col] = ""
    return df

def load_taches_terminees():
    ws = get_ws("taches")
    if ws is None: return pd.DataFrame()
    data = ws.get_all_records()
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    df.columns = [c.lower().strip() for c in df.columns]
    col_s = next((c for c in df.columns if "statut" in c), None)
    if col_s is None: return pd.DataFrame()
    return df[df[col_s].str.strip().str.lower() == "termine"].copy()

def save_trajet(row_data):
    ws = get_ws("livraisons") or init_livraisons()
    ws.append_row(row_data)
    load_livraisons.clear()

def do_update_statut(ws, row_idx, new_statut):
    col_idx = HEADER_LIVRAISONS.index("statut") + 1
    ws.update_cell(row_idx + 2, col_idx, new_statut)
    load_livraisons.clear()

def do_update_full(ws, row_idx, new_statut, new_date, new_hd, new_hf, new_cam):
    row_num = row_idx + 2
    for field, val in [("statut",new_statut),("date_livraison",str(new_date) if new_date else ""),("heure_debut",new_hd),("heure_fin",new_hf),("camion",new_cam)]:
        col_idx = HEADER_LIVRAISONS.index(field) + 1
        ws.update_cell(row_num, col_idx, val)
    load_livraisons.clear()

def do_delete_trajet(ws, row_idx):
    ws.delete_rows(row_idx + 2)
    load_livraisons.clear()

def get_semaines(n=12):
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    return [f"S{(monday+timedelta(weeks=i)).isocalendar()[1]:02d}-{(monday+timedelta(weeks=i)).isocalendar()[0]}" for i in range(-2,n)]

def semaine_to_dates(s):
    try:
        parts = s.replace("S","").split("-")
        monday = datetime.strptime(f"{parts[1]}-W{int(parts[0]):02d}-1","%Y-W%W-%w").date()
        return [monday+timedelta(days=i) for i in range(5)]
    except: return []

def heures_list():
    return [f"{hh:02d}:{mm:02d}" for hh in range(5,22) for mm in [0,15,30,45]]

def sem_courante():
    iso = date.today().isocalendar()
    return f"S{iso[1]:02d}-{iso[0]}"

def is_depasse(row):
    try:
        d = pd.to_datetime(row.get("date_livraison"), errors="coerce")
        if pd.isna(d): return False
        hf = str(row.get("heure_fin",""))
        dt_fin = datetime.combine(d.date(), datetime.strptime(hf,"%H:%M").time()) if hf else datetime.combine(d.date(), datetime.strptime("23:59","%H:%M").time())
        return dt_fin < datetime.now() and str(row.get("statut","")) != "Livre"
    except: return False

def cam_badge_html(cam):
    c = cam_color(cam, "dark")
    return f'<span class="badge-cam" style="background:{c};">{cam}</span>'

def card_html(row, archive=False):
    typ=str(row.get("type_trajet","")); desc=str(row.get("description","") or row.get("ouvrage","") or "")
    hd=str(row.get("heure_debut","")); hf=str(row.get("heure_fin",""))
    adr=str(row.get("adresse","")); cnt=str(row.get("contact_nom","")); cam=str(row.get("camion",""))
    stat=str(row.get("statut","Planifie")); affaire=str(row.get("affaire",""))
    l_dep=str(row.get("lieu_depart","")); l_dep_a=str(row.get("lieu_depart_autre",""))
    l_arr=str(row.get("lieu_arrivee","")); l_arr_a=str(row.get("lieu_arrivee_autre",""))
    lieu_dep_label = l_dep_a if l_dep=="Autre" and l_dep_a else l_dep
    lieu_arr_label = l_arr_a if l_arr=="Autre" and l_arr_a else l_arr
    cam_dark  = cam_color(cam, "dark")
    cam_light = cam_color(cam, "light")
    border_style = f"border-left-color:{cam_dark};" if not archive else ""
    cc = "archive-card" if archive else f"card {TYPE_CARD.get(typ,'card-divers')}"
    bc = TYPE_BADGE.get(typ,"badge-td")
    sc = "badge-archive" if archive else STATUT_BADGE.get(stat,"badge-planifie")
    parts=[]
    if lieu_dep_label and lieu_arr_label: parts.append(f"\U0001f4cd {lieu_dep_label} \u2192 {lieu_arr_label}")
    elif lieu_dep_label: parts.append(f"\U0001f4cd Depart : {lieu_dep_label}")
    elif lieu_arr_label: parts.append(f"\U0001f4cd Arrivee : {lieu_arr_label}")
    if affaire and typ=="Livraison ouvrage": parts.append(f"\U0001f3d7\ufe0f {affaire}")
    if hd and hf: parts.append(f"\u23f1 {hd} - {hf}")
    if adr: parts.append(f"\U0001f4cc {adr}")
    if cnt: parts.append(f"\U0001f464 {cnt}")
    cam_html = cam_badge_html(cam) if cam and not archive else (f"\U0001f69a {cam}" if cam else "")
    if cam and not archive:
        parts.append(f"\U0001f69a {cam_badge_html(cam)}")
    elif cam:
        parts.append(f"\U0001f69a {cam}")
    return f'<div class="{cc}" style="{border_style}"><div class="card-titre"><span class="badge {bc}">{typ}</span><span class="badge {sc}">{stat}</span> {desc}</div><div class="card-detail">{"<br>".join(parts)}</div></div>'

def legende_camions_html():
    items = ""
    for cam, cols in CAMION_COLORS.items():
        items += f'<div class="legende-item"><span class="legende-dot" style="background:{cols["dark"]};"></span>{cam}</div>'
    return f'<div class="legende-cam">{items}</div>'

def trajet_avec_menu(row, ws, all_rows, key_prefix=""):
    id_t=str(row.get("id_trajet","")); stat_actuel=str(row.get("statut","Planifie"))
    cam_actuel=str(row.get("camion","Camion Denjean")); heures=heures_list()
    try:
        date_actuelle=pd.to_datetime(row.get("date_livraison"),errors="coerce")
        date_actuelle=date_actuelle.date() if not pd.isna(date_actuelle) else date.today()
    except: date_actuelle=date.today()
    hd_actuel=str(row.get("heure_debut","08:00")); hf_actuel=str(row.get("heure_fin","10:00"))
    idx_hd=heures.index(hd_actuel) if hd_actuel in heures else 0
    idx_hf=heures.index(hf_actuel) if hf_actuel in heures else 4
    idx_cam=CAMIONS.index(cam_actuel) if cam_actuel in CAMIONS else 0
    col_card,col_menu=st.columns([11,1])
    with col_card: st.markdown(card_html(row),unsafe_allow_html=True)
    with col_menu:
        with st.popover("\u22ee"):
            st.markdown("**Modifier**")
            new_stat=st.selectbox("Statut",STATUTS,index=STATUTS.index(stat_actuel) if stat_actuel in STATUTS else 0,key=f"pop_stat_{key_prefix}_{id_t}")
            new_date=st.date_input("Date",value=date_actuelle,key=f"pop_date_{key_prefix}_{id_t}")
            new_hd=st.selectbox("Heure debut",heures,index=idx_hd,key=f"pop_hd_{key_prefix}_{id_t}")
            new_hf=st.selectbox("Heure fin",heures,index=idx_hf,key=f"pop_hf_{key_prefix}_{id_t}")
            new_cam=st.selectbox("Vehicule",CAMIONS,index=idx_cam,key=f"pop_cam_{key_prefix}_{id_t}")
            if st.button("Valider",key=f"pop_ok_{key_prefix}_{id_t}",use_container_width=True,type="primary"):
                if ws:
                    for ri,r in enumerate(all_rows):
                        if str(r.get("id_trajet",""))==id_t:
                            do_update_full(ws,ri,new_stat,new_date,new_hd,new_hf,new_cam)
                            st.success("Mis a jour !"); st.rerun(); break
            st.markdown("---")
            if st.button("\U0001f5d1 Supprimer",key=f"pop_del_{key_prefix}_{id_t}",use_container_width=True):
                if ws:
                    for ri,r in enumerate(all_rows):
                        if str(r.get("id_trajet",""))==id_t:
                            do_delete_trajet(ws,ri); st.success("Supprime !"); st.rerun(); break

def form_planif_rapide(affaire, ouvrage, id_tache, key_suffix=""):
    semaines=get_semaines(); sem_def=sem_courante()
    idx_s=semaines.index(sem_def) if sem_def in semaines else 2
    heures=heures_list(); idx_8=heures.index("08:00") if "08:00" in heures else 0; idx_10=heures.index("10:00") if "10:00" in heures else 4
    with st.form(key=f"form_rapide_{key_suffix}",clear_on_submit=True):
        st.markdown(f"### \U0001f3d7\ufe0f {affaire}"); st.markdown(f"**Ouvrage :** {ouvrage}"); st.markdown("---")
        c1,c2=st.columns(2)
        with c1: semaine=st.selectbox("Semaine",semaines,index=idx_s,key=f"sem_{key_suffix}")
        with c2: camion=st.selectbox("Vehicule",CAMIONS,key=f"cam_{key_suffix}")
        dates_sem=semaine_to_dates(semaine); opts_dates=[d.strftime("%A %d/%m/%Y").capitalize() for d in dates_sem]
        c3,c4=st.columns(2)
        with c3: date_str=st.selectbox("Jour",opts_dates,key=f"day_{key_suffix}")
        with c4: destination=st.selectbox("Destination",DESTINATIONS,key=f"dest_{key_suffix}")
        c5,c6=st.columns(2)
        with c5: heure_debut=st.selectbox("Heure debut",heures,index=idx_8,key=f"hd_{key_suffix}")
        with c6: heure_fin=st.selectbox("Heure fin",heures,index=idx_10,key=f"hf_{key_suffix}")
        cl1,cl2=st.columns(2)
        with cl1:
            lieu_depart=st.selectbox("Lieu de depart",LIEUX_DEPART,key=f"ldep_{key_suffix}")
            lieu_depart_autre=st.text_input("Preciser le depart",key=f"ldep_a_{key_suffix}") if lieu_depart=="Autre" else ""
        with cl2:
            lieu_arrivee=st.selectbox("Lieu d arrivee",LIEUX_ARRIVEE,key=f"larr_{key_suffix}")
            lieu_arrivee_autre=st.text_input("Preciser l arrivee",key=f"larr_a_{key_suffix}") if lieu_arrivee=="Autre" else ""
        nom_chantier=st.text_input("Nom du chantier",key=f"ch_{key_suffix}") if destination=="Chantier" else ""
        adresse=st.text_input("Adresse",key=f"adr_{key_suffix}")
        contact_nom=st.text_input("Contact sur place",key=f"cnt_{key_suffix}")
        contact_tel=st.text_input("Telephone",key=f"tel_{key_suffix}")
        commentaire=st.text_area("Commentaire",height=60,key=f"com_{key_suffix}")
        submitted=st.form_submit_button("Enregistrer la livraison",type="primary",use_container_width=True)
    if submitted:
        date_liv=""
        if dates_sem and date_str:
            try: idx_d=opts_dates.index(date_str); date_liv=dates_sem[idx_d].strftime("%Y-%m-%d")
            except: date_liv=""
        row=[str(uuid.uuid4())[:8],"Livraison ouvrage",id_tache,affaire,ouvrage,lieu_depart,lieu_depart_autre,lieu_arrivee,lieu_arrivee_autre,destination,nom_chantier,f"Livraison {ouvrage}",adresse,contact_nom,contact_tel,date_liv,semaine,heure_debut,heure_fin,camion,"Planifie",commentaire]
        try: save_trajet(row); st.success(f"Livraison planifiee : {ouvrage} le {date_str}"); st.balloons(); st.rerun()
        except Exception as e: st.error(f"Erreur : {e}")

def generate_day_pdf(date_str, trajets):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, KeepTogether)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    import io, datetime as dt2

    FONT_N = "Helvetica"
    FONT_B = "Helvetica-Bold"

    try:    d = dt2.date.fromisoformat(date_str)
    except: d = dt2.date.today()

    JOURS_FR2 = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    MOIS_FR  = {1:"janvier",2:"fevrier",3:"mars",4:"avril",5:"mai",6:"juin",
                7:"juillet",8:"aout",9:"septembre",10:"octobre",11:"novembre",12:"decembre"}
    jour_label = f"{JOURS_FR2[d.weekday()]} {d.day} {MOIS_FR[d.month]} {d.year}"

    ORANGE = colors.HexColor("#f97316")
    LIGHT  = colors.HexColor("#f8fafc")
    BORDER = colors.HexColor("#e2e8f0")
    WHITE  = colors.white

    # Couleurs camions dans PDF
    PDF_CAM_COLORS = {
        "Camion Denjean":    ("#1a2340", "#e0e7ff"),
        "Camion poseur":     ("#15803d", "#dcfce7"),
        "Camion Agenov":     ("#b45309", "#fef3c7"),
        "Camion autre Semi": ("#7c3aed", "#ede9fe"),
        "Camion Kangoo":     ("#dc2626", "#fee2e2"),
    }
    PDF_CAM_DEFAULT = ("#6b7280", "#f3f4f6")

    TYPE_COLORS = {
        "Livraison ouvrage":     colors.HexColor("#1e40af"),
        "Enlevement / Collecte": colors.HexColor("#6d28d9"),
        "Livraison autre":       colors.HexColor("#ea580c"),
        "Trajet divers":         colors.HexColor("#475569"),
    }
    TYPE_LIGHT = {
        "Livraison ouvrage":     colors.HexColor("#dbeafe"),
        "Enlevement / Collecte": colors.HexColor("#ede9fe"),
        "Livraison autre":       colors.HexColor("#ffedd5"),
        "Trajet divers":         colors.HexColor("#f1f5f9"),
    }
    STATUT_COLORS = {
        "Planifie": ("#1d4ed8", "#dbeafe"),
        "Livre":    ("#15803d", "#dcfce7"),
        "Reporte":  ("#dc2626", "#fee2e2"),
    }
    TYPE_LABEL = {
        "Livraison ouvrage":     "LIVRAISON",
        "Enlevement / Collecte": "ENLEVEMENT",
        "Livraison autre":       "LIVRAISON",
        "Trajet divers":         "TRAJET",
    }

    def p(txt, bold=False, size=10, color="#1c1c1c", align=TA_LEFT):
        fn = FONT_B if bold else FONT_N
        return Paragraph(str(txt), ParagraphStyle(
            "_", fontName=fn, fontSize=size,
            textColor=colors.HexColor(color), alignment=align, leading=size*1.4
        ))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.5*cm,  bottomMargin=1.5*cm)
    story = []

    hdr = Table([[
        p("Denjean", bold=True, size=26, color="#f97316"),
        Table([[p("Planning des livraisons", bold=True, size=15)],
               [p(jour_label, bold=True, size=12, color="#f97316")]],
              colWidths=[10*cm]),
        p(f"Imprime le {dt2.date.today().strftime('%d/%m/%Y')}", size=8, color="#9ca3af", align=TA_RIGHT),
    ]], colWidths=[4*cm, 10*cm, 4*cm])
    hdr.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("LINEBELOW",    (0,0),(-1,0),  3, ORANGE),
        ("BOTTOMPADDING",(0,0),(-1,0),  10),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    # Legende camions dans le PDF
    leg_data = [[]]
    for cam_name, (cdark, clight) in PDF_CAM_COLORS.items():
        badge = Table([[p(cam_name, bold=True, size=7, color="#ffffff")]], colWidths=[3.2*cm])
        badge.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor(cdark)),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ]))
        leg_data[0].append(badge)
    leg_table = Table(leg_data, colWidths=[3.4*cm]*5)
    leg_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),2)]))
    story.append(leg_table)
    story.append(Spacer(1, 0.4*cm))

    nb = len(trajets)
    recap = Table([[p(f"{nb} trajet(s) planifie(s)", bold=True, size=10)]], colWidths=[18*cm])
    recap.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), LIGHT),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 12),
        ("LINEBELOW",    (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(recap)
    story.append(Spacer(1, 0.5*cm))

    if not trajets:
        story.append(p("Aucun trajet planifie pour cette journee.", size=12, color="#9ca3af", align=TA_CENTER))
    else:
        for t in trajets:
            typ     = str(t.get("type_trajet","Trajet divers"))
            desc    = str(t.get("description","") or t.get("ouvrage","") or "")
            hd      = str(t.get("heure_debut",""))
            hf      = str(t.get("heure_fin",""))
            cam     = str(t.get("camion",""))
            adr     = str(t.get("adresse",""))
            cnt     = str(t.get("contact_nom",""))
            tel     = str(t.get("contact_tel",""))
            stat    = str(t.get("statut","Planifie"))
            affaire = str(t.get("affaire",""))
            ouvrage = str(t.get("ouvrage",""))
            l_dep   = str(t.get("lieu_depart",""))
            l_dep_a = str(t.get("lieu_depart_autre",""))
            l_arr   = str(t.get("lieu_arrivee",""))
            l_arr_a = str(t.get("lieu_arrivee_autre",""))
            comm    = str(t.get("commentaire",""))
            lieu_dep = l_dep_a if l_dep=="Autre" and l_dep_a else l_dep
            lieu_arr = l_arr_a if l_arr=="Autre" and l_arr_a else l_arr

            # Couleur camion pour ce trajet
            cam_dark_hex, cam_light_hex = PDF_CAM_COLORS.get(cam, PDF_CAM_DEFAULT)
            cam_dark_c  = colors.HexColor(cam_dark_hex)
            cam_light_c = colors.HexColor(cam_light_hex)

            tc  = TYPE_COLORS.get(typ, colors.HexColor("#475569"))
            tlc = TYPE_LIGHT.get(typ, LIGHT)
            sc_hex, slc_hex = STATUT_COLORS.get(stat, ("#1d4ed8","#dbeafe"))
            typ_lbl = TYPE_LABEL.get(typ, "TRAJET")

            badge_typ = Table([[p(typ_lbl, bold=True, size=8, color="#ffffff")]], colWidths=[2.6*cm])
            badge_typ.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),tc),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8)]))

            badge_stat = Table([[p(stat.upper(), bold=True, size=8, color=sc_hex)]], colWidths=[2.4*cm])
            badge_stat.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor(slc_hex)),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8)]))

            # Badge camion colore
            badge_cam = Table([[p(cam, bold=True, size=8, color="#ffffff")]], colWidths=[3.8*cm])
            badge_cam.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),cam_dark_c),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8)]))

            titre_row = Table([[
                p(f"{hd}  ->  {hf}", bold=True, size=15),
                badge_typ, badge_stat, badge_cam,
            ]], colWidths=[4*cm, 2.8*cm, 2.6*cm, 4.1*cm])
            titre_row.setStyle(TableStyle([
                ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
                ("BACKGROUND",   (0,0),(-1,-1), cam_light_c),
                ("TOPPADDING",   (0,0),(-1,-1), 12),
                ("BOTTOMPADDING",(0,0),(-1,-1), 12),
                ("LEFTPADDING",  (0,0),(-1,-1), 14),
                ("RIGHTPADDING", (0,0),(-1,-1), 8),
            ]))

            def field_row(label, value, vsize=10):
                return [p(label, size=8, color="#9ca3af"), p(value, bold=True, size=vsize)]

            body_rows = []
            if desc:    body_rows.append(field_row("OBJET DU TRAJET", desc, 11))
            if affaire or ouvrage:
                val = f"{affaire}  -  {ouvrage}" if affaire and ouvrage else affaire or ouvrage
                body_rows.append(field_row("CHANTIER / OUVRAGE", val))
            if lieu_dep or lieu_arr:
                ts = f"{lieu_dep}  ->  {lieu_arr}" if lieu_dep and lieu_arr else lieu_dep or lieu_arr
                body_rows.append(field_row("TRAJET", ts))
            if adr:     body_rows.append(field_row("ADRESSE", adr))
            if cnt or tel: body_rows.append(field_row("CONTACT", f"{cnt}   {tel}".strip()))
            if comm:    body_rows.append(field_row("NOTE", comm, 9))

            if body_rows:
                body_table = Table(body_rows, colWidths=[4*cm, 12.5*cm])
                body_table.setStyle(TableStyle([
                    ("VALIGN",       (0,0),(-1,-1),"TOP"),
                    ("TOPPADDING",   (0,0),(-1,-1), 6),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
                    ("LEFTPADDING",  (0,0),(-1,-1), 14),
                    ("LINEBELOW",    (0,0),(-1,-2), 0.3, BORDER),
                ]))
                body_wrap = Table([[body_table]], colWidths=[18*cm])
                body_wrap.setStyle(TableStyle([
                    ("BACKGROUND",   (0,0),(-1,-1), WHITE),
                    ("TOPPADDING",   (0,0),(-1,-1), 2),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
                ]))
            else:
                body_wrap = Spacer(1, 0.3*cm)

            card = Table([[titre_row],[body_wrap]], colWidths=[18*cm])
            card.setStyle(TableStyle([
                ("LINEBEFORE", (0,0),(0,-1), 5, cam_dark_c),
                ("LINEABOVE",  (0,0),(-1,0), 0.5, BORDER),
                ("LINEBELOW",  (0,-1),(-1,-1), 0.5, BORDER),
                ("LINEAFTER",  (0,0),(-1,-1), 0.5, BORDER),
            ]))
            story.append(KeepTogether([card]))
            story.append(Spacer(1, 0.5*cm))

    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.15*cm))
    story.append(p(f"Denjean - Artisan du Metal   .   {jour_label}   .   {nb} trajet(s)",
                   size=8, color="#9ca3af", align=TA_CENTER))
    doc.build(story)
    buf.seek(0)
    return buf.read()

def check_auth():
    if "auth" not in st.session_state: st.session_state.auth=False
    if not st.session_state.auth:
        st.markdown("""<div style='max-width:380px;margin:80px auto;background:white;border-radius:14px;padding:40px;box-shadow:0 8px 32px rgba(0,0,0,0.12);text-align:center;'>
          <div style='font-size:0.65rem;letter-spacing:0.18em;text-transform:uppercase;color:#9ca3af;margin-bottom:4px;'>Artisan du Metal</div>
          <div style='font-size:2.4rem;font-weight:900;color:#1c1c1c;letter-spacing:-0.04em;line-height:1;'>Denjean</div>
          <div style='width:40px;height:3px;background:#f97316;margin:10px auto 20px auto;border-radius:2px;'></div>
          <div style='font-size:0.85rem;color:#6b7280;margin-bottom:24px;'>Planning Livraisons</div>
        </div>""",unsafe_allow_html=True)
        col1,col2,col3=st.columns([1,2,1])
        with col2:
            pwd=st.text_input("Mot de passe",type="password",label_visibility="collapsed",placeholder="Mot de passe")
            if st.button("Connexion",use_container_width=True,type="primary"):
                if pwd==MOT_DE_PASSE: st.session_state.auth=True; st.rerun()
                else: st.error("Mot de passe incorrect")
        st.stop()

def onglet_dashboard(df):
    today=date.today(); sem=sem_courante()
    df_sem=df[df["semaine"]==sem] if not df.empty and "semaine" in df.columns else pd.DataFrame()
    if not df.empty:
        df["_depasse"]=df.apply(is_depasse,axis=1)
        df_actifs=df[~df["_depasse"]].copy(); df_archive=df[df["_depasse"]].copy()
    else: df_actifs=df_archive=pd.DataFrame()
    total=len(df_actifs) if not df_actifs.empty else 0
    planifies=int((df_actifs["statut"]=="Planifie").sum()) if not df_actifs.empty and "statut" in df_actifs.columns else 0
    livres=int((df["statut"]=="Livre").sum()) if not df.empty and "statut" in df.columns else 0
    c1,c2,c3,c4=st.columns(4)
    for col,num,label in [(c1,total,"Trajets actifs"),(c2,len(df_sem),"Cette semaine"),(c3,planifies,"Planifies"),(c4,livres,"Livres total")]:
        with col: st.markdown(f'<div class="stat-card"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(legende_camions_html(), unsafe_allow_html=True)
    ws=get_ws("livraisons"); all_rows=ws.get_all_records() if ws else []
    st.markdown("### \U0001f7e2 Ouvrages termines \u2014 prets a expedier")
    taches_df=load_taches_terminees()
    if not taches_df.empty:
        ids_planifies=set(df["id_tache"].astype(str).tolist()) if not df.empty and "id_tache" in df.columns else set()
        col_id=next((c for c in taches_df.columns if c in ["id","id_tache","numero"]),None)
        taches_non_planifiees=[]; taches_planifiees=[]
        for _,t in taches_df.iterrows():
            tid=str(t.get(col_id,"")) if col_id else ""
            (taches_planifiees if tid and tid in ids_planifies else taches_non_planifiees).append(t)
        if not taches_non_planifiees: st.success("Tous les ouvrages termines ont une livraison planifiee \u2713")
        else:
            st.markdown(f"**{len(taches_non_planifiees)} ouvrage(s) en attente :**")
            for t in taches_non_planifiees:
                affaire=str(t.get("affaire","")); ouvrage=str(t.get("ouvrage",t.get("designation","")))
                personne=str(t.get("personne","")); id_tache=str(t.get(col_id,"")) if col_id else ""
                key_suf=f"{affaire}_{ouvrage}_{id_tache}".replace(" ","_")
                col_info,col_btn=st.columns([8,2])
                with col_info:
                    st.markdown(f'<div class="ouvrage-card"><div><div class="ouvrage-sub" style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.05em;color:#f97316;margin-bottom:2px;">\U0001f3d7\ufe0f {affaire}</div><div class="ouvrage-label">\U0001f4e6 {ouvrage}</div><div class="ouvrage-sub">\U0001f477 {personne}</div></div></div>',unsafe_allow_html=True)
                with col_btn:
                    if st.button("Planifier \u2192",key=f"btn_planif_{key_suf}",use_container_width=True,type="primary"):
                        st.session_state[f"open_form_{key_suf}"]=True
                if st.session_state.get(f"open_form_{key_suf}",False):
                    with st.container(): form_planif_rapide(affaire,ouvrage,id_tache,key_suffix=key_suf)
        if taches_planifiees:
            with st.expander(f"\u2713 {len(taches_planifiees)} ouvrage(s) deja planifie(s)"):
                for t in taches_planifiees: st.markdown(f"- \U0001f535 **{t.get('ouvrage',t.get('designation',''))}** \u2014 {t.get('affaire','')}")
    else: st.info("Aucun ouvrage marque Termine dans le planning atelier.")
    st.markdown("---"); st.markdown("### \U0001f4c5 Prochains trajets")
    if df_actifs.empty: st.info("Aucun trajet actif pour le moment.")
    else:
        df_f=df_actifs[df_actifs["date_livraison"].notna()&(df_actifs["date_livraison"].dt.date>=today)&(df_actifs["statut"]!="Livre")].sort_values("date_livraison") if "date_livraison" in df_actifs.columns else pd.DataFrame()
        if df_f.empty: st.info("Aucun trajet a venir.")
        else:
            prev_date=None
            for _,row in df_f.head(10).iterrows():
                d=row["date_livraison"]
                if pd.notna(d):
                    d_str=d.strftime("%A %d/%m/%Y").capitalize()
                    if d_str!=prev_date: st.markdown(f"**{d_str}**"); prev_date=d_str
                trajet_avec_menu(row,ws,all_rows,key_prefix="dash")
    st.markdown("---"); st.markdown("### \U0001f4ca Repartition par type")
    if not df.empty and "type_trajet" in df.columns:
        counts=df["type_trajet"].value_counts(); cols=st.columns(max(len(counts),1))
        for i,(typ,cnt) in enumerate(counts.items()):
            with cols[i]: st.markdown(f'<div class="stat-card"><div style="font-size:1.5rem;">{TYPE_EMOJI.get(typ,"\u26ab")}</div><div class="stat-num" style="font-size:1.5rem;">{cnt}</div><div class="stat-label">{typ}</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    with st.expander(f"\U0001f4c2 Archives ({len(df_archive) if not df_archive.empty else 0})"):
        if df_archive.empty: st.info("Aucun trajet archive.")
        else:
            prev_date=None
            for _,row in df_archive.sort_values("date_livraison",ascending=False).iterrows():
                d=row.get("date_livraison")
                if pd.notna(d):
                    d_str=pd.to_datetime(d).strftime("%A %d/%m/%Y").capitalize()
                    if d_str!=prev_date: st.markdown(f"**{d_str}**"); prev_date=d_str
                col_card,col_menu=st.columns([11,1])
                with col_card: st.markdown(card_html(row,archive=True),unsafe_allow_html=True)
                with col_menu:
                    id_t=str(row.get("id_trajet",""))
                    with st.popover("\u22ee"):
                        if st.button("Marquer Livre",key=f"arch_livre_{id_t}",use_container_width=True,type="primary"):
                            if ws:
                                for ri,r in enumerate(all_rows):
                                    if str(r.get("id_trajet",""))==id_t: do_update_statut(ws,ri,"Livre"); st.success("Mis a jour !"); st.rerun(); break
                        if st.button("\U0001f5d1 Supprimer",key=f"arch_del_{id_t}",use_container_width=True):
                            if ws:
                                for ri,r in enumerate(all_rows):
                                    if str(r.get("id_trajet",""))==id_t: do_delete_trajet(ws,ri); st.success("Supprime !"); st.rerun(); break

def onglet_ajouter():
    st.markdown("### \u2795 Nouveau trajet")
    semaines=get_semaines(); sem_def=sem_courante(); idx_s=semaines.index(sem_def) if sem_def in semaines else 2
    heures=heures_list(); idx_8=heures.index("08:00") if "08:00" in heures else 0; idx_10=heures.index("10:00") if "10:00" in heures else 4
    c1,c2=st.columns(2)
    with c1: type_trajet_pre=st.selectbox("Type de trajet *",TYPES_TRAJET,key="type_trajet_sel")
    with c2: semaine=st.selectbox("Semaine *",semaines,index=idx_s,key="semaine_sel")
    affaire=ouvrage=id_tache=""
    source_mode="Saisie manuelle"
    if type_trajet_pre=="Livraison ouvrage":
        source_mode=st.radio("Source de l ouvrage",["Depuis le planning atelier","Saisie manuelle"],horizontal=True,key="source_mode_radio")
        if source_mode=="Depuis le planning atelier":
            taches_df=load_taches_terminees()
            if not taches_df.empty:
                opts_t=taches_df.apply(lambda r:f"{r.get('affaire','')} - {r.get('ouvrage',r.get('designation',''))}",axis=1).tolist()
                choix=st.selectbox("Ouvrage termine *",opts_t,key="ouvrage_termine_sel")
                rt=taches_df.iloc[opts_t.index(choix)]
                affaire=str(rt.get("affaire","")); ouvrage=str(rt.get("ouvrage",rt.get("designation",""))); id_tache=str(rt.get("id",rt.get("id_tache","")))
            else: st.warning("Aucun ouvrage marque Termine dans le planning atelier.")
    with st.form("form_trajet",clear_on_submit=True):
        dates_sem=semaine_to_dates(semaine); opts_dates=[d.strftime("%A %d/%m/%Y").capitalize() for d in dates_sem]
        c3,c4=st.columns(2)
        with c3: date_str=st.selectbox("Jour *",opts_dates) if opts_dates else st.text_input("Date")
        with c4: camion=st.selectbox("Vehicule *",CAMIONS)
        c5,c6=st.columns(2)
        with c5: heure_debut=st.selectbox("Heure debut",heures,index=idx_8)
        with c6: heure_fin=st.selectbox("Heure fin",heures,index=idx_10)
        cl1,cl2=st.columns(2)
        with cl1:
            lieu_depart=st.selectbox("Lieu de depart *",LIEUX_DEPART)
            lieu_depart_autre=st.text_input("Preciser le lieu de depart") if lieu_depart=="Autre" else ""
        with cl2:
            lieu_arrivee=st.selectbox("Lieu d arrivee *",LIEUX_ARRIVEE)
            lieu_arrivee_autre=st.text_input("Preciser le lieu d arrivee") if lieu_arrivee=="Autre" else ""
        if type_trajet_pre=="Livraison ouvrage" and source_mode=="Saisie manuelle":
            cm1,cm2=st.columns(2)
            with cm1: affaire=st.text_input("Chantier / Affaire")
            with cm2: ouvrage=st.text_input("Ouvrage")
        description=st.text_input("Description / Objet du trajet *"); adresse=st.text_input("Adresse")
        c7,c8=st.columns(2)
        with c7: contact_nom=st.text_input("Contact sur place")
        with c8: contact_tel=st.text_input("Telephone")
        destination=nom_chantier=""
        if type_trajet_pre in ["Livraison ouvrage","Livraison autre"]:
            c9,c10=st.columns(2)
            with c9: destination=st.selectbox("Destination",DESTINATIONS)
            with c10:
                if destination=="Chantier": nom_chantier=st.text_input("Nom du chantier")
        commentaire=st.text_area("Commentaire",height=70)
        submitted=st.form_submit_button("Enregistrer",type="primary",use_container_width=True)
    if submitted:
        if not description: st.error("La description est obligatoire."); return
        date_liv=""
        if dates_sem and date_str:
            try: idx_d=opts_dates.index(date_str); date_liv=dates_sem[idx_d].strftime("%Y-%m-%d")
            except: date_liv=""
        row=[str(uuid.uuid4())[:8],type_trajet_pre,id_tache,affaire,ouvrage,lieu_depart,lieu_depart_autre,lieu_arrivee,lieu_arrivee_autre,destination,nom_chantier,description,adresse,contact_nom,contact_tel,date_liv,semaine,heure_debut,heure_fin,camion,"Planifie",commentaire]
        try:
            save_trajet(row)
            st.success(f"Trajet enregistre : {description}")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

def onglet_calendrier(df):
    st.markdown("### \U0001f4c5 Calendrier de la semaine")
    semaines=get_semaines(); sem_def=sem_courante(); idx_def=semaines.index(sem_def) if sem_def in semaines else 2
    col_sel,_=st.columns([4,1])
    with col_sel: semaine=st.selectbox("Semaine",semaines,index=idx_def,label_visibility="collapsed")
    dates_sem=semaine_to_dates(semaine)
    if not dates_sem: st.error("Semaine invalide."); return
    today=date.today()
    df_sem=df[df["semaine"]==semaine].copy() if not df.empty and "semaine" in df.columns else pd.DataFrame()
    nb=len(df_sem); d0=dates_sem[0].strftime("%d/%m/%Y"); d4=dates_sem[4].strftime("%d/%m/%Y")
    st.markdown(f'<div style="background:white;border-radius:10px;padding:12px 18px;margin-bottom:8px;border-left:5px solid #f97316;"><strong>Semaine {semaine}</strong> &nbsp;|&nbsp; {d0} au {d4} &nbsp;|&nbsp; <strong>{nb} trajet(s)</strong></div>',unsafe_allow_html=True)
    st.markdown(legende_camions_html(), unsafe_allow_html=True)
    cols=st.columns(5)
    for i,(col,d) in enumerate(zip(cols,dates_sem)):
        today_cls="col-jour-today" if d==today else ""
        df_jour=df_sem[df_sem["date_livraison"].dt.date==d].sort_values("heure_debut") if not df_sem.empty and "date_livraison" in df_sem.columns else pd.DataFrame()
        with col:
            cards="".join(card_html(r) for _,r in df_jour.iterrows()) if not df_jour.empty else '<div class="day-vide">\u2014</div>'
            st.markdown(f'<div class="col-jour {today_cls}"><div class="col-jour-header">{JOURS_FR[i]}<br><span class="day-num">{d.day}</span><span style="font-size:0.75rem;color:#888;">{d.strftime("%b").capitalize()}</span></div>{cards}</div>',unsafe_allow_html=True)
            if not df_jour.empty:
                pdf_key = f"pdf_bytes_{d}"
                if st.button("\U0001f5a8\ufe0f PDF", key=f"pdf_btn_{d}", use_container_width=True,
                             help=f"Generer le PDF du {JOURS_FR[i]} {d.strftime('%d/%m/%Y')}"):
                    st.session_state[pdf_key] = generate_day_pdf(str(d), df_jour.to_dict("records"))
                if st.session_state.get(pdf_key):
                    st.download_button(
                        label="\u2b07\ufe0f Telecharger",
                        data=st.session_state[pdf_key],
                        file_name=f"livraisons_{JOURS_FR[i].lower()}_{d.strftime('%d-%m-%Y')}.pdf",
                        mime="application/pdf",
                        key=f"pdf_dl_{d}",
                        use_container_width=True,
                    )
    st.markdown("---"); st.markdown("### \U0001f4cb Detail de la semaine")
    if df_sem.empty: st.info("Aucun trajet cette semaine."); return
    ws=get_ws("livraisons"); all_rows=ws.get_all_records() if ws else []
    for i,d in enumerate(dates_sem):
        df_jour=df_sem[df_sem["date_livraison"].dt.date==d].sort_values("heure_debut") if not df_sem.empty and "date_livraison" in df_sem.columns else pd.DataFrame()
        if df_jour.empty: continue
        st.markdown(f'<div class="bandeau-jour">{JOURS_FR[i]} {d.strftime("%d/%m/%Y")} &nbsp;\u2014&nbsp; {len(df_jour)} trajet(s)</div>',unsafe_allow_html=True)
        for _,row in df_jour.iterrows(): trajet_avec_menu(row,ws,all_rows,key_prefix=f"cal_{i}")

def main():
    check_auth()
    st.markdown('<div class="app-header"><div><div class="app-header-logo">Denjean</div><div class="app-header-sub-logo">Artisan du Metal</div></div><div style="width:2px;height:40px;background:#444;border-radius:1px;"></div><div><h1>\U0001f69b Planning Livraisons &amp; Tournees</h1><p>Gestion des livraisons et tournees</p></div></div>',unsafe_allow_html=True)
    init_livraisons(); df=load_livraisons()
    tab1,tab2,tab3=st.tabs(["\U0001f3e0 Tableau de bord","\u2795 Ajouter un trajet","\U0001f4c5 Calendrier"])
    with tab1: onglet_dashboard(df)
    with tab2: onglet_ajouter()
    with tab3: onglet_calendrier(df)

if __name__ == "__main__":
    main()
