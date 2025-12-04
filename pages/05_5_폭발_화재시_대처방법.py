import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 5 - 폭발·화재시 대처방법",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 스타일 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');

    * {
        font-family: 'Nanum Gothic', sans-serif !important;
    }

    .stTextInput > div > div > input {
        background-color: #f0f0f0;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #f0f0f0;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .section-header {
        background-color: #d3e3f3;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .subsection-header {
        background-color: #e8f0f7;
        padding: 8px;
        border-radius: 3px;
        margin: 15px 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>5. 폭발·화재시 대처방법</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section5_data' not in st.session_state:
    st.session_state.section5_data = {
        '가_적절한_소화제': '',
        '나_화학물질로부터_생기는_특정_유해성': '',
        '다_화재_진압_시_착용할_보호구_및_예방조치': ''
    }

# 가. 적절한(부적절한) 소화제
st.markdown('<div class="subsection-header">가. 적절한(부적절한) 소화제</div>', unsafe_allow_html=True)

st.write("**적절한 소화제**")
적절한_소화제 = st.text_area(
    "적절한 소화제",
    value=st.session_state.section5_data.get('적절한_소화제', ''),
    height=80,
    placeholder="예: 이산화탄소, 분말소화제, 포말소화제, 물분무",
    key="suitable_extinguishing",
    label_visibility="collapsed"
)

st.write("**부적절한 소화제**")
부적절한_소화제 = st.text_area(
    "부적절한 소화제",
    value=st.session_state.section5_data.get('부적절한_소화제', ''),
    height=80,
    placeholder="예: 직사 주수",
    key="unsuitable_extinguishing",
    label_visibility="collapsed"
)

st.session_state.section5_data['가_적절한_소화제'] = f"적절한 소화제: {적절한_소화제}\n부적절한 소화제: {부적절한_소화제}"

# 나. 화학물질로부터 생기는 특정 유해성
st.markdown('<div class="subsection-header">나. 화학물질로부터 생기는 특정 유해성</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "화학물질로부터 생기는 특정 유해성",
    value=st.session_state.section5_data.get('나_화학물질로부터_생기는_특정_유해성', ''),
    height=100,
    placeholder="예: 연소 시 유독가스 발생 가능\n밀폐된 용기는 열에 의해 폭발할 수 있음",
    key="specific_hazards",
    label_visibility="collapsed"
)
st.session_state.section5_data['나_화학물질로부터_생기는_특정_유해성'] = 나_내용

# 다. 화재 진압 시 착용할 보호구 및 예방조치
st.markdown('<div class="subsection-header">다. 화재 진압 시 착용할 보호구 및 예방조치</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "화재 진압 시 착용할 보호구 및 예방조치",
    value=st.session_state.section5_data.get('다_화재_진압_시_착용할_보호구_및_예방조치', ''),
    height=100,
    placeholder="예: 자급식 공기호흡기와 완전한 보호복을 착용할 것\n화재 지역에서 용기를 멀리 이동시킬 것",
    key="firefighter_protection",
    label_visibility="collapsed"
)
st.session_state.section5_data['다_화재_진압_시_착용할_보호구_및_예방조치'] = 다_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 5 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 5가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 5. 폭발·화재시 대처방법")

    항목들 = [
        ("가. 적절한(부적절한) 소화제", '가_적절한_소화제'),
        ("나. 화학물질로부터 생기는 특정 유해성", '나_화학물질로부터_생기는_특정_유해성'),
        ("다. 화재 진압 시 착용할 보호구 및 예방조치", '다_화재_진압_시_착용할_보호구_및_예방조치')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section5_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section5_data)
