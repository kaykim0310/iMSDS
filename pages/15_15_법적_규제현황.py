import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

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
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>15. 법적 규제현황</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화 (공식 양식 기준)
if 'section15_data' not in st.session_state:
    st.session_state.section15_data = {
        '가_산업안전보건법에_의한_규제': '',
        '나_화학물질관리법에_의한_규제': '',
        '다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제': '',
        '라_위험물안전관리법에_의한_규제': '',
        '마_폐기물관리법에_의한_규제': '',
        '바_기타_국내_및_외국법에_의한_규제': ''
    }

# ============================================================
# KOSHA API 연동 섹션
# ============================================================
with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 법적 규제현황을 자동 조회합니다.")
    
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
        for mat in materials_info:
            st.write(f"  • **{mat['name']}** (CAS: {mat['cas']})")
        
        if st.button("🔍 KOSHA API에서 법적 규제현황 조회", type="primary", key="api_query_btn"):
            try:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from kosha_api_extended import get_legal_regulations, search_by_cas
                import time

                with st.spinner("KOSHA API에서 데이터를 조회 중입니다..."):
                    api_results = []

                    for cas in cas_list:
                        search_result = search_by_cas(cas)
                        if search_result.get('success'):
                            chem_id = search_result['chemId']
                            name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            regulations = get_legal_regulations(chem_id)
                            api_results.append({
                                'cas': cas,
                                'name': name,
                                'chemId': chem_id,
                                'regulations': regulations
                            })
                        else:
                            api_results.append({
                                'cas': cas,
                                'name': cas,
                                'error': search_result.get('error', '조회 실패')
                            })
                        time.sleep(0.3)

                    st.session_state['section15_api_results'] = api_results

                    # 조회 즉시 폼에 자동 반영
                    occ_safety_parts = []
                    chem_ctrl_parts = []
                    chem_reg_parts = []
                    hazmat_parts = []
                    waste_parts = []
                    other_parts = []

                    for result in api_results:
                        if 'error' in result:
                            continue
                        reg = result.get('regulations', {})
                        mat_name = result.get('name', result.get('cas', ''))

                        occ = reg.get('occupational_safety', {})
                        raw_text = occ.get('raw_text', '')
                        if raw_text:
                            occ_safety_parts.append(f"[{mat_name}] {raw_text}")
                        else:
                            occ_items = []
                            if occ.get('measurement') == 'O': occ_items.append("작업환경측정대상")
                            if occ.get('health_check') == 'O': occ_items.append("특수건강진단대상")
                            if occ.get('managed_hazard') == 'O': occ_items.append("관리대상유해물질")
                            if occ.get('special_managed') == 'O': occ_items.append("특별관리물질")
                            if occ.get('exposure_limit') == 'O': occ_items.append("노출기준설정물질")
                            if occ.get('permission') == 'O': occ_items.append("허가대상물질")
                            if occ.get('prohibited') == 'O': occ_items.append("제조금지물질")
                            if occ_items:
                                occ_safety_parts.append(f"[{mat_name}] " + ", ".join(occ_items))

                        chem = reg.get('chemical_control', {})
                        chem_raw = chem.get('raw_text', '')
                        if chem_raw:
                            chem_ctrl_parts.append(f"[{mat_name}] {chem_raw}")
                        else:
                            chem_items = []
                            if chem.get('toxic') == 'O': chem_items.append("유독물질")
                            if chem.get('permitted') == 'O': chem_items.append("허가물질")
                            if chem.get('restricted') == 'O': chem_items.append("제한물질")
                            if chem.get('prohibited') == 'O': chem_items.append("금지물질")
                            if chem.get('accident') == 'O': chem_items.append("사고대비물질")
                            if chem_items:
                                chem_ctrl_parts.append(f"[{mat_name}] " + ", ".join(chem_items))

                        cr = reg.get('chemical_registration', '')
                        if cr and cr != "해당없음":
                            chem_reg_parts.append(f"[{mat_name}] {cr}")
                        hm = reg.get('hazardous_materials', '')
                        if hm and hm != "해당없음":
                            hazmat_parts.append(f"[{mat_name}] {hm}")
                        wm = reg.get('waste_management', '')
                        if wm and wm != "해당없음":
                            waste_parts.append(f"[{mat_name}] {wm}")
                        ot = reg.get('other_regulations', '')
                        if ot and ot != "해당없음":
                            other_parts.append(f"[{mat_name}] {ot}")

                    st.session_state.section15_data['가_산업안전보건법에_의한_규제'] = "\n".join(occ_safety_parts) if occ_safety_parts else "해당없음"
                    st.session_state.section15_data['나_화학물질관리법에_의한_규제'] = "\n".join(chem_ctrl_parts) if chem_ctrl_parts else "해당없음"
                    st.session_state.section15_data['다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제'] = "\n".join(chem_reg_parts) if chem_reg_parts else "해당없음"
                    st.session_state.section15_data['라_위험물안전관리법에_의한_규제'] = "\n".join(hazmat_parts) if hazmat_parts else "해당없음"
                    st.session_state.section15_data['마_폐기물관리법에_의한_규제'] = "\n".join(waste_parts) if waste_parts else "해당없음"
                    st.session_state.section15_data['바_기타_국내_및_외국법에_의한_규제'] = "\n".join(other_parts) if other_parts else "해당없음"

                    st.rerun()

            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # API 결과 표시
    if 'section15_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과:**")

        for result in st.session_state['section15_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                reg = result.get('regulations', {})
                raw_items = reg.get('raw_items', [])
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']}) - {len(raw_items)}개 항목", expanded=True):
                    if raw_items:
                        for item in raw_items:
                            iname = item.get('name', '')
                            detail = item.get('detail', '해당없음')
                            st.markdown(f"- **{iname}**: {detail}")
                    else:
                        st.warning("⚠️ API에서 반환된 법적 규제 항목이 없습니다.")
                    with st.expander("🔧 파싱된 데이터 (진단용)"):
                        st.json(reg)

st.markdown("---")

# ============================================================
# 공식 양식 기준 입력 필드
# ============================================================

# 가. 산업안전보건법에 의한 규제
st.markdown('<div class="subsection-header">가. 산업안전보건법에 의한 규제</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "산업안전보건법에 의한 규제",
    value=st.session_state.section15_data.get('가_산업안전보건법에_의한_규제', ''),
    height=150,
    placeholder="""예:
• 작업환경측정대상물질: 해당 (TWA: 100 ppm)
• 관리대상유해물질: 해당
• 특수건강진단대상물질: 해당
• 노출기준설정물질: 해당
• 허가대상물질: 해당없음
• 제조등금지물질: 해당없음""",
    key="occupational_safety_law",
    label_visibility="collapsed"
)
st.session_state.section15_data['가_산업안전보건법에_의한_규제'] = 가_내용

# 나. 화학물질관리법에 의한 규제
st.markdown('<div class="subsection-header">나. 화학물질관리법에 의한 규제</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "화학물질관리법에 의한 규제",
    value=st.session_state.section15_data.get('나_화학물질관리법에_의한_규제', ''),
    height=150,
    placeholder="""예:
• 유독물질: 해당 (유독물질 고시번호: 97-1-xxx)
• 허가물질: 해당없음
• 제한물질: 해당없음
• 금지물질: 해당없음
• 사고대비물질: 해당 (지정수량: 1,000 kg)""",
    key="chemical_control_law",
    label_visibility="collapsed"
)
st.session_state.section15_data['나_화학물질관리법에_의한_규제'] = 나_내용

# 다. 화학물질의 등록 및 평가 등에 관한 법률에 의한 규제
st.markdown('<div class="subsection-header">다. 화학물질의 등록 및 평가 등에 관한 법률에 의한 규제</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "화학물질의 등록 및 평가 등에 관한 법률에 의한 규제",
    value=st.session_state.section15_data.get('다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제', ''),
    height=100,
    placeholder="""예:
• 기존화학물질: 해당 (KE-xxxxx)
• 등록대상기존화학물질: 해당없음
• 중점관리물질: 해당없음""",
    key="chemical_registration_law",
    label_visibility="collapsed"
)
st.session_state.section15_data['다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제'] = 다_내용

# 라. 위험물안전관리법에 의한 규제
st.markdown('<div class="subsection-header">라. 위험물안전관리법에 의한 규제</div>', unsafe_allow_html=True)

라_내용 = st.text_area(
    "위험물안전관리법에 의한 규제",
    value=st.session_state.section15_data.get('라_위험물안전관리법에_의한_규제', ''),
    height=100,
    placeholder="""예:
• 제4류 인화성액체, 제1석유류(비수용성액체), 지정수량: 200 L
또는
• 해당없음""",
    key="hazardous_materials_law",
    label_visibility="collapsed"
)
st.session_state.section15_data['라_위험물안전관리법에_의한_규제'] = 라_내용

# 마. 폐기물관리법에 의한 규제
st.markdown('<div class="subsection-header">마. 폐기물관리법에 의한 규제</div>', unsafe_allow_html=True)

마_내용 = st.text_area(
    "폐기물관리법에 의한 규제",
    value=st.session_state.section15_data.get('마_폐기물관리법에_의한_규제', ''),
    height=100,
    placeholder="""예:
• 지정폐기물: 해당 (폐유기용제류)
또는
• 해당없음""",
    key="waste_management_law",
    label_visibility="collapsed"
)
st.session_state.section15_data['마_폐기물관리법에_의한_규제'] = 마_내용

# 바. 기타 국내 및 외국법에 의한 규제
st.markdown('<div class="subsection-header">바. 기타 국내 및 외국법에 의한 규제</div>', unsafe_allow_html=True)

바_내용 = st.text_area(
    "기타 국내 및 외국법에 의한 규제",
    value=st.session_state.section15_data.get('바_기타_국내_및_외국법에_의한_규제', ''),
    height=150,
    placeholder="""예:
[국내법]
• 잔류성유기오염물질 관리법: 해당없음

[외국법]
• 미국 OSHA 규정: 해당
• 미국 CERCLA 규정: 해당없음
• 로테르담 협약: 해당없음
• 스톡홀름 협약: 해당없음
• 몬트리올 의정서: 해당없음
• EU CLP 규정: 해당 (H-문구, P-문구)""",
    key="other_regulations",
    label_visibility="collapsed"
)
st.session_state.section15_data['바_기타_국내_및_외국법에_의한_규제'] = 바_내용

# 참고 안내
st.info("""💡 **참고사항**
- 각 법규별 해당 여부는 관련 부처 고시를 확인하세요.
- 해당사항이 없는 경우 "해당없음"으로 기재하세요.
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

    항목들 = [
        ("가. 산업안전보건법에 의한 규제", '가_산업안전보건법에_의한_규제'),
        ("나. 화학물질관리법에 의한 규제", '나_화학물질관리법에_의한_규제'),
        ("다. 화학물질의 등록 및 평가 등에 관한 법률에 의한 규제", '다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제'),
        ("라. 위험물안전관리법에 의한 규제", '라_위험물안전관리법에_의한_규제'),
        ("마. 폐기물관리법에 의한 규제", '마_폐기물관리법에_의한_규제'),
        ("바. 기타 국내 및 외국법에 의한 규제", '바_기타_국내_및_외국법에_의한_규제')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section15_data.get(키, '')
        st.write(f"**{제목}**")
        st.text(내용 or '(미입력)')
        st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section15_data)
