import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib
import platform
import matplotlib.font_manager as fm

    import platform
if platform.system() == "Windows":
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == "Darwin":
    matplotlib.rcParams['font.family'] = 'AppleGothic'
else:
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# ASA 점수 매핑 및 설명
asa_explanation = {
    "I (건강한 환자)": "건강한 일반 환자",
    "II (경증 전신질환)": "경증의 전신질환이 있는 환자 (예: 잘 조절된 고혈압)",
    "III (중등도 전신질환)": "기능 제한이 있는 중등도의 전신질환 (예: 당뇨 + 심부전)",
    "IV (생명을 위협하는 질환)": "생명을 위협하는 중증 질환 동반"
}

def map_asa(asa):
    return {
        "I (건강한 환자)": 0.0,
        "II (경증 전신질환)": 1.0,
        "III (중등도 전신질환)": 2.0,
        "IV (생명을 위협하는 질환)": 3.0,
    }.get(asa, 0.0)

# 진단명 가중치 (예시)
def diagnosis_weight(diagnosis):
    return {
        "로봇 전립선절제술": 0.4,
        "로봇 자궁절제술": 0.6,
        "로봇 대장절제술": 1.0,
        "로봇 직장절제술": 1.1,
        "로봇 위절제술": 0.9,
        "로봇 갑상선절제술": 0.3,
        "로봇 신장절제술": 0.7,
        "로봇 폐엽절제술": 1.2,
        "로봇 방광절제술": 1.3,
        "로봇 췌장절제술": 1.4,
        "로봇 간절제술": 1.2,
        "로봇 식도절제술": 1.5,
        "기타": 0.5,
    }.get(diagnosis, 0.0)

# 논문 기반 위험 계산 (예: Bilimoria et al. 2013)
def calculate_risk(age, bmi, asa, diabetes, emergency, copd, dx):
    intercept = -5.8  # 논문 기반 예시값
    logit = (
        intercept +
        0.03 * age +
        0.05 * bmi +
        0.8 * diabetes +
        1.2 * emergency +
        0.9 * copd +
        0.7 * asa +
        0.6 * dx
    )
    odds = math.exp(logit)
    return round(odds / (1 + odds) * 100, 1)  # % 확률 반환

# 합병증별 결과표
def complication_table(base_score):
    complication_base = {
        "중대한 합병증": (5.5, base_score),
        "전체 합병증": (7.5, base_score * 1.1),
        "폐렴": (0.1, base_score * 0.02),
        "심장 합병증": (0.1, base_score * 0.02),
        "정맥 혈전색전증": (0.7, base_score * 0.05),
        "패혈증": (0.5, base_score * 0.03),
        "수술 부위 감염": (4.9, base_score * 0.6),
        "요로 감염": (2.0, base_score * 0.25),
        "신부전": (0.3, base_score * 0.02),
        "재입원": (3.7, base_score * 0.4),
        "재수술": (1.7, base_score * 0.3),
        "사망": (0.1, base_score * 0.01)
    }
    rows = []
    for comp, (avg, risk) in complication_base.items():
        assessment = "평균 이하" if risk < avg else "평균 초과" if risk > avg else "평균과 동일"
        rows.append([comp, round(risk, 2), avg, assessment])
    return pd.DataFrame(rows, columns=["합병증", "예측 위험도 (%)", "평균 위험도 (%)", "비교 결과"])

# Streamlit UI 시작
st.title("ACS NSQIP 기반 수술 합병증 위험 예측기")

age = st.number_input("나이", min_value=18, max_value=100, value=50)
height_cm = st.number_input("키 (cm)", value=160)
weight_kg = st.number_input("몸무게 (kg)", value=60)
bmi = weight_kg / ((height_cm / 100) ** 2)
st.write(f"계산된 BMI: {bmi:.2f}")

asa_class = st.selectbox("ASA 등급", list(asa_explanation.keys()))
st.caption(f"💡 설명: {asa_explanation[asa_class]}")

has_diabetes = st.checkbox("당뇨병 여부")
has_copd = st.checkbox("만성폐질환 (COPD) 여부")
is_emergency = st.checkbox("응급 수술 여부")
diagnosis = st.selectbox("진단명", [
    "로봇 전립선절제술", "로봇 자궁절제술", "로봇 대장절제술", "로봇 직장절제술", "로봇 위절제술",
    "로봇 갑상선절제술", "로봇 신장절제술", "로봇 폐엽절제술", "로봇 방광절제술", "로봇 췌장절제술",
    "로봇 간절제술", "로봇 식도절제술", "기타"])

if st.button("예측하기"):
    asa_score = map_asa(asa_class)
    dx_score = diagnosis_weight(diagnosis)
    calc_diabetes = 1 if has_diabetes else 0
    calc_copd = 1 if has_copd else 0
    calc_emergency = 1 if is_emergency else 0

    base_score = calculate_risk(
        age=age,
        bmi=bmi,
        asa=asa_score,
        diabetes=calc_diabetes,
        emergency=calc_emergency,
        copd=calc_copd,
        dx=dx_score
    )

    result_df = complication_table(base_score)
    st.dataframe(result_df, use_container_width=True)
    st.success("예측 완료! 아래 결과표를 확인하세요.")

    # 시각화 추가
    st.subheader("📊 예측 위험도 시각화")
    fig, ax = plt.subplots()
    ax.barh(result_df["합병증"], result_df["예측 위험도 (%)"])
    ax.set_xlabel("예측 위험도 (%)", fontsize=12)
    ax.set_title("합병증별 예측 위험도", fontsize=14)
    ax.tick_params(labelsize=10)
    st.pyplot(fig)
