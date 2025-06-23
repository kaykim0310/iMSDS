import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 10 - 안정성 및 반응성",
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
st.markdown('<div class="section-header"><h2>10. 안정성 및 반응성</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section10_data' not in st.session_state:
    st.session_state.section10_data = {
        '가_화학적_안정성_및_유해_반응의_가능성': '',
        '나_피해야_할_조건': '',
        '다_피해야_할_물질': '',
        '라_분해시_생성되는_유해물질': ''
    }

# 가. 화학적 안정성 및 유해 반응의 가능성
st.markdown('<div class="subsection-header">가. 화학적 안정성 및 유해 반응의 가능성</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "화학적 안정성 및 유해 반응의 가능성",
    value=st.session_state.section10_data.get('가_화학적_안정성_및_유해_반응의_가능성', ''),
    height=150,
    placeholder="예: 상온상압에서 안정함\n격렬한 반응 가능성 없음\n중합 반응 없음",
    key="stability_reactivity",
    label_visibility="collapsed"
)
st.session_state.section10_data['가_화학적_안정성_및_유해_반응의_가능성'] = 가_내용

# 나. 피해야 할 조건
st.markdown('<div class="subsection-header">나. 피해야 할 조건</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "피해야 할 조건",
    value=st.session_state.section10_data.get('나_피해야_할_조건', ''),
    height=100,
    placeholder="예: 열, 스파크, 화염 등 점화원\n고온\n직사광선",
    key="conditions_to_avoid",
    label_visibility="collapsed"
)
st.session_state.section10_data['나_피해야_할_조건'] = 나_내용

# 다. 피해야 할 물질
st.markdown('<div class="subsection-header">다. 피해야 할 물질</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "피해야 할 물질",
    value=st.session_state.section10_data.get('다_피해야_할_물질', ''),
    height=100,
    placeholder="예: 강산화제\n강산\n강염기",
    key="materials_to_avoid",
    label_visibility="collapsed"
)
st.session_state.section10_data['다_피해야_할_물질'] = 다_내용

# 라. 분해시 생성되는 유해물질
st.markdown('<div class="subsection-header">라. 분해시 생성되는 유해물질</div>', unsafe_allow_html=True)

라_내용 = st.text_area(
    "분해시 생성되는 유해물질",
    value=st.session_state.section10_data.get('라_분해시_생성되는_유해물질', ''),
    height=100,
    placeholder="예: 열분해시 유독가스 발생 가능\n일산화탄소, 이산화탄소",
    key="hazardous_decomposition",
    label_visibility="collapsed"
)
st.session_state.section10_data['라_분해시_생성되는_유해물질'] = 라_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 10 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 10이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 10. 안정성 및 반응성")
    
    # 각 항목별로 내용 표시
    항목들 = [
        ("가. 화학적 안정성 및 유해 반응의 가능성", '가_화학적_안정성_및_유해_반응의_가능성'),
        ("나. 피해야 할 조건", '나_피해야_할_조건'),
        ("다. 피해야 할 물질", '다_피해야_할_물질'),
        ("라. 분해시 생성되는 유해물질", '라_분해시_생성되는_유해물질')
    ]
    
    for 제목, 키 in 항목들:
        내용 = st.session_state.section10_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
            st.write("")  # 빈 줄 추가
    
    # JSON 데이터
    st.write("### 원본 데이터")
    st.json(st.session_state.section10_data)