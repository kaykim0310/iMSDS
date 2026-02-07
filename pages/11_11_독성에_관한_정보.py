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
    .stNumberInput > div > div > input { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
    .sub-item { background-color: #f5f5f5; padding: 5px 10px; margin: 5px 0; border-left: 3px solid #1976d2; }
    .ate-result { background-color: #e8f5e9; padding: 12px; border-radius: 5px; border-left: 4px solid #4caf50; margin: 10px 0; }
    .ate-warn { background-color: #fff3e0; padding: 12px; border-radius: 5px; border-left: 4px solid #ff9800; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# ============================================================
# 세션 상태 초기화
# ============================================================
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

if 'section11_categories' not in st.session_state:
    st.session_state.section11_categories = {}

# 기존 데이터 마이그레이션
if isinstance(st.session_state.section11_data.get('나_건강_유해성_정보'), str):
    old = st.session_state.section11_data.get('나_건강_유해성_정보', '')
    st.session_state.section11_data['나_건강_유해성_정보'] = {
        '급성_독성_경구': old, '급성_독성_경피': '', '급성_독성_흡입': '',
        '피부_부식성_또는_자극성': '', '심한_눈_손상_또는_자극성': '',
        '호흡기_과민성': '', '피부_과민성': '', '발암성': '', '생식세포_변이원성': '',
        '생식독성': '', '특정_표적장기_독성_1회_노출': '', '특정_표적장기_독성_반복_노출': '',
        '흡인_유해성': ''
    }

_health = st.session_state.section11_data.get('나_건강_유해성_정보', {})
if '급성_독성' in _health and '급성_독성_경구' not in _health:
    old_val = _health.pop('급성_독성', '')
    _health['급성_독성_경구'] = old_val
    _health.setdefault('급성_독성_경피', '')
    _health.setdefault('급성_독성_흡입', '')
elif '급성_독성' in _health:
    _health.pop('급성_독성', None)
for _k in ('급성_독성_경구', '급성_독성_경피', '급성_독성_흡입'):
    _health.setdefault(_k, '')


# ============================================================
# 분류 기준 데이터 (GHS)
# ============================================================
ACUTE_CRITERIA = {
    '경구': {
        'unit': 'mg/kg',
        'ranges': [(5, '구분 1'), (50, '구분 2'), (300, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
        'ate_convert': {1: 0.5, 2: 5, 3: 100, 4: 500},
        'table_header': '경구 LD50 (mg/kg)',
    },
    '경피': {
        'unit': 'mg/kg',
        'ranges': [(50, '구분 1'), (200, '구분 2'), (1000, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
        'ate_convert': {1: 5, 2: 50, 3: 300, 4: 1100},
        'table_header': '경피 LD50 (mg/kg)',
    },
    '흡입': {
        'unit': 'mg/L (증기, 4hr)',
        'ranges': [(0.5, '구분 1'), (2.0, '구분 2'), (10, '구분 3'), (20, '구분 4')],
        'ate_convert': {1: 0.05, 2: 0.5, 3: 3, 4: 11},
        'table_header': '흡입 LC50-증기 (mg/L, 4hr)',
    },
}

def classify_acute(value, route):
    if value is None or value <= 0:
        return '미분류'
    for threshold, category in ACUTE_CRITERIA[route]['ranges']:
        if value <= threshold:
            return category
    return '미분류'

def calc_atemix(components, route):
    total = 0.0
    unknown_pct = 0.0
    valid_count = 0
    for comp in components:
        ci = comp.get('concentration', 0)
        atei = comp.get('ate', 0)
        if ci > 0 and atei > 0:
            total += ci / atei
            valid_count += 1
        elif ci > 0 and atei == 0:
            unknown_pct += ci
    if total <= 0:
        return None, unknown_pct, valid_count
    atemix = 100.0 / total
    return atemix, unknown_pct, valid_count


CLASSIFICATION_HINTS = {
    '피부_부식성_또는_자극성': {
        'options': ['미분류', '구분 1A (부식성)', '구분 1B (부식성)', '구분 1C (부식성)', '구분 2 (자극성)'],
        'hint': """**[혼합물 분류 기준]**
| 구분 | 가산 방식 | 비가산 방식(강산/강염기) |
|-----|---------|-------------------|
| **구분 1 (부식성)** | 피부부식성 구분1 합계 ≥ **5%** | pH ≤2 or pH ≥11.5 성분 ≥1%, 구분1 ≥1% |
| **구분 2 (자극성)** | 구분1: 1~5%, 구분2 ≥ **10%**, (구분1×10)+구분2 ≥ **10%** | 구분2 성분 ≥ **3%** |

💡 **pH 기준:** pH ≤2 또는 pH ≥11.5 → 구분 1 (산/알칼리 완충능 고려)""",
    },
    '심한_눈_손상_또는_자극성': {
        'options': ['미분류', '구분 1 (심한 눈 손상)', '구분 2A (자극성)', '구분 2B (경미한 자극성)'],
        'hint': """**[혼합물 분류 기준]**
| 구분 | 기준 |
|-----|-----|
| **구분 1 (심한 눈 손상)** | (눈 구분1 + 피부 구분1) 합계 ≥ **3%** |
| **구분 2A (자극성)** | (눈구분1+피부구분1): 1~3%, 눈구분2 ≥ **10%**, (구분1×10)+구분2 ≥ **10%** |
| **구분 2B (경미)** | 시험에서 7일 내 회복 |

💡 피부부식성 구분1 → 눈 구분1로도 간주""",
    },
    '호흡기_과민성': {
        'options': ['미분류', '구분 1', '구분 1A', '구분 1B'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1A** | 호흡기 과민성 1A 성분 ≥ **0.1%** |
| **구분 1B** | 호흡기 과민성 1B 성분: 고체/액체 ≥ **1.0%**, 가스 ≥ **0.2%** |
| **구분 1** | 하위구분 불가 시 (≥0.1% 또는 ≥1.0%) |""",
    },
    '피부_과민성': {
        'options': ['미분류', '구분 1', '구분 1A', '구분 1B'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1A** | 피부 과민성 1A 성분 ≥ **0.1%** |
| **구분 1B** | 피부 과민성 1B 성분 ≥ **1.0%** |
| **구분 1** | 하위구분 불가 시 (≥0.1% 또는 ≥1.0%) |""",
    },
    '발암성': {
        'options': ['미분류', '구분 1A', '구분 1B', '구분 2'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1A** | 발암성 1A 성분 ≥ **0.1%** |
| **구분 1B** | 발암성 1B 성분 ≥ **0.1%** |
| **구분 2** | 발암성 2 성분 ≥ **1.0%** |

💡 **IARC 참고:** Group 1 → 구분1A, Group 2A → 구분1B, Group 2B → 구분2 (직접 대응은 아님)""",
    },
    '생식세포_변이원성': {
        'options': ['미분류', '구분 1A', '구분 1B', '구분 2'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1A** | 변이원성 1A 성분 ≥ **0.1%** |
| **구분 1B** | 변이원성 1B 성분 ≥ **0.1%** |
| **구분 2** | 변이원성 2 성분 ≥ **1.0%** |""",
    },
    '생식독성': {
        'options': ['미분류', '구분 1A', '구분 1B', '구분 2', '수유독성'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1A** | 생식독성 1A 성분 ≥ **0.3%** |
| **구분 1B** | 생식독성 1B 성분 ≥ **0.3%** |
| **구분 2** | 생식독성 2 성분 ≥ **3.0%** |
| **수유독성** | 수유독성 성분 ≥ **0.3%** |""",
    },
    '특정_표적장기_독성_1회_노출': {
        'options': ['미분류', '구분 1', '구분 2', '구분 3 (호흡기자극)', '구분 3 (마취작용)'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1** | STOT-1회 구분1 성분 ≥ **10%** |
| **구분 2** | STOT-1회 구분1: 1~10%, 또는 구분2 ≥ **10%** |
| **구분 3** | 호흡기자극 또는 마취 해당 성분 ≥ **20%** |

💡 **단일물질 용량기준:** 경구 ≤300 mg/kg → 구분1, 300~2000 → 구분2""",
    },
    '특정_표적장기_독성_반복_노출': {
        'options': ['미분류', '구분 1', '구분 2'],
        'hint': """**[혼합물 분류 기준 - 함유량]**
| 구분 | 기준 |
|-----|-----|
| **구분 1** | STOT-반복 구분1 성분 ≥ **10%** |
| **구분 2** | STOT-반복 구분1: 1~10%, 또는 구분2 ≥ **10%** |

💡 **단일물질 기준(90일):** 경구 ≤10 mg/kg/일 → 구분1, 10~100 → 구분2
⚠️ **28일 시험:** 기준값 × 3 적용""",
    },
    '흡인_유해성': {
        'options': ['미분류', '구분 1', '구분 2'],
        'hint': """**[혼합물 분류 기준]**
| 구분 | 기준 |
|-----|-----|
| **구분 1** | 흡인유해성 구분1 성분 ≥ **10%** + 40℃ 동점도 ≤ **20.5** mm²/s |
| **구분 2** | 흡인유해성 구분2 성분 ≥ **10%** + 40℃ 동점도 ≤ **14** mm²/s |

💡 주로 **탄화수소류** (석유계 용제, 나프타 등) 해당""",
    },
}


# ============================================================
# raw_items 기반 API 매핑
# ============================================================
PARENT_HEADERS_11 = {'건강 유해성 정보', '건강유해성정보'}

def _is_valid(detail):
    if not detail:
        return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "")

def _classify_item_s11(item_name):
    n = item_name.strip()
    if n in PARENT_HEADERS_11:
        return None
    if '노출' in n and '경로' in n:
        return 'exposure'
    if ('급성' in n and '독성' in n and '경구' in n) or n == '경구':
        return '급성_독성_경구'
    if '경구' in n and ('LD50' in n or 'LD' in n or '독성' in n or 'ATE' in n):
        return '급성_독성_경구'
    if ('급성' in n and '독성' in n and '경피' in n) or n == '경피':
        return '급성_독성_경피'
    if '경피' in n and ('LD50' in n or 'LD' in n or '독성' in n or 'ATE' in n):
        return '급성_독성_경피'
    if ('급성' in n and '독성' in n and '흡입' in n) or n in ('흡입', '흡입(가스)', '흡입(증기)', '흡입(분진/미스트)'):
        return '급성_독성_흡입'
    if '흡입' in n and ('LC50' in n or 'LC' in n or '독성' in n or 'ATE' in n):
        return '급성_독성_흡입'
    if '급성' in n and '독성' in n:
        return '급성_독성_경구'
    if '피부' in n and ('부식' in n or '자극' in n) and '과민' not in n:
        return '피부_부식성_또는_자극성'
    if '눈' in n and ('손상' in n or '자극' in n):
        return '심한_눈_손상_또는_자극성'
    if '호흡기' in n and '과민' in n:
        return '호흡기_과민성'
    if '피부' in n and '과민' in n:
        return '피부_과민성'
    if '발암' in n:
        return '발암성'
    if '생식세포' in n and '변이' in n:
        return '생식세포_변이원성'
    if '생식독성' in n or ('생식' in n and '독성' in n):
        return '생식독성'
    if '표적' in n and '장기' in n and ('1회' in n or '단일' in n):
        return '특정_표적장기_독성_1회_노출'
    if '표적' in n and '장기' in n and '반복' in n:
        return '특정_표적장기_독성_반복_노출'
    if '표적' in n and '장기' in n:
        return '특정_표적장기_독성_1회_노출'
    if '흡인' in n and '유해' in n:
        return '흡인_유해성'
    return None


def apply_api_results_to_section11(api_results):
    all_exposure = []
    all_health = {k: [] for k in st.session_state.section11_data['나_건강_유해성_정보']}

    for result in api_results:
        if 'error' in result:
            continue
        name = result.get('name', result.get('cas', ''))
        raw_items = result.get('toxicity', {}).get('raw_items', [])
        if not raw_items:
            continue

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

        if mat_exposure:
            all_exposure.append(f"[{name}] " + " / ".join(mat_exposure))
        for fk in all_health:
            if mat_health[fk]:
                all_health[fk].append(f"[{name}]\n" + "\n".join(mat_health[fk]))

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

# ============================================================
# 나. 건강 유해성 정보
# ============================================================
st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

# ----------------------------------------------------------
# 구성성분 정보 가져오기
# ----------------------------------------------------------
components_from_s3 = []
if 'section3_data' in st.session_state:
    for comp in st.session_state.get('section3_data', {}).get('components', []):
        if comp.get('물질명'):
            raw_content = comp.get('함유량(%)', '')
            try:
                pct = float(raw_content)
            except:
                pct = 0.0
            components_from_s3.append({
                'name': comp['물질명'],
                'cas': comp.get('CAS번호', ''),
                'pct': pct,
            })

# ----------------------------------------------------------
# 급성 독성 3개: ATEmix 계산기 포함
# ----------------------------------------------------------
ACUTE_ITEMS = [
    ('급성_독성_경구', '○ 급성 독성 - 경구 (Oral)', '경구',
     "예: LD50 (경구, 랫드): > 2000 mg/kg\nATE(경구): > 5000 mg/kg"),
    ('급성_독성_경피', '○ 급성 독성 - 경피 (Dermal)', '경피',
     "예: LD50 (경피, 토끼): > 2000 mg/kg\nATE(경피): > 5000 mg/kg"),
    ('급성_독성_흡입', '○ 급성 독성 - 흡입 (Inhalation)', '흡입',
     "예: LC50 (흡입, 랫드, 4hr): > 5 mg/L (증기)\nATE(흡입): > 20 mg/L"),
]

for field_key, label, route, placeholder in ACUTE_ITEMS:
    st.markdown(f'<div class="sub-item">{label}</div>', unsafe_allow_html=True)

    # 2열: 좌=텍스트, 우=구분 표시
    left_col, right_col = st.columns([3, 1])

    with left_col:
        val = st.text_area(
            label,
            value=st.session_state.section11_data['나_건강_유해성_정보'].get(field_key, ''),
            height=80,
            placeholder=placeholder,
            key=f"s11_{field_key}",
            label_visibility="collapsed"
        )
        st.session_state.section11_data['나_건강_유해성_정보'][field_key] = val

    with right_col:
        saved_cat = st.session_state.section11_categories.get(field_key, '미분류')
        if saved_cat != '미분류':
            st.markdown(f"**구분 판정:**")
            st.markdown(f"### {saved_cat}")
        else:
            st.markdown("**구분 판정:**")
            st.markdown("*아래 계산기 사용*")

    # ATEmix 계산기
    criteria = ACUTE_CRITERIA[route]
    with st.expander(f"🧮 ATEmix 계산기 - {route} ({criteria['unit']})", expanded=False):

        # 분류기준표
        st.markdown(f"**📋 {criteria['table_header']} 분류 기준:**")
        range_data = []
        for threshold, cat in criteria['ranges']:
            range_data.append({'구분': cat, f'기준 ({criteria["unit"]})': f'≤ {threshold}'})
        range_data.append({'구분': '미분류', f'기준 ({criteria["unit"]})': f'> {criteria["ranges"][-1][0]}'})
        st.table(pd.DataFrame(range_data))

        # ATE 변환표
        st.markdown(f"**🔄 ATE 변환표** (구분만 알고 수치 모를 때 대입):")
        ate_conv = criteria['ate_convert']
        conv_data = [{'구분': f'구분 {k}', f'ATE 변환값 ({criteria["unit"]})': v} for k, v in ate_conv.items()]
        st.table(pd.DataFrame(conv_data))

        st.markdown("---")
        st.markdown("**📝 성분별 ATE 값 입력:**")
        st.caption("공식: **100 / ATEmix = Σ(Ci / ATEi)**  →  **ATEmix = 100 / Σ(Ci / ATEi)**")

        # 동적 성분 수 관리
        extra_key = f"ate_{route}_extra_count"
        if extra_key not in st.session_state:
            st.session_state[extra_key] = 0

        num_rows = max(len(components_from_s3), 2) + st.session_state[extra_key]

        # 헤더
        hc = st.columns([3, 1.5, 2, 1.5])
        with hc[0]:
            st.markdown("**성분명**")
        with hc[1]:
            st.markdown("**함유량 (%)**")
        with hc[2]:
            st.markdown(f"**ATE값 ({criteria['unit']})**")
        with hc[3]:
            st.markdown("**개별 구분**")

        calc_components = []

        for i in range(num_rows):
            rc = st.columns([3, 1.5, 2, 1.5])

            default_name = components_from_s3[i]['name'] if i < len(components_from_s3) else ''
            default_pct = components_from_s3[i]['pct'] if i < len(components_from_s3) else 0.0

            with rc[0]:
                comp_name = st.text_input(
                    f"이름{i}", value=default_name,
                    key=f"ate_{route}_n_{i}",
                    label_visibility="collapsed", placeholder=f"성분 {i+1}"
                )
            with rc[1]:
                ci = st.number_input(
                    f"Ci{i}", min_value=0.0, max_value=100.0,
                    value=float(default_pct),
                    step=0.1, format="%.1f",
                    key=f"ate_{route}_ci_{i}",
                    label_visibility="collapsed"
                )
            with rc[2]:
                atei = st.number_input(
                    f"ATE{i}", min_value=0.0, value=0.0,
                    step=1.0, format="%.2f",
                    key=f"ate_{route}_atei_{i}",
                    label_visibility="collapsed"
                )
            with rc[3]:
                if atei > 0:
                    st.markdown(f"**{classify_acute(atei, route)}**")
                else:
                    st.markdown("*-*")

            if ci > 0:
                calc_components.append({'name': comp_name, 'concentration': ci, 'ate': atei})

        # 성분 추가 버튼
        if st.button("➕ 행 추가", key=f"ate_{route}_add_btn"):
            st.session_state[extra_key] += 1
            st.rerun()

        # 계산 결과
        st.markdown("---")
        if calc_components:
            atemix, unknown_pct, valid_count = calc_atemix(calc_components, route)

            if atemix is not None:
                category = classify_acute(atemix, route)
                st.markdown(f"""<div class="ate-result">
                    <b>📊 ATEmix 계산 결과:</b><br>
                    • Σ(Ci/ATEi) = <b>{100.0/atemix:.4f}</b><br>
                    • ATEmix = 100 / {100.0/atemix:.4f} = <b>{atemix:.2f} {criteria['unit']}</b><br>
                    • 판정: <b>🏷️ {category}</b>
                    {f'<br><br>⚠️ ATE값 미입력 성분 함유량 합계: {unknown_pct:.1f}%' if unknown_pct > 0 else ''}
                </div>""", unsafe_allow_html=True)

                st.session_state.section11_categories[field_key] = category

                if unknown_pct > 10:
                    st.markdown(f"""<div class="ate-warn">
                        ⚠️ <b>주의:</b> ATE값을 알 수 없는 성분이 10% 초과 ({unknown_pct:.1f}%)입니다.<br>
                        공식 2 적용 필요: 100/ATEmix = Σ(Ci/ATEi) + Σ(알수없는 성분%)
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("ℹ️ ATE값이 입력된 성분이 없습니다. 각 성분의 ATE값을 입력해주세요.")
                st.session_state.section11_categories[field_key] = '미분류'
        else:
            st.info("ℹ️ 함유량(%)이 입력된 성분이 없습니다. 섹션 3에 성분을 등록하거나 직접 입력해주세요.")
            st.session_state.section11_categories[field_key] = '미분류'


# ----------------------------------------------------------
# 나머지 8개 항목: 구분 선택 + 판단근거 힌트
# ----------------------------------------------------------
OTHER_ITEMS = [
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

for key, label, placeholder in OTHER_ITEMS:
    st.markdown(f'<div class="sub-item">{label}</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns([3, 1])

    with left_col:
        val = st.text_area(
            label,
            value=st.session_state.section11_data['나_건강_유해성_정보'].get(key, ''),
            height=80,
            placeholder=placeholder,
            key=f"s11_{key}",
            label_visibility="collapsed"
        )
        st.session_state.section11_data['나_건강_유해성_정보'][key] = val

    with right_col:
        hint_info = CLASSIFICATION_HINTS.get(key, {})
        options = hint_info.get('options', ['미분류'])

        saved_cat = st.session_state.section11_categories.get(key, '미분류')
        default_idx = options.index(saved_cat) if saved_cat in options else 0

        selected_cat = st.selectbox(
            "구분",
            options=options,
            index=default_idx,
            key=f"s11_cat_{key}",
        )
        st.session_state.section11_categories[key] = selected_cat

    # 판단근거 힌트
    hint_text = hint_info.get('hint', '')
    if hint_text:
        with st.expander(f"💡 분류 기준 힌트 - {label.replace('○ ', '')}", expanded=False):
            st.markdown(hint_text)


# ============================================================
# 분류 요약
# ============================================================
st.markdown("---")
st.markdown('<div class="subsection-header">📊 건강 유해성 분류 요약</div>', unsafe_allow_html=True)

summary_data = []
all_keys = [a[0] for a in ACUTE_ITEMS] + [o[0] for o in OTHER_ITEMS]
all_labels = {a[0]: a[1] for a in ACUTE_ITEMS}
all_labels.update({o[0]: o[1] for o in OTHER_ITEMS})

for k in all_keys:
    cat = st.session_state.section11_categories.get(k, '미분류')
    lbl = all_labels.get(k, k).replace('○ ', '')
    summary_data.append({'항목': lbl, '구분 판정': cat})

summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

classified_count = sum(1 for d in summary_data if d['구분 판정'] != '미분류')
st.info(f"📋 총 {len(summary_data)}개 항목 중 **{classified_count}개** 분류 완료")


# ============================================================
# 저장
# ============================================================
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 노출 경로**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', '') or '(미입력)')
    st.write("\n**나. 건강 유해성 정보**")
    for k in all_keys:
        lbl = all_labels.get(k, k)
        val = st.session_state.section11_data['나_건강_유해성_정보'].get(k, '')
        cat = st.session_state.section11_categories.get(k, '미분류')
        st.write(f"  {lbl}: {val or '(미입력)'} → **[{cat}]**")
    st.json(st.session_state.section11_data)
    st.json(st.session_state.section11_categories)
