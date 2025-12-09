import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from st_cookies_manager import CookieManager
from streamlit_navigation_bar import st_navbar
import importlib

st.set_page_config(page_title="📊 HC Stats", layout="wide", initial_sidebar_state="collapsed")

pages = ["Stats", "Teams", "Admin", "Rules"]
styles = {
    "nav": {"background-color": "rgb(255, 170, 85)", "padding": "4px 0"},
    "div": {"max-width": "100vw"},
    "span": {
        "border-radius": "0.3rem",
        "color": "rgb(49, 51, 63)",
        "margin": "0 0.05rem",
        "padding": "0.2rem 0.45rem",
        "font-weight": "600",
        "font-size": "0.8rem",
        "white-space": "nowrap",
    },
    "active": {"background-color": "rgba(255,255,255,0.35)"},
    "hover": {"background-color": "rgba(255,255,255,0.5)"},
}
page = st_navbar(pages, styles=styles)

st.markdown("<style>#MainMenu{display:none;} footer{display:none;} .css-1n76uvr{padding-bottom:75px;}</style>", unsafe_allow_html=True)

cookies = CookieManager()
if not cookies.ready():
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_KEY = os.getenv("ADMIN_KEY")
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "admin" not in st.session_state:
    st.session_state.admin = (cookies.get("hc_admin_logged_in") == "true")


def recalc_team_elo(team_id):
    ps = sb.table("team_players").select("player_abv").eq("team_id", team_id).execute().data
    if not ps:
        sb.table("teams").update({"elo": 1000}).eq("id", team_id).execute()
        return
    abvs = [x["player_abv"] for x in ps]
    pl = sb.table("players").select("elo").in_("abv", abvs).execute().data
    new = int(sum(x["elo"] for x in pl) / len(pl))
    sb.table("teams").update({"elo": new}).eq("id", team_id).execute()


def load_players():
    res = sb.table("players").select("*").order("elo", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["abv", "elo"])


def load_teams():
    res = sb.table("teams").select("*").order("elo", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "name", "elo"])


def load_team_players(team_id):
    r = sb.table("team_players").select("player_abv").eq("team_id", team_id).execute().data
    return [x["player_abv"] for x in r] if r else []


def create_team(name, player_list):
    if not player_list:
        return
    res = sb.table("teams").insert({"name": name, "elo": 1000}).execute()
    tid = res.data[0]["id"]
    for p in player_list:
        sb.table("team_players").insert({"team_id": tid, "player_abv": p}).execute()
    recalc_team_elo(tid)


def update_player(old, new, elo):
    sb.table("players").update({"abv": new, "elo": elo}).eq("abv", old).execute()
    sb.table("team_players").update({"player_abv": new}).eq("player_abv", old).execute()
    for t in load_teams()["id"].tolist():
        recalc_team_elo(t)


def delete_player(abv):
    sb.table("team_players").delete().eq("player_abv", abv).execute()
    sb.table("players").delete().eq("abv", abv).execute()
    for t in load_teams()["id"].tolist():
        recalc_team_elo(t)


def update_team(id, name):
    sb.table("teams").update({"name": name}).eq("id", id).execute()
    recalc_team_elo(id)


def delete_team(team_id):
    sb.table("team_players").delete().eq("team_id", team_id).execute()
    sb.table("teams").delete().eq("id", team_id).execute()


def get_rank(elo):
    if elo < 1000: return "😵 Get Lost"
    if elo < 3000: return "🟢 Newbie"
    if elo < 5000: return "🔵 Pro"
    if elo < 7000: return "🟣 Hacker"
    if elo < 9000: return "🏅 God"
    return "👑 Legend"


if page == "Stats":
    st.title("📊 Leaderboard")
    df = load_players()
    if df.empty:
        st.info("Add some sweaty players first 😭")
        st.stop()
    df["Rank"] = df["elo"].apply(get_rank)
    df = df.reset_index(drop=True)
    df["#"] = df.index + 1
    q = st.text_input("Search Player")
    f = st.selectbox("Rank Filter", ["All"] + df["Rank"].unique().tolist())
    r = df.copy()
    if q: r = r[r["abv"].str.lower().str.contains(q.lower())]
    if f != "All": r = r[r["Rank"] == f]
    st.dataframe(r[["#", "abv", "elo", "Rank"]], use_container_width=True, hide_index=True)


elif page == "Teams":
    st.title("👥 Teams")
    players = load_players()
    if players.empty:
        st.error("Add players lol")
        st.stop()

    t1, t2 = st.tabs(["Create Team", "Leaderboard"])

    with t1:
        name = st.text_input("Team Name")
        chosen = st.multiselect("Players", players["abv"].tolist())
        if st.button("Save Team") and name and chosen:
            create_team(name, chosen)
            st.rerun()

    with t2:
        t = load_teams()
        if t.empty:
            st.info("Where teams?")
        else:
            t["#"] = range(1, len(t) + 1)
            st.dataframe(t[["#", "name", "elo"]], use_container_width=True, hide_index=True)


elif page == "Admin":
    st.title("🔑 Admin Panel")
    if not st.session_state.admin:
        pwd = st.text_input("Key", type="password")
        if st.button("Login") and pwd == ADMIN_KEY:
            st.session_state.admin = True
            cookies["hc_admin_logged_in"] = "true"
            cookies.save()
            st.rerun()
        st.stop()

    df = load_players()
    st.subheader("Players")
    if not df.empty:
        sel = st.selectbox("Select Player", df["abv"].tolist())
        new_abv = st.text_input("Rename Player", sel)
        new_elo = st.number_input("Update Elo", value=int(df[df["abv"] == sel]["elo"].iloc[0]))
        if st.button("Save Player"):
            update_player(sel, new_abv, new_elo)
            st.rerun()
        if st.button("Delete Player"):
            delete_player(sel)
            st.rerun()

    st.divider()
    st.subheader("Teams")
    t = load_teams()
    if not t.empty:
        sel_team = st.selectbox("Select Team", t["name"].tolist())
        row = t[t["name"] == sel_team].iloc[0]
        tid = row["id"]
        new_name = st.text_input("Rename Team", row["name"])
        if st.button("Save Team"):
            update_team(tid, new_name)
            st.rerun()

        roster = load_team_players(tid)
        add = st.selectbox("Add Player to Team", [p for p in df["abv"].tolist() if p not in roster])
        if st.button("Add Player"):
            sb.table("team_players").insert({"team_id": tid, "player_abv": add}).execute()
            recalc_team_elo(tid)
            st.rerun()

        if roster:
            kick = st.selectbox("Kick From Team", roster)
            if st.button("Kick Player"):
                sb.table("team_players").delete().eq("team_id", tid).eq("player_abv", kick).execute()
                recalc_team_elo(tid)
                st.rerun()

        if st.button("Delete Team"):
            delete_team(tid)
            st.rerun()

    if st.button("Logout"):
        cookies["hc_admin_logged_in"] = "false"
        cookies.save()
        st.session_state.admin = False
        st.rerun()


elif page == "Rules":
    rules = importlib.import_module("Rules")
    rules.show_rules()
    
