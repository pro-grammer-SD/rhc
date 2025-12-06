import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📊 HC Stats", layout="wide")

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

if page == "Stats":
    st.title("📊 Handcricket Stats")
    df = pd.read_csv(DATA_PATH)
    df["Rank"] = df["ELO"].apply(get_rank)
    df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1

    st.dataframe(df[["Sl", "Abv", "ELO", "Rank"]], use_container_width=True, hide_index=True)

    if "admin" not in st.session_state:
        st.session_state.admin = False

    with st.expander("🛠️ Admin Controls"):
        if not st.session_state.admin:
            pwd = st.text_input("Enter Admin Passcode 🔐", type="password")
            if st.button("Login"):
                if pwd == st.secrets["ADMIN_KEY"]:
                    st.session_state.admin = True
                    st.success("Admin Mode Enabled 🚀")
                else:
                    st.error("Access Denied 💀")
        else:
            edited_df = st.data_editor(df[["Abv", "ELO"]], num_rows="dynamic")
            if st.button("Save"):
                df["ELO"] = edited_df["ELO"]
                df.to_csv(DATA_PATH, index=False)
                st.success("Stats Updated 🎯")
                
