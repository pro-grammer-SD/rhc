import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from st_cookies_manager import CookieManager
import importlib

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
    return pd.DataFrame(data.data) if data.data else pd.DataFrame(columns=["Abv","ELO"])

def save_players(df):
    sb.table("players").delete().neq("Abv","").execute()
    for _, r in df.iterrows():
        sb.table("players").insert({"Abv": r["Abv"], "ELO": int(r["ELO"])}).execute()

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

page = st.sidebar.selectbox("📌 Navigate", ["Stats","Rules"])

if page == "Stats":
    st.title("📊 Handcricket Stats")

    df = load_players()

    if not df.empty:
        df["Rank"] = df["ELO"].apply(get_rank)
        df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
        df["Sl"] = df.index + 1
    else:
        df = pd.DataFrame(columns=["Sl","Abv","ELO","Rank"])

    st.subheader("🏆 Leaderboard")
    st.dataframe(df[["Sl","Abv","ELO","Rank"]], width='stretch', hide_index=True)

    st.write("---")
    st.subheader("🛠️ Admin Panel")

    if not st.session_state.admin:
        pwd = st.text_input("Enter Admin Passcode 🔐", type="password")
        if st.button("Login"):
            if pwd == ADMIN_KEY:
                st.session_state.admin = True
                cookies["hc_admin_logged_in"] = "true"
                cookies.save()
                st.success("Admin Mode Enabled 👑")
                st.rerun()
            else:
                st.error("Bruh 💀 Wrong password.")
    else:
        st.success("Admin Mode Enabled 👑")

        new_df = st.data_editor(
            df[["Abv","ELO"]],
            num_rows="dynamic",
            width='stretch',
            key="edit_table"
        )

        col1, col2 = st.columns(2)

        if col1.button("Save Changes 💾"):
            new_df["ELO"] = new_df["ELO"].fillna(1000)
            save_players(new_df)
            st.success("Updated Successfully ✔️")
            st.rerun()

        if col2.button("Sign Out 🚪"):
            cookies["hc_admin_logged_in"] = "false"
            cookies.save()
            st.session_state.admin = False
            st.rerun()

elif page == "Rules":
    try:
        rules_module = importlib.import_module("Rules")
        rules_module.show_rules()
    except Exception as e:
        st.error(f"Failed to load Rules page.\n\n{e}")
        