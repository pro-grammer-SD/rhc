import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from st_cookies_manager import CookieManager

st.set_page_config(page_title="📊 HC Stats", layout="wide")

cookies = CookieManager()
if not cookies.ready():
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_KEY = os.getenv("ADMIN_KEY")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_players():
    data = sb.table("players").select("*").execute()
    return pd.DataFrame(data.data) if data.data else pd.DataFrame(columns=["abv","elo"])

def save_players(df):
    sb.table("players").delete().neq("abv","").execute()
    for _, r in df.iterrows():
        sb.table("players").insert({"abv": r["abv"], "elo": int(r["elo"])}).execute()

def load_teams():
    data = sb.table("teams").select("*").execute()
    return pd.DataFrame(data.data) if data.data else pd.DataFrame(columns=["team","players","elo"])

def save_team(name, players, elo):
    sb.table("teams").insert({
        "team": name,
        "players": ",".join(players),
        "elo": int(elo)
    }).execute()

def get_rank(elo):
    if elo < 1000: return "😵 Get Lost"
    if elo < 3000: return "🟢 Newbie"
    if elo < 5000: return "🔵 Pro"
    if elo < 7000: return "🟣 Hacker"
    if elo < 9000: return "🏅 God"
    return "👑 Legend"

if "admin" not in st.session_state:
    admin_cookie = cookies.get("hc_admin_logged_in")
    st.session_state.admin = (admin_cookie == "true")

page = st.sidebar.selectbox("📌 Navigate", ["Stats","Teams","Admin"])

# ==================== 📊 Stats Page ====================
if page == "Stats":
    st.title("📊 Player Leaderboard")

    df = load_players()
    if df.empty:
        st.info("No players yet 😭")
        st.stop()

    df["Rank"] = df["elo"].apply(get_rank)
    df = df.sort_values(by="elo", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1

    search = st.text_input("🔍 Search Player", key="search")
    rank_filter = st.selectbox("Filter by Rank", 
        ["All","😵 Get Lost","🟢 Newbie","🔵 Pro","🟣 Hacker","🏅 God","👑 Legend"])

    result = df.copy()

    if search:
        q = search.lower()
        result = result[result["abv"].str.lower().str.contains(q)]

    if rank_filter != "All":
        result = result[result["Rank"] == rank_filter]

    st.dataframe(result[["Sl","abv","elo","Rank"]], width="stretch", hide_index=True)

# ==================== 👥 Teams Tab ====================
elif page == "Teams":
    st.title("👥 Team Builder & Leaderboard")

    players = load_players()
    if players.empty:
        st.error("Add players first 💀")
        st.stop()

    team_name = st.text_input("Team Name")
    chosen = st.multiselect("Pick Players", players["abv"].tolist())

    if chosen:
        team_elo = int(players.set_index("abv").loc[chosen]["elo"].mean())
        st.metric("Avg Team ELO", team_elo)

        if st.button("Save Team 💾"):
            if not team_name.strip():
                st.error("Team needs a name bruv")
            else:
                save_team(team_name, chosen, team_elo)
                st.success("Saved 🎯")
                st.rerun()

    st.write("----")
    st.subheader("🏆 Team Leaderboard")

    teams = load_teams()
    if not teams.empty:
        teams = teams.sort_values("elo", ascending=False).reset_index(drop=True)
        teams["Sl"] = teams.index + 1
        st.dataframe(teams[["Sl","team","players","elo"]], width="stretch", hide_index=True)
    else:
        st.info("No teams saved yet 🫠")

# ==================== 👑 Admin Page ====================
elif page == "Admin":
    st.title("👑 Admin Control")

    if not st.session_state.admin:
        pwd = st.text_input("Passcode", type="password")
        if st.button("Login"):
            if pwd == ADMIN_KEY:
                st.session_state.admin = True
                cookies["hc_admin_logged_in"] = "true"
                cookies.save()
                st.success("Admin Mode Enabled 🔥")
                st.rerun()
            else:
                st.error("Nah 💀")
    else:
        st.success("Admin Mode On 🔥")
        df = load_players()
        new_df = st.data_editor(df, num_rows="dynamic", width="stretch")

        if st.button("Save Players 💾"):
            save_players(new_df)
            st.success("Saved ✔️")
            st.rerun()

        if st.button("Logout 🚪"):
            cookies["hc_admin_logged_in"] = "false"
            cookies.save()
            st.session_state.admin = False
            st.rerun()
            