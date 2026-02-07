import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

st.set_page_config(
    page_title="MSDS 섹션 15 - 법적 규제현황",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    * { font-family: 'Nanum Gothic', sans-serif !important; }
    .stTextInput > div > div > input { background-color: #f0f0f0; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>15. 법적 규제현황</h2></div>', unsafe_allow_html=True)

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
# raw_items 기반 매핑
# ============================================================
def _is_valid(detail):
    if not detail:
        return False
    return detail.strip() not in ("자료없음", "해당없음", "")


def _classify_item_s15(item_name):
    """raw_item name으로 필드 분류"""
    n = item_name.strip()

    if '산업안전보건법' in n:
        return '가_산업안전보건법에_의한_규제'
    if '화학물질관리법' in n or '유해화학물질' in n:
        return '나_화학물질관리법에_의한_규제'
    if ('등록' in n and '평가' in n) or '화평법' in n or '화학물질의 등록' in n:
        return '다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제'
    if '위험물' in n and ('안전' in n or '관리' in n):
        return '라_위험물안전관리법에_의한_규제'
    if '폐기물' in n and ('관리' in n or '법' in n):
        return '마_폐기물관리법에_의한_규제'
    if '기타' in n and ('국내' in n or '외국' in n or '법' in n):
        return '바_기타_국내_및_외국법에_의한_규제'

    # 하위 항목일 수 있으므로 추가 키워드 매칭
    # (API가 세부 항목을 별도로 내려주는 경우 대비)
    if n in ('작업환경측정대상물질', '관리대상유해물질', '특수건강진단대상물질',
             '특별관리물질', '노출기준설정물질', '허가대상물질', '제조등금지물질',
             '작업환경측정', '특수건강진단', '관리대상', '특별관리', '노출기준'):
        return '가_산업안전보건법에_의한_규제'

    if n in ('유독물질', '허가물질', '제한물질', '금지물질', '사고대비물질'):
        return '나_화학물질관리법에_의한_규제'

    if n in ('기존화학물질', '등록대상', '중점관리물질'):
        return '다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제'

    # 외국법 관련
    if 'OSHA' in n or 'CERCLA' in n or 'EPCRA' in n or '로테르담' in n or '스톡홀름' in n or '몬트리올' in n:
        return '바_기타_국내_및_외국법에_의한_규제'

    return None


def apply_api_results_to_section15(api_results):
    """raw_items를 직접 분류하여 section15_data에 매핑"""
    all_field_data = {k: [] for k in st.session_state.section15_data}

    for result in api_results:
        if 'error' in result:
            continue

        name = result.get('name', result.get('cas', ''))
        raw_items = result.get('regulations', {}).get('raw_items', [])
        if not raw_items:
            continue

        material_fields = {k: [] for k in all_field_data}

        for item in raw_items:
            item_name = item.get('name', '').strip()
            item_detail = item.get('detail', '').strip()

            if not _is_valid(item_detail):
                continue

            field_key = _classify_item_s15(item_name)
            if field_key:
                material_fields[field_key].append(f"  ○ {item_name}: {item_detail}")

        for fk in all_field_data:
            if material_fields[fk]:
                all_field_data[fk].append(f"[{name}]\n" + "\n".join(material_fields[fk]))

    s15 = st.session_state.section15_data
    for fk, lines in all_field_data.items():
        if lines:
            s15[fk] = "\n\n".join(lines)


# ============================================================
# KOSHA API 연동 섹션
# ============================================================
with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 법적 규제현황을 자동 조회합니다.")

    cas_list = []
    materials_info = []

    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                cas_list.append(comp['CAS번호'])
                materials_info.append({'name': comp['물질명'], 'cas': comp['CAS번호']})

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
                            chem_name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            regulations = get_legal_regulations(chem_id)
                            api_results.append({'cas': cas, 'name': chem_name, 'regulations': regulations})
                        else:
                            api_results.append({'cas': cas, 'name': cas, 'error': search_result.get('error', '조회 실패')})
                        time.sleep(0.3)

                    st.session_state['section15_api_results'] = api_results
                    apply_api_results_to_section15(api_results)
                    st.rerun()

            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    if 'section15_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과 (API 원본):**")
        for result in st.session_state['section15_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                regs = result.get('regulations', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']})"):
                    for item in regs.get('raw_items', []):
                        marker = "🔹" if _is_valid(item['detail']) else "⬜"
                        st.write(f"  {marker} **{item['name']}**: {item['detail']}")

        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section15(st.session_state['section15_api_results'])
            st.success("✅ 반영 완료!")
            st.rerun()

st.markdown("---")

# ============================================================
# 입력 필드
# ============================================================
section_items = [
    ('가_산업안전보건법에_의한_규제', '가. 산업안전보건법에 의한 규제',
     "예:\n• 작업환경측정대상물질: 해당\n• 관리대상유해물질: 해당\n• 특수건강진단대상물질: 해당"),
    ('나_화학물질관리법에_의한_규제', '나. 화학물질관리법에 의한 규제',
     "예:\n• 유독물질: 해당\n• 사고대비물질: 해당"),
    ('다_화학물질의_등록_및_평가_등에_관한_법률에_의한_규제', '다. 화학물질의 등록 및 평가 등에 관한 법률에 의한 규제',
     "예:\n• 기존화학물질: 해당 (KE-xxxxx)"),
    ('라_위험물안전관리법에_의한_규제', '라. 위험물안전관리법에 의한 규제',
     "예:\n• 제4류 인화성액체, 제1석유류"),
    ('마_폐기물관리법에_의한_규제', '마. 폐기물관리법에 의한 규제',
     "예:\n• 지정폐기물: 해당 (폐유기용제류)"),
    ('바_기타_국내_및_외국법에_의한_규제', '바. 기타 국내 및 외국법에 의한 규제',
     "예:\n[국내법]\n• 잔류성유기오염물질 관리법: 해당없음\n[외국법]\n• 미국 OSHA: 해당"),
]

for key, label, placeholder in section_items:
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(
        label,
        value=st.session_state.section15_data.get(key, ''),
        height=130,
        placeholder=placeholder,
        key=f"s15_{key}",
        label_visibility="collapsed"
    )
    st.session_state.section15_data[key] = val

st.info("""💡 **참고사항**
- 각 법규별 해당 여부는 관련 부처 고시를 확인하세요.
- 해당사항이 없는 경우 "해당없음"으로 기재하세요.
- 화학물질정보시스템(https://icis.me.go.kr) 등을 참조할 수 있습니다.
""")

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 15 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 15가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for key, label, _ in section_items:
        st.write(f"**{label}**")
        st.text(st.session_state.section15_data.get(key, '') or '(미입력)')
        st.write("")
    st.json(st.session_state.section15_data)
