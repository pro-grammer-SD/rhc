import streamlit as st
import pandas as pd

st.set_page_config(page_title="📊 HC Stats", layout="wide")

st.title("📊 Handcricket Stats")

# Load CSV
df = pd.read_csv("stats.csv")

# Function to assign rank based on ELO
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

# Assign ranks
df["Rank"] = df["ELO"].apply(get_rank)

# Sort by ELO descending
df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
df["Sl"] = df.index + 1

# Display table
st.dataframe(
    df[["Sl", "Abv", "ELO", "Rank"]],
    use_container_width=True,
    hide_index=True
)

# Downloadable CSV
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Stats CSV",
    data=csv,
    file_name='hc_stats.csv',
    mime='text/csv'
)
