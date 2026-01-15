import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# KOSHA API 모듈 경로 추가
sys.path.insert(0, '/home/claude')

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
    .api-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #4caf50;
        margin: 15px 0;
    }
    .material-result {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #2196f3;
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
        '마_기타_유해_영향': '',
        'api_data': {}  # API에서 가져온 데이터 저장
    }

# ============================================================
# KOSHA API 연동 섹션
# ============================================================
st.markdown('<div class="api-box">', unsafe_allow_html=True)
st.markdown("### 🔗 KOSHA API 연동")
st.markdown("섹션 3에 등록된 구성성분의 CAS 번호를 기반으로 환경 영향 정보를 자동으로 조회합니다.")

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
    
    if st.button("🔍 KOSHA API에서 환경 영향 정보 조회", type="primary"):
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
                
                st.session_state.section12_data['api_data'] = api_results
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
if st.session_state.section12_data.get('api_data'):
    st.markdown("### 📊 API 조회 결과")
    
    api_data = st.session_state.section12_data['api_data']
    
    # 종합된 환경 영향 정보 생성
    combined_aquatic = []
    combined_persistence = []
    combined_bioaccumulation = []
    combined_soil = []
    combined_other = []
    
    for cas, data in api_data.items():
        if not data.get('success'):
            st.warning(f"⚠️ {cas}: {data.get('error', '조회 실패')}")
            continue
        
        name = data.get('name', cas)
        environmental = data.get('section12_environmental', {})
        
        st.markdown(f'<div class="material-result">', unsafe_allow_html=True)
        st.write(f"**{name}** (CAS: {cas})")
        
        # 수생 독성
        aquatic = environmental.get('aquatic_toxicity', {})
        aquatic_text = []
        if aquatic.get('fish'):
            aquatic_text.append(f"어류 LC50: {aquatic['fish']}")
        if aquatic.get('daphnia'):
            aquatic_text.append(f"물벼룩 EC50: {aquatic['daphnia']}")
        if aquatic.get('algae'):
            aquatic_text.append(f"조류 EC50: {aquatic['algae']}")
        if aquatic.get('chronic'):
            aquatic_text.append(f"만성 수생독성: {aquatic['chronic']}")
        if aquatic_text:
            combined_aquatic.append(f"[{name}]\n" + "\n".join(aquatic_text))
            st.write("  **수생 독성:**")
            for txt in aquatic_text:
                st.write(f"    • {txt}")
        
        # 잔류성 및 분해성
        if environmental.get('persistence'):
            combined_persistence.append(f"[{name}] {environmental['persistence']}")
            st.write(f"  **잔류성/분해성:** {environmental['persistence']}")
        
        # 생물 농축성
        if environmental.get('bioaccumulation'):
            combined_bioaccumulation.append(f"[{name}] {environmental['bioaccumulation']}")
            st.write(f"  **생물 농축성:** {environmental['bioaccumulation']}")
        
        # 토양 이동성
        if environmental.get('soil_mobility'):
            combined_soil.append(f"[{name}] {environmental['soil_mobility']}")
            st.write(f"  **토양 이동성:** {environmental['soil_mobility']}")
        
        # 기타 유해 영향
        if environmental.get('other_effects'):
            combined_other.append(f"[{name}] {environmental['other_effects']}")
            st.write(f"  **기타 유해 영향:** {environmental['other_effects']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 자동 채우기 버튼
    if st.button("📝 조회 결과를 아래 양식에 자동 채우기"):
        if combined_aquatic:
            st.session_state.section12_data['가_수생_환경_유해성'] = "\n\n".join(combined_aquatic)
        if combined_persistence:
            st.session_state.section12_data['나_잔류성_및_분해성'] = "\n".join(combined_persistence)
        if combined_bioaccumulation:
            st.session_state.section12_data['다_생물_농축성'] = "\n".join(combined_bioaccumulation)
        if combined_soil:
            st.session_state.section12_data['라_토양_이동성'] = "\n".join(combined_soil)
        if combined_other:
            st.session_state.section12_data['마_기타_유해_영향'] = "\n".join(combined_other)
        
        st.success("✅ 데이터가 자동으로 채워졌습니다!")
        st.rerun()

st.markdown("---")

# ============================================================
# 기존 입력 양식
# ============================================================

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
        st.success("✅ 섹션 12가 저장되었습니다!")

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
    # API 데이터는 제외하고 표시
    display_data = {k: v for k, v in st.session_state.section12_data.items() if k != 'api_data'}
    st.json(display_data)
