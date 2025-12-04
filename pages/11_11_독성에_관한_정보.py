import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 11 - 독성에 관한 정보",
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
st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출_경로에_관한_정보': '',
        '나_건강_유해성_정보': '',
        '다_급성_독성_수치': '',
        '라_자극성_부식성_민감성': '',
        '마_만성_독성_및_발암성': ''
    }

# 가. 가능성이 높은 노출 경로에 관한 정보
st.markdown('<div class="subsection-header">가. 가능성이 높은 노출 경로에 관한 정보</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "가능성이 높은 노출 경로에 관한 정보",
    value=st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', ''),
    height=150,
    placeholder="예: 흡입, 피부접촉, 눈접촉, 경구",
    key="exposure_routes",
    label_visibility="collapsed"
)
st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = 가_내용

# 나. 건강 유해성 정보
st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "건강 유해성 정보",
    value=st.session_state.section11_data.get('나_건강_유해성_정보', ''),
    height=150,
    placeholder="예: 눈에 자극을 일으킴\n피부에 자극을 일으킴\n흡입시 호흡기 자극을 일으킬 수 있음",
    key="health_hazard_info",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보'] = 나_내용

# 다. 급성 독성 수치
st.markdown('<div class="subsection-header">다. 급성 독성 수치</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "급성 독성 수치",
    value=st.session_state.section11_data.get('다_급성_독성_수치', ''),
    height=150,
    placeholder="예: LD50 (경구, 랫드): >2000 mg/kg\nLD50 (경피, 토끼): >2000 mg/kg\nLC50 (흡입, 랫드): >5000 mg/m³",
    key="acute_toxicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['다_급성_독성_수치'] = 다_내용

# 라. 자극성/부식성/민감성
st.markdown('<div class="subsection-header">라. 자극성/부식성/민감성</div>', unsafe_allow_html=True)

라_내용 = st.text_area(
    "자극성/부식성/민감성",
    value=st.session_state.section11_data.get('라_자극성_부식성_민감성', ''),
    height=150,
    placeholder="예: 피부 자극성: 자료없음\n눈 자극성: 자료없음\n호흡기 자극성: 자료없음\n피부 민감성: 자료없음",
    key="irritation_corrosivity",
    label_visibility="collapsed"
)
st.session_state.section11_data['라_자극성_부식성_민감성'] = 라_내용

# 마. 만성 독성 및 발암성
st.markdown('<div class="subsection-header">마. 만성 독성 및 발암성</div>', unsafe_allow_html=True)

마_내용 = st.text_area(
    "만성 독성 및 발암성",
    value=st.session_state.section11_data.get('마_만성_독성_및_발암성', ''),
    height=150,
    placeholder="예: 발암성: 자료없음\n생식독성: 자료없음\n특정표적장기독성(1회노출): 자료없음\n특정표적장기독성(반복노출): 자료없음",
    key="chronic_toxicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['마_만성_독성_및_발암성'] = 마_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 11. 독성에 관한 정보")

    # 각 항목별로 내용 표시
    항목들 = [
        ("가. 가능성이 높은 노출 경로에 관한 정보", '가_가능성이_높은_노출_경로에_관한_정보'),
        ("나. 건강 유해성 정보", '나_건강_유해성_정보'),
        ("다. 급성 독성 수치", '다_급성_독성_수치'),
        ("라. 자극성/부식성/민감성", '라_자극성_부식성_민감성'),
        ("마. 만성 독성 및 발암성", '마_만성_독성_및_발암성')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section11_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")  # 빈 줄 추가

    # JSON 데이터
    st.write("### 원본 데이터")
    st.json(st.session_state.section11_data)
