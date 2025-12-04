import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 2 - 유해성·위험성",
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
st.markdown('<div class="section-header"><h2>2. 유해성·위험성</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section2_data' not in st.session_state:
    st.session_state.section2_data = {
        '가_유해성_위험성_분류': '',
        '나_예방조치문구를_포함한_경고표지_항목': '',
        '다_유해성_위험성_분류기준에_포함되지_않는_기타_유해성_위험성': ''
    }

# 가. 유해성·위험성 분류
st.markdown('<div class="subsection-header">가. 유해성·위험성 분류</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "유해성·위험성 분류",
    value=st.session_state.section2_data.get('가_유해성_위험성_분류', ''),
    height=150,
    placeholder="예: 인화성 액체 구분 3\n피부 자극성 구분 2\n심한 눈 손상/자극성 구분 2",
    key="hazard_classification",
    label_visibility="collapsed"
)
st.session_state.section2_data['가_유해성_위험성_분류'] = 가_내용

# 나. 예방조치문구를 포함한 경고표지 항목
st.markdown('<div class="subsection-header">나. 예방조치문구를 포함한 경고표지 항목</div>', unsafe_allow_html=True)

st.write("**그림문자**")
그림문자 = st.text_input(
    "그림문자",
    value=st.session_state.section2_data.get('그림문자', ''),
    placeholder="예: 화염, 느낌표",
    key="pictogram",
    label_visibility="collapsed"
)

st.write("**신호어**")
신호어 = st.text_input(
    "신호어",
    value=st.session_state.section2_data.get('신호어', ''),
    placeholder="예: 경고, 위험",
    key="signal_word",
    label_visibility="collapsed"
)

st.write("**유해·위험 문구**")
유해위험문구 = st.text_area(
    "유해·위험 문구",
    value=st.session_state.section2_data.get('유해위험문구', ''),
    height=100,
    placeholder="예: H226 인화성 액체 및 증기\nH315 피부에 자극을 일으킴",
    key="hazard_statements",
    label_visibility="collapsed"
)

st.write("**예방조치문구**")
예방조치문구 = st.text_area(
    "예방조치문구",
    value=st.session_state.section2_data.get('예방조치문구', ''),
    height=150,
    placeholder="예: P210 열·스파크·화염·고온으로부터 멀리하시오\nP280 보호장갑/보호의/보안경/안면보호구를 착용하시오",
    key="precautionary_statements",
    label_visibility="collapsed"
)

st.session_state.section2_data['나_예방조치문구를_포함한_경고표지_항목'] = f"그림문자: {그림문자}\n신호어: {신호어}\n유해·위험 문구:\n{유해위험문구}\n예방조치문구:\n{예방조치문구}"

# 다. 유해성·위험성 분류기준에 포함되지 않는 기타 유해성·위험성
st.markdown('<div class="subsection-header">다. 유해성·위험성 분류기준에 포함되지 않는 기타 유해성·위험성</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "기타 유해성·위험성",
    value=st.session_state.section2_data.get('다_유해성_위험성_분류기준에_포함되지_않는_기타_유해성_위험성', ''),
    height=100,
    placeholder="예: 자료없음",
    key="other_hazards",
    label_visibility="collapsed"
)
st.session_state.section2_data['다_유해성_위험성_분류기준에_포함되지_않는_기타_유해성_위험성'] = 다_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 2 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 2가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 2. 유해성·위험성")

    항목들 = [
        ("가. 유해성·위험성 분류", '가_유해성_위험성_분류'),
        ("나. 예방조치문구를 포함한 경고표지 항목", '나_예방조치문구를_포함한_경고표지_항목'),
        ("다. 유해성·위험성 분류기준에 포함되지 않는 기타 유해성·위험성", '다_유해성_위험성_분류기준에_포함되지_않는_기타_유해성_위험성')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section2_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section2_data)
