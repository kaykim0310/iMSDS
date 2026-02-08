import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

st.set_page_config(page_title="MSDS 섹션 12 - 환경에 미치는 영향", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    * { font-family: 'Nanum Gothic', sans-serif !important; }
    /* Streamlit 아이콘 폰트 복원 */
    [data-testid="stIconMaterial"],
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stTextInput > div > div > input { background-color: #f0f0f0; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

if 'section12_data' not in st.session_state:
    st.session_state.section12_data = {
        '가_생태독성': '', '나_잔류성_및_분해성': '', '다_생물_농축성': '',
        '라_토양_이동성': '', '마_기타_유해_영향': ''
    }

PARENT_HEADERS = {'생태독성', '잔류성 및 분해성', '생물농축성', '생물 농축성'}

def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "")

def _classify_item(item_name):
    n = item_name.strip()
    if n in PARENT_HEADERS: return None
    if n in ('어류', '갑각류', '조류'): return '가_생태독성'
    if '수생' in n or '생태' in n: return '가_생태독성'
    if n in ('잔류성', '분해성'): return '나_잔류성_및_분해성'
    if '잔류' in n or '분해' in n:
        if '생분해' in n: return '다_생물_농축성'
        return '나_잔류성_및_분해성'
    if n in ('농축성', '생분해성'): return '다_생물_농축성'
    if '농축' in n: return '다_생물_농축성'
    if '토양' in n and '이동' in n: return '라_토양_이동성'
    if n == '토양이동성': return '라_토양_이동성'
    if '기타' in n and '유해' in n: return '마_기타_유해_영향'
    return None

def apply_api_results_to_section12(api_results):
    all_field_data = {k: [] for k in st.session_state.section12_data}
    for result in api_results:
        if 'error' in result: continue
        name = result.get('name', result.get('cas', ''))
        raw_items = result.get('environmental', {}).get('raw_items', [])
        if not raw_items: continue
        material_fields = {k: [] for k in all_field_data}
        for item in raw_items:
            item_name = item.get('name', '').strip()
            item_detail = item.get('detail', '').strip()
            if not _is_valid(item_detail): continue
            field_key = _classify_item(item_name)
            if field_key: material_fields[field_key].append(f"  ○ {item_name}: {item_detail}")
        for fk in all_field_data:
            if material_fields[fk]:
                all_field_data[fk].append(f"[{name}]\n" + "\n".join(material_fields[fk]))
    s12 = st.session_state.section12_data
    for fk, lines in all_field_data.items():
        if lines:
            new_val = "\n\n".join(lines)
            s12[fk] = new_val
            st.session_state[f"s12_{fk}"] = new_val

with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 환경 영향 정보를 자동 조회합니다.")
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
        if st.button("🔍 KOSHA API에서 환경 영향 정보 조회", type="primary", key="api_query_btn"):
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from kosha_api_extended import get_environmental_info, search_by_cas
                import time
                with st.spinner("KOSHA API에서 데이터를 조회 중입니다..."):
                    api_results = []
                    for cas in cas_list:
                        search_result = search_by_cas(cas)
                        if search_result.get('success'):
                            chem_id = search_result['chemId']
                            chem_name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            env_info = get_environmental_info(chem_id)
                            api_results.append({'cas': cas, 'name': chem_name, 'environmental': env_info})
                        else:
                            api_results.append({'cas': cas, 'name': cas, 'error': search_result.get('error', '조회 실패')})
                        time.sleep(0.3)
                    st.session_state['section12_api_results'] = api_results
                    apply_api_results_to_section12(api_results)
                    st.rerun()
            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")
    if 'section12_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과 (API 원본):**")
        for result in st.session_state['section12_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                env = result.get('environmental', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']})"):
                    for item in env.get('raw_items', []):
                        marker = "🔹" if _is_valid(item['detail']) else "⬜"
                        st.write(f"  {marker} **{item['name']}**: {item['detail']}")
        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section12(st.session_state['section12_api_results'])
            st.success("✅ 반영 완료!")
            st.rerun()

st.markdown("---")

section_items = [
    ('가_생태독성', '가. 생태독성', "예:\n어류: LC50 = 10 mg/L (96hr)\n갑각류: EC50 = 5 mg/L (48hr)\n조류: EC50 = 2 mg/L (72hr)"),
    ('나_잔류성_및_분해성', '나. 잔류성 및 분해성', "예:\n잔류성: log Kow = 2.73\n분해성: 이분해성"),
    ('다_생물_농축성', '다. 생물 농축성', "예:\n농축성: BCF = 90\n생분해성: 80% (20일)"),
    ('라_토양_이동성', '라. 토양 이동성', "예:\n토양 흡착 계수(Koc): 자료없음"),
    ('마_기타_유해_영향', '마. 기타 유해 영향', "예:\n오존층 파괴 물질: 해당없음"),
]

for key, label, placeholder in section_items:
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=st.session_state.section12_data.get(key, ''), height=120 if key == '가_생태독성' else 100, placeholder=placeholder, key=f"s12_{key}", label_visibility="collapsed")
    st.session_state.section12_data[key] = val

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 12 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 12가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for key, label, _ in section_items:
        st.write(f"**{label}**")
        st.text(st.session_state.section12_data.get(key, '') or '(미입력)')
    st.json(st.session_state.section12_data)
