import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 6 - 누출 사고시 대처방법",
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
st.markdown('<div class="section-header"><h2>6. 누출 사고시 대처방법</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section6_data' not in st.session_state:
    st.session_state.section6_data = {
        '가_인체를_보호하기_위해_필요한_조치사항_및_보호구': '',
        '나_환경을_보호하기_위해_필요한_조치사항': '',
        '다_정화_또는_제거_방법': ''
    }

# 가. 인체를 보호하기 위해 필요한 조치사항 및 보호구
st.markdown('<div class="subsection-header">가. 인체를 보호하기 위해 필요한 조치사항 및 보호구</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "인체를 보호하기 위해 필요한 조치사항 및 보호구",
    value=st.session_state.section6_data.get('가_인체를_보호하기_위해_필요한_조치사항_및_보호구', ''),
    height=120,
    placeholder="예: 적절한 보호장비를 착용하지 않은 작업자는 누출지역 접근을 금할 것\n적절한 보호구를 착용할 것\n누출지역을 환기시킬 것",
    key="personal_precautions",
    label_visibility="collapsed"
)
st.session_state.section6_data['가_인체를_보호하기_위해_필요한_조치사항_및_보호구'] = 가_내용

# 나. 환경을 보호하기 위해 필요한 조치사항
st.markdown('<div class="subsection-header">나. 환경을 보호하기 위해 필요한 조치사항</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "환경을 보호하기 위해 필요한 조치사항",
    value=st.session_state.section6_data.get('나_환경을_보호하기_위해_필요한_조치사항', ''),
    height=120,
    placeholder="예: 하수구, 수계 또는 토양으로 유입되지 않도록 할 것\n대량 누출 시 관계기관에 연락할 것",
    key="environmental_precautions",
    label_visibility="collapsed"
)
st.session_state.section6_data['나_환경을_보호하기_위해_필요한_조치사항'] = 나_내용

# 다. 정화 또는 제거 방법
st.markdown('<div class="subsection-header">다. 정화 또는 제거 방법</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "정화 또는 제거 방법",
    value=st.session_state.section6_data.get('다_정화_또는_제거_방법', ''),
    height=120,
    placeholder="예: 누출물을 적절한 흡착제로 흡수시킬 것\n오염된 흡착제를 밀폐 용기에 담아 폐기할 것\n누출 지역을 물로 세척할 것",
    key="cleanup_methods",
    label_visibility="collapsed"
)
st.session_state.section6_data['다_정화_또는_제거_방법'] = 다_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 6 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 6이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 6. 누출 사고시 대처방법")

    항목들 = [
        ("가. 인체를 보호하기 위해 필요한 조치사항 및 보호구", '가_인체를_보호하기_위해_필요한_조치사항_및_보호구'),
        ("나. 환경을 보호하기 위해 필요한 조치사항", '나_환경을_보호하기_위해_필요한_조치사항'),
        ("다. 정화 또는 제거 방법", '다_정화_또는_제거_방법')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section6_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section6_data)
