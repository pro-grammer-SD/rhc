import streamlit as st
import pandas as pd
import os
import random
import smtplib
from email.mime.text import MIMEText

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

def send_otp(email, otp):
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "HandCricket Admin OTP 🔐"
    msg["From"] = st.secrets["EMAIL_FROM"]
    msg["To"] = email
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(st.secrets["EMAIL_FROM"], st.secrets["EMAIL_APP_PASSWORD"])
    server.sendmail(st.secrets["EMAIL_FROM"], email, msg.as_string())
    server.quit()

if page == "Stats":
    st.title("📊 Handcricket Stats")
    df = pd.read_csv(DATA_PATH)
    df["Rank"] = df["ELO"].apply(get_rank)
    df = df.sort_values(by="ELO", ascending=False).reset_index(drop=True)
    df["Sl"] = df.index + 1
    st.dataframe(df[["Sl", "Abv", "ELO", "Rank"]], use_container_width=True, hide_index=True)

    if "otp_verified" not in st.session_state:
        st.session_state.otp_verified = False

    with st.expander("🛠️ Edit Stats (Admin Only)"):
        if not st.session_state.otp_verified:
            email = st.text_input("Admin Email")
            if st.button("Send OTP"):
                if email == st.secrets["EMAIL_FROM"]:
                    otp = random.randint(100000, 999999)
                    st.session_state.otp = otp
                    send_otp(email, otp)
                    st.success("OTP Sent 📩 Check your inbox!")
                else:
                    st.error("Unauthorized Email ❌")

            otp_input = st.text_input("Enter OTP")
            if st.button("Verify OTP"):
                if otp_input == str(st.session_state.get("otp", "")):
                    st.session_state.otp_verified = True
                    st.success("Access Granted 🎯")
                else:
                    st.error("Wrong OTP 😤 Try again.")

        else:
            edited_df = st.data_editor(df[["Abv", "ELO"]], num_rows="dynamic")
            if st.button("Save Changes 💾"):
                df["ELO"] = edited_df["ELO"]
                df.to_csv(DATA_PATH, index=False)
                st.success("Leaderboard Updated 🚀")
                
