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
                # 프로젝트 루트에 kosha_api_extended.py 파일이 있어야 합니다
                import sys
                import os
                # 현재 파일의 상위 디렉토리(프로젝트 루트)를 path에 추가
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
                                'chemId': chem_id,
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

                    # 조회 즉시 폼에 자동 반영
                    exposure_parts = []
                    acute_parts = []
                    skin_corrosion_parts = []
                    eye_damage_parts = []
                    resp_sens_parts = []
                    skin_sens_parts = []
                    carcino_parts = []
                    mutagen_parts = []
                    repro_parts = []
                    stot_single_parts = []
                    stot_repeated_parts = []
                    aspiration_parts = []

                    for result in api_results:
                        if 'error' in result:
                            continue
                        tox = result.get('toxicity', {})
                        mat_name = result.get('name', result.get('cas', ''))

                        def _val(v):
                            return v if v and v != "자료없음" else ""

                        if _val(tox.get('exposure_routes')):
                            exposure_parts.append(f"[{mat_name}] {tox['exposure_routes']}")

                        acute = tox.get('acute_toxicity', {})
                        acute_lines = []
                        if _val(acute.get('oral')):
                            acute_lines.append(f"경구: {acute['oral']}")
                        if _val(acute.get('dermal')):
                            acute_lines.append(f"경피: {acute['dermal']}")
                        if _val(acute.get('inhalation')):
                            acute_lines.append(f"흡입: {acute['inhalation']}")
                        if acute_lines:
                            acute_parts.append(f"[{mat_name}] " + " / ".join(acute_lines))

                        if _val(tox.get('skin_corrosion')):
                            skin_corrosion_parts.append(f"[{mat_name}] {tox['skin_corrosion']}")
                        if _val(tox.get('eye_damage')):
                            eye_damage_parts.append(f"[{mat_name}] {tox['eye_damage']}")
                        if _val(tox.get('respiratory_sensitization')):
                            resp_sens_parts.append(f"[{mat_name}] {tox['respiratory_sensitization']}")
                        if _val(tox.get('skin_sensitization')):
                            skin_sens_parts.append(f"[{mat_name}] {tox['skin_sensitization']}")
                        if _val(tox.get('carcinogenicity')):
                            carcino_parts.append(f"[{mat_name}] {tox['carcinogenicity']}")
                        if _val(tox.get('germ_cell_mutagenicity')):
                            mutagen_parts.append(f"[{mat_name}] {tox['germ_cell_mutagenicity']}")
                        if _val(tox.get('reproductive_toxicity')):
                            repro_parts.append(f"[{mat_name}] {tox['reproductive_toxicity']}")
                        if _val(tox.get('stot_single')):
                            stot_single_parts.append(f"[{mat_name}] {tox['stot_single']}")
                        if _val(tox.get('stot_repeated')):
                            stot_repeated_parts.append(f"[{mat_name}] {tox['stot_repeated']}")
                        if _val(tox.get('aspiration_hazard')):
                            aspiration_parts.append(f"[{mat_name}] {tox['aspiration_hazard']}")

                    st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = "\n".join(exposure_parts) if exposure_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['급성_독성'] = "\n".join(acute_parts) if acute_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['피부_부식성_또는_자극성'] = "\n".join(skin_corrosion_parts) if skin_corrosion_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['심한_눈_손상_또는_자극성'] = "\n".join(eye_damage_parts) if eye_damage_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['호흡기_과민성'] = "\n".join(resp_sens_parts) if resp_sens_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['피부_과민성'] = "\n".join(skin_sens_parts) if skin_sens_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['발암성'] = "\n".join(carcino_parts) if carcino_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['생식세포_변이원성'] = "\n".join(mutagen_parts) if mutagen_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['생식독성'] = "\n".join(repro_parts) if repro_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['특정_표적장기_독성_1회_노출'] = "\n".join(stot_single_parts) if stot_single_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['특정_표적장기_독성_반복_노출'] = "\n".join(stot_repeated_parts) if stot_repeated_parts else "자료없음"
                    st.session_state.section11_data['나_건강_유해성_정보']['흡인_유해성'] = "\n".join(aspiration_parts) if aspiration_parts else "자료없음"

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
                raw_items = tox.get('raw_items', [])
                chem_id = result.get('chemId', '?')
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']}, chemId: {chem_id}) - {len(raw_items)}개 항목", expanded=True):
                    if raw_items:
                        for item in raw_items:
                            iname = item.get('name', '')
                            detail = item.get('detail', '자료없음')
                            st.markdown(f"- **{iname}**: {detail}")
                    else:
                        st.warning("⚠️ API에서 반환된 독성 항목이 없습니다. (raw_items 비어있음)")
                    # 진단용: 파싱된 데이터 확인
                    with st.expander("🔧 파싱된 데이터 (진단용)"):
                        st.json(tox)

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

# 나-1. 급성 독성
st.markdown('<div class="sub-item">○ 급성 독성 (노출 가능한 모든 경로에 대해 기재)</div>', unsafe_allow_html=True)
급성독성 = st.text_area(
    "급성 독성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('급성_독성', ''),
    height=100,
    placeholder="예: 경구 LD50 (랫드): > 2000 mg/kg\n경피 LD50 (토끼): > 2000 mg/kg\n흡입 LC50 (랫드, 4hr): > 5 mg/L",
    key="acute_toxicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['급성_독성'] = 급성독성

# 나-2. 피부 부식성 또는 자극성
st.markdown('<div class="sub-item">○ 피부 부식성 또는 자극성</div>', unsafe_allow_html=True)
피부자극성 = st.text_area(
    "피부 부식성 또는 자극성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('피부_부식성_또는_자극성', ''),
    height=80,
    placeholder="예: 자료없음 / 피부에 자극을 일으킴 (구분 2)",
    key="skin_corrosion",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['피부_부식성_또는_자극성'] = 피부자극성

# 나-3. 심한 눈 손상 또는 자극성
st.markdown('<div class="sub-item">○ 심한 눈 손상 또는 자극성</div>', unsafe_allow_html=True)
눈자극성 = st.text_area(
    "심한 눈 손상 또는 자극성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('심한_눈_손상_또는_자극성', ''),
    height=80,
    placeholder="예: 자료없음 / 눈에 심한 자극을 일으킴 (구분 2A)",
    key="eye_damage",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['심한_눈_손상_또는_자극성'] = 눈자극성

# 나-4. 호흡기 과민성
st.markdown('<div class="sub-item">○ 호흡기 과민성</div>', unsafe_allow_html=True)
호흡기과민성 = st.text_area(
    "호흡기 과민성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('호흡기_과민성', ''),
    height=80,
    placeholder="예: 자료없음 / 흡입 시 알레르기성 반응, 천식 또는 호흡 곤란을 일으킬 수 있음",
    key="respiratory_sensitization",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['호흡기_과민성'] = 호흡기과민성

# 나-5. 피부 과민성
st.markdown('<div class="sub-item">○ 피부 과민성</div>', unsafe_allow_html=True)
피부과민성 = st.text_area(
    "피부 과민성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('피부_과민성', ''),
    height=80,
    placeholder="예: 자료없음 / 알레르기성 피부 반응을 일으킬 수 있음",
    key="skin_sensitization",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['피부_과민성'] = 피부과민성

# 나-6. 발암성
st.markdown('<div class="sub-item">○ 발암성</div>', unsafe_allow_html=True)
발암성 = st.text_area(
    "발암성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('발암성', ''),
    height=80,
    placeholder="예: 자료없음 / IARC: Group 1 (인체 발암성 물질)\nACGIH: A1 (확인된 인체 발암성 물질)",
    key="carcinogenicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['발암성'] = 발암성

# 나-7. 생식세포 변이원성
st.markdown('<div class="sub-item">○ 생식세포 변이원성</div>', unsafe_allow_html=True)
변이원성 = st.text_area(
    "생식세포 변이원성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('생식세포_변이원성', ''),
    height=80,
    placeholder="예: 자료없음 / 유전적인 결함을 일으킬 수 있음 (구분 1B)",
    key="germ_cell_mutagenicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['생식세포_변이원성'] = 변이원성

# 나-8. 생식독성
st.markdown('<div class="sub-item">○ 생식독성</div>', unsafe_allow_html=True)
생식독성 = st.text_area(
    "생식독성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('생식독성', ''),
    height=80,
    placeholder="예: 자료없음 / 태아 또는 생식능력에 손상을 일으킬 수 있음 (구분 1A)",
    key="reproductive_toxicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['생식독성'] = 생식독성

# 나-9. 특정 표적장기 독성 (1회 노출)
st.markdown('<div class="sub-item">○ 특정 표적장기 독성 (1회 노출)</div>', unsafe_allow_html=True)
표적장기1회 = st.text_area(
    "특정 표적장기 독성 (1회 노출)",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('특정_표적장기_독성_1회_노출', ''),
    height=80,
    placeholder="예: 자료없음 / 호흡기계 자극을 일으킬 수 있음 (구분 3)",
    key="stot_single",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['특정_표적장기_독성_1회_노출'] = 표적장기1회

# 나-10. 특정 표적장기 독성 (반복 노출)
st.markdown('<div class="sub-item">○ 특정 표적장기 독성 (반복 노출)</div>', unsafe_allow_html=True)
표적장기반복 = st.text_area(
    "특정 표적장기 독성 (반복 노출)",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('특정_표적장기_독성_반복_노출', ''),
    height=80,
    placeholder="예: 자료없음 / 장기간 또는 반복 노출되면 간에 손상을 일으킬 수 있음 (구분 2)",
    key="stot_repeated",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['특정_표적장기_독성_반복_노출'] = 표적장기반복

# 나-11. 흡인 유해성
st.markdown('<div class="sub-item">○ 흡인 유해성</div>', unsafe_allow_html=True)
흡인유해성 = st.text_area(
    "흡인 유해성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('흡인_유해성', ''),
    height=80,
    placeholder="예: 자료없음 / 삼켜서 기도로 유입되면 치명적일 수 있음 (구분 1)",
    key="aspiration_hazard",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['흡인_유해성'] = 흡인유해성

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
    
    건강유해성_항목 = [
        ('급성_독성', '급성 독성'),
        ('피부_부식성_또는_자극성', '피부 부식성 또는 자극성'),
        ('심한_눈_손상_또는_자극성', '심한 눈 손상 또는 자극성'),
        ('호흡기_과민성', '호흡기 과민성'),
        ('피부_과민성', '피부 과민성'),
        ('발암성', '발암성'),
        ('생식세포_변이원성', '생식세포 변이원성'),
        ('생식독성', '생식독성'),
        ('특정_표적장기_독성_1회_노출', '특정 표적장기 독성 (1회 노출)'),
        ('특정_표적장기_독성_반복_노출', '특정 표적장기 독성 (반복 노출)'),
        ('흡인_유해성', '흡인 유해성')
    ]
    
    for key, label in 건강유해성_항목:
        value = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        st.write(f"  ○ **{label}**: {value or '(미입력)'}")
    
    st.write("\n### 원본 데이터")
    st.json(st.session_state.section11_data)
