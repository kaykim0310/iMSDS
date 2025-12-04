import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 12 - 환경에 미치는 영향",
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
st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section12_data' not in st.session_state:
    st.session_state.section12_data = {
        '가_수생_환경_유해성': '',
        '나_잔류성_및_분해성': '',
        '다_생물_농축성': '',
        '라_토양_이동성': '',
        '마_기타_유해_영향': ''
    }

# 가. 수생/환경 유해성
st.markdown('<div class="subsection-header">가. 수생/환경 유해성</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "수생/환경 유해성",
    value=st.session_state.section12_data.get('가_수생_환경_유해성', ''),
    height=150,
    placeholder="예: 어류 LC50: 자료없음\n물벼룩 EC50: 자료없음\n조류 EC50: 자료없음",
    key="aquatic_toxicity",
    label_visibility="collapsed"
)
st.session_state.section12_data['가_수생_환경_유해성'] = 가_내용

# 나. 잔류성 및 분해성
st.markdown('<div class="subsection-header">나. 잔류성 및 분해성</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "잔류성 및 분해성",
    value=st.session_state.section12_data.get('나_잔류성_및_분해성', ''),
    height=150,
    placeholder="예: 생분해성: 자료없음\n비생물적 분해: 자료없음",
    key="persistence_degradability",
    label_visibility="collapsed"
)
st.session_state.section12_data['나_잔류성_및_분해성'] = 나_내용

# 다. 생물 농축성
st.markdown('<div class="subsection-header">다. 생물 농축성</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "생물 농축성",
    value=st.session_state.section12_data.get('다_생물_농축성', ''),
    height=150,
    placeholder="예: 생물농축계수(BCF): 자료없음\nlog Kow: 자료없음",
    key="bioaccumulation",
    label_visibility="collapsed"
)
st.session_state.section12_data['다_생물_농축성'] = 다_내용

# 라. 토양 이동성
st.markdown('<div class="subsection-header">라. 토양 이동성</div>', unsafe_allow_html=True)

라_내용 = st.text_area(
    "토양 이동성",
    value=st.session_state.section12_data.get('라_토양_이동성', ''),
    height=150,
    placeholder="예: 토양 흡착 계수(Koc): 자료없음\n이동성: 자료없음",
    key="soil_mobility",
    label_visibility="collapsed"
)
st.session_state.section12_data['라_토양_이동성'] = 라_내용

# 마. 기타 유해 영향
st.markdown('<div class="subsection-header">마. 기타 유해 영향</div>', unsafe_allow_html=True)

마_내용 = st.text_area(
    "기타 유해 영향",
    value=st.session_state.section12_data.get('마_기타_유해_영향', ''),
    height=150,
    placeholder="예: 오존층 파괴 물질: 해당없음\n지구 온난화 물질: 해당없음",
    key="other_adverse_effects",
    label_visibility="collapsed"
)
st.session_state.section12_data['마_기타_유해_영향'] = 마_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 12 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 12이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 12. 환경에 미치는 영향")

    # 각 항목별로 내용 표시
    항목들 = [
        ("가. 수생/환경 유해성", '가_수생_환경_유해성'),
        ("나. 잔류성 및 분해성", '나_잔류성_및_분해성'),
        ("다. 생물 농축성", '다_생물_농축성'),
        ("라. 토양 이동성", '라_토양_이동성'),
        ("마. 기타 유해 영향", '마_기타_유해_영향')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section12_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")  # 빈 줄 추가

    # JSON 데이터
    st.write("### 원본 데이터")
    st.json(st.session_state.section12_data)
