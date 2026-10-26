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
CAMIONS       = ["Camion 1","Camion 2","Camion 3","Vehicule leger"]
STATUTS       = ["Planifie","Livre","Reporte"]
JOURS_FR      = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi"]
TYPE_CARD  = {"Livraison ouvrage":"card-livraison","Enlevement / Collecte":"card-enlevement","Livraison autre":"card-autre","Trajet divers":"card-divers"}
TYPE_BADGE = {"Livraison ouvrage":"badge-tl","Enlevement / Collecte":"badge-te","Livraison autre":"badge-ta","Trajet divers":"badge-td"}
TYPE_EMOJI = {"Livraison ouvrage":"\U0001f535","Enlevement / Collecte":"\U0001f7e3","Livraison autre":"\U0001f7e0","Trajet divers":"\u26ab"}
STATUT_BADGE = {"Planifie":"badge-planifie","Livre":"badge-livre","Reporte":"badge-reporte"}
HEADER_LIVRAISONS = ["id_trajet","type_trajet","id_tache","affaire","ouvrage","lieu_depart","lieu_depart_autre","lieu_arrivee","lieu_arrivee_autre","destination","nom_chantier","description","adresse","contact_nom","contact_tel","date_livraison","semaine","heure_debut","heure_fin","camion","statut","commentaire"]

@st.cache_resource
def get_client():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n","\n")
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

def open_sheet():
    return get_client().open_by_url(SHEET_URL)

def get_ws(name):
    try:    return open_sheet().worksheet(name)
    except gspread.WorksheetNotFound: return None

def init_livraisons():
    if st.session_state.get("livraisons_init_done"):
        return get_ws("livraisons")
    sh = open_sheet()
    try:
        ws = sh.worksheet("livraisons")
        # Verifier le header seulement si la feuille semble vide
        try:
            first_row = ws.row_values(1)
            if first_row and first_row[0] == "id_trajet":
                pass  # Header deja present, on ne touche a rien
            elif not first_row:
                ws.append_row(HEADER_LIVRAISONS)
            else:
                ws.clear(); ws.append_row(HEADER_LIVRAISONS)
        except Exception:
            pass  # En cas d erreur API on continue quand meme
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet("livraisons", rows=1000, cols=25)
        ws.append_row(HEADER_LIVRAISONS)
    st.session_state["livraisons_init_done"] = True
    return ws

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

def do_update_statut(ws, row_idx, new_statut):
    col_idx = HEADER_LIVRAISONS.index("statut") + 1
    ws.update_cell(row_idx + 2, col_idx, new_statut)

def do_update_full(ws, row_idx, new_statut, new_date, new_hd, new_hf, new_cam):
    row_num = row_idx + 2
    for field, val in [("statut",new_statut),("date_livraison",str(new_date) if new_date else ""),("heure_debut",new_hd),("heure_fin",new_hf),("camion",new_cam)]:
        col_idx = HEADER_LIVRAISONS.index(field) + 1
        ws.update_cell(row_num, col_idx, val)

def do_delete_trajet(ws, row_idx):
    ws.delete_rows(row_idx + 2)

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

def card_html(row, archive=False):
    typ=str(row.get("type_trajet","")); desc=str(row.get("description","") or row.get("ouvrage","") or "")
    hd=str(row.get("heure_debut","")); hf=str(row.get("heure_fin",""))
    adr=str(row.get("adresse","")); cnt=str(row.get("contact_nom","")); cam=str(row.get("camion",""))
    stat=str(row.get("statut","Planifie")); affaire=str(row.get("affaire",""))
    l_dep=str(row.get("lieu_depart","")); l_dep_a=str(row.get("lieu_depart_autre",""))
    l_arr=str(row.get("lieu_arrivee","")); l_arr_a=str(row.get("lieu_arrivee_autre",""))
    lieu_dep_label = l_dep_a if l_dep=="Autre" and l_dep_a else l_dep
    lieu_arr_label = l_arr_a if l_arr=="Autre" and l_arr_a else l_arr
    cc="archive-card" if archive else TYPE_CARD.get(typ,"card-divers")
    bc=TYPE_BADGE.get(typ,"badge-td"); sc="badge-archive" if archive else STATUT_BADGE.get(stat,"badge-planifie")
    parts=[]
    if lieu_dep_label and lieu_arr_label: parts.append(f"\U0001f4cd {lieu_dep_label} \u2192 {lieu_arr_label}")
    elif lieu_dep_label: parts.append(f"\U0001f4cd Depart : {lieu_dep_label}")
    elif lieu_arr_label: parts.append(f"\U0001f4cd Arrivee : {lieu_arr_label}")
    if affaire and typ=="Livraison ouvrage": parts.append(f"\U0001f3d7\ufe0f {affaire}")
    if hd and hf: parts.append(f"\u23f1 {hd} - {hf}")
    if adr: parts.append(f"\U0001f4cc {adr}")
    if cnt: parts.append(f"\U0001f464 {cnt}")
    if cam: parts.append(f"\U0001f69a {cam}")
    return f'<div class="{cc}"><div class="card-titre"><span class="badge {bc}">{typ}</span><span class="badge {sc}">{stat}</span> {desc}</div><div class="card-detail">{"<br>".join(parts)}</div></div>'

def trajet_avec_menu(row, ws, all_rows, key_prefix=""):
    id_t=str(row.get("id_trajet","")); stat_actuel=str(row.get("statut","Planifie"))
    cam_actuel=str(row.get("camion","Camion 1")); heures=heures_list()
    try:
        date_actuelle=pd.to_datetime(row.get("date_livraison"),errors="coerce")
        date_actuelle=date_actuelle.date() if not pd.isna(date_actuelle) else date.today()
    except: date_actuelle=date.today()
    hd_actuel=str(row.get("heure_debut","08:00")); hf_actuel=str(row.get("heure_fin","10:00"))
    idx_hd=heures.index(hd_actuel) if hd_actuel in heures else 0
    idx_hf=heures.index(hf_actuel) if hf_actuel in heures else 4
    col_card,col_menu=st.columns([11,1])
    with col_card: st.markdown(card_html(row),unsafe_allow_html=True)
    with col_menu:
        with st.popover("\u22ee"):
            st.markdown("**Modifier**")
            new_stat=st.selectbox("Statut",STATUTS,index=STATUTS.index(stat_actuel) if stat_actuel in STATUTS else 0,key=f"pop_stat_{key_prefix}_{id_t}")
            new_date=st.date_input("Date",value=date_actuelle,key=f"pop_date_{key_prefix}_{id_t}")
            new_hd=st.selectbox("Heure debut",heures,index=idx_hd,key=f"pop_hd_{key_prefix}_{id_t}")
            new_hf=st.selectbox("Heure fin",heures,index=idx_hf,key=f"pop_hf_{key_prefix}_{id_t}")
            new_cam=st.selectbox("Vehicule",CAMIONS,index=CAMIONS.index(cam_actuel) if cam_actuel in CAMIONS else 0,key=f"pop_cam_{key_prefix}_{id_t}")
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
        try: save_trajet(row); st.success(f"Trajet enregistre : {description}"); st.balloons()
        except Exception as e: st.error(f"Erreur : {e}")

def onglet_calendrier(df):
    st.markdown("### \U0001f4c5 Calendrier de la semaine")
    semaines=get_semaines(); sem_def=sem_courante(); idx_def=semaines.index(sem_def) if sem_def in semaines else 2
    col_sel,col_btn=st.columns([4,1])
    with col_sel: semaine=st.selectbox("Semaine",semaines,index=idx_def,label_visibility="collapsed")
    with col_btn:
        if st.button("\U0001f5a8\ufe0f Imprimer",use_container_width=True): components.html("<script>window.parent.print();</script>",height=0)
    dates_sem=semaine_to_dates(semaine)
    if not dates_sem: st.error("Semaine invalide."); return
    today=date.today()
    df_sem=df[df["semaine"]==semaine].copy() if not df.empty and "semaine" in df.columns else pd.DataFrame()
    nb=len(df_sem); d0=dates_sem[0].strftime("%d/%m/%Y"); d4=dates_sem[4].strftime("%d/%m/%Y")
    st.markdown(f'<div style="background:white;border-radius:10px;padding:12px 18px;margin-bottom:16px;border-left:5px solid #f97316;"><strong>Semaine {semaine}</strong> &nbsp;|&nbsp; {d0} au {d4} &nbsp;|&nbsp; <strong>{nb} trajet(s)</strong></div>',unsafe_allow_html=True)
    cols=st.columns(5)
    for i,(col,d) in enumerate(zip(cols,dates_sem)):
        today_cls="col-jour-today" if d==today else ""
        df_jour=df_sem[df_sem["date_livraison"].dt.date==d].sort_values("heure_debut") if not df_sem.empty and "date_livraison" in df_sem.columns else pd.DataFrame()
        with col:
            cards="".join(card_html(r) for _,r in df_jour.iterrows()) if not df_jour.empty else '<div class="day-vide">\u2014</div>'
            st.markdown(f'<div class="col-jour {today_cls}"><div class="col-jour-header">{JOURS_FR[i]}<br><span class="day-num">{d.day}</span><span style="font-size:0.75rem;color:#888;">{d.strftime("%b").capitalize()}</span></div>{cards}</div>',unsafe_allow_html=True)
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
