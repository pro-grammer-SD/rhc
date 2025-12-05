import streamlit as st

st.set_page_config(page_title="🏏 Ranked HC Rules", layout="wide")

st.title("🏏 Ranked Handcricket Rules")

rules = [
    "🎮 Players must know how to play Handcricket (HC) to register.",
    "📊 Rank is based on ELO points.",
    "📈 ELO ranges and ranks:",
    "  • <1000 → 😵 Get Lost (GL)",
    "  • 1000-3000 → 🟢 Newbie",
    "  • 3000-5000 → 🔵 Pro",
    "  • 5000-7000 → 🟣 Hacker",
    "  • 7000-9000 → 🏅 God",
    "  • 9000+ → 👑 Legend",
    "🏃‍♂️ Runs scored between r and r+10 → + (r+10) ELO points. Example: 40-50 runs → +50 ELO.",
    "😈 Misconduct by a player → -500 ELO.",
    "💥 Misconduct by a single team player → team ELO -1000.",
    "🙅‍♂️ No passes allowed in batting, unless the player is unwell.",
    "🎯 Each wicket taken → +20 ELO.",
    "⛔ No 6-limit matches allowed. Only 10-limit matches.",
    "🏆 Player with the highest added ELO in a match is POTM (Player of the Match).",
    "👥 Team ELO is the average of playing members' ELOs: sum(ELOs)/number of players."
]

for rule in rules:
    st.markdown(f"• {rule}")
    