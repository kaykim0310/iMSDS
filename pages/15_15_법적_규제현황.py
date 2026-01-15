import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# KOSHA API 모듈 경로 추가
sys.path.insert(0, '/home/claude')

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 15 - 법적 규제현황",
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
        background-color: #fce4ec;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #e91e63;
    }
    .regulation-category {
        background-color: #f5f5f5;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        font-weight: bold;
    }
    .regulation-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .regulation-table th, .regulation-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .regulation-table th {
        background-color: #f0f0f0;
    }
    .applicable {
        color: #28a745;
        font-weight: bold;
    }
    .not-applicable {
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>15. 법적 규제현황</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section15_data' not in st.session_state:
    st.session_state.section15_data = {
        '가_산업안전보건법': {},
        '나_화학물질관리법': {},
        '다_위험물안전관리법': '',
        '라_폐기물관리법': '',
        '마_기타_국내_및_외국법': {},
        'api_data': {}  # API에서 가져온 데이터 저장
    }

# ============================================================
# KOSHA API 연동 섹션
# ============================================================
st.markdown('<div class="api-box">', unsafe_allow_html=True)
st.markdown("### 🔗 KOSHA API 연동")
st.markdown("섹션 3에 등록된 구성성분의 CAS 번호를 기반으로 법적 규제현황을 자동으로 조회합니다.")

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
    
    if st.button("🔍 KOSHA API에서 법적 규제현황 조회", type="primary"):
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
                
                st.session_state.section15_data['api_data'] = api_results
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
if st.session_state.section15_data.get('api_data'):
    st.markdown("### 📊 API 조회 결과")
    
    api_data = st.session_state.section15_data['api_data']
    
    # 물질별 규제 현황 테이블 생성
    table_data = []
    
    for cas, data in api_data.items():
        if not data.get('success'):
            st.warning(f"⚠️ {cas}: {data.get('error', '조회 실패')}")
            continue
        
        name = data.get('name', cas)
        regulations = data.get('section15_regulations', {})
        
        occ = regulations.get('occupational_safety', {})
        chem = regulations.get('chemical_control', {})
        
        row = {
            '물질명': name,
            'CAS번호': cas,
            '작업환경측정': '✅' if occ.get('measurement') == '해당' else '-',
            '관리대상유해물질': '✅' if occ.get('managed_hazard') == '해당' else '-',
            '특수건강진단': '✅' if occ.get('health_check') == '해당' else '-',
            '노출기준설정': '✅' if occ.get('exposure_limit') == '해당' else '-',
            '유독물질': '✅' if chem.get('toxic') == '해당' else '-',
            '사고대비물질': '✅' if chem.get('accident_preparedness') == '해당' else '-',
        }
        table_data.append(row)
    
    if table_data:
        st.markdown("#### 규제 현황 요약")
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    
    # 상세 정보 표시
    for cas, data in api_data.items():
        if not data.get('success'):
            continue
        
        name = data.get('name', cas)
        regulations = data.get('section15_regulations', {})
        
        st.markdown(f'<div class="material-result">', unsafe_allow_html=True)
        st.write(f"**{name}** (CAS: {cas})")
        
        occ = regulations.get('occupational_safety', {})
        chem = regulations.get('chemical_control', {})
        
        # 산업안전보건법
        if occ.get('raw_text'):
            st.write(f"  📋 **산업안전보건법:** {occ['raw_text']}")
        
        # 화학물질관리법
        if chem.get('raw_text'):
            st.write(f"  📋 **화학물질관리법:** {chem['raw_text']}")
        
        # 위험물안전관리법
        dangerous = regulations.get('dangerous_goods', '')
        if dangerous:
            st.write(f"  📋 **위험물안전관리법:** {dangerous}")
        
        # 폐기물관리법
        waste = regulations.get('waste_management', '')
        if waste:
            st.write(f"  📋 **폐기물관리법:** {waste}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 자동 채우기 버튼
    if st.button("📝 조회 결과를 아래 양식에 자동 채우기"):
        # 산업안전보건법 자동 채우기
        산안법_결과 = {
            '작업환경측정대상물질': {'결론': '', '해당물질': []},
            '관리대상유해물질': {'결론': '', '해당물질': []},
            '특수건강진단대상물질': {'결론': '', '해당물질': []},
            '노출기준설정물질': {'결론': '', '해당물질': []},
            '허용기준설정물질': {'결론': '', '해당물질': []},
            '허가대상물질': {'결론': '', '해당물질': []},
            '제조금지물질': {'결론': '', '해당물질': []}
        }
        
        화관법_결과 = {
            '유독물질': {'결론': '', '해당물질': []},
            '허가물질': {'결론': '', '해당물질': []},
            '제한물질': {'결론': '', '해당물질': []},
            '금지물질': {'결론': '', '해당물질': []},
            '사고대비물질': {'결론': '', '해당물질': []}
        }
        
        위험물_결과 = []
        폐기물_결과 = []
        
        for cas, data in api_data.items():
            if not data.get('success'):
                continue
            
            name = data.get('name', cas)
            regulations = data.get('section15_regulations', {})
            occ = regulations.get('occupational_safety', {})
            chem = regulations.get('chemical_control', {})
            
            # 산업안전보건법
            if occ.get('measurement') == '해당':
                산안법_결과['작업환경측정대상물질']['해당물질'].append(name)
            if occ.get('managed_hazard') == '해당':
                산안법_결과['관리대상유해물질']['해당물질'].append(name)
            if occ.get('health_check') == '해당':
                산안법_결과['특수건강진단대상물질']['해당물질'].append(name)
            if occ.get('exposure_limit') == '해당':
                산안법_결과['노출기준설정물질']['해당물질'].append(name)
            if occ.get('permission_limit') == '해당':
                산안법_결과['허용기준설정물질']['해당물질'].append(name)
            if occ.get('permission_required') == '해당':
                산안법_결과['허가대상물질']['해당물질'].append(name)
            if occ.get('prohibited') == '해당':
                산안법_결과['제조금지물질']['해당물질'].append(name)
            
            # 화학물질관리법
            if chem.get('toxic') == '해당':
                화관법_결과['유독물질']['해당물질'].append(name)
            if chem.get('permission') == '해당':
                화관법_결과['허가물질']['해당물질'].append(name)
            if chem.get('restricted') == '해당':
                화관법_결과['제한물질']['해당물질'].append(name)
            if chem.get('prohibited') == '해당':
                화관법_결과['금지물질']['해당물질'].append(name)
            if chem.get('accident_preparedness') == '해당':
                화관법_결과['사고대비물질']['해당물질'].append(name)
            
            # 위험물안전관리법
            if regulations.get('dangerous_goods'):
                위험물_결과.append(f"[{name}] {regulations['dangerous_goods']}")
            
            # 폐기물관리법
            if regulations.get('waste_management'):
                폐기물_결과.append(f"[{name}] {regulations['waste_management']}")
        
        # 결론 자동 설정
        for key in 산안법_결과:
            if 산안법_결과[key]['해당물질']:
                산안법_결과[key]['결론'] = f"해당 ({', '.join(산안법_결과[key]['해당물질'])})"
            else:
                산안법_결과[key]['결론'] = "해당없음"
        
        for key in 화관법_결과:
            if 화관법_결과[key]['해당물질']:
                화관법_결과[key]['결론'] = f"해당 ({', '.join(화관법_결과[key]['해당물질'])})"
            else:
                화관법_결과[key]['결론'] = "해당없음"
        
        # 세션 상태에 저장
        st.session_state.section15_data['가_산업안전보건법_자동'] = 산안법_결과
        st.session_state.section15_data['나_화학물질관리법_자동'] = 화관법_결과
        st.session_state.section15_data['다_위험물안전관리법'] = "\n".join(위험물_결과) if 위험물_결과 else "해당없음"
        st.session_state.section15_data['라_폐기물관리법'] = "\n".join(폐기물_결과) if 폐기물_결과 else "해당없음"
        
        st.success("✅ 데이터가 자동으로 채워졌습니다!")
        st.rerun()

st.markdown("---")

# ============================================================
# API 결과 기반 자동 생성된 양식
# ============================================================
if st.session_state.section15_data.get('가_산업안전보건법_자동'):
    st.markdown("### 📋 자동 생성된 규제 현황")
    
    # 가. 산업안전보건법
    st.markdown('<div class="subsection-header">가. 산업안전보건법에 의한 규제</div>', unsafe_allow_html=True)
    
    산안법_자동 = st.session_state.section15_data.get('가_산업안전보건법_자동', {})
    
    for 항목, 데이터 in 산안법_자동.items():
        결론 = 데이터.get('결론', '해당없음')
        css_class = 'applicable' if '해당 (' in 결론 else 'not-applicable'
        st.markdown(f"**{항목}**: <span class='{css_class}'>{결론}</span>", unsafe_allow_html=True)
    
    # 나. 화학물질관리법
    st.markdown('<div class="subsection-header">나. 화학물질관리법에 의한 규제</div>', unsafe_allow_html=True)
    
    화관법_자동 = st.session_state.section15_data.get('나_화학물질관리법_자동', {})
    
    for 항목, 데이터 in 화관법_자동.items():
        결론 = 데이터.get('결론', '해당없음')
        css_class = 'applicable' if '해당 (' in 결론 else 'not-applicable'
        st.markdown(f"**{항목}**: <span class='{css_class}'>{결론}</span>", unsafe_allow_html=True)
    
    st.markdown("---")

# ============================================================
# 기존 입력 양식 (수동 입력용)
# ============================================================
st.markdown("### ✏️ 수동 입력 양식")

# 다. 위험물안전관리법에 의한 규제
st.markdown('<div class="subsection-header">다. 위험물안전관리법에 의한 규제</div>', unsafe_allow_html=True)
위험물_value = st.text_area(
    "위험물안전관리법",
    value=st.session_state.section15_data.get('다_위험물안전관리법', ''),
    height=80,
    placeholder="예: 제4류 인화성액체, 제1석유류(비수용성액체), 200ℓ",
    key="위험물안전관리법"
)
st.session_state.section15_data['다_위험물안전관리법'] = 위험물_value

# 라. 폐기물관리법에 의한 규제
st.markdown('<div class="subsection-header">라. 폐기물관리법에 의한 규제</div>', unsafe_allow_html=True)
폐기물_value = st.text_area(
    "폐기물관리법",
    value=st.session_state.section15_data.get('라_폐기물관리법', ''),
    height=80,
    placeholder="예: 지정폐기물(폐유기용제)",
    key="폐기물관리법"
)
st.session_state.section15_data['라_폐기물관리법'] = 폐기물_value

# 마. 기타 국내 및 외국법에 의한 규제
st.markdown('<div class="subsection-header">마. 기타 국내 및 외국법에 의한 규제</div>', unsafe_allow_html=True)

기타규제_value = st.text_area(
    "기타 국내 및 외국법",
    value=st.session_state.section15_data.get('마_기타_국내_및_외국법_텍스트', ''),
    height=150,
    placeholder="예:\n- 잔류성유기오염물질관리법: 해당없음\n- 미국 OSHA 규정: 해당\n- EU 분류: 해당",
    key="기타_국내_및_외국법"
)
st.session_state.section15_data['마_기타_국내_및_외국법_텍스트'] = 기타규제_value

# 추가 정보 안내
st.info("""
💡 **참고사항**
- 각 법규별 해당 여부는 관련 부처 고시를 확인하세요.
- KOSHA API 조회 결과는 참고용이며, 최신 법규 개정 사항을 추가로 확인하세요.
- 화학물질정보시스템(https://icis.me.go.kr) 등을 참조할 수 있습니다.
""")

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 15 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 15가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 15. 법적 규제현황")
    
    # 자동 생성 데이터
    if st.session_state.section15_data.get('가_산업안전보건법_자동'):
        st.write("**가. 산업안전보건법에 의한 규제 (API 조회)**")
        for 항목, 데이터 in st.session_state.section15_data['가_산업안전보건법_자동'].items():
            st.write(f"  - {항목}: {데이터.get('결론', '')}")
    
    if st.session_state.section15_data.get('나_화학물질관리법_자동'):
        st.write("\n**나. 화학물질관리법에 의한 규제 (API 조회)**")
        for 항목, 데이터 in st.session_state.section15_data['나_화학물질관리법_자동'].items():
            st.write(f"  - {항목}: {데이터.get('결론', '')}")
    
    if st.session_state.section15_data.get('다_위험물안전관리법'):
        st.write(f"\n**다. 위험물안전관리법에 의한 규제**")
        st.write(f"  {st.session_state.section15_data['다_위험물안전관리법']}")
    
    if st.session_state.section15_data.get('라_폐기물관리법'):
        st.write(f"\n**라. 폐기물관리법에 의한 규제**")
        st.write(f"  {st.session_state.section15_data['라_폐기물관리법']}")
    
    if st.session_state.section15_data.get('마_기타_국내_및_외국법_텍스트'):
        st.write(f"\n**마. 기타 국내 및 외국법에 의한 규제**")
        st.write(f"  {st.session_state.section15_data['마_기타_국내_및_외국법_텍스트']}")
    
    # JSON 데이터
    st.write("\n### 원본 데이터")
    # API 데이터는 제외하고 표시
    display_data = {k: v for k, v in st.session_state.section15_data.items() if k != 'api_data'}
    st.json(display_data)
