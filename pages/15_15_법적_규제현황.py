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
# API 결과 → 입력 필드 자동 매핑 헬퍼 함수
# ============================================================
def _val(text):
    """자료없음/해당없음이면 빈 문자열 반환"""
    if not text or text.strip() in ("자료없음", "해당없음", ""):
        return ""
    return text.strip()


def _build_osha_text(name, osha_data):
    """산업안전보건법 데이터를 사람이 읽기 좋은 텍스트로 변환"""
    lines = [f"[{name}]"]

    label_map = {
        'measurement': '작업환경측정대상물질',
        'health_check': '특수건강진단대상물질',
        'managed_hazard': '관리대상유해물질',
        'special_managed': '특별관리물질',
        'exposure_limit': '노출기준설정물질',
        'permission': '허가대상물질',
        'prohibited': '제조등금지물질',
    }

    for key, label in label_map.items():
        val = osha_data.get(key, 'X')
        status = "해당" if val == "O" else "해당없음"
        lines.append(f"  • {label}: {status}")

    # raw_text가 있으면 참고용으로 추가
    raw = _val(osha_data.get('raw_text', ''))
    if raw:
        lines.append(f"  (원문: {raw})")

    return "\n".join(lines)


def _build_chem_control_text(name, cc_data):
    """화학물질관리법 데이터를 텍스트로 변환"""
    lines = [f"[{name}]"]

    label_map = {
        'toxic': '유독물질',
        'permitted': '허가물질',
        'restricted': '제한물질',
        'prohibited': '금지물질',
        'accident': '사고대비물질',
    }

    for key, label in label_map.items():
        val = cc_data.get(key, 'X')
        status = "해당" if val == "O" else "해당없음"
        lines.append(f"  • {label}: {status}")

    raw = _val(cc_data.get('raw_text', ''))
    if raw:
        lines.append(f"  (원문: {raw})")

    return "\n".join(lines)


def apply_api_results_to_section15(api_results):
    """
    API 조회 결과를 section15_data 세션 상태에 매핑합니다.
    """
    osha_lines = []
    chem_control_lines = []
    chem_reg_lines = []
    hazmat_lines = []
    waste_lines = []
    other_lines = []

    for result in api_results:
        if 'error' in result:
            continue

        name = result.get('name', result.get('cas', ''))
        regs = result.get('regulations', {})

        # 가. 산업안전보건법
        osha = regs.get('occupational_safety', {})
        # O가 하나라도 있는지 또는 raw_text가 있는지 확인
        has_osha = any(osha.get(k) == "O" for k in
                       ['measurement', 'health_check', 'managed_hazard',
                        'special_managed', 'exposure_limit', 'permission', 'prohibited'])
        has_osha = has_osha or bool(_val(osha.get('raw_text', '')))
        if has_osha:
            osha_lines.append(_build_osha_text(name, osha))

        # 나. 화학물질관리법
        cc = regs.get('chemical_control', {})
        has_cc = any(cc.get(k) == "O" for k in
                     ['toxic', 'permitted', 'restricted', 'prohibited', 'accident'])
        has_cc = has_cc or bool(_val(cc.get('raw_text', '')))
        if has_cc:
            chem_control_lines.append(_build_chem_control_text(name, cc))

        # 다. 화학물질의 등록 및 평가 등에 관한 법률
        v = _val(regs.get('chemical_registration', ''))
        if v:
            chem_reg_lines.append(f"[{name}] {v}")

        # 라. 위험물안전관리법
        v = _val(regs.get('hazardous_materials', ''))
        if v:
            hazmat_lines.append(f"[{name}] {v}")

        # 마. 폐기물관리법
        v = _val(regs.get('waste_management', ''))
        if v:
            waste_lines.append(f"[{name}] {v}")

        # 바. 기타
        v = _val(regs.get('other_regulations', ''))
        if v:
            other_lines.append(f"[{name}] {v}")

    # 세션 상태에 반영
    s15 = st.session_state.section15_data

    if osha_lines:
        s15['가_산업안전보건법에_의한_규제'] = "\n\n".join(osha_lines)
    if chem_control_lines:
        s15['나_화학물질관리법에_의한_규제'] = "\n\n".join(chem_control_lines)
    if chem_reg_lines:
        s15['다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제'] = "\n".join(chem_reg_lines)
    if hazmat_lines:
        s15['라_위험물안전관리법에_의한_규제'] = "\n".join(hazmat_lines)
    if waste_lines:
        s15['마_폐기물관리법에_의한_규제'] = "\n".join(waste_lines)
    if other_lines:
        s15['바_기타_국내_및_외국법에_의한_규제'] = "\n".join(other_lines)


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

                    # ★ 핵심 수정: API 결과를 입력 필드에 자동 매핑
                    apply_api_results_to_section15(api_results)

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
                regs = result.get('regulations', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']}) - 상세 보기"):
                    raw = regs.get('raw_items', [])
                    if raw:
                        for item in raw:
                            st.write(f"  • **{item['name']}**: {item['detail']}")
                    else:
                        st.write("  (raw_items 없음)")

                    # 산업안전보건법 O/X 요약
                    osha = regs.get('occupational_safety', {})
                    st.write("**산업안전보건법 요약:**")
                    for k, label in [('measurement', '작업환경측정'), ('health_check', '특수건강진단'),
                                     ('managed_hazard', '관리대상유해물질'), ('exposure_limit', '노출기준설정')]:
                        st.write(f"  {label}: {'⭕' if osha.get(k) == 'O' else '❌'}")

        # 수동 재적용 버튼
        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section15(st.session_state['section15_api_results'])
            st.success("✅ API 조회 결과가 아래 입력란에 반영되었습니다.")
            st.rerun()

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
