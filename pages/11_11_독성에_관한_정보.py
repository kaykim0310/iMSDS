import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# KOSHA API 모듈 경로 추가
sys.path.insert(0, '/home/claude')

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
    .api-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #4caf50;
        margin: 15px 0;
    }
    .material-result {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #ff9800;
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
        '마_만성_독성_및_발암성': '',
        'api_data': {}  # API에서 가져온 데이터 저장
    }

# ============================================================
# KOSHA API 연동 섹션
# ============================================================
st.markdown('<div class="api-box">', unsafe_allow_html=True)
st.markdown("### 🔗 KOSHA API 연동")
st.markdown("섹션 3에 등록된 구성성분의 CAS 번호를 기반으로 독성 정보를 자동으로 조회합니다.")

# 섹션 3에서 CAS 번호 가져오기
cas_list = []
materials_info = []

if 'section3_data' in st.session_state:
    for comp in st.session_state.get('section3_data', {}).get('components', []):
        if comp.get('CAS번호') and comp.get('물질명'):
            cas_list.append(comp['CAS번호'])
            materials_info.append({
                'name': comp['물질명'],
                'cas': comp['CAS번호'],
                'content': comp.get('함유량(%)', '')
            })

if cas_list:
    st.success(f"✅ 섹션 3에서 {len(cas_list)}개의 CAS 번호를 찾았습니다.")
    
    # CAS 번호 목록 표시
    for mat in materials_info:
        st.write(f"  • **{mat['name']}** (CAS: {mat['cas']}, 함유량: {mat['content']}%)")
    
    if st.button("🔍 KOSHA API에서 독성 정보 조회", type="primary"):
        try:
            from kosha_api_extended import get_msds_sections_11_12_15
            
            with st.spinner("KOSHA API에서 데이터를 조회 중입니다..."):
                api_results = {}
                progress_bar = st.progress(0)
                
                for i, cas in enumerate(cas_list):
                    st.write(f"  조회 중: {cas}...")
                    result = get_msds_sections_11_12_15(cas)
                    api_results[cas] = result
                    progress_bar.progress((i + 1) / len(cas_list))
                
                st.session_state.section11_data['api_data'] = api_results
                st.success("✅ API 조회 완료!")
                st.rerun()
                
        except ImportError as e:
            st.error(f"API 모듈 로드 실패: {e}")
            st.info("kosha_api_extended.py 파일이 필요합니다.")
        except Exception as e:
            st.error(f"API 조회 중 오류 발생: {e}")
else:
    st.warning("⚠️ 섹션 3에서 CAS 번호가 등록된 구성성분이 없습니다. 먼저 섹션 3을 작성해주세요.")

st.markdown('</div>', unsafe_allow_html=True)

# API 조회 결과 표시 및 자동 채우기
if st.session_state.section11_data.get('api_data'):
    st.markdown("### 📊 API 조회 결과")
    
    api_data = st.session_state.section11_data['api_data']
    
    # 종합된 독성 정보 생성
    combined_exposure = []
    combined_health = []
    combined_acute = []
    combined_irritation = []
    combined_chronic = []
    
    for cas, data in api_data.items():
        if not data.get('success'):
            st.warning(f"⚠️ {cas}: {data.get('error', '조회 실패')}")
            continue
        
        name = data.get('name', cas)
        toxicity = data.get('section11_toxicity', {})
        
        st.markdown(f'<div class="material-result">', unsafe_allow_html=True)
        st.write(f"**{name}** (CAS: {cas})")
        
        # 노출 경로
        if toxicity.get('exposure_routes'):
            combined_exposure.append(f"[{name}] {toxicity['exposure_routes']}")
        
        # 건강 유해성
        if toxicity.get('health_hazard_info'):
            combined_health.append(f"[{name}] {toxicity['health_hazard_info']}")
        
        # 급성 독성
        acute = toxicity.get('acute_toxicity', {})
        acute_text = []
        if acute.get('oral'):
            acute_text.append(f"경구: {acute['oral']}")
        if acute.get('dermal'):
            acute_text.append(f"경피: {acute['dermal']}")
        if acute.get('inhalation'):
            acute_text.append(f"흡입: {acute['inhalation']}")
        if acute_text:
            combined_acute.append(f"[{name}] " + ", ".join(acute_text))
        
        # 자극성
        irritation = toxicity.get('irritation', {})
        irr_text = []
        if irritation.get('skin'):
            irr_text.append(f"피부: {irritation['skin']}")
        if irritation.get('eye'):
            irr_text.append(f"눈: {irritation['eye']}")
        if irr_text:
            combined_irritation.append(f"[{name}] " + ", ".join(irr_text))
        
        # 만성 독성
        chronic = toxicity.get('chronic_toxicity', {})
        chronic_text = []
        if chronic.get('carcinogenicity'):
            chronic_text.append(f"발암성: {chronic['carcinogenicity']}")
        if chronic.get('reproductive'):
            chronic_text.append(f"생식독성: {chronic['reproductive']}")
        if chronic_text:
            combined_chronic.append(f"[{name}] " + ", ".join(chronic_text))
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 자동 채우기 버튼
    if st.button("📝 조회 결과를 아래 양식에 자동 채우기"):
        if combined_exposure:
            st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = "\n".join(combined_exposure)
        if combined_health:
            st.session_state.section11_data['나_건강_유해성_정보'] = "\n".join(combined_health)
        if combined_acute:
            st.session_state.section11_data['다_급성_독성_수치'] = "\n".join(combined_acute)
        if combined_irritation:
            st.session_state.section11_data['라_자극성_부식성_민감성'] = "\n".join(combined_irritation)
        if combined_chronic:
            st.session_state.section11_data['마_만성_독성_및_발암성'] = "\n".join(combined_chronic)
        
        st.success("✅ 데이터가 자동으로 채워졌습니다!")
        st.rerun()

st.markdown("---")

# ============================================================
# 기존 입력 양식
# ============================================================

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
    # API 데이터는 제외하고 표시
    display_data = {k: v for k, v in st.session_state.section11_data.items() if k != 'api_data'}
    st.json(display_data)
