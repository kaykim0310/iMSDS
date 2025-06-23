import streamlit as st
import pandas as pd
from datetime import datetime, date

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 16 - 기타 참고사항",
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
    .reference-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        border: 1px solid #dee2e6;
    }
    .date-table {
        margin: 20px 0;
    }
    .note-text {
        font-size: 0.9em;
        color: #666;
        line-height: 1.6;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>16. 기타 참고사항</h2></div>', unsafe_allow_html=True)

# 세션 1에서 날짜 정보 가져오기
initial_date = date.today()
revision_date = date.today()

if 'section1_data' in st.session_state:
    initial_date = st.session_state.section1_data.get('initial_date', date.today())
    revision_date = st.session_state.section1_data.get('revision_date', date.today())

# 세션 상태 초기화
if 'section16_data' not in st.session_state:
    st.session_state.section16_data = {
        '자료의_출처': [
            "본 제품의 기존 영문 MSDS.",
            "고용노동부, 화학물질의 분류·표시 및 물질안전보건자료에 관한 기준.",
            "산업안전보건법, 화학물질관리법, 위험물안전관리법, 환경관련 법령.",
            "Guideline for Globally Harmonized System of Classification and Labelling of Chemicals (GHS)",
            "OECD SIDS (UNEP)",
            "EU European Chemicals Bureau (ECB): International Uniform Chemical Information Database (IUCLID)",
            "European Union Risk Assessment Report (European Commission) (EU-RAR)",
            "Hazardous Substances Data Bank (HSDB)",
            "WHO/IPCS : International Chemical Safety Cards (ICSC)",
            "National Library of Medicine (NLM) DB.",
            "IARC(International Agency for Research on Cancer) Monographs.",
            "일본, National Institute of Technology and Evaluation (NITE) 자료.",
            "Registry of Toxic Effects of Chemical Substances (RTECS)",
            "미국, NFPA 704 Standard System for the Identification of the Hazards of Materials for Emergency Response.",
            "유럽연합, European Chemicals Agency(ECHA)"
        ],
        '최초작성일': initial_date,
        '개정횟수_및_최종_개정일자': {
            '개정횟수': '0 회',
            '최종개정일자': revision_date
        },
        '기타': '',
        '참고사항': [
            "본 MSDS는 산업안전보건법 제 110조 및 고용노동부고시 제2020-130호 (화학물질의 분류 표시 및 물질안전보건자료에 관한 기준)에 근거하여 작성된 것으로, 근로자의 건강 보호를 위하여 제공하는 자료입니다. 또한 지정된 제품에만 관련되는 것이며, 다른 제품이나 공정과 혼합하여 사용시는 유효성이 없습니다. 본 정보는 사용자의 주의 및 검토가 요구되며, 사용 전 다음 상품이 적용되는 지역의 독성 정보 및 법적 절차를 확인하기 바랍니다.",
            "본 MSDS를 사전 허가 없이 상업적 목적으로 재판매, 한글 이외의 제3국어 번역은 저작권에 관련된 국내외 법에 의해 처벌을 받거나 소송을 제기 당할 수 있음을 주지하시기 바랍니다."
        ]
    }

# 가. 자료의 출처
st.markdown('<div class="subsection-header">가. 자료의 출처</div>', unsafe_allow_html=True)

# 자료 출처 목록 표시
st.markdown('<div class="reference-box">', unsafe_allow_html=True)
for idx, source in enumerate(st.session_state.section16_data['자료의_출처'], 1):
    st.write(f"{idx}. {source}")
st.markdown('</div>', unsafe_allow_html=True)

# 나. 최초작성일
st.markdown('<div class="subsection-header">나. 최초작성일</div>', unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    st.write(initial_date.strftime('%Y-%m-%d'))

# 다. 개정횟수 및 최종 개정일자
st.markdown('<div class="subsection-header">다. 개정횟수 및 최종 개정일자</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    st.markdown("**개정횟수**")
    개정횟수 = st.text_input(
        "개정횟수",
        value=st.session_state.section16_data['개정횟수_및_최종_개정일자']['개정횟수'],
        key="revision_count",
        label_visibility="collapsed"
    )
    st.session_state.section16_data['개정횟수_및_최종_개정일자']['개정횟수'] = 개정횟수

with col3:
    st.markdown("**최종개정일자**")
    st.write(revision_date.strftime('%Y-%m-%d'))

# 라. 기타
st.markdown('<div class="subsection-header">라. 기타</div>', unsafe_allow_html=True)
기타_내용 = st.text_area(
    "기타 사항",
    value=st.session_state.section16_data.get('기타', ''),
    height=100,
    placeholder="추가 참고사항이 있으면 입력하세요",
    key="other_info",
    label_visibility="collapsed"
)
st.session_state.section16_data['기타'] = 기타_내용

# 참고사항 (고정 텍스트)
st.markdown("---")
st.markdown("### 📌 참고사항")

for note in st.session_state.section16_data['참고사항']:
    st.markdown(f'<p class="note-text">※ {note}</p>', unsafe_allow_html=True)

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 16 저장", type="primary", use_container_width=True):
        # 섹션 1의 날짜 정보 업데이트
        st.session_state.section16_data['최초작성일'] = initial_date
        st.session_state.section16_data['개정횟수_및_최종_개정일자']['최종개정일자'] = revision_date
        
        st.success("✅ 섹션 16이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 16. 기타 참고사항")
    
    st.write("**가. 자료의 출처**")
    for idx, source in enumerate(st.session_state.section16_data['자료의_출처'], 1):
        st.write(f"{idx}. {source}")
    
    st.write(f"\n**나. 최초작성일**: {st.session_state.section16_data['최초작성일']}")
    
    st.write(f"\n**다. 개정횟수 및 최종 개정일자**")
    st.write(f"- 개정횟수: {st.session_state.section16_data['개정횟수_및_최종_개정일자']['개정횟수']}")
    st.write(f"- 최종개정일자: {st.session_state.section16_data['개정횟수_및_최종_개정일자']['최종개정일자']}")
    
    if st.session_state.section16_data.get('기타'):
        st.write(f"\n**라. 기타**")
        st.write(st.session_state.section16_data['기타'])
    
    # JSON 데이터
    st.write("\n### 원본 데이터")
    st.json(st.session_state.section16_data)