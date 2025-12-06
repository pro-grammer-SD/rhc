import streamlit as st
import pandas as pd
import os
from st_cookies_manager import CookieManager
import importlib

st.set_page_config(page_title="📊 HC Stats", layout="wide")

# ---- COOKIE / ADMIN SETUP ----
cookies = CookieManager()
if not cookies.ready():
    st.stop()

if "admin" not in st.session_state:
    admin_cookie = cookies.get("hc_admin_logged_in")
    st.session_state.admin = (admin_cookie == "true")

# ---- PAGE SWITCHING ----
page = st.sidebar.selectbox("📌 Navigate", ["Stats", "Rules"])

# ---- DATA PATH ----
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "stats.csv")

# ---- RANK FUNCTION ----
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

# ---- STATS PAGE ----
if page == "Stats":
    st.title("📊 Handcricket Stats")

    # Load CSV
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
    else:
        df = pd.DataFrame(columns=["Abv", "ELO"])

    # Ensure numeric ELO
    df["ELO"] = pd.to_numeric(df["ELO"], errors="coerce").fillna(1000)
    df["Rank"] = df["ELO"].apply(get_rank)
    df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1

    st.subheader("🏆 Leaderboard")
    st.dataframe(df[["Sl", "Abv", "ELO", "Rank"]],
                 width='stretch', hide_index=True)

    st.write("---")
    st.subheader("🛠️ Admin Panel")

    # ---- ADMIN LOGIN ----
    if not st.session_state.admin:
        pwd = st.text_input("Enter Admin Passcode 🔐", type="password")
        if st.button("Login"):
            if pwd == st.secrets["ADMIN_KEY"]:
                st.session_state.admin = True
                cookies["hc_admin_logged_in"] = "true"
                cookies.save()
                st.success("Admin Mode Enabled 👑")
                st.rerun()
            else:
                st.error("Bruh 💀 Wrong password.")
    else:
        st.success("Admin Mode Enabled 👑")

        # Editable table
        new_df = st.data_editor(
            df[["Abv", "ELO"]],
            num_rows="dynamic",
            width='stretch',
            key="edit_table"
        )

        col1, col2 = st.columns(2)

        # Save changes
        if col1.button("Save Changes 💾"):
            # Add new rows if any
            for idx, row in new_df.iterrows():
                if row["Abv"] not in df["Abv"].values:
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            # Update existing values
            df["Abv"] = new_df["Abv"]
            df["ELO"] = new_df["ELO"].fillna(1000)
            df.to_csv(DATA_PATH, index=False)
            st.success("Updated Successfully ✔️")
            st.rerun()

        # Sign out
        if col2.button("Sign Out 🚪"):
            cookies["hc_admin_logged_in"] = "false"
            cookies.save()
            st.session_state.admin = False
            st.rerun()

# ---- RULES PAGE ----
elif page == "Rules":
    try:
        rules_module = importlib.import_module("pages.Rules")
        rules_module.show_rules()
    except Exception as e:
        st.error(f"Failed to load Rules page. Check pages/Rules.py\n\n{e}")
        cookies["hc_admin_logged_in"] = "true"
                cookies.save()
                st.success("Admin Mode Enabled 👑")
                st.rerun()
            else:
                st.error("Bruh 💀 Wrong password.")
    else:
        st.success("Admin Mode Enabled 👑")

        # Editable table with dynamic rows
        new_df = st.data_editor(
            df[["Abv", "ELO"]],
            num_rows="dynamic",
            width='stretch',
            key="edit_table"
        )

        col1, col2 = st.columns(2)

        # Save changes permanently
        if col1.button("Save Changes 💾"):
            # Add new rows if any
            for idx, row in new_df.iterrows():
                if row["Abv"] not in df["Abv"].values:
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df["Abv"] = new_df["Abv"]
            df["ELO"] = new_df["ELO"].fillna(1000)  # default ELO if left blank
            df.to_csv(DATA_PATH, index=False)
            st.success("Updated Successfully ✔️")
            st.rerun()

        # Sign out admin
        if col2.button("Sign Out 🚪"):
            cookies["hc_admin_logged_in"] = "false"
            cookies.save()
            st.session_state.admin = False
            st.rerun()
            
