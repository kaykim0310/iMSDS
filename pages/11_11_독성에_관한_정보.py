import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

st.set_page_config(
    page_title="MSDS 섹션 11 - 독성에 관한 정보",
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
    .sub-item { background-color: #f5f5f5; padding: 5px 10px; margin: 5px 0; border-left: 3px solid #1976d2; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출_경로에_관한_정보': '',
        '나_건강_유해성_정보': {
            '급성_독성_경구': '',
            '급성_독성_경피': '',
            '급성_독성_흡입': '',
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

# 기존 데이터가 문자열이면 딕셔너리로 변환
if isinstance(st.session_state.section11_data.get('나_건강_유해성_정보'), str):
    old = st.session_state.section11_data.get('나_건강_유해성_정보', '')
    st.session_state.section11_data['나_건강_유해성_정보'] = {
        '급성_독성_경구': old, '급성_독성_경피': '', '급성_독성_흡입': '',
        '피부_부식성_또는_자극성': '', '심한_눈_손상_또는_자극성': '',
        '호흡기_과민성': '', '피부_과민성': '', '발암성': '', '생식세포_변이원성': '',
        '생식독성': '', '특정_표적장기_독성_1회_노출': '', '특정_표적장기_독성_반복_노출': '',
        '흡인_유해성': ''
    }

# 기존 '급성_독성' 단일 키가 있으면 경구/경피/흡입으로 마이그레이션
_health = st.session_state.section11_data.get('나_건강_유해성_정보', {})
if '급성_독성' in _health and '급성_독성_경구' not in _health:
    old_val = _health.pop('급성_독성', '')
    _health['급성_독성_경구'] = old_val
    _health.setdefault('급성_독성_경피', '')
    _health.setdefault('급성_독성_흡입', '')
elif '급성_독성' in _health:
    _health.pop('급성_독성', None)
# 누락 키 보충
for _k in ('급성_독성_경구', '급성_독성_경피', '급성_독성_흡입'):
    _health.setdefault(_k, '')


# ============================================================
# raw_items 기반 매핑
# ============================================================
# API 응답의 raw_items name 예시:
#   가능성이 높은 노출 경로에 관한 정보 / 노출경로
#   급성 독성-경구 / 경구 / 급성독성(경구) → 급성_독성_경구
#   급성 독성-경피 / 경피              → 급성_독성_경피
#   급성 독성-흡입 / 흡입 / 흡입(가스) / 흡입(증기) / 흡입(분진/미스트) → 급성_독성_흡입
#   피부 부식성/자극성 / 피부부식성 또는 자극성
#   심한 눈 손상/자극성 / 눈 손상 또는 자극성
#   호흡기 과민성 / 호흡기과민성
#   피부 과민성 / 피부과민성
#   발암성
#   생식세포 변이원성
#   생식독성
#   특정 표적장기 독성(1회 노출) / 특정표적장기독성(단일노출)
#   특정 표적장기 독성(반복 노출)
#   흡인 유해성

# 부모 헤더 (값이 "자료없음"인 상위 항목)
PARENT_HEADERS_11 = {'건강 유해성 정보', '건강유해성정보'}

def _is_valid(detail):
    if not detail:
        return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "")


def _classify_item_s11(item_name):
    """raw_item name으로 section11 필드 분류"""
    n = item_name.strip()

    if n in PARENT_HEADERS_11:
        return None

    # 가. 노출 경로
    if '노출' in n and '경로' in n:
        return 'exposure'

    # 급성 독성 - 경구
    if ('급성' in n and '독성' in n and '경구' in n) or n == '경구':
        return '급성_독성_경구'
    if '경구' in n and ('LD50' in n or 'LD' in n or '독성' in n or 'ATE' in n):
        return '급성_독성_경구'

    # 급성 독성 - 경피
    if ('급성' in n and '독성' in n and '경피' in n) or n == '경피':
        return '급성_독성_경피'
    if '경피' in n and ('LD50' in n or 'LD' in n or '독성' in n or 'ATE' in n):
        return '급성_독성_경피'

    # 급성 독성 - 흡입
    if ('급성' in n and '독성' in n and '흡입' in n) or n in ('흡입', '흡입(가스)', '흡입(증기)', '흡입(분진/미스트)'):
        return '급성_독성_흡입'
    if '흡입' in n and ('LC50' in n or 'LC' in n or '독성' in n or 'ATE' in n):
        return '급성_독성_흡입'

    # 급성 독성 - 경로 구분 불가 시 경구로 기본 배치
    if '급성' in n and '독성' in n:
        return '급성_독성_경구'

    # 피부 부식성/자극성 (피부 과민성과 구분!)
    if '피부' in n and ('부식' in n or '자극' in n) and '과민' not in n:
        return '피부_부식성_또는_자극성'

    # 심한 눈 손상/자극성
    if '눈' in n and ('손상' in n or '자극' in n):
        return '심한_눈_손상_또는_자극성'

    # 호흡기 과민성
    if '호흡기' in n and '과민' in n:
        return '호흡기_과민성'

    # 피부 과민성
    if '피부' in n and '과민' in n:
        return '피부_과민성'

    # 발암성
    if '발암' in n:
        return '발암성'

    # 생식세포 변이원성
    if '생식세포' in n and '변이' in n:
        return '생식세포_변이원성'

    # 생식독성
    if '생식독성' in n or ('생식' in n and '독성' in n):
        return '생식독성'

    # 특정 표적장기 독성 (1회)
    if '표적' in n and '장기' in n and ('1회' in n or '단일' in n):
        return '특정_표적장기_독성_1회_노출'

    # 특정 표적장기 독성 (반복)
    if '표적' in n and '장기' in n and '반복' in n:
        return '특정_표적장기_독성_반복_노출'

    # 특정 표적장기 독성 (구분 못하면 1회로 일단 배치)
    if '표적' in n and '장기' in n:
        return '특정_표적장기_독성_1회_노출'

    # 흡인 유해성
    if '흡인' in n and '유해' in n:
        return '흡인_유해성'

    return None


def apply_api_results_to_section11(api_results):
    """raw_items를 직접 분류하여 section11_data에 매핑"""
    all_exposure = []
    all_health = {k: [] for k in st.session_state.section11_data['나_건강_유해성_정보']}

    for result in api_results:
        if 'error' in result:
            continue

        name = result.get('name', result.get('cas', ''))
        raw_items = result.get('toxicity', {}).get('raw_items', [])
        if not raw_items:
            continue

        # 물질별 분류
        mat_exposure = []
        mat_health = {k: [] for k in all_health}

        for item in raw_items:
            item_name = item.get('name', '').strip()
            item_detail = item.get('detail', '').strip()

            if not _is_valid(item_detail):
                continue

            field = _classify_item_s11(item_name)

            if field == 'exposure':
                mat_exposure.append(item_detail)
            elif field and field in mat_health:
                mat_health[field].append(f"  ○ {item_name}: {item_detail}")

        # 노출 경로
        if mat_exposure:
            all_exposure.append(f"[{name}] " + " / ".join(mat_exposure))

        # 건강 유해성
        for fk in all_health:
            if mat_health[fk]:
                all_health[fk].append(f"[{name}]\n" + "\n".join(mat_health[fk]))

    # 세션 상태 반영
    s11 = st.session_state.section11_data
    if all_exposure:
        new_val = "\n".join(all_exposure)
        s11['가_가능성이_높은_노출_경로에_관한_정보'] = new_val
        st.session_state["exposure_routes"] = new_val

    for fk, lines in all_health.items():
        if lines:
            new_val = "\n\n".join(lines)
            s11['나_건강_유해성_정보'][fk] = new_val
            st.session_state[f"s11_{fk}"] = new_val


# ============================================================
# KOSHA API 연동 섹션
# ============================================================
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

            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    if 'section11_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과 (API 원본):**")
        for result in st.session_state['section11_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
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

# ============================================================
# 입력 필드
# ============================================================

# 가. 노출 경로
st.markdown('<div class="subsection-header">가. 가능성이 높은 노출 경로에 관한 정보</div>', unsafe_allow_html=True)
가_val = st.text_area(
    "노출 경로",
    value=st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', ''),
    height=100,
    placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구",
    key="exposure_routes",
    label_visibility="collapsed"
)
st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = 가_val

# 나. 건강 유해성 정보
st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

health_items = [
    ('급성_독성_경구', '○ 급성 독성 - 경구 (Oral)',
     "예: LD50 (경구, 랫드): > 2000 mg/kg\nATE(경구): > 5000 mg/kg"),
    ('급성_독성_경피', '○ 급성 독성 - 경피 (Dermal)',
     "예: LD50 (경피, 토끼): > 2000 mg/kg\nATE(경피): > 5000 mg/kg"),
    ('급성_독성_흡입', '○ 급성 독성 - 흡입 (Inhalation)',
     "예: LC50 (흡입, 랫드, 4hr): > 5 mg/L (증기)\nATE(흡입): > 20 mg/L"),
    ('피부_부식성_또는_자극성', '○ 피부 부식성 또는 자극성',
     "예: 피부에 자극을 일으킴 (구분 2)"),
    ('심한_눈_손상_또는_자극성', '○ 심한 눈 손상 또는 자극성',
     "예: 눈에 심한 자극을 일으킴 (구분 2A)"),
    ('호흡기_과민성', '○ 호흡기 과민성',
     "예: 흡입 시 알레르기성 반응을 일으킬 수 있음"),
    ('피부_과민성', '○ 피부 과민성',
     "예: 알레르기성 피부 반응을 일으킬 수 있음"),
    ('발암성', '○ 발암성',
     "예: IARC: Group 1 / ACGIH: A1"),
    ('생식세포_변이원성', '○ 생식세포 변이원성',
     "예: 유전적인 결함을 일으킬 수 있음 (구분 1B)"),
    ('생식독성', '○ 생식독성',
     "예: 태아 또는 생식능력에 손상을 일으킬 수 있음"),
    ('특정_표적장기_독성_1회_노출', '○ 특정 표적장기 독성 (1회 노출)',
     "예: 호흡기계 자극을 일으킬 수 있음 (구분 3)"),
    ('특정_표적장기_독성_반복_노출', '○ 특정 표적장기 독성 (반복 노출)',
     "예: 장기간 노출되면 간에 손상을 일으킬 수 있음 (구분 2)"),
    ('흡인_유해성', '○ 흡인 유해성',
     "예: 삼켜서 기도로 유입되면 치명적일 수 있음 (구분 1)"),
]

for key, label, placeholder in health_items:
    st.markdown(f'<div class="sub-item">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(
        label,
        value=st.session_state.section11_data['나_건강_유해성_정보'].get(key, ''),
        height=80,
        placeholder=placeholder,
        key=f"s11_{key}",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['나_건강_유해성_정보'][key] = val

st.info("💡 **참고**: 가.항 및 나.항을 합쳐서 노출 경로와 건강 유해성 정보를 함께 기재할 수 있습니다.")

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 노출 경로**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', '') or '(미입력)')
    st.write("\n**나. 건강 유해성 정보**")
    for key, label, _ in health_items:
        val = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        st.write(f"  {label}: {val or '(미입력)'}")
    st.json(st.session_state.section11_data)
