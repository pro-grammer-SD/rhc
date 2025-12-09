import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from st_cookies_manager import CookieManager
from streamlit_navigation_bar import st_navbar
import importlib

st.set_page_config(page_title="📊 HC Stats", layout="wide", initial_sidebar_state="collapsed")

pages = ["Stats","Teams","Admin","Rules"]
styles = {
    "nav": {"background-color": "rgb(255, 179, 102)"},
    "div": {"max-width": "48rem"},
    "span": {
        "border-radius": "0.5rem",
        "color": "rgb(49, 51, 63)",
        "margin": "0 0.125rem",
        "padding": "0.4375rem 1rem",
        "font-weight": "600",
        "font-size": "1.05rem",
    },
    "active": {"background-color": "rgba(255, 255, 255, 0.3)"},
    "hover": {"background-color": "rgba(255, 255, 255, 0.4)"},
}
page = st_navbar(pages, styles=styles)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

cookies = CookieManager()
if not cookies.ready():
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_KEY = os.getenv("ADMIN_KEY")
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "admin" not in st.session_state:
    admin_cookie = cookies.get("hc_admin_logged_in")
    st.session_state.admin = (admin_cookie == "true")

def load_players():
    data = sb.table("players").select("*").execute()
    return pd.DataFrame(data.data) if data.data else pd.DataFrame(columns=["abv","elo"])

def load_teams():
    data = sb.table("teams").select("*").execute()
    return pd.DataFrame(data.data) if data.data else pd.DataFrame(columns=["id","name","elo"])

def load_team_players(team_id):
    data = sb.table("team_players").select("player_abv").eq("team_id", team_id).execute()
    return [p["player_abv"] for p in data.data] if data.data else []

def create_team(name, player_list, elo):
    r = sb.table("teams").insert({"name": name, "elo": elo}).execute()
    team_id = r.data[0]["id"]
    for p in player_list:
        sb.table("team_players").insert({"team_id": team_id, "player_abv": p}).execute()

def delete_team(team_id):
    sb.table("teams").delete().eq("id", team_id).execute()

def update_team(id, name, elo):
    sb.table("teams").update({"name": name, "elo": elo}).eq("id", id).execute()

def update_player(old, new_abv, elo):
    sb.table("players").update({"abv": new_abv, "elo": elo}).eq("abv", old).execute()
    if old != new_abv:
        sb.rpc("rename_player", {"old_abv": old, "new_abv": new_abv}).execute()

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
        st.info("No players yet 😭")
        st.stop()
    df["Rank"] = df["elo"].apply(get_rank)
    df = df.sort_values("elo", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1
    q = st.text_input("Search")
    rank_filter = st.selectbox("Rank Filter", ["All"] + df["Rank"].unique().tolist())
    res = df.copy()
    if q:
        res = res[res["abv"].str.lower().str.contains(q.lower())]
    if rank_filter != "All":
        res = res[res["Rank"] == rank_filter]
    st.dataframe(res[["Sl","abv","elo","Rank"]], width="stretch", hide_index=True)

elif page == "Teams":
    st.title("👥 Teams")
    players = load_players()
    if players.empty:
        st.error("Add players bruv")
        st.stop()

    tab1, tab2 = st.tabs(["Create Team","Leaderboard"])

    with tab1:
        name = st.text_input("Team Name")
        chosen = st.multiselect("Players", players["abv"].tolist())
        if chosen:
            team_elo = int(players.set_index("abv").loc[chosen]["elo"].mean())
            st.metric("Team Elo", team_elo)
            if st.button("Save Team"):
                create_team(name, chosen, team_elo)
                st.success("Saved")
                st.rerun()

    with tab2:
        t = load_teams()
        if not t.empty:
            t = t.sort_values("elo", ascending=False).reset_index(drop=True)
            t["Sl"] = t.index + 1
            st.dataframe(t[["Sl","name","elo"]], width="stretch", hide_index=True)
        else:
            st.info("No teams")

elif page == "Admin":
    st.title("Admin")
    if not st.session_state.admin:
        pwd = st.text_input("Key", type="password")
        if st.button("Login"):
            if pwd == ADMIN_KEY:
                st.session_state.admin = True
                cookies["hc_admin_logged_in"] = "true"
                cookies.save()
                st.rerun()
            else:
                st.error("Bruh no.")
    else:
        st.success("Admin Enabled")

        st.subheader("Players")
        df = load_players()
        sel = st.selectbox("Player", df["abv"].tolist())
        new_abv = st.text_input("Rename", sel)
        new_elo = st.number_input("Elo", value=int(df[df["abv"]==sel]["elo"].iloc[0]))
        if st.button("Update Player"):
            update_player(sel, new_abv, new_elo)
            st.rerun()
        if st.button("Delete Player", type="primary"):
            sb.table("players").delete().eq("abv", sel).execute()
            sb.table("team_players").delete().eq("player_abv", sel).execute()
            st.rerun()

        st.divider()
        st.subheader("Teams")
        t = load_teams()
        if not t.empty:
            sel_team = st.selectbox("Team", t["name"].tolist())
            row = t[t["name"]==sel_team].iloc[0]
            tid = row["id"]
            new_name = st.text_input("Rename Team", sel_team)
            new_team_elo = st.number_input("Team Elo", value=int(row["elo"]))
            roster = load_team_players(tid)
            all_ps = players["abv"].tolist()
            addp = st.selectbox("Add Player", [p for p in all_ps if p not in roster])
            if st.button("Add"):
                sb.table("team_players").insert({"team_id": tid, "player_abv": addp}).execute()
                st.rerun()
            remp = st.selectbox("Kick Player", roster)
            if st.button("Kick"):
                sb.table("team_players").delete().eq("team_id", tid).eq("player_abv", remp).execute()
                st.rerun()
            if st.button("Update Team"):
                update_team(tid, new_name, new_team_elo)
                st.rerun()
            if st.button("Delete Team", type="primary"):
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
    
