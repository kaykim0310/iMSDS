import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

st.set_page_config(page_title="MSDS 섹션 11 - 독성에 관한 정보", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출경로에_관한_정보': '',
        '나_건강_유해성_정보': {
            '급성독성_경구': '', '급성독성_경피': '', '급성독성_흡입': '',
            '피부_부식성_또는_자극성': '', '심한_눈_손상_또는_자극성': '',
            '호흡기_과민성': '', '피부_과민성': '', '발암성': '', '생식세포_변이원성': '',
            '생식독성': '', '특정_표적장기_독성_1회노출': '', '특정_표적장기_독성_반복노출': '',
            '흡인_유해성': ''
        }
    }

def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "")

def _classify_item_s11(item_name):
    n = item_name.strip()
    if '경구' in n: return '급성독성_경구'
    if '경피' in n: return '급성독성_경피'
    if '흡입' in n and '급성' in n: return '급성독성_흡입'
    if '피부' in n and ('부식' in n or '자극' in n): return '피부_부식성_또는_자극성'
    if '눈' in n and ('손상' in n or '자극' in n): return '심한_눈_손상_또는_자극성'
    if '호흡기' in n and '과민' in n: return '호흡기_과민성'
    if '피부' in n and '과민' in n: return '피부_과민성'
    if '발암' in n: return '발암성'
    if '변이원' in n or '돌연변이' in n: return '생식세포_변이원성'
    if '생식독성' in n or '생식' in n: return '생식독성'
    if '1회' in n and '표적' in n: return '특정_표적장기_독성_1회노출'
    if '반복' in n and '표적' in n: return '특정_표적장기_독성_반복노출'
    if '흡인' in n: return '흡인_유해성'
    return None

def apply_api_results_to_section11(api_results):
    all_field_data = {k: [] for k in st.session_state.section11_data['나_건강_유해성_정보']}
    exposure_info = []
    for result in api_results:
        if 'error' in result: continue
        name = result.get('name', result.get('cas', ''))
        raw_items = result.get('toxicity', {}).get('raw_items', [])
        if not raw_items: continue
        material_fields = {k: [] for k in all_field_data}
        for item in raw_items:
            item_name = item.get('name', '').strip()
            item_detail = item.get('detail', '').strip()
            if not _is_valid(item_detail): continue
            field_key = _classify_item_s11(item_name)
            if field_key:
                material_fields[field_key].append(f"  ○ {item_name}: {item_detail}")
        for fk in all_field_data:
            if material_fields[fk]:
                all_field_data[fk].append(f"[{name}]\n" + "\n".join(material_fields[fk]))
    s11 = st.session_state.section11_data
    for fk, lines in all_field_data.items():
        if lines:
            new_val = "\n\n".join(lines)
            s11['나_건강_유해성_정보'][fk] = new_val
            st.session_state[f"s11_{fk}"] = new_val

with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 독성 정보를 자동 조회합니다.")
    cas_list = []
    materials_info = []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                cas_list.append(comp['CAS번호'])
                materials_info.append({'name': comp['물질명'], 'cas': comp['CAS번호']})
    if cas_list:
        st.success(f"✅ 섹션 3에서 {len(cas_list)}개의 CAS 번호를 찾았습니다.")
        for mat in materials_info: st.write(f"  • **{mat['name']}** (CAS: {mat['cas']})")
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
                            chem_name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            toxicity = get_toxicity_info(chem_id)
                            api_results.append({'cas': cas, 'name': chem_name, 'toxicity': toxicity})
                        else:
                            api_results.append({'cas': cas, 'name': cas, 'error': search_result.get('error', '조회 실패')})
                        time.sleep(0.3)
                    st.session_state['section11_api_results'] = api_results
                    apply_api_results_to_section11(api_results)
                    st.rerun()
            except ImportError: st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e: st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")
    if 'section11_api_results' in st.session_state:
        st.markdown("---")
        for result in st.session_state['section11_api_results']:
            if 'error' in result: st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                tox = result.get('toxicity', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']})"):
                    for item in tox.get('raw_items', []):
                        marker = "🔹" if _is_valid(item['detail']) else "⬜"
                        st.write(f"  {marker} **{item['name']}**: {item['detail']}")
        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section11(st.session_state['section11_api_results'])
            st.success("✅ 반영 완료!")
            st.rerun()

st.markdown("---")

st.markdown('<div class="subsection-header">가. 가능성이 높은 노출경로에 관한 정보</div>', unsafe_allow_html=True)
노출경로 = st.text_area("노출경로", value=st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', ''), height=100, placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구", key="exposure_routes", label_visibility="collapsed")
st.session_state.section11_data['가_가능성이_높은_노출경로에_관한_정보'] = 노출경로

st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

health_items = [
    ('급성독성_경구', '급성독성 (경구)', "예: LD50 = 5800 mg/kg (Rat)"),
    ('급성독성_경피', '급성독성 (경피)', "예: LD50 > 2000 mg/kg (Rabbit)"),
    ('급성독성_흡입', '급성독성 (흡입)', "예: LC50 = 76 mg/L (Rat, 4hr)"),
    ('피부_부식성_또는_자극성', '피부 부식성 또는 자극성', "예: 구분 2 (피부 자극성)"),
    ('심한_눈_손상_또는_자극성', '심한 눈 손상 또는 자극성', "예: 구분 2A (눈 자극성)"),
    ('호흡기_과민성', '호흡기 과민성', "예: 자료없음"),
    ('피부_과민성', '피부 과민성', "예: 자료없음"),
    ('발암성', '발암성', "예: IARC - Group 3 (인체발암성 미분류)"),
    ('생식세포_변이원성', '생식세포 변이원성', "예: 자료없음"),
    ('생식독성', '생식독성', "예: 자료없음"),
    ('특정_표적장기_독성_1회노출', '특정 표적장기 독성 (1회 노출)', "예: 구분 3 (호흡기계 자극, 마취작용)"),
    ('특정_표적장기_독성_반복노출', '특정 표적장기 독성 (반복 노출)', "예: 자료없음"),
    ('흡인_유해성', '흡인 유해성', "예: 자료없음"),
]

for key, label, placeholder in health_items:
    st.markdown(f"**{label}**")
    val = st.text_area(label, value=st.session_state.section11_data['나_건강_유해성_정보'].get(key, ''), height=80, placeholder=placeholder, key=f"s11_{key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][key] = val

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 노출경로**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', '') or '(미입력)')
    st.write("**나. 건강 유해성 정보**")
    for key, label, _ in health_items:
        val = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        if val: st.write(f"  • **{label}**: {val}")
    st.json(st.session_state.section11_data)
