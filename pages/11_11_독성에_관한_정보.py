import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

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
    .sub-item {
        background-color: #f5f5f5;
        padding: 5px 10px;
        margin: 5px 0;
        border-left: 3px solid #1976d2;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화 (공식 양식 기준)
if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출_경로에_관한_정보': '',
        '나_건강_유해성_정보': {
            '급성_독성': '',
            '피부_부식성_또는_자극성': '',
            '심한_눈_손상_또는_자극성': '',
            '호흡기_과민성': '',
            '피부_과민성': '',
            '발암성': '',
            '생식세포_변이원성': '',
            '생식독성': '',
            '특정_표적장기_독성_1회_노출': '',
            '특정_표적장기_독성_반복_노출': '',
            '흡인_유해성': ''
        }
    }

# 기존 데이터가 문자열 형태인 경우 새 형식으로 변환
if isinstance(st.session_state.section11_data.get('나_건강_유해성_정보'), str):
    old_value = st.session_state.section11_data.get('나_건강_유해성_정보', '')
    st.session_state.section11_data['나_건강_유해성_정보'] = {
        '급성_독성': old_value,
        '피부_부식성_또는_자극성': '',
        '심한_눈_손상_또는_자극성': '',
        '호흡기_과민성': '',
        '피부_과민성': '',
        '발암성': '',
        '생식세포_변이원성': '',
        '생식독성': '',
        '특정_표적장기_독성_1회_노출': '',
        '특정_표적장기_독성_반복_노출': '',
        '흡인_유해성': ''
    }


# ============================================================
# API 결과 → 입력 필드 자동 매핑 헬퍼 함수
# ============================================================
def _val(text):
    """자료없음이면 빈 문자열 반환, 아니면 원본 반환"""
    if not text or text.strip() in ("자료없음", ""):
        return ""
    return text.strip()


def apply_api_results_to_section11(api_results):
    """
    API 조회 결과를 section11_data 세션 상태에 매핑합니다.
    여러 물질이 있으면 '물질명: 값' 형태로 합쳐서 기재합니다.
    """
    exposure_lines = []
    acute_lines = []
    skin_corrosion_lines = []
    eye_damage_lines = []
    resp_sens_lines = []
    skin_sens_lines = []
    carcinogenicity_lines = []
    mutagenicity_lines = []
    repro_tox_lines = []
    stot_single_lines = []
    stot_repeated_lines = []
    aspiration_lines = []

    for result in api_results:
        if 'error' in result:
            continue

        name = result.get('name', result.get('cas', ''))
        tox = result.get('toxicity', {})

        # 가. 노출 경로
        v = _val(tox.get('exposure_routes', ''))
        if v:
            exposure_lines.append(f"[{name}] {v}")

        # 급성 독성 — 경구/경피/흡입을 합쳐서 기재
        acute_parts = []
        oral = _val(tox.get('acute_toxicity', {}).get('oral', ''))
        dermal = _val(tox.get('acute_toxicity', {}).get('dermal', ''))
        inhal = _val(tox.get('acute_toxicity', {}).get('inhalation', ''))
        if oral:
            acute_parts.append(f"경구: {oral}")
        if dermal:
            acute_parts.append(f"경피: {dermal}")
        if inhal:
            acute_parts.append(f"흡입: {inhal}")
        if acute_parts:
            acute_lines.append(f"[{name}] " + " / ".join(acute_parts))

        # 나머지 항목들
        for field, lines_list in [
            ('skin_corrosion', skin_corrosion_lines),
            ('eye_damage', eye_damage_lines),
            ('respiratory_sensitization', resp_sens_lines),
            ('skin_sensitization', skin_sens_lines),
            ('carcinogenicity', carcinogenicity_lines),
            ('germ_cell_mutagenicity', mutagenicity_lines),
            ('reproductive_toxicity', repro_tox_lines),
            ('stot_single', stot_single_lines),
            ('stot_repeated', stot_repeated_lines),
            ('aspiration_hazard', aspiration_lines),
        ]:
            v = _val(tox.get(field, ''))
            if v:
                lines_list.append(f"[{name}] {v}")

    # 세션 상태에 반영 (기존 값이 비어있을 때만 덮어쓰기)
    def _join(lines):
        return "\n".join(lines) if lines else ""

    s11 = st.session_state.section11_data

    if exposure_lines:
        s11['가_가능성이_높은_노출_경로에_관한_정보'] = _join(exposure_lines)

    mapping = {
        '급성_독성': acute_lines,
        '피부_부식성_또는_자극성': skin_corrosion_lines,
        '심한_눈_손상_또는_자극성': eye_damage_lines,
        '호흡기_과민성': resp_sens_lines,
        '피부_과민성': skin_sens_lines,
        '발암성': carcinogenicity_lines,
        '생식세포_변이원성': mutagenicity_lines,
        '생식독성': repro_tox_lines,
        '특정_표적장기_독성_1회_노출': stot_single_lines,
        '특정_표적장기_독성_반복_노출': stot_repeated_lines,
        '흡인_유해성': aspiration_lines,
    }

    for key, lines in mapping.items():
        if lines:
            s11['나_건강_유해성_정보'][key] = _join(lines)


# ============================================================
# KOSHA API 연동 섹션
# ============================================================
with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 독성 정보를 자동 조회합니다.")

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

        if st.button("🔍 KOSHA API에서 독성 정보 조회", type="primary", key="api_query_btn"):
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from kosha_api_extended import get_toxicity_info, search_by_cas
                import time

                with st.spinner("KOSHA API에서 데이터를 조회 중입니다..."):
                    api_results = []

                    for cas in cas_list:
                        search_result = search_by_cas(cas)
                        if search_result.get('success'):
                            chem_id = search_result['chemId']
                            name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            toxicity = get_toxicity_info(chem_id)
                            api_results.append({
                                'cas': cas,
                                'name': name,
                                'toxicity': toxicity
                            })
                        else:
                            api_results.append({
                                'cas': cas,
                                'name': cas,
                                'error': search_result.get('error', '조회 실패')
                            })
                        time.sleep(0.3)

                    st.session_state['section11_api_results'] = api_results

                    # ★ 핵심 수정: API 결과를 입력 필드에 자동 매핑
                    apply_api_results_to_section11(api_results)

                    st.rerun()

            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # API 결과 표시
    if 'section11_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과:**")

        for result in st.session_state['section11_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                tox = result.get('toxicity', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']}) - 상세 보기"):
                    # raw_items 표시
                    raw = tox.get('raw_items', [])
                    if raw:
                        for item in raw:
                            st.write(f"  • **{item['name']}**: {item['detail']}")
                    else:
                        st.write("  (raw_items 없음)")

        # ★ 수동 재적용 버튼 (이미 조회한 결과를 다시 매핑하고 싶을 때)
        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section11(st.session_state['section11_api_results'])
            st.success("✅ API 조회 결과가 아래 입력란에 반영되었습니다.")
            st.rerun()

st.markdown("---")

# ============================================================
# 공식 양식 기준 입력 필드
# ============================================================

# 가. 가능성이 높은 노출 경로에 관한 정보
st.markdown('<div class="subsection-header">가. 가능성이 높은 노출 경로에 관한 정보</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "가능성이 높은 노출 경로에 관한 정보",
    value=st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', ''),
    height=100,
    placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구",
    key="exposure_routes",
    label_visibility="collapsed"
)
st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = 가_내용

# 나. 건강 유해성 정보
st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

# 건강 유해성 하위 항목 정의
health_hazard_items = [
    ('급성_독성', '○ 급성 독성 (노출 가능한 모든 경로에 대해 기재)',
     "예: 경구 LD50 (랫드): > 2000 mg/kg\n경피 LD50 (토끼): > 2000 mg/kg\n흡입 LC50 (랫드, 4hr): > 5 mg/L"),
    ('피부_부식성_또는_자극성', '○ 피부 부식성 또는 자극성',
     "예: 자료없음 / 피부에 자극을 일으킴 (구분 2)"),
    ('심한_눈_손상_또는_자극성', '○ 심한 눈 손상 또는 자극성',
     "예: 자료없음 / 눈에 심한 자극을 일으킴 (구분 2A)"),
    ('호흡기_과민성', '○ 호흡기 과민성',
     "예: 자료없음 / 흡입 시 알레르기성 반응, 천식 또는 호흡 곤란을 일으킬 수 있음"),
    ('피부_과민성', '○ 피부 과민성',
     "예: 자료없음 / 알레르기성 피부 반응을 일으킬 수 있음"),
    ('발암성', '○ 발암성',
     "예: 자료없음 / IARC: Group 1 (인체 발암성 물질)\nACGIH: A1 (확인된 인체 발암성 물질)"),
    ('생식세포_변이원성', '○ 생식세포 변이원성',
     "예: 자료없음 / 유전적인 결함을 일으킬 수 있음 (구분 1B)"),
    ('생식독성', '○ 생식독성',
     "예: 자료없음 / 태아 또는 생식능력에 손상을 일으킬 수 있음 (구분 1A)"),
    ('특정_표적장기_독성_1회_노출', '○ 특정 표적장기 독성 (1회 노출)',
     "예: 자료없음 / 호흡기계 자극을 일으킬 수 있음 (구분 3)"),
    ('특정_표적장기_독성_반복_노출', '○ 특정 표적장기 독성 (반복 노출)',
     "예: 자료없음 / 장기간 또는 반복 노출되면 간에 손상을 일으킬 수 있음 (구분 2)"),
    ('흡인_유해성', '○ 흡인 유해성',
     "예: 자료없음 / 삼켜서 기도로 유입되면 치명적일 수 있음 (구분 1)"),
]

for key, label, placeholder in health_hazard_items:
    st.markdown(f'<div class="sub-item">{label}</div>', unsafe_allow_html=True)
    value = st.text_area(
        label,
        value=st.session_state.section11_data['나_건강_유해성_정보'].get(key, ''),
        height=80,
        placeholder=placeholder,
        key=f"s11_{key}",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['나_건강_유해성_정보'][key] = value

# 참고 안내
st.info("💡 **참고**: 가.항 및 나.항을 합쳐서 노출 경로와 건강 유해성 정보를 함께 기재할 수 있습니다.")

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 11. 독성에 관한 정보")

    st.write("**가. 가능성이 높은 노출 경로에 관한 정보**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', '') or '(미입력)')

    st.write("\n**나. 건강 유해성 정보**")

    for key, label, _ in health_hazard_items:
        value = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        st.write(f"  {label.split('○')[1].strip() if '○' in label else label}: {value or '(미입력)'}")

    st.write("\n### 원본 데이터")
    st.json(st.session_state.section11_data)import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

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
    .sub-item {
        background-color: #f5f5f5;
        padding: 5px 10px;
        margin: 5px 0;
        border-left: 3px solid #1976d2;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화 (공식 양식 기준)
if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출_경로에_관한_정보': '',
        '나_건강_유해성_정보': {
            '급성_독성': '',
            '피부_부식성_또는_자극성': '',
            '심한_눈_손상_또는_자극성': '',
            '호흡기_과민성': '',
            '피부_과민성': '',
            '발암성': '',
            '생식세포_변이원성': '',
            '생식독성': '',
            '특정_표적장기_독성_1회_노출': '',
            '특정_표적장기_독성_반복_노출': '',
            '흡인_유해성': ''
        }
    }

# 기존 데이터가 문자열 형태인 경우 새 형식으로 변환
if isinstance(st.session_state.section11_data.get('나_건강_유해성_정보'), str):
    old_value = st.session_state.section11_data.get('나_건강_유해성_정보', '')
    st.session_state.section11_data['나_건강_유해성_정보'] = {
        '급성_독성': old_value,
        '피부_부식성_또는_자극성': '',
        '심한_눈_손상_또는_자극성': '',
        '호흡기_과민성': '',
        '피부_과민성': '',
        '발암성': '',
        '생식세포_변이원성': '',
        '생식독성': '',
        '특정_표적장기_독성_1회_노출': '',
        '특정_표적장기_독성_반복_노출': '',
        '흡인_유해성': ''
    }


# ============================================================
# API 결과 → 입력 필드 자동 매핑 헬퍼 함수
# ============================================================
def _val(text):
    """자료없음이면 빈 문자열 반환, 아니면 원본 반환"""
    if not text or text.strip() in ("자료없음", ""):
        return ""
    return text.strip()


def apply_api_results_to_section11(api_results):
    """
    API 조회 결과를 section11_data 세션 상태에 매핑합니다.
    여러 물질이 있으면 '물질명: 값' 형태로 합쳐서 기재합니다.
    """
    exposure_lines = []
    acute_lines = []
    skin_corrosion_lines = []
    eye_damage_lines = []
    resp_sens_lines = []
    skin_sens_lines = []
    carcinogenicity_lines = []
    mutagenicity_lines = []
    repro_tox_lines = []
    stot_single_lines = []
    stot_repeated_lines = []
    aspiration_lines = []

    for result in api_results:
        if 'error' in result:
            continue

        name = result.get('name', result.get('cas', ''))
        tox = result.get('toxicity', {})

        # 가. 노출 경로
        v = _val(tox.get('exposure_routes', ''))
        if v:
            exposure_lines.append(f"[{name}] {v}")

        # 급성 독성 — 경구/경피/흡입을 합쳐서 기재
        acute_parts = []
        oral = _val(tox.get('acute_toxicity', {}).get('oral', ''))
        dermal = _val(tox.get('acute_toxicity', {}).get('dermal', ''))
        inhal = _val(tox.get('acute_toxicity', {}).get('inhalation', ''))
        if oral:
            acute_parts.append(f"경구: {oral}")
        if dermal:
            acute_parts.append(f"경피: {dermal}")
        if inhal:
            acute_parts.append(f"흡입: {inhal}")
        if acute_parts:
            acute_lines.append(f"[{name}] " + " / ".join(acute_parts))

        # 나머지 항목들
        for field, lines_list in [
            ('skin_corrosion', skin_corrosion_lines),
            ('eye_damage', eye_damage_lines),
            ('respiratory_sensitization', resp_sens_lines),
            ('skin_sensitization', skin_sens_lines),
            ('carcinogenicity', carcinogenicity_lines),
            ('germ_cell_mutagenicity', mutagenicity_lines),
            ('reproductive_toxicity', repro_tox_lines),
            ('stot_single', stot_single_lines),
            ('stot_repeated', stot_repeated_lines),
            ('aspiration_hazard', aspiration_lines),
        ]:
            v = _val(tox.get(field, ''))
            if v:
                lines_list.append(f"[{name}] {v}")

    # 세션 상태에 반영 (기존 값이 비어있을 때만 덮어쓰기)
    def _join(lines):
        return "\n".join(lines) if lines else ""

    s11 = st.session_state.section11_data

    if exposure_lines:
        s11['가_가능성이_높은_노출_경로에_관한_정보'] = _join(exposure_lines)

    mapping = {
        '급성_독성': acute_lines,
        '피부_부식성_또는_자극성': skin_corrosion_lines,
        '심한_눈_손상_또는_자극성': eye_damage_lines,
        '호흡기_과민성': resp_sens_lines,
        '피부_과민성': skin_sens_lines,
        '발암성': carcinogenicity_lines,
        '생식세포_변이원성': mutagenicity_lines,
        '생식독성': repro_tox_lines,
        '특정_표적장기_독성_1회_노출': stot_single_lines,
        '특정_표적장기_독성_반복_노출': stot_repeated_lines,
        '흡인_유해성': aspiration_lines,
    }

    for key, lines in mapping.items():
        if lines:
            s11['나_건강_유해성_정보'][key] = _join(lines)


# ============================================================
# KOSHA API 연동 섹션
# ============================================================
with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 독성 정보를 자동 조회합니다.")

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

        if st.button("🔍 KOSHA API에서 독성 정보 조회", type="primary", key="api_query_btn"):
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from kosha_api_extended import get_toxicity_info, search_by_cas
                import time

                with st.spinner("KOSHA API에서 데이터를 조회 중입니다..."):
                    api_results = []

                    for cas in cas_list:
                        search_result = search_by_cas(cas)
                        if search_result.get('success'):
                            chem_id = search_result['chemId']
                            name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            toxicity = get_toxicity_info(chem_id)
                            api_results.append({
                                'cas': cas,
                                'name': name,
                                'toxicity': toxicity
                            })
                        else:
                            api_results.append({
                                'cas': cas,
                                'name': cas,
                                'error': search_result.get('error', '조회 실패')
                            })
                        time.sleep(0.3)

                    st.session_state['section11_api_results'] = api_results

                    # ★ 핵심 수정: API 결과를 입력 필드에 자동 매핑
                    apply_api_results_to_section11(api_results)

                    st.rerun()

            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # API 결과 표시
    if 'section11_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과:**")

        for result in st.session_state['section11_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                tox = result.get('toxicity', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']}) - 상세 보기"):
                    # raw_items 표시
                    raw = tox.get('raw_items', [])
                    if raw:
                        for item in raw:
                            st.write(f"  • **{item['name']}**: {item['detail']}")
                    else:
                        st.write("  (raw_items 없음)")

        # ★ 수동 재적용 버튼 (이미 조회한 결과를 다시 매핑하고 싶을 때)
        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section11(st.session_state['section11_api_results'])
            st.success("✅ API 조회 결과가 아래 입력란에 반영되었습니다.")
            st.rerun()

st.markdown("---")

# ============================================================
# 공식 양식 기준 입력 필드
# ============================================================

# 가. 가능성이 높은 노출 경로에 관한 정보
st.markdown('<div class="subsection-header">가. 가능성이 높은 노출 경로에 관한 정보</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "가능성이 높은 노출 경로에 관한 정보",
    value=st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', ''),
    height=100,
    placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구",
    key="exposure_routes",
    label_visibility="collapsed"
)
st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = 가_내용

# 나. 건강 유해성 정보
st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

# 건강 유해성 하위 항목 정의
health_hazard_items = [
    ('급성_독성', '○ 급성 독성 (노출 가능한 모든 경로에 대해 기재)',
     "예: 경구 LD50 (랫드): > 2000 mg/kg\n경피 LD50 (토끼): > 2000 mg/kg\n흡입 LC50 (랫드, 4hr): > 5 mg/L"),
    ('피부_부식성_또는_자극성', '○ 피부 부식성 또는 자극성',
     "예: 자료없음 / 피부에 자극을 일으킴 (구분 2)"),
    ('심한_눈_손상_또는_자극성', '○ 심한 눈 손상 또는 자극성',
     "예: 자료없음 / 눈에 심한 자극을 일으킴 (구분 2A)"),
    ('호흡기_과민성', '○ 호흡기 과민성',
     "예: 자료없음 / 흡입 시 알레르기성 반응, 천식 또는 호흡 곤란을 일으킬 수 있음"),
    ('피부_과민성', '○ 피부 과민성',
     "예: 자료없음 / 알레르기성 피부 반응을 일으킬 수 있음"),
    ('발암성', '○ 발암성',
     "예: 자료없음 / IARC: Group 1 (인체 발암성 물질)\nACGIH: A1 (확인된 인체 발암성 물질)"),
    ('생식세포_변이원성', '○ 생식세포 변이원성',
     "예: 자료없음 / 유전적인 결함을 일으킬 수 있음 (구분 1B)"),
    ('생식독성', '○ 생식독성',
     "예: 자료없음 / 태아 또는 생식능력에 손상을 일으킬 수 있음 (구분 1A)"),
    ('특정_표적장기_독성_1회_노출', '○ 특정 표적장기 독성 (1회 노출)',
     "예: 자료없음 / 호흡기계 자극을 일으킬 수 있음 (구분 3)"),
    ('특정_표적장기_독성_반복_노출', '○ 특정 표적장기 독성 (반복 노출)',
     "예: 자료없음 / 장기간 또는 반복 노출되면 간에 손상을 일으킬 수 있음 (구분 2)"),
    ('흡인_유해성', '○ 흡인 유해성',
     "예: 자료없음 / 삼켜서 기도로 유입되면 치명적일 수 있음 (구분 1)"),
]

for key, label, placeholder in health_hazard_items:
    st.markdown(f'<div class="sub-item">{label}</div>', unsafe_allow_html=True)
    value = st.text_area(
        label,
        value=st.session_state.section11_data['나_건강_유해성_정보'].get(key, ''),
        height=80,
        placeholder=placeholder,
        key=f"s11_{key}",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['나_건강_유해성_정보'][key] = value

# 참고 안내
st.info("💡 **참고**: 가.항 및 나.항을 합쳐서 노출 경로와 건강 유해성 정보를 함께 기재할 수 있습니다.")

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 11. 독성에 관한 정보")

    st.write("**가. 가능성이 높은 노출 경로에 관한 정보**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', '') or '(미입력)')

    st.write("\n**나. 건강 유해성 정보**")

    for key, label, _ in health_hazard_items:
        value = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        st.write(f"  {label.split('○')[1].strip() if '○' in label else label}: {value or '(미입력)'}")

    st.write("\n### 원본 데이터")
    st.json(st.session_state.section11_data)
