import streamlit as st
import pandas as pd
import os
from streamlit_cookie_manager import CookieManager

st.set_page_config(page_title="📊 HC Stats", layout="wide")

cookies = CookieManager()
cookies.get_all()

page = st.sidebar.selectbox("📌 Navigate", ["Stats", "Rules"])

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "stats.csv")

def get_rank(elo):
    if elo < 1000:
        return "😵 Get Lost"
    elif 1000 <= elo < 3000:
        return "🟢 Newbie"
    elif 3000 <= elo < 5000:
        return "🔵 Pro"
    elif 5000 <= elo < 7000:
        return "🟣 Hacker"
    elif 7000 <= elo < 9000:
        return "🏅 God"
    else:
        return "👑 Legend"

if "admin" not in st.session_state:
    admin_cookie = cookies.get("hc_admin_logged_in")
    st.session_state.admin = (admin_cookie == "true")

if page == "Stats":
    st.title("📊 Handcricket Stats")

    df = pd.read_csv(DATA_PATH)
    df["Rank"] = df["ELO"].apply(get_rank)
    df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1

    st.subheader("🏆 Leaderboard")
    st.dataframe(df[["Sl", "Abv", "ELO", "Rank"]],
                 use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("🛠️ Admin Panel")

    if not st.session_state.admin:
        pwd = st.text_input("Enter Admin Passcode 🔐", type="password")
        if st.button("Login"):
            if pwd == st.secrets["ADMIN_KEY"]:
                st.session_state.admin = True
                cookies.set("hc_admin_logged_in", "true")
                st.success("Admin Mode Enabled 👑")
                st.rerun()
            else:
                st.error("Bruh 💀 Wrong password.")

    else:
        st.success("Admin Mode Enabled 👑")

        new_df = st.data_editor(
            df[["Abv", "ELO"]],
            num_rows="dynamic",
            use_container_width=True,
            key="edit_table"
        )

        col1, col2 = st.columns(2)

        if col1.button("Save Changes 💾"):
            df["Abv"] = new_df["Abv"]
            df["ELO"] = new_df["ELO"]
            df.to_csv(DATA_PATH, index=False)
            st.success("Updated Successfully ✔️")
            st.rerun()

        if col2.button("Sign Out 🚪"):
            cookies.delete("hc_admin_logged_in")
            st.session_state.admin = False
            st.rerun()
            
