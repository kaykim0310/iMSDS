import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 4 - 응급조치 요령",
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
st.markdown('<div class="section-header"><h2>4. 응급조치 요령</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section4_data' not in st.session_state:
    st.session_state.section4_data = {
        '가_눈에_들어갔을_때': '',
        '나_피부에_접촉했을_때': '',
        '다_흡입했을_때': '',
        '라_먹었을_때': '',
        '마_기타_의사의_주의사항': ''
    }

# 가. 눈에 들어갔을 때
st.markdown('<div class="subsection-header">가. 눈에 들어갔을 때</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "눈에 들어갔을 때",
    value=st.session_state.section4_data.get('가_눈에_들어갔을_때', ''),
    height=100,
    placeholder="예: 즉시 다량의 물로 15분 이상 씻어내고 의사의 진료를 받을 것\n콘택트렌즈를 착용하고 있는 경우 가능하면 렌즈를 제거할 것",
    key="eye_contact",
    label_visibility="collapsed"
)
st.session_state.section4_data['가_눈에_들어갔을_때'] = 가_내용

# 나. 피부에 접촉했을 때
st.markdown('<div class="subsection-header">나. 피부에 접촉했을 때</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "피부에 접촉했을 때",
    value=st.session_state.section4_data.get('나_피부에_접촉했을_때', ''),
    height=100,
    placeholder="예: 오염된 의복을 벗기고 피부를 물과 비누로 씻을 것\n피부 자극이 지속되면 의사의 진료를 받을 것",
    key="skin_contact",
    label_visibility="collapsed"
)
st.session_state.section4_data['나_피부에_접촉했을_때'] = 나_내용

# 다. 흡입했을 때
st.markdown('<div class="subsection-header">다. 흡입했을 때</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "흡입했을 때",
    value=st.session_state.section4_data.get('다_흡입했을_때', ''),
    height=100,
    placeholder="예: 신선한 공기가 있는 곳으로 옮기고 호흡하기 쉬운 자세로 안정을 취할 것\n호흡 곤란 시 산소를 공급하고 의사의 진료를 받을 것",
    key="inhalation",
    label_visibility="collapsed"
)
st.session_state.section4_data['다_흡입했을_때'] = 다_내용

# 라. 먹었을 때
st.markdown('<div class="subsection-header">라. 먹었을 때</div>', unsafe_allow_html=True)

라_내용 = st.text_area(
    "먹었을 때",
    value=st.session_state.section4_data.get('라_먹었을_때', ''),
    height=100,
    placeholder="예: 입을 씻어내고 즉시 의사의 진료를 받을 것\n의식이 없는 경우 절대로 구토를 유발하지 말 것",
    key="ingestion",
    label_visibility="collapsed"
)
st.session_state.section4_data['라_먹었을_때'] = 라_내용

# 마. 기타 의사의 주의사항
st.markdown('<div class="subsection-header">마. 기타 의사의 주의사항</div>', unsafe_allow_html=True)

마_내용 = st.text_area(
    "기타 의사의 주의사항",
    value=st.session_state.section4_data.get('마_기타_의사의_주의사항', ''),
    height=100,
    placeholder="예: 증상에 따라 치료할 것\n이 제품의 물질안전보건자료를 의사에게 제시할 것",
    key="physician_notes",
    label_visibility="collapsed"
)
st.session_state.section4_data['마_기타_의사의_주의사항'] = 마_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 4 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 4가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 4. 응급조치 요령")

    항목들 = [
        ("가. 눈에 들어갔을 때", '가_눈에_들어갔을_때'),
        ("나. 피부에 접촉했을 때", '나_피부에_접촉했을_때'),
        ("다. 흡입했을 때", '다_흡입했을_때'),
        ("라. 먹었을 때", '라_먹었을_때'),
        ("마. 기타 의사의 주의사항", '마_기타_의사의_주의사항')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section4_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section4_data)
