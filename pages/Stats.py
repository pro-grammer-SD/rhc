import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from st_cookies_manager import CookieManager
from streamlit_navigation_bar import st_navbar
import importlib
import plotly.express as px

st.set_page_config(page_title="📊 HC Stats", layout="wide", initial_sidebar_state="collapsed")

pages = ["Stats","Teams","Admin","Rules"]
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
st.markdown("<style>#MainMenu{display:none;} footer{display:none;}</style>", unsafe_allow_html=True)

cookies = CookieManager()
if not cookies.ready():
    st.stop()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_KEY = os.getenv("ADMIN_KEY")
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "admin" not in st.session_state:
    st.session_state.admin = (cookies.get("hc_admin_logged_in") == "true")

# ---------------------- Helpers ----------------------
def get_rank(elo):
    if elo < 1000: return "😵 Get Lost"
    if elo < 3000: return "🟢 Newbie"
    if elo < 5000: return "🔵 Pro"
    if elo < 7000: return "🟣 Hacker"
    if elo < 9000: return "🏅 God"
    return "👑 Legend"

def load_players():
    res = sb.table("players").select("*").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["abv","elo"])
    df["elo"] = pd.to_numeric(df["elo"], errors="coerce").fillna(0)
    return df

def load_teams():
    res = sb.table("teams").select("*").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id","name","elo"])
    df["elo"] = pd.to_numeric(df["elo"], errors="coerce").fillna(0)
    return df

def load_team_players(team_id):
    res = sb.table("team_players").select("player_abv").eq("team_id", team_id).execute()
    return [x["player_abv"] for x in (res.data or [])]

def recalc_team_elo(team_id):
    roster = load_team_players(team_id)
    if not roster:
        sb.table("teams").update({"elo": 0}).eq("id", team_id).execute()
        return
    players = sb.table("players").select("abv","elo").in_("abv", roster).execute().data or []
    elos = [int(p.get("elo",0)) for p in players]
    new_elo = int(sum(elos)/len(elos)) if elos else 0
    sb.table("teams").update({"elo": new_elo}).eq("id", team_id).execute()

def recalc_all_teams():
    for tid in load_teams()["id"].tolist():
        recalc_team_elo(tid)

def create_team(name, roster):
    if not name or not roster: return
    res = sb.table("teams").insert({"name": name, "elo": 0}).execute()
    tid = res.data[0]["id"]
    for p in roster:
        sb.table("team_players").insert({"team_id": tid, "player_abv": p}).execute()
    recalc_team_elo(tid)

def update_player(old, new, elo):
    sb.table("players").update({"abv": new, "elo": elo}).eq("abv", old).execute()
    sb.table("team_players").update({"player_abv": new}).eq("player_abv", old).execute()
    recalc_all_teams()

def delete_player(abv):
    sb.table("team_players").delete().eq("player_abv", abv).execute()
    sb.table("players").delete().eq("abv", abv).execute()
    recalc_all_teams()

def update_team(tid, name):
    sb.table("teams").update({"name": name}).eq("id", tid).execute()
    recalc_team_elo(tid)

def delete_team(tid):
    sb.table("team_players").delete().eq("team_id", tid).execute()
    sb.table("teams").delete().eq("id", tid).execute()

# ---------------------- Pages ----------------------
if page == "Stats":
    st.title("📊 Player Leaderboard")
    df = load_players()
    if df.empty:
        st.info("Add some players first 😭")
        st.stop()
    df["Rank"] = df["elo"].apply(get_rank)
    df = df.sort_values("elo", ascending=False).reset_index(drop=True)
    df["#"] = df.index + 1

    q = st.text_input("Search")
    f = st.selectbox("Rank Filter", ["All"] + df["Rank"].unique().tolist())
    r = df.copy()
    if q: r = r[r["abv"].str.lower().str.contains(q.lower())]
    if f != "All": r = r[r["Rank"]==f]
    st.dataframe(r[["#","abv","elo","Rank"]], use_container_width=True, hide_index=True)

    st.markdown("### 📈 Player ELO Chart")
    if not r.empty:
        fig = px.bar(r, x="abv", y="elo", text="elo", labels={"abv":"Player","elo":"ELO"})
        fig.update_traces(textposition="outside")
        fig.update_layout(modebar={"remove":["zoom","pan","select","lasso","resetScale"]})
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No data to display.")

elif page == "Teams":
    st.title("👥 Teams")
    players = load_players()
    if players.empty:
        st.error("Add players first")
        st.stop()

    recalc_all_teams()
    t1, t2 = st.tabs(["Create Team","Leaderboard"])

    with t1:
        name = st.text_input("Team Name")
        chosen = st.multiselect("Players", players["abv"].tolist())
        if st.button("Save") and name and chosen:
            create_team(name, chosen)
            st.success("Team Created")
            st.rerun()

    with t2:
        teams_df = load_teams()
        if teams_df.empty:
            st.info("No teams yet")
        else:
            teams_df = teams_df.sort_values("elo", ascending=False).reset_index(drop=True)
            teams_df["#"] = teams_df.index+1
            st.dataframe(teams_df[["#","name","elo"]], use_container_width=True, hide_index=True)

            st.markdown("### 📊 Team Player Contributions")
            team_ids = teams_df["id"].tolist()
            sel_team = st.selectbox("Select Team", team_ids,
                                    format_func=lambda x: teams_df[teams_df["id"]==x]["name"].iloc[0] 
                                    if not teams_df[teams_df["id"]==x].empty else "Unknown")
            filtered = teams_df[teams_df["id"]==sel_team]
            if not filtered.empty:
                tid = filtered.iloc[0]["id"]
                roster = load_team_players(tid)
                if roster:
                    pl_data = sb.table("players").select("abv","elo").in_("abv", roster).execute().data or []
                    pl_df = pd.DataFrame(pl_data).sort_values("elo", ascending=False)
                    if not pl_df.empty:
                        fig = px.bar(pl_df, x="abv", y="elo", text="elo", labels={"abv":"Player","elo":"ELO"})
                        fig.update_traces(textposition="outside")
                        fig.update_layout(modebar={"remove":["zoom","pan","select","lasso","resetScale"]})
                        st.plotly_chart(fig, width="stretch")

elif page == "Admin":
    st.title("🔑 Admin Panel")

    if not st.session_state.admin:
        pwd = st.text_input("Key", type="password")
        if st.button("Login") and pwd == ADMIN_KEY:
            st.session_state.admin = True
            cookies["hc_admin_logged_in"]="true"
            cookies.save()
            st.rerun()
        st.stop()
    else:
        if st.button("Sign Out"):
            st.session_state.admin = False
            cookies["hc_admin_logged_in"]="false"
            cookies.save()
            st.success("Signed out!")
            st.rerun()

    df = load_players()
    t = load_teams()

    st.subheader("Players")
    if not df.empty:
        sel = st.selectbox("Select Player", df["abv"].tolist())
        if sel:
            new_abv = st.text_input("Rename", sel)
            new_elo = st.number_input("ELO", value=int(df[df["abv"]==sel]["elo"].iloc[0]))
            if st.button("Update Player"):
                update_player(sel, new_abv, new_elo)
                st.success("Player updated")
                st.rerun()
            if st.button("Delete Player"):
                delete_player(sel)
                st.success("Player deleted")
                st.rerun()

    st.subheader("Teams")
    if not t.empty:
        sel_team_name = st.selectbox("Select Team", t["name"].tolist())
        filtered = t[t["name"]==sel_team_name]
        if not filtered.empty:
            tid = filtered.iloc[0]["id"]
            new_name = st.text_input("Rename Team", filtered.iloc[0]["name"])
            if st.button("Update Team"):
                update_team(tid, new_name)
                st.success("Team updated")
                st.rerun()

            roster = load_team_players(tid)
            add = st.selectbox("Add Player", [p for p in df["abv"].tolist() if p not in roster])
            if st.button("Add"):
                sb.table("team_players").insert({"team_id": tid, "player_abv": add}).execute()
                recalc_team_elo(tid)
                st.success(f"Added {add}")
                st.rerun()

            if roster:
                kick = st.selectbox("Kick Player", roster)
                if st.button("Kick"):
                    sb.table("team_players").delete().eq("team_id", tid).eq("player_abv", kick).execute()
                    recalc_team_elo(tid)
                    st.success(f"Kicked {kick}")
                    st.rerun()

elif page == "Rules":
    rules = importlib.import_module("Rules")
    rules.show_rules()
    
