import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ------------------ Google Sheets Setup ------------------
SHEET_NAME = "stock-dashboard"   # ชื่อ sheet ใน Google Sheets

# กำหนด scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# อ่าน credentials จาก Streamlit secrets
service_account_info = st.secrets["gcp_service_account"]

# ใช้ google-auth สร้าง Credentials
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

# เปิดไฟล์ Google Sheet
sheet = client.open(SHEET_NAME).sheet1

# โหลดค่าปัจจุบันจาก Google Sheets เป็น dict
data = sheet.get_all_records()
# ใช้ key เป็นตัวดึงค่า
values_dict = {row["key"]: float(row["value"]) for row in data} if data else {}

# ฟังก์ชันดึงค่า
def get_value(name, default):
    return values_dict.get(name, default)

# ฟังก์ชันอัพเดตค่า
def set_value(name, val):
    records = sheet.get_all_records()
    keys = [r["key"] for r in records]
    if name in keys:
        row_index = keys.index(name) + 2  # index + header
        sheet.update_cell(row_index, 3, val)  # column 3 = value
    else:
        sheet.append_row([name, "US", val, pd.Timestamp.now().date()])

# ------------------ Streamlit App ------------------
st.set_page_config(page_title="🌍 Global Macro Dashboard", layout="wide")
st.title("🌍 Global Macro Dashboard — Historicals & Signals")
st.markdown("อัพเดตตัวเลข แล้วดูสัญญาณ + แนวโน้มสินทรัพย์แบบอัตโนมัติ (ตามกฎเชิงประวัติศาสตร์)")

# ------------------ Input Fields ------------------
core_pce = st.number_input("Core PCE (%)", value=get_value("Core PCE", 2.0))
core_cpi = st.number_input("Core CPI (%)", value=get_value("Core CPI", 2.0))
ten_y = st.number_input("US 10Y Yield (%)", value=get_value("US 10Y Yield", 3.5))
fed_rate = st.number_input("Fed Funds Rate (%)", value=get_value("Fed Funds Rate", 2.0))
pmi = st.number_input("PMI", value=get_value("PMI", 50.0))
unemp = st.number_input("Unemployment (%)", value=get_value("Unemployment", 4.0))
dxy = st.number_input("DXY", value=get_value("DXY", 100.0))
debt_gdp = st.number_input("Debt-to-GDP (%)", value=get_value("Debt-to-GDP", 80.0))
m2 = st.number_input("M2 Growth (%)", value=get_value("M2 Growth", 5.0))
repo = st.number_input("Repo (%)", value=get_value("Repo", 2.0))
margin = st.number_input("Margin Debt", value=get_value("Margin Debt", 500.0))
gold = st.number_input("Gold", value=get_value("Gold", 1800.0))
spx = st.number_input("S&P 500", value=get_value("S&P 500", 4000.0))
btc = st.number_input("Bitcoin", value=get_value("Bitcoin", 30000.0))

# ------------------ Save Button ------------------
if st.button("💾 Save to Google Sheets"):
    set_value("Core PCE", core_pce)
    set_value("Core CPI", core_cpi)
    set_value("US 10Y Yield", ten_y)
    set_value("Fed Funds Rate", fed_rate)
    set_value("PMI", pmi)
    set_value("Unemployment", unemp)
    set_value("DXY", dxy)
    set_value("Debt-to-GDP", debt_gdp)
    set_value("M2 Growth", m2)
    set_value("Repo", repo)
    set_value("Margin Debt", margin)
    set_value("Gold", gold)
    set_value("S&P 500", spx)
    set_value("Bitcoin", btc)
    st.success("บันทึกข้อมูลเรียบร้อย ✅")
    
# ---------- Rules ----------
signals = []

def add_signal(name, note, assets_in, assets_out=None):
    signals.append({
        "Signal / สัญญาณ": name,
        "Implication / ความหมาย": note,
        "Favored Assets / สินทรัพย์ที่ได้ประโยชน์": ", ".join(assets_in),
        "Unfavored Assets / สินทรัพย์ที่กดดัน": ", ".join(assets_out) if assets_out else ""
    })

# Inflation (Core PCE/CPI)
infl = max(core_pce, core_cpi)
if infl > 3.0:
    add_signal("High Inflation >3% / เงินเฟ้อสูง", "Fed likely to tighten / Fed มีแนวโน้มคุมเข้ม", ["ทอง", "BTC", "พันธบัตรสั้น"], ["หุ้น Growth/Tech"])
elif infl < 1.5:
    add_signal("Low Inflation <1.5% / เงินเฟ้อต่ำ", "Risk of slowdown → easing / เสี่ยงชะลอ → Fed ผ่อน", ["ทอง", "พันธบัตรยาว", "REITs"], [])
else:
    add_signal("Inflation ~2% / เงินเฟ้อใกล้เป้า", "Goldilocks zone", ["หุ้น Tech/Growth", "EM equities"], [])

# 10Y rules
if ten_y > 4.5:
    add_signal(
        "10Y พุ่ง (>4.5%)",
        "Discount rate สูง → กดดัน Valuation",
        ["พันธบัตรสั้น", "หุ้นปันผล", "Defensive"],
        ["หุ้น Tech/Growth", "REITs"]
    )
elif ten_y < 3.5:
    add_signal(
        "10Y ต่ำ (<3.5%)",
        "เอื้อสินทรัพย์เสี่ยง/ปลอดภัยพร้อมกัน (ขึ้นกับบริบท)",
        ["ทอง", "Bitcoin", "พันธบัตรยาว", "REITs"],
        []
    )

# PMI rules
if pmi < 50.0:
    add_signal(
        "PMI < 50 (หดตัว)",
        "Cyclicals แพ้, Safe haven เด่น",
        ["ทอง", "หุ้น Defensive", "Healthcare", "Utilities"],
        ["Cyclicals (Retail/Industrials)"]
    )
elif pmi >= 52.0:
    add_signal(
        "PMI > 52 (ขยายตัวแรง)",
        "Cyclicals/พลังงาน/โภคภัณฑ์เด่น",
        ["Industrials", "Energy", "EM equities", "Commodities"],
        []
    )

# Unemployment rules
if 3.0 <= unemp <= 3.5:
    add_signal(
        "ว่างงานต่ำ (3–3.5%)",
        "ตลาดแรงงานตึง → Fed ชะลอลดดอกเบี้ย",
        ["หุ้น Defensive", "ดอลลาร์", "พันธบัตรสั้น"],
        []
    )
elif unemp >= 4.5:
    add_signal(
        "ว่างงานสูง (>4.5%)",
        "เสี่ยงถดถอย → Fed เร่งผ่อน",
        ["ทอง", "Bitcoin", "พันธบัตรยาว", "REITs (เมื่อดอกเบี้ยลดจริง)"],
        []
    )

# DXY rules
if dxy >= 105.0:
    add_signal(
        "ดอลลาร์แข็ง (>105)",
        "กดดันทอง/คริปโต/EM; US assets ได้เปรียบ",
        ["หุ้นสหรัฐ Large Cap", "พันธบัตรสหรัฐ", "เงินสด USD"],
        ["ทอง", "Bitcoin", "EM equities"]
    )
elif dxy <= 100.0:
    add_signal(
        "ดอลลาร์อ่อน (<100)",
        "เงินไหลเข้า EM/ทอง/คริปโต",
        ["ทอง", "Bitcoin", "EM equities", "Commodities"],
        []
    )

# Fed Funds Rate
if fed_rate > 5.0:
    add_signal("Fed Rate >5% / ดอกเบี้ยสูง", "Historic risk of recession / เสี่ยงถดถอย", ["พันธบัตรสั้น", "หุ้น Defensive"], ["หุ้น Tech/Growth"])
elif fed_rate < 2.0:
    add_signal("Fed Rate <2% / ดอกเบี้ยต่ำ", "Stimulus mode / ภาวะกระตุ้นเศรษฐกิจ", ["หุ้น", "ทอง", "BTC"], [])

# Debt-to-GDP
if debt_gdp > 120:
    add_signal("Debt/GDP >120%", "Fiscal risk long-term / ความเสี่ยงการคลัง", ["ทอง", "BTC"], [])
elif debt_gdp < 80:
    add_signal("Debt/GDP <80%", "Healthy debt level / หนี้อยู่ในระดับปลอดภัย", ["หุ้น", "พันธบัตร"], [])

# M2
if m2 > 10:
    add_signal("M2 Growth >10%", "Liquidity boom / สภาพคล่องล้น", ["หุ้น", "ทอง", "BTC"], [])
elif m2 < 0:
    add_signal("M2 Negative", "Liquidity contraction / สภาพคล่องหด", ["เงินสด", "USD", "พันธบัตร"], [])

# Repo
if repo > 8:
    add_signal("Repo Spike >8%", "Funding stress / ตึงสภาพคล่อง", ["ทอง", "พันธบัตรสั้น"], ["หุ้น"])
    
# Margin Debt
if margin > 1000:
    add_signal("Margin Debt >1T", "Bubble risk / เสี่ยงฟองสบู่", [], ["หุ้นเก็งกำไร", "คริปโต"])
elif margin < 500:
    add_signal("Margin Debt <500B", "Low leverage / การกู้ต่ำ", ["ตลาดปลอดภัยขึ้น"], [])

# ---------- Show Signals ----------
st.subheader("📌 Signals Now / สัญญาณปัจจุบัน")
st.dataframe(pd.DataFrame(signals), use_container_width=True)

st.markdown("---")
st.subheader("📖 Historical Reference / อ้างอิงเชิงประวัติศาสตร์")
hist_rows = [
    ["Core PCE/CPI > 3%", "หุ้นกดดัน; ทอง/คริปโตบางช่วงบวก", "Defensive, พันธบัตรสั้น", ""],
    ["Core PCE/CPI ~2%", "Goldilocks", "หุ้น Growth/Tech, EM", ""],
    ["Core PCE/CPI < 1.5%", "เสี่ยงชะลอ, Fed ผ่อน", "พันธบัตรยาว, ทอง, REITs", ""],
    ["10Y > 4.5%", "Discount rate สูง", "Dividend/Defensive", ""],
    ["10Y < 3.5%", "หนุน risk-on และ bonds ยาว", "ทอง, BTC, REITs", ""],
    ["PMI < 50", "หดตัว", "Defensive, ทอง", ""],
    ["PMI > 52", "ขยายตัวแรง", "Cyclicals, Energy, EM", ""],
    ["Unemp > 4.5%", "เสี่ยงถดถอย", "Safe haven, Bonds ยาว", "บางครั้งต่ำมาก (3–3.5%) นานหลายปีโดยไม่ crash ทันที → ต้องดูควบคู่ Fed policy"],
    ["DXY > 105", "USD แข็ง", "US assets; ระวังทอง/BTC/EM", ""],
    ["DXY < 100", "USD อ่อน", "ทอง, BTC, EM, Commodities", ""],
    ["Fed Funds >5%", "Recession risk / เสี่ยงถดถอย", "หุ้น Defensive, พันธบัตรสั้น", ""],
    ["M2 Growth >10%", "Assets boom / สินทรัพย์บูม", "หุ้น, ทอง, BTC", ""],
    ["M2 <0%", "Liquidity crunch / สภาพคล่องหด", "เงินสด, USD", ""],
    ["Margin Debt Peak", "Often market top / มักตรงจุดสูงสุดตลาด", "Bubble assets", "ไม่มี threshold เด็ดขาด (US >120% ยังไม่ crash เพราะ USD เป็น reserve currency)"],
    ["Repo Spike >8%", "Funding crisis / ตึงสภาพคล่อง", "ทอง, พันธบัตรสั้น", ""]
]

hist_df = pd.DataFrame(hist_rows, columns=["Condition / เงื่อนไข", "Impact / ผลกระทบ", "Favored / เด่น", "Note / หมายเหตุ"])
st.dataframe(hist_df, use_container_width=True)

st.info("หมายเหตุ / Note: ความสัมพันธ์เป็นเชิงประวัติศาสตร์ ไม่ใช่การรับประกันอนาคต — โปรดพิจารณาสภาพคล่อง นโยบาย และภูมิรัฐศาสตร์ร่วมด้วย")
