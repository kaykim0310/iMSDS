import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 5 - 폭발·화재시 대처방법", layout="wide", initial_sidebar_state="collapsed")

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
    .stTextArea > div > div > textarea { background-color: #f0f0f0; font-family: 'Nanum Gothic', sans-serif !important; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-family: 'Nanum Gothic', sans-serif !important; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>5. 폭발·화재시 대처방법</h2></div>', unsafe_allow_html=True)

if 'section5_data' not in st.session_state:
    st.session_state.section5_data = {
        '가_적절한_소화제': '', '나_화학물질로부터_생기는_특정_유해성': '',
        '다_화재_진압_시_착용할_보호구_및_예방조치': ''
    }

st.markdown('<div class="subsection-header">가. 적절한(부적절한) 소화제</div>', unsafe_allow_html=True)
st.write("**적절한 소화제**")
적절한_소화제 = st.text_area("적절한 소화제", value=st.session_state.section5_data.get('적절한_소화제', ''), height=80, placeholder="예: 이산화탄소, 분말소화제, 포말소화제, 물분무", key="suitable_extinguishing", label_visibility="collapsed")
st.write("**부적절한 소화제**")
부적절한_소화제 = st.text_area("부적절한 소화제", value=st.session_state.section5_data.get('부적절한_소화제', ''), height=80, placeholder="예: 직사 주수", key="unsuitable_extinguishing", label_visibility="collapsed")
st.session_state.section5_data['가_적절한_소화제'] = f"적절한 소화제: {적절한_소화제}\n부적절한 소화제: {부적절한_소화제}"

st.markdown('<div class="subsection-header">나. 화학물질로부터 생기는 특정 유해성</div>', unsafe_allow_html=True)
나_내용 = st.text_area("특정 유해성", value=st.session_state.section5_data.get('나_화학물질로부터_생기는_특정_유해성', ''), height=100, placeholder="예: 연소 시 유독가스 발생 가능", key="specific_hazards", label_visibility="collapsed")
st.session_state.section5_data['나_화학물질로부터_생기는_특정_유해성'] = 나_내용

st.markdown('<div class="subsection-header">다. 화재 진압 시 착용할 보호구 및 예방조치</div>', unsafe_allow_html=True)
다_내용 = st.text_area("보호구 및 예방조치", value=st.session_state.section5_data.get('다_화재_진압_시_착용할_보호구_및_예방조치', ''), height=100, placeholder="예: 자급식 공기호흡기와 완전한 보호복을 착용할 것", key="firefighter_protection", label_visibility="collapsed")
st.session_state.section5_data['다_화재_진압_시_착용할_보호구_및_예방조치'] = 다_내용

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 5 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 5가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for 제목, 키 in [("가. 적절한(부적절한) 소화제", '가_적절한_소화제'), ("나. 화학물질로부터 생기는 특정 유해성", '나_화학물질로부터_생기는_특정_유해성'), ("다. 화재 진압 시 착용할 보호구 및 예방조치", '다_화재_진압_시_착용할_보호구_및_예방조치')]:
        내용 = st.session_state.section5_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
    st.json(st.session_state.section5_data)
