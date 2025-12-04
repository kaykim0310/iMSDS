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
    page_title="MSDS 섹션 9 - 물리화학적 특성",
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
    .section-header {
        background-color: #d3e3f3;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .fetch-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #b8d4e3;
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>9. 물리화학적 특성</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section9_data' not in st.session_state:
    st.session_state.section9_data = {
        '가_외관': {'성상': '', '색상': '', '출처': ''},
        '나_냄새': {'값': '', '출처': ''},
        '다_냄새역치': {'값': '', '출처': ''},
        '라_pH': {'값': '', '출처': ''},
        '마_녹는점_어는점': {'값': '', '출처': ''},
        '바_초기끓는점과_끓는점범위': {'값': '', '출처': ''},
        '사_인화점': {'값': '', '출처': ''},
        '아_증발속도': {'값': '', '출처': ''},
        '자_인화성_고체_기체': {'값': '', '출처': ''},
        '차_인화_또는_폭발범위의_상한_하한': {'값': '', '출처': ''},
        '카_증기압': {'값': '', '출처': ''},
        '타_용해도': {'값': '', '출처': ''},
        '파_증기밀도': {'값': '', '출처': ''},
        '하_비중': {'값': '', '출처': ''},
        '거_n옥탄올_물분배계수': {'값': '', '출처': ''},
        '너_자연발화온도': {'값': '', '출처': ''},
        '더_분해온도': {'값': '', '출처': ''},
        '러_점도': {'값': '', '출처': ''},
        '머_분자량': {'값': '', '출처': ''}
    }

# ===== 외부 데이터 가져오기 섹션 =====
st.markdown("### 외부 데이터베이스에서 가져오기")
st.markdown('<div class="fetch-box">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "CAS 번호 또는 화학물질명",
        placeholder="예: 71-43-2 (벤젠) 또는 Benzene",
        key="search_query_9"
    )

with col2:
    search_type = st.selectbox(
        "검색 유형",
        options=['cas', 'name'],
        format_func=lambda x: 'CAS 번호' if x == 'cas' else '화학물질명',
        key="search_type_9"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    fetch_button = st.button("데이터 가져오기", type="primary", key="fetch_btn_9")

if fetch_button and search_query:
    if FETCHER_AVAILABLE:
        with st.spinner("PubChem에서 데이터를 가져오는 중..."):
            try:
                fetcher = ChemicalDataFetcher()
                data = fetcher.get_section9_data(search_query, search_type)

                if data:
                    st.success("데이터를 성공적으로 가져왔습니다!")

                    # 가져온 데이터를 세션 상태에 매핑
                    mapping = {
                        '외관': ('가_외관', '성상'),
                        '냄새': ('나_냄새', '값'),
                        'pH': ('라_pH', '값'),
                        '녹는점': ('마_녹는점_어는점', '값'),
                        '끓는점': ('바_초기끓는점과_끓는점범위', '값'),
                        '인화점': ('사_인화점', '값'),
                        '증기압': ('카_증기압', '값'),
                        '용해도': ('타_용해도', '값'),
                        '비중': ('하_비중', '값'),
                        '분자량': ('머_분자량', '값'),
                        '옥탄올_물분배계수': ('거_n옥탄올_물분배계수', '값'),
                        '자연발화온도': ('너_자연발화온도', '값'),
                        '분해온도': ('더_분해온도', '값'),
                        '점도': ('러_점도', '값')
                    }

                    updated_count = 0
                    for src_key, (dest_key, field) in mapping.items():
                        if data.get(src_key):
                            if field == '성상':
                                st.session_state.section9_data[dest_key]['성상'] = data[src_key]
                            else:
                                st.session_state.section9_data[dest_key]['값'] = data[src_key]
                            st.session_state.section9_data[dest_key]['출처'] = 'PubChem'
                            updated_count += 1

                    st.info(f"{updated_count}개 항목이 업데이트되었습니다.")
                    st.rerun()
                else:
                    st.warning("해당 물질의 데이터를 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"데이터 가져오기 실패: {str(e)}")
    else:
        st.error("데이터 가져오기 모듈을 불러올 수 없습니다. utils/chemical_data_fetcher.py 파일을 확인하세요.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
> **데이터 소스 안내**
> - **PubChem**: 미국 NIH 국립생물공학정보센터의 화학물질 데이터베이스 (무료)
> - **KOSHA MSDS**: 안전보건공단 MSDS 정보 ([공공데이터포털 API 필요](https://www.data.go.kr/data/15001197/openapi.do))
> - **eChemPortal**: OECD 화학물질 정보 포털 ([echemportal.org](https://www.echemportal.org))
""")

st.markdown("---")

# ===== 물리화학적 특성 입력 테이블 =====
st.markdown("### 물리화학적 특성 정보")

# 가. 외관 (성상, 색상 별도 입력)
st.markdown("#### 가. 외관")
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    성상 = st.text_input(
        "성상",
        value=st.session_state.section9_data['가_외관'].get('성상', ''),
        placeholder="예: 액체",
        key="appearance_state"
    )
with col2:
    색상 = st.text_input(
        "색상",
        value=st.session_state.section9_data['가_외관'].get('색상', ''),
        placeholder="예: 무색투명",
        key="appearance_color"
    )
with col3:
    외관_출처 = st.text_input(
        "출처",
        value=st.session_state.section9_data['가_외관'].get('출처', ''),
        placeholder="출처 입력 (선택사항)",
        key="appearance_source"
    )

st.session_state.section9_data['가_외관'] = {
    '성상': 성상,
    '색상': 색상,
    '출처': 외관_출처
}

# 나머지 항목들
properties = [
    ('나_냄새', '나. 냄새', '예: 무취'),
    ('다_냄새역치', '다. 냄새역치', '예: 자료없음'),
    ('라_pH', '라. pH', '예: 7.0'),
    ('마_녹는점_어는점', '마. 녹는점/어는점', '예: 0℃'),
    ('바_초기끓는점과_끓는점범위', '바. 초기 끓는점과 끓는점 범위', '예: 100℃'),
    ('사_인화점', '사. 인화점', '예: 자료없음'),
    ('아_증발속도', '아. 증발속도', '예: 자료없음'),
    ('자_인화성_고체_기체', '자. 인화성(고체, 기체)', '예: 해당없음'),
    ('차_인화_또는_폭발범위의_상한_하한', '차. 인화 또는 폭발 범위의 상한/하한', '예: 자료없음'),
    ('카_증기압', '카. 증기압', '예: 23.8 mmHg (25℃)'),
    ('타_용해도', '타. 용해도', '예: 물에 가용'),
    ('파_증기밀도', '파. 증기밀도', '예: 자료없음'),
    ('하_비중', '하. 비중', '예: 1.0'),
    ('거_n옥탄올_물분배계수', '거. n-옥탄올/물분배계수', '예: 자료없음'),
    ('너_자연발화온도', '너. 자연발화온도', '예: 자료없음'),
    ('더_분해온도', '더. 분해온도', '예: 자료없음'),
    ('러_점도', '러. 점도', '예: 자료없음'),
    ('머_분자량', '머. 분자량', '예: 18.015')
]

# 각 특성별 입력 필드
for key, label, placeholder in properties:
    st.markdown(f"#### {label}")
    col1, col2 = st.columns([2, 1])

    with col1:
        value = st.text_input(
            label,
            value=st.session_state.section9_data[key].get('값', ''),
            placeholder=placeholder,
            key=f"{key}_value",
            label_visibility="collapsed"
        )

    with col2:
        source = st.text_input(
            f"{label} 출처",
            value=st.session_state.section9_data[key].get('출처', ''),
            placeholder="출처 입력 (선택사항)",
            key=f"{key}_source",
            label_visibility="collapsed"
        )

    st.session_state.section9_data[key] = {
        '값': value,
        '출처': source
    }

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 9 저장", type="primary", use_container_width=True):
        st.success("섹션 9가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인 (출력 형식 미리보기)"):
    st.write("### 저장된 물리화학적 특성")

    # 출력 형식으로 표시
    preview_data = []

    # 가. 외관
    외관_값 = f"성상: {st.session_state.section9_data['가_외관']['성상']}, 색상: {st.session_state.section9_data['가_외관']['색상']}"
    외관_출처 = st.session_state.section9_data['가_외관']['출처']
    if 외관_출처:
        외관_표시 = f"{외관_값} [{외관_출처}]"
    else:
        외관_표시 = 외관_값
    preview_data.append(["가. 외관", 외관_표시])

    # 나머지 항목들
    for key, label, _ in properties:
        값 = st.session_state.section9_data[key]['값']
        출처 = st.session_state.section9_data[key]['출처']

        if 출처:
            표시값 = f"{값} [{출처}]"
        else:
            표시값 = 값

        preview_data.append([label, 표시값])

    # 테이블로 표시
    preview_df = pd.DataFrame(preview_data, columns=['항목', '값'])
    st.table(preview_df.set_index('항목'))

    # JSON 데이터
    st.write("### 원본 데이터")
    st.json(st.session_state.section9_data)
