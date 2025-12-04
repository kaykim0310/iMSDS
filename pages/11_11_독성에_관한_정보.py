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
        border-left: 4px solid #d3e3f3;
        margin-bottom: 15px;
    }
    .fetch-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #b8d4e3;
        margin-bottom: 20px;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ffc107;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_급성독성': {
            '경구': {'값': '', '출처': ''},
            '경피': {'값': '', '출처': ''},
            '흡입': {'값': '', '출처': ''}
        },
        '나_피부부식성_자극성': {'값': '', '출처': ''},
        '다_심한눈손상_자극성': {'값': '', '출처': ''},
        '라_호흡기과민성': {'값': '', '출처': ''},
        '마_피부과민성': {'값': '', '출처': ''},
        '바_생식세포변이원성': {'값': '', '출처': ''},
        '사_발암성': {'값': '', '출처': ''},
        '아_생식독성': {'값': '', '출처': ''},
        '자_특정표적장기독성_1회노출': {'값': '', '출처': ''},
        '차_특정표적장기독성_반복노출': {'값': '', '출처': ''},
        '카_흡인유해성': {'값': '', '출처': ''},
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
        key="search_query_11"
    )

with col2:
    search_type = st.selectbox(
        "검색 유형",
        options=['cas', 'name'],
        format_func=lambda x: 'CAS 번호' if x == 'cas' else '화학물질명',
        key="search_type_11"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_button = st.button("데이터 가져오기", type="primary", key="fetch_btn_11")

if fetch_button and search_query:
    if FETCHER_AVAILABLE:
        with st.spinner("PubChem에서 독성 데이터를 가져오는 중..."):
            try:
                fetcher = ChemicalDataFetcher()
                data = fetcher.get_section11_data(search_query, search_type)

                if data:
                    st.success("데이터를 성공적으로 가져왔습니다!")

                    # 가져온 데이터를 세션 상태에 매핑
                    updated_count = 0

                    # 급성독성
                    if data.get('급성독성'):
                        for route in ['경구', '경피', '흡입']:
                            if data['급성독성'].get(route):
                                st.session_state.section11_data['가_급성독성'][route]['값'] = data['급성독성'][route]
                                st.session_state.section11_data['가_급성독성'][route]['출처'] = 'PubChem'
                                updated_count += 1

                    # 기타 독성 정보 매핑
                    toxicity_mapping = {
                        '피부부식성_자극성': '나_피부부식성_자극성',
                        '심한눈손상_자극성': '다_심한눈손상_자극성',
                        '호흡기과민성': '라_호흡기과민성',
                        '피부과민성': '마_피부과민성',
                        '생식세포변이원성': '바_생식세포변이원성',
                        '발암성': '사_발암성',
                        '생식독성': '아_생식독성',
                        '특정표적장기독성_1회': '자_특정표적장기독성_1회노출',
                        '특정표적장기독성_반복': '차_특정표적장기독성_반복노출',
                        '흡인유해성': '카_흡인유해성'
                    }

                    for src_key, dest_key in toxicity_mapping.items():
                        if data.get(src_key):
                            st.session_state.section11_data[dest_key]['값'] = data[src_key]
                            st.session_state.section11_data[dest_key]['출처'] = 'PubChem'
                            updated_count += 1

                    # 기타 정보
                    if data.get('기타정보'):
                        st.session_state.section11_data['기타정보'] = data['기타정보'][:5]  # 최대 5개

                    st.info(f"{updated_count}개 항목이 업데이트되었습니다.")
                    st.rerun()
                else:
                    st.warning("해당 물질의 독성 데이터를 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"데이터 가져오기 실패: {str(e)}")
    else:
        st.error("데이터 가져오기 모듈을 불러올 수 없습니다.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
> **데이터 소스 안내**
> - **PubChem**: LD50, LC50, 발암성 분류 등 독성 데이터 제공
> - **KOSHA MSDS**: 국내 규제 기준 독성 정보 ([공공데이터포털](https://www.data.go.kr/data/15001197/openapi.do))
> - **eChemPortal**: OECD 화학물질 독성 데이터 ([echemportal.org](https://www.echemportal.org))
""")

st.markdown("---")

# ===== 독성 정보 입력 섹션 =====
st.markdown("### 독성에 관한 정보")

# 가. 급성 독성
st.markdown('<div class="sub-section">', unsafe_allow_html=True)
st.markdown("#### 가. 급성 독성")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**경구 (LD50)**")
    경구_값 = st.text_input(
        "경구 LD50",
        value=st.session_state.section11_data['가_급성독성']['경구'].get('값', ''),
        placeholder="예: LD50 = 930 mg/kg (rat)",
        key="acute_oral_value",
        label_visibility="collapsed"
    )
    경구_출처 = st.text_input(
        "경구 출처",
        value=st.session_state.section11_data['가_급성독성']['경구'].get('출처', ''),
        placeholder="출처",
        key="acute_oral_source",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['가_급성독성']['경구'] = {'값': 경구_값, '출처': 경구_출처}

with col2:
    st.markdown("**경피 (LD50)**")
    경피_값 = st.text_input(
        "경피 LD50",
        value=st.session_state.section11_data['가_급성독성']['경피'].get('값', ''),
        placeholder="예: LD50 > 2000 mg/kg (rabbit)",
        key="acute_dermal_value",
        label_visibility="collapsed"
    )
    경피_출처 = st.text_input(
        "경피 출처",
        value=st.session_state.section11_data['가_급성독성']['경피'].get('출처', ''),
        placeholder="출처",
        key="acute_dermal_source",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['가_급성독성']['경피'] = {'값': 경피_값, '출처': 경피_출처}

with col3:
    st.markdown("**흡입 (LC50)**")
    흡입_값 = st.text_input(
        "흡입 LC50",
        value=st.session_state.section11_data['가_급성독성']['흡입'].get('값', ''),
        placeholder="예: LC50 = 13,700 ppm/4hr (rat)",
        key="acute_inhalation_value",
        label_visibility="collapsed"
    )
    흡입_출처 = st.text_input(
        "흡입 출처",
        value=st.session_state.section11_data['가_급성독성']['흡입'].get('출처', ''),
        placeholder="출처",
        key="acute_inhalation_source",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['가_급성독성']['흡입'] = {'값': 흡입_값, '출처': 흡입_출처}

st.markdown("</div>", unsafe_allow_html=True)

# 나머지 독성 항목들
toxicity_items = [
    ('나_피부부식성_자극성', '나. 피부 부식성/자극성', '예: 피부 자극성 있음 (구분 2)'),
    ('다_심한눈손상_자극성', '다. 심한 눈 손상/자극성', '예: 심한 눈 손상성 (구분 1)'),
    ('라_호흡기과민성', '라. 호흡기 과민성', '예: 자료없음'),
    ('마_피부과민성', '마. 피부 과민성', '예: 피부 과민성 물질 (구분 1)'),
    ('바_생식세포변이원성', '바. 생식세포 변이원성', '예: 자료없음'),
    ('사_발암성', '사. 발암성', '예: 발암성 물질 (구분 1A) - IARC Group 1'),
    ('아_생식독성', '아. 생식독성', '예: 자료없음'),
    ('자_특정표적장기독성_1회노출', '자. 특정 표적장기 독성 (1회 노출)', '예: 중추신경계, 호흡기계 (구분 1)'),
    ('차_특정표적장기독성_반복노출', '차. 특정 표적장기 독성 (반복 노출)', '예: 조혈기관 (구분 1)'),
    ('카_흡인유해성', '카. 흡인 유해성', '예: 흡인 유해성 있음 (구분 1)')
]

for key, label, placeholder in toxicity_items:
    st.markdown(f'<div class="sub-section">', unsafe_allow_html=True)
    st.markdown(f"#### {label}")

    col1, col2 = st.columns([3, 1])

    with col1:
        value = st.text_area(
            label,
            value=st.session_state.section11_data[key].get('값', ''),
            placeholder=placeholder,
            key=f"{key}_value",
            label_visibility="collapsed",
            height=80
        )

    with col2:
        source = st.text_input(
            f"{label} 출처",
            value=st.session_state.section11_data[key].get('출처', ''),
            placeholder="출처",
            key=f"{key}_source",
            label_visibility="collapsed"
        )

    st.session_state.section11_data[key] = {'값': value, '출처': source}
    st.markdown("</div>", unsafe_allow_html=True)

# 기타 독성 정보
st.markdown('<div class="sub-section">', unsafe_allow_html=True)
st.markdown("#### 기타 독성 정보")

기타정보_text = st.text_area(
    "기타 독성 관련 정보",
    value="\n".join(st.session_state.section11_data.get('기타정보', [])),
    placeholder="추가적인 독성 정보를 입력하세요 (줄바꿈으로 구분)",
    height=100,
    key="other_toxicity_info"
)

if 기타정보_text:
    st.session_state.section11_data['기타정보'] = [line.strip() for line in 기타정보_text.split('\n') if line.strip()]

st.markdown("</div>", unsafe_allow_html=True)

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("섹션 11이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 저장된 독성 정보")

    preview_data = []

    # 급성 독성
    급성독성_표시 = []
    for route in ['경구', '경피', '흡입']:
        값 = st.session_state.section11_data['가_급성독성'][route]['값']
        출처 = st.session_state.section11_data['가_급성독성'][route]['출처']
        if 값:
            if 출처:
                급성독성_표시.append(f"{route}: {값} [{출처}]")
            else:
                급성독성_표시.append(f"{route}: {값}")
    preview_data.append(["가. 급성 독성", "\n".join(급성독성_표시) if 급성독성_표시 else "자료없음"])

    # 나머지 항목들
    for key, label, _ in toxicity_items:
        값 = st.session_state.section11_data[key]['값']
        출처 = st.session_state.section11_data[key]['출처']

        if 출처 and 값:
            표시값 = f"{값} [{출처}]"
        else:
            표시값 = 값 if 값 else "자료없음"

        preview_data.append([label, 표시값])

    # 기타 정보
    기타정보 = st.session_state.section11_data.get('기타정보', [])
    if 기타정보:
        preview_data.append(["기타 정보", "\n".join(기타정보)])

    preview_df = pd.DataFrame(preview_data, columns=['항목', '값'])
    st.table(preview_df.set_index('항목'))

    st.write("### 원본 데이터")
    st.json(st.session_state.section11_data)
