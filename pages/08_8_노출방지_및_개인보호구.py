import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 8 - 노출방지 및 개인보호구", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    
    * {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    /* Streamlit 아이콘 폰트 복원 */
    [data-testid="stIconMaterial"],
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    
    .stTextInput > div > div > input { background-color: #f0f0f0; font-family: 'Nanum Gothic', sans-serif !important; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-family: 'Nanum Gothic', sans-serif !important; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 10px 0; font-weight: bold; }
    .material-name { color: #0066cc; font-weight: bold; margin-left: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>8. 노출방지 및 개인보호구</h2></div>', unsafe_allow_html=True)

if 'section3_data' not in st.session_state:
    st.warning("⚠️ 섹션 3의 구성성분 정보를 먼저 입력해주세요.")
    st.stop()

materials = []
for comp in st.session_state.get('section3_data', {}).get('components', []):
    if comp.get('물질명'):
        materials.append(comp['물질명'])

if not materials:
    st.warning("⚠️ 섹션 3에 등록된 물질이 없습니다.")
    st.stop()

if 'section8_data' not in st.session_state:
    st.session_state.section8_data = {
        '화학물질_노출기준': {}, 'ACGIH_규정': {}, '생물학적_노출기준': {}, '기타_노출기준': {},
        '공학적_관리': '공정격리, 국소배기를 사용하거나, 공기수준을 노출기준 이하로 조절하는 다른 공학적 관리를 하시오.\n이 물질을 저장하거나 사용하는 설비는 세안설비와 안전 샤워를 설치하시오.',
        '호흡기_보호': '방독마스크',
        '개인보호구': {
            '눈_보호': '적합한 접촉/노출 가능성이 있는 경우 한국산업안전보건공단 인증을 받은 보안경을 사용할 것.',
            '손_보호': '적합한 접촉/노출 가능성이 있는 경우 한국산업안전보건공단 인증을 받은 화학물질용 안전장갑을 사용할 것.',
            '신체_보호': '적합한 접촉/노출 가능성이 있는 경우 한국산업안전보건공단 인증을 받은 화학물질용 보호복 사용할 것.'
        }
    }

st.subheader("가. 화학물질의 노출기준, 생물학적 노출기준 등")

for title, key_suffix in [("국내규정", "국내규정_TWA"), ("ACGIH 규정", "ACGIH"), ("생물학적 노출기준", "생물학적"), ("기타 노출기준", "기타")]:
    st.markdown(f'<div class="subsection-header">{title}</div>', unsafe_allow_html=True)
    for i, material in enumerate(materials):
        if i > 0: st.markdown("---")
        st.markdown(f'<div class="material-name">{material}</div>', unsafe_allow_html=True)
        st.text_input(f"{material} - {title}", value="자료없음", key=f"{material}_{key_suffix}")

st.subheader("나. 적절한 공학적 관리")
st.text_area("공학적 관리 방법", value="공정격리, 국소배기를 사용하거나, 공기수준을 노출기준 이하로 조절하는 다른 공학적 관리를 하시오.\n이 물질을 저장하거나 사용하는 설비는 세안설비와 안전 샤워를 설치하시오.", height=100, key="engineering_control")

st.subheader("다. 개인보호구")
st.markdown("**호흡기 보호**")
col1, col2 = st.columns([1, 3])
with col1:
    respiratory_option = st.selectbox("마스크 종류 선택", ["방독마스크", "방진마스크"], key="respiratory_type", label_visibility="collapsed")
with col2:
    st.text_area("호흡기 보호", value=f"노출되는 물질의 물리화학적 특성에 맞는 한국산업안전보건공단의 인증을 필한 {respiratory_option}를 착용하시오", height=80, key="respiratory_protection_text", label_visibility="collapsed")

for key, default_value in {"눈 보호": "적합한 접촉/노출 가능성이 있는 경우 한국산업안전보건공단 인증을 받은 보안경을 사용할 것.", "손 보호": "적합한 접촉/노출 가능성이 있는 경우 한국산업안전보건공단 인증을 받은 화학물질용 안전장갑을 사용할 것.", "신체 보호": "적합한 접촉/노출 가능성이 있는 경우 한국산업안전보건공단 인증을 받은 화학물질용 보호복 사용할 것."}.items():
    st.markdown(f"**{key}**")
    st.text_area(key, value=default_value, height=80, key=f"protection_{key}", label_visibility="collapsed")

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 8 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 8이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("### 섹션 3에서 가져온 물질명:")
    for i, material in enumerate(materials, 1):
        st.write(f"{i}. {material}")
    st.json(st.session_state.section8_data)
