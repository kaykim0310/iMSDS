import streamlit as st
import pandas as pd
import re
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
    .ate-result-box { background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50; margin: 8px 0; }
    .ate-warn-box { background-color: #fff3e0; padding: 10px; border-radius: 5px; border-left: 4px solid #ff9800; margin: 8px 0; }
    .ate-badge { display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: bold; color: white; font-size: 1.1em; }
    .badge-cat1 { background-color: #c62828; }
    .badge-cat2 { background-color: #e65100; }
    .badge-cat3 { background-color: #f57f17; color: #333; }
    .badge-cat4 { background-color: #fbc02d; color: #333; }
    .badge-cat5 { background-color: #aed581; color: #333; }
    .badge-none { background-color: #90a4ae; }
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
            '급성_독성_경구': '', '급성_독성_경피': '', '급성_독성_흡입': '',
            '피부_부식성_또는_자극성': '', '심한_눈_손상_또는_자극성': '',
            '호흡기_과민성': '', '피부_과민성': '', '발암성': '',
            '생식세포_변이원성': '', '생식독성': '',
            '특정_표적장기_독성_1회_노출': '', '특정_표적장기_독성_반복_노출': '',
            '흡인_유해성': ''
        }
    }

if 'section11_categories' not in st.session_state:
    st.session_state.section11_categories = {}

if 'section11_atemix_results' not in st.session_state:
    st.session_state.section11_atemix_results = {}

# API에서 파싱한 ATE 프리필 값 {route: {물질명: ate_value}}
if 'section11_ate_prefill' not in st.session_state:
    st.session_state.section11_ate_prefill = {'경구': {}, '경피': {}, '흡입': {}}

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
# GHS 급성독성 분류 기준
# ============================================================
ACUTE_CRITERIA = {
    '경구': {
        'unit': 'mg/kg', 'type': 'LD50',
        'ranges': [(5, '구분 1'), (50, '구분 2'), (300, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
        'ate_convert': {1: 0.5, 2: 5, 3: 100, 4: 500},
    },
    '경피': {
        'unit': 'mg/kg', 'type': 'LD50',
        'ranges': [(50, '구분 1'), (200, '구분 2'), (1000, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
        'ate_convert': {1: 5, 2: 50, 3: 300, 4: 1100},
    },
    '흡입': {
        'unit': 'mg/L (증기 4hr)', 'type': 'LC50',
        'ranges': [(0.5, '구분 1'), (2.0, '구분 2'), (10, '구분 3'), (20, '구분 4')],
        'ate_convert': {1: 0.05, 2: 0.5, 3: 3, 4: 11},
    },
}

def classify_acute(value, route):
    if value is None or value <= 0:
        return '미분류'
    for threshold, category in ACUTE_CRITERIA[route]['ranges']:
        if value <= threshold:
            return category
    return '미분류'

def calc_atemix(components):
    total = 0.0
    unknown_pct = 0.0
    for comp in components:
        ci = comp.get('ci', 0)
        atei = comp.get('ate', 0)
        if ci > 0 and atei > 0:
            total += ci / atei
        elif ci > 0:
            unknown_pct += ci
    if total <= 0:
        return None, unknown_pct
    return 100.0 / total, unknown_pct

def _get_badge_class(cat_str):
    if '구분 1' in cat_str: return 'badge-cat1'
    if '구분 2' in cat_str: return 'badge-cat2'
    if '구분 3' in cat_str: return 'badge-cat3'
    if '구분 4' in cat_str: return 'badge-cat4'
    if '구분 5' in cat_str: return 'badge-cat5'
    return 'badge-none'


# ============================================================
# LD50/LC50 숫자 추출 함수
# ============================================================
def _extract_numeric(text):
    """독성값 문자열에서 숫자 추출. 예: 'LD50 800 mg/kg' → 800.0"""
    if not text:
        return None
    # > 또는 ≥ 기호가 있으면 그 뒤의 숫자
    # 숫자 패턴: 정수 또는 소수, 쉼표 포함 가능
    text = text.replace(',', '')
    patterns = [
        r'(?:LD50|LC50|ATE)\s*[:=]?\s*[>≥<≤]?\s*([\d.]+)',
        r'[>≥<≤]\s*([\d.]+)\s*(?:mg|ppm|mg/kg|mg/L|mg/㎥)',
        r'([\d.]+)\s*(?:mg/kg|mg/L|ppm|mg/㎥)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    # 마지막 시도: 아무 숫자
    nums = re.findall(r'(\d+\.?\d*)', text)
    if nums:
        try:
            return float(nums[0])
        except:
            pass
    return None


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

# field_key → route 매핑
_FIELD_TO_ROUTE = {
    '급성_독성_경구': '경구',
    '급성_독성_경피': '경피',
    '급성_독성_흡입': '흡입',
}

def apply_api_results_to_section11(api_results):
    all_exposure = []
    all_health = {k: [] for k in st.session_state.section11_data['나_건강_유해성_정보']}

    # ATE 프리필 초기화 — CAS 번호 기반으로 저장
    ate_prefill_by_cas = {'경구': {}, '경피': {}, '흡입': {}}

    for result in api_results:
        if 'error' in result:
            continue
        name = result.get('name', result.get('cas', ''))
        cas = result.get('cas', '')
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

                # ★ 급성독성 항목이면 숫자값도 추출하여 프리필 (CAS 기준)
                route = _FIELD_TO_ROUTE.get(field)
                if route and cas:
                    numeric_val = _extract_numeric(item_detail)
                    if numeric_val and numeric_val > 0:
                        if cas not in ate_prefill_by_cas[route]:
                            ate_prefill_by_cas[route][cas] = numeric_val

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

    # ★ ATE 프리필 값 저장 + 위젯키에도 반영 (CAS 기반 매칭)
    st.session_state.section11_ate_prefill = ate_prefill_by_cas

    # 섹션3 성분의 CAS번호로 매칭하여 위젯키 직접 설정
    components_s3 = []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('물질명'):
                components_s3.append({
                    'name': comp['물질명'],
                    'cas': comp.get('CAS번호', '').strip(),
                })

    for route_kr, cas_val_map in ate_prefill_by_cas.items():
        for i, comp_info in enumerate(components_s3):
            comp_cas = comp_info['cas']
            if comp_cas and comp_cas in cas_val_map:
                wk = f"ate_{route_kr}_atei_{i}"
                st.session_state[wk] = cas_val_map[comp_cas]


# ============================================================
# 분류 힌트 (나머지 항목용)
# ============================================================
CLASSIFICATION_HINTS = {
    '피부_부식성_또는_자극성': {
        'options': ['미분류', '구분 1A (부식성)', '구분 1B (부식성)', '구분 1C (부식성)', '구분 2 (자극성)'],
        'hint': """**[혼합물 분류 기준]**
| 구분 | 가산 방식 | 비가산(강산/강염기) |
|-----|---------|---------------|
| **구분 1 (부식성)** | 구분1 합계 ≥ **5%** | pH≤2/≥11.5 성분≥1% |
| **구분 2 (자극성)** | 구분1: 1~5%, 구분2≥**10%**, (구분1×10)+구분2≥**10%** | 구분2≥**3%** |

💡 pH ≤2 또는 pH ≥11.5 → 구분 1 (산/알칼리 완충능 고려)""",
    },
    '심한_눈_손상_또는_자극성': {
        'options': ['미분류', '구분 1 (심한 눈 손상)', '구분 2A (자극성)', '구분 2B (경미)'],
        'hint': """**[혼합물 분류 기준]**
| 구분 | 기준 |
|-----|-----|
| **구분 1** | (눈구분1 + 피부구분1) ≥ **3%** |
| **구분 2A** | (눈구분1+피부구분1): 1~3%, 눈구분2 ≥ **10%** |
| **구분 2B** | 시험에서 7일 내 회복 |

💡 피부부식성 구분1 → 눈 구분1로도 간주""",
    },
    '호흡기_과민성': {
        'options': ['미분류', '구분 1', '구분 1A', '구분 1B'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1A** | ≥ **0.1%** |
| **1B** | 고체/액체 ≥ **1.0%**, 가스 ≥ **0.2%** |""",
    },
    '피부_과민성': {
        'options': ['미분류', '구분 1', '구분 1A', '구분 1B'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1A** | ≥ **0.1%** |
| **1B** | ≥ **1.0%** |""",
    },
    '발암성': {
        'options': ['미분류', '구분 1A', '구분 1B', '구분 2'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1A** | ≥ **0.1%** |
| **1B** | ≥ **0.1%** |
| **2** | ≥ **1.0%** |

💡 IARC: Gr.1→1A, Gr.2A→1B, Gr.2B→2 (참고)""",
    },
    '생식세포_변이원성': {
        'options': ['미분류', '구분 1A', '구분 1B', '구분 2'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1A/1B** | ≥ **0.1%** |
| **2** | ≥ **1.0%** |""",
    },
    '생식독성': {
        'options': ['미분류', '구분 1A', '구분 1B', '구분 2', '수유독성'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1A/1B** | ≥ **0.3%** |
| **2** | ≥ **3.0%** |
| **수유독성** | ≥ **0.3%** |""",
    },
    '특정_표적장기_독성_1회_노출': {
        'options': ['미분류', '구분 1', '구분 2', '구분 3 (호흡기자극)', '구분 3 (마취작용)'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1** | 구분1 성분 ≥ **10%** |
| **2** | 구분1: 1~10%, 구분2 ≥ **10%** |
| **3** | 호흡기자극/마취 성분 ≥ **20%** |

💡 단일물질: 경구 ≤300→구분1, 300~2000→구분2""",
    },
    '특정_표적장기_독성_반복_노출': {
        'options': ['미분류', '구분 1', '구분 2'],
        'hint': """**[혼합물 - 함유량 기준]**
| 구분 | 기준 |
|-----|-----|
| **1** | 구분1 성분 ≥ **10%** |
| **2** | 구분1: 1~10%, 구분2 ≥ **10%** |

💡 단일물질(90일): ≤10 mg/kg/일→구분1, 10~100→구분2
⚠️ 28일 시험: 기준값 × 3""",
    },
    '흡인_유해성': {
        'options': ['미분류', '구분 1', '구분 2'],
        'hint': """**[혼합물 분류 기준]**
| 구분 | 기준 |
|-----|-----|
| **1** | 구분1 ≥ **10%** + 동점도 ≤ **20.5** mm²/s (40℃) |
| **2** | 구분2 ≥ **10%** + 동점도 ≤ **14** mm²/s (40℃) |

💡 주로 탄화수소류(석유계 용제) 해당""",
    },
}


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
            st.success("✅ 반영 완료! (ATE값도 자동 입력)")
            st.rerun()

st.markdown("---")

# ============================================================
# 가. 노출 경로
# ============================================================
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

# 구성성분 정보
components_from_s3 = []
if 'section3_data' in st.session_state:
    for comp in st.session_state.get('section3_data', {}).get('components', []):
        if comp.get('물질명'):
            raw_c = comp.get('함유량(%)', '')
            try:
                pct = float(raw_c)
            except:
                pct = 0.0
            components_from_s3.append({
                'name': comp['물질명'],
                'cas': comp.get('CAS번호', ''),
                'pct': pct,
            })

# ----------------------------------------------------------
# 급성 독성 3개 항목
# ----------------------------------------------------------
ACUTE_ITEMS = [
    ('급성_독성_경구', '○ 급성 독성 - 경구 (Oral)', '경구',
     "예: LD50 (경구, 랫드): > 2000 mg/kg"),
    ('급성_독성_경피', '○ 급성 독성 - 경피 (Dermal)', '경피',
     "예: LD50 (경피, 토끼): > 2000 mg/kg"),
    ('급성_독성_흡입', '○ 급성 독성 - 흡입 (Inhalation)', '흡입',
     "예: LC50 (흡입, 랫드, 4hr): > 5 mg/L (증기)"),
]

for field_key, label, route, placeholder in ACUTE_ITEMS:
    st.markdown(f'<div class="sub-item">{label}</div>', unsafe_allow_html=True)
    criteria = ACUTE_CRITERIA[route]

    # === 텍스트 입력 ===
    val = st.text_area(
        label,
        value=st.session_state.section11_data['나_건강_유해성_정보'].get(field_key, ''),
        height=80,
        placeholder=placeholder,
        key=f"s11_{field_key}",
        label_visibility="collapsed"
    )
    st.session_state.section11_data['나_건강_유해성_정보'][field_key] = val

    # === ATEmix 계산기 (항상 표시) ===
    st.markdown(f"**🧮 ATEmix 계산 - {route}** (공식: 100/ATEmix = Σ(Ci/ATEi))")

    # 동적 행 수
    extra_key = f"ate_{route}_extra_count"
    if extra_key not in st.session_state:
        st.session_state[extra_key] = 0
    num_rows = max(len(components_from_s3), 2) + st.session_state[extra_key]

    # 프리필 데이터
    prefill = st.session_state.section11_ate_prefill.get(route, {})

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

    calc_comps = []
    for i in range(num_rows):
        rc = st.columns([3, 1.5, 2, 1.5])

        d_name = components_from_s3[i]['name'] if i < len(components_from_s3) else ''
        d_pct = components_from_s3[i]['pct'] if i < len(components_from_s3) else 0.0
        d_cas = components_from_s3[i]['cas'] if i < len(components_from_s3) else ''

        # ATE 기본값: 위젯키에 이미 있으면 그걸 쓰고, 없으면 CAS로 프리필
        ate_widget_key = f"ate_{route}_atei_{i}"
        if ate_widget_key not in st.session_state:
            d_ate = prefill.get(d_cas, 0.0) if d_cas else 0.0
            if d_ate > 0:
                st.session_state[ate_widget_key] = d_ate

        with rc[0]:
            st.text_input(
                f"이름{i}", value=d_name,
                key=f"ate_{route}_n_{i}",
                label_visibility="collapsed", placeholder=f"성분 {i+1}"
            )
        with rc[1]:
            ci = st.number_input(
                f"Ci{i}", min_value=0.0, max_value=100.0,
                value=float(d_pct), step=0.1, format="%.1f",
                key=f"ate_{route}_ci_{i}",
                label_visibility="collapsed"
            )
        with rc[2]:
            atei = st.number_input(
                f"ATE{i}", min_value=0.0, value=0.0,
                step=1.0, format="%.2f",
                key=ate_widget_key,
                label_visibility="collapsed"
            )
        with rc[3]:
            if atei > 0:
                st.markdown(f"**{classify_acute(atei, route)}**")
            else:
                st.markdown("*-*")

        if ci > 0:
            calc_comps.append({'name': d_name, 'ci': ci, 'ate': atei})

    # 행 추가 버튼
    if st.button("➕ 행 추가", key=f"ate_{route}_add_btn"):
        st.session_state[extra_key] += 1
        st.rerun()

    # ★★★ ATEmix 계산 결과 (바로 보이게!) ★★★
    if calc_comps:
        atemix, unknown_pct = calc_atemix(calc_comps)
        if atemix is not None:
            category = classify_acute(atemix, route)
            badge_cls = _get_badge_class(category)

            sum_ci_atei = 100.0 / atemix

            st.markdown(f"""<div class="ate-result-box">
                <b>📊 ATEmix 계산 결과 ({route})</b><br>
                Σ(Ci/ATEi) = <b>{sum_ci_atei:.4f}</b> → 
                ATEmix = 100 / {sum_ci_atei:.4f} = <b>{atemix:.2f} {criteria['unit']}</b><br>
                <span class="ate-badge {badge_cls}">🏷️ {category}</span>
                {f'&nbsp;&nbsp;⚠️ ATE 미입력 성분: {unknown_pct:.1f}%' if unknown_pct > 0 else ''}
            </div>""", unsafe_allow_html=True)

            st.session_state.section11_categories[field_key] = category
            st.session_state.section11_atemix_results[field_key] = atemix

            if unknown_pct > 10:
                st.markdown(f"""<div class="ate-warn-box">
                    ⚠️ <b>주의:</b> ATE 미입력 성분이 10% 초과({unknown_pct:.1f}%). 
                    공식 2: 100/ATEmix = Σ(Ci/ATEi) + Σ(알수없는 %)
                </div>""", unsafe_allow_html=True)
        else:
            st.info("ℹ️ ATE값이 입력된 성분이 없습니다.")
            st.session_state.section11_categories[field_key] = '미분류'
    else:
        st.caption("ℹ️ 함유량(%)을 입력하면 ATEmix가 자동 계산됩니다.")
        st.session_state.section11_categories[field_key] = '미분류'

    # 분류기준 참고표 (접이식)
    with st.expander(f"📋 분류기준표 & ATE변환표 - {route}", expanded=False):
        st.markdown(f"**급성독성 분류 기준 ({route}, {criteria['unit']}):**")
        range_data = []
        for threshold, cat in criteria['ranges']:
            range_data.append({'구분': cat, f'기준 ({criteria["unit"]})': f'≤ {threshold}'})
        range_data.append({'구분': '미분류', f'기준 ({criteria["unit"]})': f'> {criteria["ranges"][-1][0]}'})
        st.table(pd.DataFrame(range_data))

        st.markdown(f"**ATE 변환표** (구분만 알고 수치 모를 때):")
        conv_data = [{'구분': f'구분 {k}', f'ATE 변환값': v} for k, v in criteria['ate_convert'].items()]
        st.table(pd.DataFrame(conv_data))

    st.markdown("---")


# ----------------------------------------------------------
# 나머지 8개 항목
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
            "구분", options=options, index=default_idx,
            key=f"s11_cat_{key}",
        )
        st.session_state.section11_categories[key] = selected_cat

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
    extra = ''
    if k in st.session_state.section11_atemix_results:
        r = _FIELD_TO_ROUTE.get(k, '')
        u = ACUTE_CRITERIA.get(r, {}).get('unit', '')
        extra = f" (ATEmix={st.session_state.section11_atemix_results[k]:.1f} {u})"
    summary_data.append({'항목': lbl, '구분 판정': cat + extra})

summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

classified = sum(1 for d in summary_data if '미분류' not in d['구분 판정'])
st.info(f"📋 총 {len(summary_data)}개 항목 중 **{classified}개** 분류 완료")

# ============================================================
# 저장
# ============================================================
st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 노출 경로**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', '') or '(미입력)')
    st.write("\n**나. 건강 유해성 정보**")
    for k in all_keys:
        lbl = all_labels.get(k, k)
        v = st.session_state.section11_data['나_건강_유해성_정보'].get(k, '')
        cat = st.session_state.section11_categories.get(k, '미분류')
        st.write(f"  {lbl}: {v or '(미입력)'} → **[{cat}]**")
    st.json(st.session_state.section11_data)
    st.json(st.session_state.section11_categories)
