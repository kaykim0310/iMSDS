import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 7 - 취급 및 저장방법",
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
st.markdown('<div class="section-header"><h2>7. 취급 및 저장방법</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section7_data' not in st.session_state:
    st.session_state.section7_data = {
        '가_안전취급요령': '',
        '나_안전한_저장방법': ''
    }

# 가. 안전취급요령
st.markdown('<div class="subsection-header">가. 안전취급요령</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "안전취급요령",
    value=st.session_state.section7_data.get('가_안전취급요령', ''),
    height=150,
    placeholder="예: 모든 안전주의사항을 읽고 이해하기 전에는 취급하지 말 것\n취급 후에는 손을 철저히 씻을 것\n사용 시 음식을 먹거나 마시거나 흡연하지 말 것\n보호장갑/보호의/보안경/안면보호구를 착용할 것",
    key="handling_precautions",
    label_visibility="collapsed"
)
st.session_state.section7_data['가_안전취급요령'] = 가_내용

# 나. 안전한 저장방법 (피해야 할 조건을 포함함)
st.markdown('<div class="subsection-header">나. 안전한 저장방법 (피해야 할 조건을 포함함)</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "안전한 저장방법",
    value=st.session_state.section7_data.get('나_안전한_저장방법', ''),
    height=150,
    placeholder="예: 용기를 단단히 밀폐하여 환기가 잘 되는 곳에 저장할 것\n직사광선을 피하고 서늘한 곳에 보관할 것\n열, 스파크, 화염, 고온으로부터 멀리할 것\n혼합금지 물질과 분리하여 저장할 것",
    key="storage_conditions",
    label_visibility="collapsed"
)
st.session_state.section7_data['나_안전한_저장방법'] = 나_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 7 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 7이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 7. 취급 및 저장방법")

    항목들 = [
        ("가. 안전취급요령", '가_안전취급요령'),
        ("나. 안전한 저장방법 (피해야 할 조건을 포함함)", '나_안전한_저장방법')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section7_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section7_data)
