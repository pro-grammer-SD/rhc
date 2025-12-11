import streamlit as st

def show_rules():
    st.title("🏏 Ranked Handcricket Rules")
    rules = [
        "🎮 Players must know how to play Handcricket (HC) to register.",
        "📊 Rank is based on ELO points.",
        "📈 ELO ranges and ranks:",
        "<1000 → 😵 Get Lost (GL)",
        "1000-3000 → 🟢 Newbie",
        "3000-5000 → 🔵 Pro",
        "5000-7000 → 🟣 Hacker",
        "7000-9000 → 🏅 God",
        "9000+ → 👑 Legend",
        "🏃‍♂️ Runs scored between r and r+10 → + (r+10) ELO points.",
        "😈 Misconduct by a player → -500 ELO.",
        "🫂 For Aided Wickets (AW), the player who delivered the ball gets +20 ELO and the player who helped the bowler for the numerical decision gets +10 ELO."
        "🙅‍♂️ No passes allowed in batting, unless the player is unwell.",
        "🎯 Each wicket taken → +20 ELO.",
        "⛔ No 6-limit matches allowed. Only 10-limit matches.",
        "🏆 Player with the highest added ELO in a match is POTM.",
        "👥 Team ELO is the average of playing members' ELOs."
    ]
    for rule in rules:
        st.markdown(f"• {rule}")
        
