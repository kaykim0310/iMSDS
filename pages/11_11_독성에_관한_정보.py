import streamlit as st
import sys
import os
import time
import re
import math

st.set_page_config(page_title="MSDS 섹션 11 - 독성에 관한 정보", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    * { font-family: 'Nanum Gothic', sans-serif !important; }
    [data-testid="stIconMaterial"], .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stTextInput > div > div > input { background-color: #f0f0f0; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
    .field-header { background-color: #f5f5f5; padding: 10px; border-radius: 5px; border-left: 4px solid #1976d2; margin: 15px 0 5px 0; font-weight: bold; font-size: 1.05em; }
    .calc-box { background: #fff3e0; padding: 12px; border-radius: 8px; border: 1px solid #ffb74d; margin: 8px 0; }
    .result-box { background: #e8f5e9; padding: 12px; border-radius: 8px; border: 1px solid #66bb6a; margin: 8px 0; }
    .warn-box { background: #fce4ec; padding: 12px; border-radius: 8px; border: 1px solid #ef5350; margin: 8px 0; }
    .confirm-badge { background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# ============================================================
# GHS 혼합물 분류 기준 (고용노동부 고시 별표 1)
# ============================================================

# ATEmix 구분 기준
ATE_CRITERIA = {
    '경구': [(5, '구분 1'), (50, '구분 2'), (300, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
    '경피': [(50, '구분 1'), (200, '구분 2'), (1000, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
    '흡입_증기': [(0.5, '구분 1'), (2.0, '구분 2'), (10, '구분 3'), (20, '구분 4')],
    '흡입_분진': [(0.05, '구분 1'), (0.5, '구분 2'), (1.0, '구분 3'), (5, '구분 4')],
}

# ATE 변환표 (구분 → 점추정치)
ATE_CONVERSION = {
    '경구': {'구분 1': 0.5, '구분 2': 5, '구분 3': 100, '구분 4': 500, '구분 5': 2500},
    '경피': {'구분 1': 5, '구분 2': 50, '구분 3': 300, '구분 4': 1100, '구분 5': 2500},
}

# 함유량 기준 분류 (항목별)
CONC_CRITERIA = {
    '피부_부식성_또는_자극성': {
        'desc': '피부 부식성/자극성',
        'rules': [
            {'label': '구분 1 (부식성)', 'condition': '구분1 성분 합계 ≥ 5%', 'field': '구분1', 'threshold': 5.0},
            {'label': '구분 2 (자극성)', 'condition': '구분1: 1~5% 또는 구분2 ≥10% 또는 (구분1×10)+구분2 ≥10%', 'field': '구분2', 'threshold': 10.0},
        ]
    },
    '심한_눈_손상_또는_자극성': {
        'desc': '심한 눈 손상/자극성',
        'rules': [
            {'label': '구분 1 (심한 눈 손상)', 'condition': '(눈 구분1 + 피부 구분1) 합계 ≥ 3%', 'threshold': 3.0},
            {'label': '구분 2 (자극성)', 'condition': '(눈 구분1 + 피부 구분1): 1~3% 또는 눈 구분2 ≥10%', 'threshold': 10.0},
        ]
    },
    '호흡기_과민성': {
        'desc': '호흡기 과민성',
        'rules': [
            {'label': '구분 1A', 'condition': '호흡기 과민성 성분 ≥ 0.1%', 'threshold': 0.1},
            {'label': '구분 1B', 'condition': '고체/액체 ≥ 1.0%, 가스 ≥ 0.2%', 'threshold': 1.0},
        ]
    },
    '피부_과민성': {
        'desc': '피부 과민성',
        'rules': [
            {'label': '구분 1A', 'condition': '피부 과민성 성분 ≥ 0.1%', 'threshold': 0.1},
            {'label': '구분 1B', 'condition': '피부 과민성 성분 ≥ 1.0%', 'threshold': 1.0},
        ]
    },
    '발암성': {
        'desc': '발암성',
        'rules': [
            {'label': '구분 1A/1B', 'condition': '발암성 구분1 성분 ≥ 0.1%', 'threshold': 0.1},
            {'label': '구분 2', 'condition': '발암성 구분2 성분 ≥ 1.0%', 'threshold': 1.0},
        ]
    },
    '생식세포_변이원성': {
        'desc': '생식세포 변이원성',
        'rules': [
            {'label': '구분 1A/1B', 'condition': '변이원성 구분1 성분 ≥ 0.1%', 'threshold': 0.1},
            {'label': '구분 2', 'condition': '변이원성 구분2 성분 ≥ 1.0%', 'threshold': 1.0},
        ]
    },
    '생식독성': {
        'desc': '생식독성',
        'rules': [
            {'label': '구분 1A/1B', 'condition': '생식독성 구분1 성분 ≥ 0.3%', 'threshold': 0.3},
            {'label': '구분 2', 'condition': '생식독성 구분2 성분 ≥ 3.0%', 'threshold': 3.0},
            {'label': '수유독성', 'condition': '수유독성 성분 ≥ 0.3%', 'threshold': 0.3},
        ]
    },
    '특정_표적장기_독성_1회노출': {
        'desc': '특정 표적장기 독성 (1회 노출)',
        'rules': [
            {'label': '구분 1', 'condition': 'STOT-1회 구분1 성분 ≥ 10%', 'threshold': 10.0},
            {'label': '구분 2', 'condition': 'STOT-1회 구분1: 1~10% 또는 구분2 ≥ 10%', 'threshold': 10.0},
            {'label': '구분 3 (호흡기자극/마취)', 'condition': '구분3 성분 ≥ 20%', 'threshold': 20.0},
        ]
    },
    '특정_표적장기_독성_반복노출': {
        'desc': '특정 표적장기 독성 (반복 노출)',
        'rules': [
            {'label': '구분 1', 'condition': 'STOT-반복 구분1 성분 ≥ 10%', 'threshold': 10.0},
            {'label': '구분 2', 'condition': 'STOT-반복 구분1: 1~10% 또는 구분2 ≥ 10%', 'threshold': 10.0},
        ]
    },
    '흡인_유해성': {
        'desc': '흡인 유해성',
        'rules': [
            {'label': '구분 1', 'condition': '흡인 구분1 성분 ≥ 10% + 동점도 ≤ 20.5 mm²/s', 'threshold': 10.0},
        ]
    },
}

# ============================================================
# 세션 초기화
# ============================================================
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

if 'confirmed_classifications' not in st.session_state:
    st.session_state.confirmed_classifications = {}

TOXICITY_FIELDS = [
    ('급성독성_경구', '급성독성 (경구)', ['경구', 'oral', 'Acute Oral', 'ingestion'], "예: LD50 = 5800 mg/kg (Rat)"),
    ('급성독성_경피', '급성독성 (경피)', ['경피', 'dermal', 'Acute Dermal', 'skin absorption'], "예: LD50 > 2000 mg/kg (Rabbit)"),
    ('급성독성_흡입', '급성독성 (흡입)', ['흡입', 'inhalation', 'Acute Inhalation'], "예: LC50 = 76 mg/L (Rat, 4hr)"),
    ('피부_부식성_또는_자극성', '피부 부식성/자극성', ['피부부식', '피부 부식', '피부자극', '피부 자극', 'Skin Corrosion', 'Skin Irritation', 'skin irrit'], ""),
    ('심한_눈_손상_또는_자극성', '심한 눈 손상/자극성', ['눈손상', '눈 손상', '눈자극', '눈 자극', 'Eye Damage', 'Eye Irritation', 'Serious Eye', 'eye irrit'], ""),
    ('호흡기_과민성', '호흡기 과민성', ['호흡기과민', '호흡기 과민', 'Respiratory Sensitiz', 'respiratory sensit'], ""),
    ('피부_과민성', '피부 과민성', ['피부과민', '피부 과민', 'Skin Sensitiz', 'skin sensit'], ""),
    ('발암성', '발암성', ['발암', 'Carcinogen', 'IARC', 'NTP', 'carcino'], ""),
    ('생식세포_변이원성', '생식세포 변이원성', ['변이원', '돌연변이', 'Genotoxic', 'Mutagen', 'mutageni', 'genotox', 'Ames'], ""),
    ('생식독성', '생식독성', ['생식독성', '생식', 'Reproductive Toxic', 'Developmental Toxic', 'reproduct', 'teratogen'], ""),
    ('특정_표적장기_독성_1회노출', '특정 표적장기 독성 (1회 노출)', ['1회', '단회', 'single exposure'], ""),
    ('특정_표적장기_독성_반복노출', '특정 표적장기 독성 (반복 노출)', ['반복', 'Chronic Toxic', 'Repeated Dose', 'chronic', 'repeated', 'subchronic'], ""),
    ('흡인_유해성', '흡인 유해성', ['흡인', 'Aspiration', 'aspiration'], ""),
]


def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


def extract_numeric(text):
    """텍스트에서 LD50/LC50 수치를 추출한다.
    예: 'LD50 270 mg/kg' → 270.0
        'LD50 = 5800 mg/kg' → 5800.0
        'LD50 >5000 mg/kg' → 5000.0
        'LC50 76 mg/L (4hr)' → 76.0
    """
    if not text:
        return None
    # &gt; → >, &lt; → < 변환
    text = text.replace('&gt;', '>').replace('&lt;', '<')
    # LD50/LC50 뒤의 숫자를 우선 추출
    m = re.search(r'(?:LD50|LC50|EC50|ATE)\s*[=:>< ]*\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass
    # 일반 숫자 추출 (단위 mg/kg, mg/L 앞의 숫자)
    m = re.search(r'([\d,]+\.?\d*)\s*(?:mg/kg|mg/L|ppm|mg/m)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass
    # 최후: 아무 숫자나
    m = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return None


def classify_ate(ate_value, route='경구'):
    """ATE값으로 급성독성 구분 판정"""
    criteria = ATE_CRITERIA.get(route, ATE_CRITERIA['경구'])
    for threshold, label in criteria:
        if ate_value <= threshold:
            return label
    return '분류되지 않음'


# ============================================================
# API 조회 함수
# ============================================================
def query_kosha(cas_no):
    try:
        import requests
        import xml.etree.ElementTree as ET
        API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
        BASE = "https://msds.kosha.or.kr/openapi/service/msdschem"
        resp = requests.get(f"{BASE}/chemlist", params={"serviceKey": API_KEY, "searchWrd": cas_no, "searchCnd": 1, "numOfRows": 5}, timeout=20)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        if not items: return {"success": False, "raw_items": []}
        chem_id = items[0].findtext("chemId", "")
        chem_name = items[0].findtext("chemNameKor", cas_no)
        time.sleep(0.3)
        resp2 = requests.get(f"{BASE}/chemdetail11", params={"serviceKey": API_KEY, "chemId": chem_id}, timeout=20)
        root2 = ET.fromstring(resp2.content)
        raw = []
        for it in root2.findall(".//item"):
            name = it.findtext("msdsItemNameKor", "").strip()
            detail = it.findtext("itemDetail", "").strip()
            if name and detail and _is_valid(detail):
                raw.append({"name": name, "detail": detail, "source": "KOSHA"})
        return {"success": True, "name": chem_name, "raw_items": raw}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def query_pubchem(cas_no):
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from echa_api import get_toxicity_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        tox = get_toxicity_info(cas_no, sub_id)
        return {"success": bool(tox.get("raw_items")), "name": name, "raw_items": tox.get("raw_items", []), "error": tox.get("error", "")}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name, detail=""):
    combined = (item_name + " " + detail).strip()
    cl = combined.lower()
    if "ld50" in cl:
        if "oral" in cl or "경구" in cl: return "급성독성_경구"
        if "dermal" in cl or "경피" in cl: return "급성독성_경피"
        if "inhal" in cl or "흡입" in cl: return "급성독성_흡입"
        return "급성독성_경구"
    if "lc50" in cl: return "급성독성_흡입"
    for key, label, keywords, _ in TOXICITY_FIELDS:
        for kw in keywords:
            if kw.lower() in cl: return key
    return None


# ============================================================
# 섹션 3에서 성분 정보 가져오기
# ============================================================
def get_components():
    """섹션 3에서 물질명, CAS, 함유량(%) 가져오기"""
    comps = []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                pct_str = comp.get('함유량', comp.get('함유량(%)', ''))
                pct = None
                if pct_str:
                    m = re.search(r'[\d.]+', str(pct_str))
                    if m:
                        try: pct = float(m.group())
                        except: pass
                comps.append({'name': comp['물질명'], 'cas': comp['CAS번호'], 'pct': pct})
    return comps

components = get_components()

# ============================================================
# 1. API 조회 + 데이터 선택
# ============================================================
with st.expander("🔍 KOSHA + 국제DB(PubChem) 동시 조회", expanded=False):
    st.markdown("섹션 3의 CAS 번호로 **🟢 KOSHA** 와 **🔵 국제DB(PubChem)** 독성 데이터를 동시 조회합니다.")

    if components:
        st.success(f"✅ {len(components)}개 물질 발견")
        for m in components:
            pct_txt = f", 함유량: {m['pct']}%" if m['pct'] is not None else ""
            st.write(f"  • **{m['name']}** (CAS: {m['cas']}{pct_txt})")

        if st.button("🔍 KOSHA + 국제DB 동시 조회", type="primary", key="dual_query_s11"):
            all_results = []
            mat_field_found = {m['name']: set() for m in components}
            prog = st.progress(0)
            total = len(components) * 2
            step = 0

            for m in components:
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas'])
                if kr.get('success'):
                    for item in kr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk:
                            all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m['pct'],
                                'src': 'KOSHA', 'field': fk, 'label': item['name'], 'detail': item['detail']})
                            mat_field_found[m['name']].add(fk)
                step += 1; time.sleep(0.3)

                prog.progress(step / total, f"🔵 국제DB: {m['name']}...")
                pr = query_pubchem(m['cas'])
                if pr.get('success'):
                    KOSHA_ONLY_FIELDS = {'발암성'}
                    for item in pr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk and fk not in KOSHA_ONLY_FIELDS:
                            all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m['pct'],
                                'src': 'PubChem', 'field': fk, 'label': item['name'], 'detail': item['detail']})
                            mat_field_found[m['name']].add(fk)
                step += 1; time.sleep(0.3)

            for m in components:
                for fk, fl, _, _ in TOXICITY_FIELDS:
                    if fk not in mat_field_found[m['name']]:
                        all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m['pct'],
                            'src': '-', 'field': fk, 'label': fl, 'detail': '자료없음', 'no_data': True})

            prog.progress(1.0, "✅ 조회 완료!")
            for i, r in enumerate(all_results): r['idx'] = i
            st.session_state['s11_all'] = all_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # 결과 체크박스
    if 's11_all' in st.session_state and st.session_state['s11_all']:
        all_results = st.session_state['s11_all']
        st.markdown("---")
        st.markdown("### 📊 항목별 데이터 선택")
        st.info("☑ 원하는 독성값을 체크 → **[선택 반영]** → 아래 ATEmix 계산 및 분류 판정으로 진행")

        for fk, fl, _, _ in TOXICITY_FIELDS:
            items_in_field = [r for r in all_results if r['field'] == fk]
            if not items_in_field: continue
            st.markdown(f'<div class="field-header">📋 {fl}</div>', unsafe_allow_html=True)
            for r in items_in_field:
                idx = r['idx']
                if r.get('no_data'):
                    display = f"⬜ {r['mat']}: 자료없음"
                else:
                    emoji = "🟢" if r['src'] == 'KOSHA' else "🔵"
                    display = f"{emoji} **{r['src']}** | {r['mat']}: {r['detail'][:180]}"
                c1, c2 = st.columns([0.05, 0.95])
                with c1: st.checkbox("선택", key=f"chk11_{idx}", label_visibility="collapsed")
                with c2: st.markdown(display)
            st.markdown("")

        st.markdown("---")
        if st.button("✅ 선택한 데이터를 입력란에 반영", type="primary", key="apply_s11"):
            selected_by_field = {fk: [] for fk, _, _, _ in TOXICITY_FIELDS}
            for r in all_results:
                if st.session_state.get(f"chk11_{r['idx']}", False):
                    selected_by_field[r['field']].append(f"{r['mat']}: {r['detail']}")
            applied = 0
            for fk, _, _, _ in TOXICITY_FIELDS:
                if selected_by_field[fk]:
                    combined = "\n".join(selected_by_field[fk])
                    st.session_state.section11_data['나_건강_유해성_정보'][fk] = combined
                    wk = f"s11_{fk}"
                    if wk in st.session_state: st.session_state[wk] = combined
                    applied += len(selected_by_field[fk])
            if applied > 0:
                st.success(f"✅ {applied}개 값 반영!")
                st.rerun()
            else:
                st.warning("⚠️ 선택된 값이 없습니다.")

# ============================================================
# 2. 독성 정보 입력 + ATEmix/분류 계산
# ============================================================
st.markdown("---")
st.markdown("### ✍️ 독성 정보 입력 및 혼합물 분류 판정")

st.markdown('<div class="subsection-header">가. 가능성이 높은 노출경로에 관한 정보</div>', unsafe_allow_html=True)
v = st.text_area("노출경로", value=st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', ''),
    height=80, placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구", key="exposure_routes", label_visibility="collapsed")
st.session_state.section11_data['가_가능성이_높은_노출경로에_관한_정보'] = v

st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

# ── 급성독성 (경구/경피/흡입) : ATEmix 계산 ──
for route_key, route_label, route_kws, route_ph in TOXICITY_FIELDS[:3]:
    route_type = route_key.split('_')[-1]  # 경구, 경피, 흡입

    st.markdown(f'<div class="field-header">📋 {route_label}</div>', unsafe_allow_html=True)
    cur = st.session_state.section11_data['나_건강_유해성_정보'].get(route_key, '')
    val = st.text_area(route_label, value=cur, height=100,
        placeholder=f"조회 결과가 여기에 표시됩니다. 예: LD50 = 5800 mg/kg (Rat)",
        key=f"s11_{route_key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][route_key] = val

    # ── ATEmix 계산 패널 ──
    is_confirmed = st.session_state.confirmed_classifications.get(route_key)
    if is_confirmed:
        st.markdown(f'<div class="result-box">✅ <b>확정 분류:</b> {is_confirmed} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

    with st.expander(f"🧮 ATEmix 계산 ({route_label})", expanded=False):
        st.markdown(f"""
        <div class="calc-box">
        <b>ATEmix 공식:</b> 100/ATEmix = Σ(Ci/ATEi)<br>
        <small>Ci = 성분 함유량(%), ATEi = 성분의 ATE값 (실험 LD50/LC50 또는 구분별 변환값)</small>
        </div>
        """, unsafe_allow_html=True)

        if not components:
            st.warning("섹션 3에 성분이 없습니다.")
        else:
            # ── 텍스트 영역에서 성분별 독성값 자동 추출 ──
            auto_ate = {}
            if val:
                for line in val.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    for comp in components:
                        if comp['name'] in line:
                            # 전체 라인에서 LD50/LC50 수치 추출
                            # 예: "포름알데히드: LD50 270 mg/kg 실험종 : Rabbit|..."
                            num = extract_numeric(line)
                            if num and num > 0:
                                auto_ate[comp['name']] = num

            # 자동추출값을 session_state에 미리 세팅 (아직 0이거나 없을 때만)
            for i, comp in enumerate(components):
                ss_key = f"ate_val_{route_key}_{i}"
                if comp['name'] in auto_ate:
                    if ss_key not in st.session_state or st.session_state[ss_key] == 0.0:
                        st.session_state[ss_key] = auto_ate[comp['name']]

            st.markdown("**성분별 ATE 입력:**")
            # 컬럼 헤더
            hc1, hc2, hc3, hc4 = st.columns([2, 1, 2, 1.5])
            with hc1: st.caption("성분명")
            with hc2: st.caption("함유량(%)")
            with hc3: st.caption("ATE값 (LD50/LC50)")
            with hc4: st.caption("구분변환")

            ate_data = []
            for i, comp in enumerate(components):
                c1, c2, c3, c4 = st.columns([2, 1, 2, 1.5])

                ss_key = f"ate_val_{route_key}_{i}"

                with c1:
                    ate_badge = ""
                    if comp['name'] in auto_ate:
                        ate_badge = f" ← **{auto_ate[comp['name']]}** 자동추출"
                    st.markdown(f"{comp['name']}{ate_badge}")
                with c2:
                    pct = st.number_input("함유량(%)", value=comp['pct'] or 0.0,
                        min_value=0.0, max_value=100.0, step=0.1,
                        key=f"ate_pct_{route_key}_{i}", label_visibility="collapsed")
                with c3:
                    ate_val = st.number_input("ATE값",
                        value=0.0, min_value=0.0, step=0.1, format="%.2f",
                        key=ss_key, label_visibility="collapsed")
                with c4:
                    conv_options = ["직접입력"] + list(ATE_CONVERSION.get(route_type, {}).keys())
                    conv_sel = st.selectbox("구분변환", conv_options,
                        key=f"ate_conv_{route_key}_{i}", label_visibility="collapsed")

                    final_ate = ate_val
                    if conv_sel != "직접입력" and route_type in ATE_CONVERSION:
                        final_ate = ATE_CONVERSION[route_type].get(conv_sel, ate_val)

                ate_data.append({'name': comp['name'], 'pct': pct, 'ate': final_ate})

            # 계산 실행
            st.markdown("---")
            if st.button(f"📊 ATEmix 계산", key=f"calc_ate_{route_key}"):
                valid_entries = [d for d in ate_data if d['pct'] > 0 and d['ate'] > 0]
                if not valid_entries:
                    st.error("⚠️ 함유량(%)과 ATE값을 모두 입력해주세요.")
                else:
                    sum_ci_atei = sum(d['pct'] / d['ate'] for d in valid_entries)
                    unknown_pct = sum(d['pct'] for d in ate_data if d['pct'] > 0 and d['ate'] == 0)

                    if sum_ci_atei > 0:
                        ate_mix = 100 / sum_ci_atei
                        classification = classify_ate(ate_mix, route_type)

                        st.markdown("**계산 과정:**")
                        calc_lines = []
                        for d in valid_entries:
                            calc_lines.append(f"  {d['name']}: {d['pct']}% / {d['ate']} = {d['pct']/d['ate']:.4f}")
                        st.code('\n'.join(calc_lines) +
                            f"\n\n  Σ(Ci/ATEi) = {sum_ci_atei:.4f}" +
                            f"\n  ATEmix = 100 / {sum_ci_atei:.4f} = {ate_mix:.2f}" +
                            (f"\n  ⚠ ATE 미확인 성분: {unknown_pct:.1f}%" if unknown_pct > 0 else ""))

                        st.markdown(f'<div class="result-box">📌 <b>ATEmix = {ate_mix:.2f}</b> → <b>{classification}</b></div>', unsafe_allow_html=True)

                        st.session_state[f'ate_result_{route_key}'] = f"ATEmix = {ate_mix:.2f} → {classification}"

            # ATEmix 결과가 있으면 확정 버튼
            if f'ate_result_{route_key}' in st.session_state:
                result_text = st.session_state[f'ate_result_{route_key}']
                st.markdown(f"**산정 결과:** {result_text}")
                if st.button(f"✅ 이 결과를 확정합니다", key=f"confirm_ate_{route_key}"):
                    st.session_state.confirmed_classifications[route_key] = result_text
                    st.success(f"✅ {route_label}: {result_text} 확정!")
                    st.rerun()


# ── 나머지 항목: 함유량 기준 분류 ──
for key, label, kws, ph in TOXICITY_FIELDS[3:]:
    st.markdown(f'<div class="field-header">📋 {label}</div>', unsafe_allow_html=True)
    cur = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
    val = st.text_area(label, value=cur, height=80, placeholder=ph or "조회 결과가 여기에 표시됩니다.",
        key=f"s11_{key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][key] = val

    is_confirmed = st.session_state.confirmed_classifications.get(key)
    if is_confirmed:
        st.markdown(f'<div class="result-box">✅ <b>확정 분류:</b> {is_confirmed} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

    if key in CONC_CRITERIA and components:
        criteria = CONC_CRITERIA[key]

        with st.expander(f"📐 함유량 기준 분류 판정 ({label})", expanded=False):
            st.markdown(f"""
            <div class="calc-box">
            <b>{criteria['desc']}</b> - 혼합물 분류 (함유량 기준)<br>
            <small>각 성분의 해당 구분 함유량 합계로 혼합물 구분 판정</small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**분류 기준:**")
            for rule in criteria['rules']:
                st.write(f"  • **{rule['label']}**: {rule['condition']}")

            st.markdown("---")
            st.markdown("**성분별 해당 구분 정보 입력:**")

            comp_class_data = []
            for i, comp in enumerate(components):
                c1, c2, c3 = st.columns([2, 1.5, 2])
                with c1:
                    pct_display = f"{comp['pct']}%" if comp['pct'] is not None else "미입력"
                    st.markdown(f"**{comp['name']}** ({pct_display})")
                with c2:
                    pct = st.number_input("함유량(%)", value=comp['pct'] or 0.0,
                        min_value=0.0, max_value=100.0, step=0.1,
                        key=f"conc_pct_{key}_{i}", label_visibility="collapsed")
                with c3:
                    # 이 성분이 해당 항목에서 어떤 구분인지
                    class_options = ["해당없음", "구분 1A", "구분 1B", "구분 1C", "구분 1",
                                     "구분 2", "구분 3", "자료없음"]
                    cls = st.selectbox(f"{comp['name']} 구분", class_options,
                        key=f"conc_cls_{key}_{i}", label_visibility="collapsed")

                comp_class_data.append({'name': comp['name'], 'pct': pct, 'cls': cls})

            # 자동 판정
            st.markdown("---")
            if st.button(f"📊 분류 판정", key=f"calc_conc_{key}"):
                # 구분별 함유량 합산
                cls1_sum = sum(d['pct'] for d in comp_class_data
                    if d['cls'] in ['구분 1', '구분 1A', '구분 1B', '구분 1C'])
                cls2_sum = sum(d['pct'] for d in comp_class_data if d['cls'] == '구분 2')
                cls3_sum = sum(d['pct'] for d in comp_class_data if d['cls'] == '구분 3')
                unknown = sum(d['pct'] for d in comp_class_data if d['cls'] == '자료없음')

                st.markdown("**함유량 합산:**")
                st.code(f"  구분1 합계: {cls1_sum:.2f}%\n  구분2 합계: {cls2_sum:.2f}%"
                    + (f"\n  구분3 합계: {cls3_sum:.2f}%" if cls3_sum > 0 else "")
                    + (f"\n  ⚠ 자료없음: {unknown:.2f}%" if unknown > 0 else ""))

                # 판정 로직
                recommendation = "분류되지 않음"
                details = []

                for rule in criteria['rules']:
                    threshold = rule['threshold']
                    rule_label = rule['label']
                    field_type = rule.get('field', '')

                    if '구분1' in rule_label or '1A' in rule_label or '1B' in rule_label:
                        if cls1_sum >= threshold:
                            recommendation = rule_label
                            details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ {threshold}% → {rule_label}")
                            break
                    elif '구분 2' in rule_label:
                        if cls2_sum >= threshold:
                            recommendation = rule_label
                            details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ {threshold}% → {rule_label}")
                            break
                        # 가산 방식: (구분1×10)+구분2 ≥ 10
                        if '가산' in rule.get('condition', '') or '×10' in rule.get('condition', ''):
                            combined = cls1_sum * 10 + cls2_sum
                            if combined >= threshold:
                                recommendation = rule_label
                                details.append(f"(구분1×10)+구분2 = {combined:.2f}% ≥ {threshold}% → {rule_label}")
                                break
                    elif '구분 3' in rule_label:
                        if cls3_sum >= threshold:
                            recommendation = rule_label
                            details.append(f"구분3 합계 {cls3_sum:.2f}% ≥ {threshold}% → {rule_label}")
                            break

                if not details:
                    details.append("모든 기준 미달 → 분류되지 않음")

                for d in details:
                    st.write(f"  → {d}")

                if recommendation != "분류되지 않음":
                    st.markdown(f'<div class="result-box">📌 <b>판정: {recommendation}</b></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="calc-box">📌 <b>판정: 분류되지 않음</b></div>', unsafe_allow_html=True)

                if unknown > 0:
                    st.markdown(f'<div class="warn-box">⚠️ 자료없음 성분 {unknown:.2f}% — 추가 조사 권장</div>', unsafe_allow_html=True)

                st.session_state[f'conc_result_{key}'] = recommendation

            if f'conc_result_{key}' in st.session_state:
                result_text = st.session_state[f'conc_result_{key}']
                st.markdown(f"**판정 결과:** {result_text}")
                if st.button(f"✅ 이 결과를 확정합니다", key=f"confirm_conc_{key}"):
                    st.session_state.confirmed_classifications[key] = result_text
                    st.success(f"✅ {label}: {result_text} 확정!")
                    st.rerun()

# ============================================================
# 3. 확정 분류 요약 + 저장
# ============================================================
st.markdown("---")
st.markdown("### 📋 확정 분류 요약")

confirmed = st.session_state.confirmed_classifications
if confirmed:
    for fk, fl, _, _ in TOXICITY_FIELDS:
        if fk in confirmed:
            st.markdown(f"  ✅ **{fl}**: {confirmed[fk]}")
else:
    st.caption("아직 확정된 분류가 없습니다. 위 각 항목에서 계산 후 [확정] 버튼을 눌러주세요.")

st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.json(st.session_state.section11_data)
    st.json(st.session_state.confirmed_classifications)
