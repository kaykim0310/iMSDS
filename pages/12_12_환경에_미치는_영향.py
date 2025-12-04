import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# utils 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.chemical_data_fetcher import ChemicalDataFetcher
    FETCHER_AVAILABLE = True
except ImportError:
    FETCHER_AVAILABLE = False

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

    .stTextInput > div > div > input,
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
    .sub-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 15px;
    }
    .fetch-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #b8d4e3;
        margin-bottom: 20px;
    }
    .eco-warning {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section12_data' not in st.session_state:
    st.session_state.section12_data = {
        '가_수생생태독성': {
            '어류': {'값': '', '출처': ''},
            '갑각류': {'값': '', '출처': ''},
            '조류': {'값': '', '출처': ''}
        },
        '나_잔류성_분해성': {'값': '', '출처': ''},
        '다_생물농축성': {'값': '', '출처': ''},
        '라_토양이동성': {'값': '', '출처': ''},
        '마_유해성_평가결과': {'값': '', '출처': ''},
        '바_기타유해영향': {'값': '', '출처': ''},
        '오존층유해성': {'값': '', '출처': ''},
        '기타정보': []
    }

# ===== 외부 데이터 가져오기 섹션 =====
st.markdown("### 외부 데이터베이스에서 가져오기")
st.markdown('<div class="fetch-box">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "CAS 번호 또는 화학물질명",
        placeholder="예: 71-43-2 (벤젠) 또는 Benzene",
        key="search_query_12"
    )

with col2:
    search_type = st.selectbox(
        "검색 유형",
        options=['cas', 'name'],
        format_func=lambda x: 'CAS 번호' if x == 'cas' else '화학물질명',
        key="search_type_12"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_button = st.button("데이터 가져오기", type="primary", key="fetch_btn_12")

if fetch_button and search_query:
    if FETCHER_AVAILABLE:
        with st.spinner("PubChem에서 환경 영향 데이터를 가져오는 중..."):
            try:
                fetcher = ChemicalDataFetcher()
                data = fetcher.get_section12_data(search_query, search_type)

                if data:
                    st.success("데이터를 성공적으로 가져왔습니다!")

                    updated_count = 0

                    # 수생생태독성
                    if data.get('수생생태독성'):
                        for species in ['어류', '갑각류', '조류']:
                            if data['수생생태독성'].get(species):
                                st.session_state.section12_data['가_수생생태독성'][species]['값'] = data['수생생태독성'][species]
                                st.session_state.section12_data['가_수생생태독성'][species]['출처'] = 'PubChem'
                                updated_count += 1

                    # 기타 환경 정보 매핑
                    eco_mapping = {
                        '잔류성_분해성': '나_잔류성_분해성',
                        '생물농축성': '다_생물농축성',
                        '토양이동성': '라_토양이동성',
                        '오존층유해성': '오존층유해성'
                    }

                    for src_key, dest_key in eco_mapping.items():
                        if data.get(src_key):
                            st.session_state.section12_data[dest_key]['값'] = data[src_key]
                            st.session_state.section12_data[dest_key]['출처'] = 'PubChem'
                            updated_count += 1

                    # 기타 유해 영향
                    if data.get('기타유해영향'):
                        st.session_state.section12_data['기타정보'] = data['기타유해영향'][:5]

                    st.info(f"{updated_count}개 항목이 업데이트되었습니다.")
                    st.rerun()
                else:
                    st.warning("해당 물질의 환경 영향 데이터를 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"데이터 가져오기 실패: {str(e)}")
    else:
        st.error("데이터 가져오기 모듈을 불러올 수 없습니다.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
> **데이터 소스 안내**
> - **PubChem**: 수생독성(LC50, EC50), 생분해성, BCF 등 환경 데이터 제공
> - **eChemPortal**: OECD 화학물질 환경 영향 데이터 ([echemportal.org](https://www.echemportal.org))
> - **KOSHA MSDS**: 국내 환경 규제 정보 ([공공데이터포털](https://www.data.go.kr/data/15001197/openapi.do))
""")

st.markdown("---")

# ===== 환경 영향 정보 입력 섹션 =====
st.markdown("### 환경에 미치는 영향")

# 가. 수생 생태독성
st.markdown('<div class="sub-section">', unsafe_allow_html=True)
st.markdown("#### 가. 수생 생태독성")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**어류 (LC50/EC50)**")
    어류_값 = st.text_input(
        "어류 독성",
        value=st.session_state.section12_data['가_수생생태독성']['어류'].get('값', ''),
        placeholder="예: LC50 = 5.3 mg/L (96hr, 무지개송어)",
        key="fish_value",
        label_visibility="collapsed"
    )
    어류_출처 = st.text_input(
        "어류 출처",
        value=st.session_state.section12_data['가_수생생태독성']['어류'].get('출처', ''),
        placeholder="출처",
        key="fish_source",
        label_visibility="collapsed"
    )
    st.session_state.section12_data['가_수생생태독성']['어류'] = {'값': 어류_값, '출처': 어류_출처}

with col2:
    st.markdown("**갑각류 (LC50/EC50)**")
    갑각류_값 = st.text_input(
        "갑각류 독성",
        value=st.session_state.section12_data['가_수생생태독성']['갑각류'].get('값', ''),
        placeholder="예: EC50 = 10 mg/L (48hr, 물벼룩)",
        key="crustacean_value",
        label_visibility="collapsed"
    )
    갑각류_출처 = st.text_input(
        "갑각류 출처",
        value=st.session_state.section12_data['가_수생생태독성']['갑각류'].get('출처', ''),
        placeholder="출처",
        key="crustacean_source",
        label_visibility="collapsed"
    )
    st.session_state.section12_data['가_수생생태독성']['갑각류'] = {'값': 갑각류_값, '출처': 갑각류_출처}

with col3:
    st.markdown("**조류 (EC50)**")
    조류_값 = st.text_input(
        "조류 독성",
        value=st.session_state.section12_data['가_수생생태독성']['조류'].get('값', ''),
        placeholder="예: EC50 = 29 mg/L (72hr)",
        key="algae_value",
        label_visibility="collapsed"
    )
    조류_출처 = st.text_input(
        "조류 출처",
        value=st.session_state.section12_data['가_수생생태독성']['조류'].get('출처', ''),
        placeholder="출처",
        key="algae_source",
        label_visibility="collapsed"
    )
    st.session_state.section12_data['가_수생생태독성']['조류'] = {'값': 조류_값, '출처': 조류_출처}

st.markdown("</div>", unsafe_allow_html=True)

# 나머지 환경 영향 항목들
eco_items = [
    ('나_잔류성_분해성', '나. 잔류성 및 분해성',
     '예: 생분해성 - 28일 후 67% 분해 (OECD 301D)'),
    ('다_생물농축성', '다. 생물 농축성',
     '예: BCF = 19 (생물농축 가능성 낮음)'),
    ('라_토양이동성', '라. 토양 이동성',
     '예: log Koc = 1.8-2.3 (중간 정도의 토양 이동성)'),
    ('마_유해성_평가결과', '마. 유해성 평가 결과 (PBT, vPvB)',
     '예: PBT 물질 아님, vPvB 물질 아님'),
    ('오존층유해성', '오존층 유해성',
     '예: 오존층 파괴물질 아님 (몬트리올 의정서 해당없음)'),
    ('바_기타유해영향', '바. 기타 유해 영향',
     '예: 수생환경 유해성 분류 - 급성 1, 만성 1')
]

for key, label, placeholder in eco_items:
    st.markdown(f'<div class="sub-section">', unsafe_allow_html=True)
    st.markdown(f"#### {label}")

    col1, col2 = st.columns([3, 1])

    with col1:
        value = st.text_area(
            label,
            value=st.session_state.section12_data[key].get('값', ''),
            placeholder=placeholder,
            key=f"{key}_value",
            label_visibility="collapsed",
            height=80
        )

    with col2:
        source = st.text_input(
            f"{label} 출처",
            value=st.session_state.section12_data[key].get('출처', ''),
            placeholder="출처",
            key=f"{key}_source",
            label_visibility="collapsed"
        )

    st.session_state.section12_data[key] = {'값': value, '출처': source}
    st.markdown("</div>", unsafe_allow_html=True)

# 기타 환경 정보
st.markdown('<div class="sub-section">', unsafe_allow_html=True)
st.markdown("#### 기타 환경 관련 정보")

기타정보_text = st.text_area(
    "기타 환경 관련 정보",
    value="\n".join(st.session_state.section12_data.get('기타정보', [])),
    placeholder="추가적인 환경 영향 정보를 입력하세요 (줄바꿈으로 구분)",
    height=100,
    key="other_eco_info"
)

if 기타정보_text:
    st.session_state.section12_data['기타정보'] = [line.strip() for line in 기타정보_text.split('\n') if line.strip()]

st.markdown("</div>", unsafe_allow_html=True)

# 환경 유해성 경고
st.markdown('<div class="eco-warning">', unsafe_allow_html=True)
st.markdown("""
**환경 유해성 분류 기준 참고**
- **급성 수생 독성**: 구분 1 (LC50 ≤ 1 mg/L), 구분 2 (1 < LC50 ≤ 10 mg/L), 구분 3 (10 < LC50 ≤ 100 mg/L)
- **만성 수생 독성**: 구분 1 (NOEC ≤ 0.1 mg/L), 구분 2 (0.1 < NOEC ≤ 1 mg/L)
- **생물농축성**: BCF > 500 또는 log Kow > 4 인 경우 생물농축 가능성 있음
""")
st.markdown("</div>", unsafe_allow_html=True)

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 12 저장", type="primary", use_container_width=True):
        st.success("섹션 12가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 저장된 환경 영향 정보")

    preview_data = []

    # 수생생태독성
    수생독성_표시 = []
    for species in ['어류', '갑각류', '조류']:
        값 = st.session_state.section12_data['가_수생생태독성'][species]['값']
        출처 = st.session_state.section12_data['가_수생생태독성'][species]['출처']
        if 값:
            if 출처:
                수생독성_표시.append(f"{species}: {값} [{출처}]")
            else:
                수생독성_표시.append(f"{species}: {값}")
    preview_data.append(["가. 수생 생태독성", "\n".join(수생독성_표시) if 수생독성_표시 else "자료없음"])

    # 나머지 항목들
    for key, label, _ in eco_items:
        값 = st.session_state.section12_data[key]['값']
        출처 = st.session_state.section12_data[key]['출처']

        if 출처 and 값:
            표시값 = f"{값} [{출처}]"
        else:
            표시값 = 값 if 값 else "자료없음"

        preview_data.append([label, 표시값])

    # 기타 정보
    기타정보 = st.session_state.section12_data.get('기타정보', [])
    if 기타정보:
        preview_data.append(["기타 정보", "\n".join(기타정보)])

    preview_df = pd.DataFrame(preview_data, columns=['항목', '값'])
    st.table(preview_df.set_index('항목'))

    st.write("### 원본 데이터")
    st.json(st.session_state.section12_data)
