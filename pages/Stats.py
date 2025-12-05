import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📊 HC Stats", layout="wide")

# Sidebar navigation
page = st.sidebar.selectbox("📌 Navigate", ["Stats", "Rules"])

# Path to CSV
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "stats.csv")

# Rank function
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

# Page content
if page == "Stats":
    st.title("📊 Handcricket Stats")
    df = pd.read_csv(DATA_PATH)
    df["Rank"] = df["ELO"].apply(get_rank)
    df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1
    st.dataframe(df[["Sl", "Abv", "ELO", "Rank"]], use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Stats CSV", csv, "hc_stats.csv", "text/csv")
elif page == "Rules":
    import importlib
    rules_module = importlib.import_module("pages.Rules")
    rules_module.show_rules()
    