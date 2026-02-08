import streamlit as st
import sys
import os
import time
import re
import math

st.set_page_config(page_title="MSDS 섹션 12 - 환경에 미치는 영향", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

# ============================================================
# GHS 수생환경 유해성 분류 기준
# ============================================================
ACUTE_AQUATIC_CRITERIA = [
    (1.0, '급성 구분 1', 'H400'),
]
# 급성 구분 1: L(E)C50mix ≤ 1 mg/L

CHRONIC_AQUATIC_CRITERIA = [
    (0.1, '만성 구분 1', 'H410'),
    (1.0, '만성 구분 2', 'H411'),
    (10.0, '만성 구분 3', 'H412'),
    (100.0, '만성 구분 4', 'H413'),
]

# ============================================================
# 세션 초기화
# ============================================================
if 'section12_data' not in st.session_state:
    st.session_state.section12_data = {
        '가1_급성_수생독성_어류': '', '가2_급성_수생독성_갑각류': '', '가3_급성_수생독성_조류': '',
        '가4_만성_수생독성': '',
        '나_잔류성_및_분해성': '', '다_생물_농축성': '',
        '라_토양_이동성': '', '마_기타_유해_영향': ''
    }

if 'confirmed_env_classifications' not in st.session_state:
    st.session_state.confirmed_env_classifications = {}

# 환경 항목 정의
ENV_FIELDS = [
    ('가1_급성_수생독성_어류', '가. 생태독성 - 급성 수생독성 (어류)',
     ['어류', 'fish', 'rainbow', 'fathead', 'bluegill', 'oncorhynchus',
      'pimephales', 'danio', 'oryzias', 'lepomis', 'salmo',
      '급성 수생독성 (어류)'],
     "예: LC50 = 8.3 mg/L (96hr, Rainbow trout)"),
    ('가2_급성_수생독성_갑각류', '가. 생태독성 - 급성 수생독성 (갑각류)',
     ['갑각류', 'daphn', 'crustacea', 'mysid', 'ceriodaphnia',
      'americamysis', 'gammarus', 'hyalella',
      '급성 수생독성 (갑각류)'],
     "예: EC50 = 5 mg/L (48hr, Daphnia magna)"),
    ('가3_급성_수생독성_조류', '가. 생태독성 - 급성 수생독성 (조류)',
     ['조류', 'alga', 'selenastrum', 'desmodesmus', 'pseudokirchneriella',
      'chlorella', 'scenedesmus', 'skeletonema',
      '급성 수생독성 (조류)'],
     "예: EC50 = 11 mg/L (72hr, Desmodesmus subspicatus)"),
    ('가4_만성_수생독성', '가. 생태독성 - 만성 수생독성',
     ['만성', 'chronic', 'NOEC', 'LOEC', 'long-term', '만성 수생독성'],
     "예: NOEC = 0.02 mg/L (21d, Daphnia magna)"),
    ('나_잔류성_및_분해성', '나. 잔류성 및 분해성',
     ['잔류', '분해', 'log Kow', 'BOD', 'COD', 'biodeg', 'half-life', '반감기',
      'Biodegradation', 'Environmental Fate', 'Abiotic', 'persistence',
      'hydrolysis', 'photolysis'],
     "예: log Kow=2.73, 이분해성"),
    ('다_생물_농축성', '다. 생물 농축성',
     ['농축', 'BCF', '생분해', 'bioconcentrat', 'Bioaccumulation',
      'Octanol', 'log P', 'partition coefficient'],
     "예: BCF=90"),
    ('라_토양_이동성', '라. 토양 이동성',
     ['토양', '이동', 'Koc', 'soil', 'adsorption', 'mobility',
      'Soil Adsorption', 'Mobility in Soil'],
     "예: Koc=자료없음"),
    ('마_기타_유해_영향', '마. 기타 유해 영향',
     ['기타', '오존', 'atmospheric', 'ozone', 'Other Coverage'],
     "예: 오존층파괴물질 해당없음"),
]

# 급성 수생독성 3종
ACUTE_SPECIES = ['가1_급성_수생독성_어류', '가2_급성_수생독성_갑각류', '가3_급성_수생독성_조류']
ACUTE_SPECIES_LABELS = {'가1_급성_수생독성_어류': '어류', '가2_급성_수생독성_갑각류': '갑각류', '가3_급성_수생독성_조류': '조류'}


def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


def extract_numeric(text):
    """LC50/EC50/NOEC 수치 추출"""
    if not text: return None
    text = text.replace('&gt;', '>').replace('&lt;', '<')
    m = re.search(r'(?:LC50|EC50|IC50|NOEC|LOEC|L\(E\)C50)\s*[=:>< ]*\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if m:
        try: return float(m.group(1).replace(',', ''))
        except: pass
    m = re.search(r'([\d,]+\.?\d*)\s*(?:mg/L|mg/l|µg/L|ug/L)', text, re.IGNORECASE)
    if m:
        try: return float(m.group(1).replace(',', ''))
        except: pass
    m = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    if m:
        try: return float(m.group())
        except: pass
    return None


def classify_acute_aquatic(ecmix):
    """급성 수생환경 유해성 분류"""
    for threshold, label, hcode in ACUTE_AQUATIC_CRITERIA:
        if ecmix <= threshold:
            return f"{label} ({hcode})"
    return "분류되지 않음"


def classify_chronic_aquatic(ecmix):
    """만성 수생환경 유해성 분류"""
    for threshold, label, hcode in CHRONIC_AQUATIC_CRITERIA:
        if ecmix <= threshold:
            return f"{label} ({hcode})"
    return "분류되지 않음"


def conservative_score(detail, field_key=''):
    """보수적(독성↑) 순으로 점수 부여.
    ★ 핵심: 정량 데이터(수치) > 정성 데이터(키워드)
    - 정량: +500 보너스 → 항상 정성보다 우선, 값 낮을수록 독성↑
    - 정성: 키워드 기반 (최대 ~100)
    """
    if not detail or detail.strip() in ('자료없음', '해당없음', '(없음)', ''):
        return -9999
    num = extract_numeric(detail)
    if num and num > 0:
        # 정량 보너스(500) + 역수 → 항상 정성(최대100)보다 높음
        return 500.0 + (10000.0 / num)
    # ── 이하 정성 데이터 (최대 ~100점) ──
    dl = detail.lower()
    severe_kw = {
        'toxic': 70, '독성': 70, 'harmful': 60, '유해': 60,
        'not classified': 10, '분류되지': 10,
        '난분해': 65, 'not readily': 65, 'persistent': 65,
        '이분해': 30, 'readily': 30,
    }
    best = 0
    for kw, sc in severe_kw.items():
        if kw in dl:
            best = max(best, sc)
    return best if best > 0 else 1


def auto_select_conservative(all_results, prefix="chk12"):
    """물질별·항목별로 가장 보수적인 결과 1개씩 자동 선택"""
    from collections import defaultdict
    any_manual = any(
        st.session_state.get(f"{prefix}_{r['idx']}", False)
        for r in all_results if not r.get('no_data')
    )
    if any_manual:
        return
    groups = defaultdict(list)
    for r in all_results:
        if r.get('no_data'): continue
        groups[(r['mat'], r['field'])].append(r)
    for (mat, fk), items in groups.items():
        if not items: continue
        scored = [(conservative_score(r['detail'], fk), r) for r in items]
        scored.sort(key=lambda x: x[0], reverse=True)
        st.session_state[f"{prefix}_{scored[0][1]['idx']}"] = True


# ============================================================
# 성분 정보 가져오기
# ============================================================
def get_components():
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
        resp2 = requests.get(f"{BASE}/chemdetail12", params={"serviceKey": API_KEY, "chemId": chem_id}, timeout=20)
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
        from echa_api import get_environmental_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        env = get_environmental_info(cas_no, sub_id)
        return {"success": bool(env.get("raw_items")), "name": name,
                "raw_items": env.get("raw_items", []), "error": env.get("error", "")}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name, detail=""):
    """항목명+내용을 환경 필드 키로 매핑 (급성/만성 수생독성 구분)"""
    combined = (item_name + " " + detail).strip()
    cl = combined.lower()

    is_aquatic = any(k in cl for k in [
        "어류", "갑각류", "조류", "수생", "생태", "ecotox",
        "lc50", "ec50", "ic50", "noec", "loec",
        "fish", "daphn", "alga", "crustacea", "aquatic",
        "rainbow", "fathead", "bluegill", "mysid", "selenastrum",
        "oncorhynchus", "pimephales", "danio", "oryzias",
        "ceriodaphnia", "americamysis", "desmodesmus", "chlorella",
    ])

    if is_aquatic:
        is_chronic = any(k in cl for k in [
            "만성", "chronic", "noec", "loec", "long-term",
            "21 day", "28 day", "21d", "28d", "reproduction",
        ])
        if is_chronic:
            return '가4_만성_수생독성'
        if any(k in cl for k in ["어류", "fish", "rainbow", "fathead", "bluegill",
                                   "oncorhynchus", "pimephales", "danio", "oryzias",
                                   "lepomis", "salmo"]):
            return '가1_급성_수생독성_어류'
        if any(k in cl for k in ["갑각류", "daphn", "crustacea", "mysid",
                                   "ceriodaphnia", "americamysis", "gammarus", "hyalella"]):
            return '가2_급성_수생독성_갑각류'
        if any(k in cl for k in ["조류", "alga", "selenastrum", "desmodesmus",
                                   "pseudokirchneriella", "chlorella", "scenedesmus",
                                   "skeletonema"]):
            return '가3_급성_수생독성_조류'
        return '가1_급성_수생독성_어류'

    for key, label, keywords, _ in ENV_FIELDS:
        if key.startswith('가'):
            continue
        for kw in keywords:
            if kw.lower() in cl:
                return key
    return None


# ============================================================
# 1. API 조회 + 데이터 선택
# ============================================================
with st.expander("🔍 KOSHA + 국제DB(PubChem) 동시 조회", expanded=False):
    st.markdown("섹션 3의 CAS 번호로 **🟢 KOSHA** 와 **🔵 국제DB(PubChem)** 환경 데이터를 동시 조회합니다.")

    cas_list, mat_info = [], []
    if components:
        for m in components:
            cas_list.append(m['cas'])
            mat_info.append(m)

    if cas_list:
        st.success(f"✅ {len(cas_list)}개 물질 발견")
        for m in mat_info:
            pct_txt = f", 함유량: {m['pct']}%" if m.get('pct') else ""
            st.write(f"  • **{m['name']}** (CAS: {m['cas']}{pct_txt})")

        if st.button("🔍 KOSHA + 국제DB 동시 조회", type="primary", key="dual_query_s12"):
            all_results = []
            mat_field_found = {m['name']: set() for m in mat_info}
            prog = st.progress(0)
            total = len(cas_list) * 2
            step = 0

            for m in mat_info:
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas'])
                if kr.get('success'):
                    for item in kr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk:
                            all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m.get('pct'),
                                'src': 'KOSHA', 'field': fk, 'label': item['name'], 'detail': item['detail']})
                            mat_field_found[m['name']].add(fk)
                step += 1; time.sleep(0.3)

                prog.progress(step / total, f"🔵 국제DB: {m['name']}...")
                pr = query_pubchem(m['cas'])
                if pr.get('success'):
                    for item in pr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk:
                            all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m.get('pct'),
                                'src': 'PubChem', 'field': fk, 'label': item['name'], 'detail': item['detail']})
                            mat_field_found[m['name']].add(fk)
                step += 1; time.sleep(0.3)

            for m in mat_info:
                for fk, fl, _, _ in ENV_FIELDS:
                    if fk not in mat_field_found[m['name']]:
                        all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m.get('pct'),
                            'src': '-', 'field': fk, 'label': fl, 'detail': '자료없음', 'no_data': True})

            prog.progress(1.0, "✅ 조회 완료!")
            for i, r in enumerate(all_results): r['idx'] = i
            st.session_state['s12_all'] = all_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # 결과 체크박스
    if 's12_all' in st.session_state and st.session_state['s12_all']:
        all_results = st.session_state['s12_all']

        # ── 자동 보수적 선택 (최초 1회) ──
        auto_select_conservative(all_results, prefix="chk12")

        st.markdown("---")
        st.markdown("### 📊 항목별 데이터 선택")
        st.info("⚡ **가장 보수적인 값**(독성↑)이 자동 선택되었습니다. 필요 시 수정하세요.")

        for fk, fl, _, _ in ENV_FIELDS:
            items_in_field = [r for r in all_results if r['field'] == fk]
            if not items_in_field: continue
            st.markdown(f'<div class="field-header">📋 {fl}</div>', unsafe_allow_html=True)
            for r in items_in_field:
                idx = r['idx']
                if r.get('no_data'):
                    display = f"⬜ {r['mat']}: 자료없음"
                else:
                    emoji = "🟢" if r['src'] == 'KOSHA' else "🔵"
                    score = conservative_score(r['detail'], fk)
                    if score >= 500:
                        score_tag = f" `📊 정량 [{score:.0f}]`"
                    elif score > 0:
                        score_tag = f" `📝 정성 [{score:.0f}]`"
                    else:
                        score_tag = ""
                    display = f"{emoji} **{r['src']}** | {r['mat']}: {r['detail'][:160]}{score_tag}"
                c1, c2 = st.columns([0.05, 0.95])
                with c1: st.checkbox("선택", key=f"chk12_{idx}", label_visibility="collapsed")
                with c2: st.markdown(display)
            st.markdown("")

        st.markdown("---")
        if st.button("✅ 선택한 데이터를 입력란에 반영", type="primary", key="apply_s12"):
            selected_by_field = {fk: [] for fk, _, _, _ in ENV_FIELDS}
            for r in all_results:
                if st.session_state.get(f"chk12_{r['idx']}", False):
                    selected_by_field[r['field']].append(f"{r['mat']}: {r['detail']}")
            applied = 0
            for fk, _, _, _ in ENV_FIELDS:
                if selected_by_field[fk]:
                    combined = "\n".join(selected_by_field[fk])
                    st.session_state.section12_data[fk] = combined
                    wk = f"s12_{fk}"
                    if wk in st.session_state: st.session_state[wk] = combined
                    applied += len(selected_by_field[fk])
            if applied > 0:
                st.success(f"✅ {applied}개 값 반영!")
                st.rerun()
            else:
                st.warning("⚠️ 선택된 값이 없습니다.")


# ============================================================
# 2. 환경 영향 정보 입력 (어류/갑각류/조류/만성 + 나~마)
# ============================================================
st.markdown("---")
st.markdown("### ✍️ 환경 영향 정보 입력 및 혼합물 분류 판정")

# ── 급성 수생독성 3종 입력란 ──
for key, label, _, ph in ENV_FIELDS[:3]:
    cur = st.session_state.section12_data.get(key, '')
    st.markdown(f'<div class="field-header">📋 {label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=cur, height=100, placeholder=ph,
        key=f"s12_{key}", label_visibility="collapsed")
    st.session_state.section12_data[key] = val

# ── 만성 수생독성 입력란 ──
key_chr, label_chr, _, ph_chr = ENV_FIELDS[3]
cur_chr = st.session_state.section12_data.get(key_chr, '')
st.markdown(f'<div class="field-header">📋 {label_chr}</div>', unsafe_allow_html=True)
val_chr = st.text_area(label_chr, value=cur_chr, height=100, placeholder=ph_chr,
    key=f"s12_{key_chr}", label_visibility="collapsed")
st.session_state.section12_data[key_chr] = val_chr


# ============================================================
# 3. ECmix 계산기 (급성 수생독성)
# ============================================================
st.markdown("---")
is_confirmed_acute = st.session_state.confirmed_env_classifications.get('급성_수생독성')
if is_confirmed_acute:
    st.markdown(f'<div class="result-box">✅ <b>급성 수생독성 확정:</b> {is_confirmed_acute} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

with st.expander("🧮 급성 ECmix 계산 (어류/갑각류/조류 중 선택)", expanded=False):
    st.markdown("""
    <div class="calc-box">
    <b>ECmix 공식 (급성):</b> 100 / L(E)C50mix = Σ( Ci / L(E)C50i )<br>
    <small>Ci = 성분 함유량(%), L(E)C50i = 성분의 어류·갑각류·조류 중 <b>선택한</b> L(E)C50값 (mg/L)</small><br>
    <small>각 성분별로 어류, 갑각류, 조류의 LC50/EC50 중 하나를 선택하여 혼합물 독성을 산정합니다.</small>
    </div>
    """, unsafe_allow_html=True)

    if not components:
        st.warning("섹션 3에 성분이 없습니다.")
    else:
        # ── 각 입력란에서 성분별 EC50/LC50 자동 추출 ──
        auto_vals = {}  # {성분명: {'어류': 값, '갑각류': 값, '조류': 값}}
        for sp_key in ACUTE_SPECIES:
            sp_label = ACUTE_SPECIES_LABELS[sp_key]
            text_val = st.session_state.section12_data.get(sp_key, '')
            if text_val:
                for line in text_val.split('\n'):
                    line = line.strip()
                    if not line: continue
                    for comp in components:
                        if comp['name'] in line:
                            num = extract_numeric(line)
                            if num and num > 0:
                                if comp['name'] not in auto_vals:
                                    auto_vals[comp['name']] = {}
                                auto_vals[comp['name']][sp_label] = num

        # session_state 사전 세팅
        for i, comp in enumerate(components):
            comp_auto = auto_vals.get(comp['name'], {})
            for sp_label in ['어류', '갑각류', '조류']:
                ss_key = f"ec_val_{sp_label}_{i}"
                if sp_label in comp_auto:
                    if ss_key not in st.session_state or st.session_state[ss_key] == 0.0:
                        st.session_state[ss_key] = comp_auto[sp_label]

        # ── 테이블 헤더 ──
        st.markdown("**성분별 수생독성값 (mg/L) — 각 성분에서 ECmix에 사용할 종을 선택하세요:**")
        hcols = st.columns([2, 1, 1.2, 1.2, 1.2, 1.2])
        with hcols[0]: st.caption("성분명")
        with hcols[1]: st.caption("함유량(%)")
        with hcols[2]: st.caption("🐟 어류 LC50")
        with hcols[3]: st.caption("🦐 갑각류 EC50")
        with hcols[4]: st.caption("🌿 조류 EC50")
        with hcols[5]: st.caption("◉ 선택")

        ec_data = []
        for i, comp in enumerate(components):
            comp_auto = auto_vals.get(comp['name'], {})
            cols = st.columns([2, 1, 1.2, 1.2, 1.2, 1.2])

            with cols[0]:
                badges = []
                for sp in ['어류', '갑각류', '조류']:
                    if sp in comp_auto:
                        badges.append(f"{sp}={comp_auto[sp]}")
                badge_txt = f" ← *{'  '.join(badges)}*" if badges else ""
                st.markdown(f"**{comp['name']}**{badge_txt}")
            with cols[1]:
                pct = st.number_input("함유량", value=comp['pct'] or 0.0,
                    min_value=0.0, max_value=100.0, step=0.1,
                    key=f"ec_pct_{i}", label_visibility="collapsed")
            with cols[2]:
                fish_val = st.number_input("어류", value=0.0, min_value=0.0,
                    step=0.01, format="%.3f",
                    key=f"ec_val_어류_{i}", label_visibility="collapsed")
            with cols[3]:
                crust_val = st.number_input("갑각류", value=0.0, min_value=0.0,
                    step=0.01, format="%.3f",
                    key=f"ec_val_갑각류_{i}", label_visibility="collapsed")
            with cols[4]:
                algae_val = st.number_input("조류", value=0.0, min_value=0.0,
                    step=0.01, format="%.3f",
                    key=f"ec_val_조류_{i}", label_visibility="collapsed")
            with cols[5]:
                # 어류/갑각류/조류 중 값이 입력된 것만 선택지로
                options = ["미선택"]
                if fish_val > 0: options.append("어류")
                if crust_val > 0: options.append("갑각류")
                if algae_val > 0: options.append("조류")
                choice = st.selectbox("선택", options,
                    key=f"ec_choice_{i}", label_visibility="collapsed")

            chosen_val = 0.0
            if choice == "어류": chosen_val = fish_val
            elif choice == "갑각류": chosen_val = crust_val
            elif choice == "조류": chosen_val = algae_val

            ec_data.append({
                'name': comp['name'], 'pct': pct,
                'fish': fish_val, 'crust': crust_val, 'algae': algae_val,
                'choice': choice, 'chosen_val': chosen_val
            })

        # ── 계산 ──
        st.markdown("---")
        if st.button("📊 급성 ECmix 계산", key="calc_ecmix_acute"):
            valid = [d for d in ec_data if d['pct'] > 0 and d['chosen_val'] > 0]
            not_selected = [d for d in ec_data if d['pct'] > 0 and d['choice'] == '미선택']

            if not valid:
                st.error("⚠️ 함유량(%)과 EC50값을 입력하고, 각 성분별로 종을 선택해주세요.")
            else:
                sum_ci = sum(d['pct'] / d['chosen_val'] for d in valid)
                unknown_pct = sum(d['pct'] for d in not_selected)

                if sum_ci > 0:
                    ecmix = 100 / sum_ci
                    classification = classify_acute_aquatic(ecmix)

                    st.markdown("**계산 과정:**")
                    lines = []
                    for d in valid:
                        lines.append(f"  {d['name']} ({d['choice']}): {d['pct']}% / {d['chosen_val']:.3f} mg/L = {d['pct']/d['chosen_val']:.4f}")
                    code_text = '\n'.join(lines)
                    code_text += f"\n\n  Σ(Ci/L(E)C50i) = {sum_ci:.4f}"
                    code_text += f"\n  L(E)C50mix = 100 / {sum_ci:.4f} = {ecmix:.4f} mg/L"
                    if unknown_pct > 0:
                        code_text += f"\n  ⚠ 미선택 성분: {unknown_pct:.1f}%"
                    st.code(code_text)

                    st.markdown(f'<div class="result-box">📌 <b>L(E)C50mix = {ecmix:.4f} mg/L</b> → <b>{classification}</b></div>', unsafe_allow_html=True)
                    st.session_state['ecmix_acute_result'] = f"L(E)C50mix = {ecmix:.4f} mg/L → {classification}"

        if 'ecmix_acute_result' in st.session_state:
            st.markdown("---")
            st.markdown("**최종 판정 결과** (수정 가능):")
            edited_acute = st.text_input(
                "판정 결과", value=st.session_state['ecmix_acute_result'],
                key="edit_ecmix_acute", label_visibility="collapsed")
            if st.button("✅ 급성 수생독성 결과를 확정합니다", key="confirm_ecmix_acute"):
                st.session_state.confirmed_env_classifications['급성_수생독성'] = edited_acute
                st.success("✅ 급성 수생독성 확정!")
                st.rerun()

        # ── 직접 분류 (계산 없이) ──
        st.markdown("---")
        st.markdown("**또는 직접 분류 선택:**")
        acute_options = ["선택 안 함", "급성 구분 1 (H400)", "분류되지 않음", "자료없음"]
        direct_acute = st.selectbox("급성 수생독성 직접 분류", acute_options,
            key="direct_acute_cls", label_visibility="collapsed")
        if direct_acute != "선택 안 함":
            if st.button("✅ 직접 분류를 확정합니다", key="confirm_direct_acute"):
                st.session_state.confirmed_env_classifications['급성_수생독성'] = direct_acute
                st.success(f"✅ 급성 수생독성: {direct_acute} 확정!")
                st.rerun()


# ============================================================
# 4. EqNOECmix 계산기 (만성 수생독성)
# ============================================================
is_confirmed_chronic = st.session_state.confirmed_env_classifications.get('만성_수생독성')
if is_confirmed_chronic:
    st.markdown(f'<div class="result-box">✅ <b>만성 수생독성 확정:</b> {is_confirmed_chronic} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

with st.expander("🧮 만성 EqNOECmix 계산 (분해성 고려)", expanded=False):
    st.markdown("""
    <div class="calc-box">
    <b>EqNOECmix 공식 (만성):</b><br>
    100 / EqNOECmix = Σ( Ci / NOECi ) + Σ( Cj × 2 / NOECj )<br>
    <small>이분해성(readily) 성분: Ci/NOECi &nbsp;|&nbsp; 난분해성(not readily) 성분: Cj×2/NOECj</small>
    </div>
    """, unsafe_allow_html=True)

    if not components:
        st.warning("섹션 3에 성분이 없습니다.")
    else:
        # 자동 추출
        auto_noec = {}
        if val_chr:
            for line in val_chr.split('\n'):
                line = line.strip()
                if not line: continue
                for comp in components:
                    if comp['name'] in line:
                        num = extract_numeric(line)
                        if num and num > 0:
                            auto_noec[comp['name']] = num

        for i, comp in enumerate(components):
            ss_key = f"noec_val_{i}"
            if comp['name'] in auto_noec:
                if ss_key not in st.session_state or st.session_state[ss_key] == 0.0:
                    st.session_state[ss_key] = auto_noec[comp['name']]

        st.markdown("**성분별 NOEC 및 분해성 입력:**")
        hcols = st.columns([2, 1, 1.5, 1.5])
        with hcols[0]: st.caption("성분명")
        with hcols[1]: st.caption("함유량(%)")
        with hcols[2]: st.caption("NOEC (mg/L)")
        with hcols[3]: st.caption("분해성")

        noec_data = []
        for i, comp in enumerate(components):
            cols = st.columns([2, 1, 1.5, 1.5])
            with cols[0]:
                badge = f" ← *NOEC={auto_noec[comp['name']]}*" if comp['name'] in auto_noec else ""
                st.markdown(f"**{comp['name']}**{badge}")
            with cols[1]:
                pct = st.number_input("함유량", value=comp['pct'] or 0.0,
                    min_value=0.0, max_value=100.0, step=0.1,
                    key=f"noec_pct_{i}", label_visibility="collapsed")
            with cols[2]:
                noec = st.number_input("NOEC", value=0.0, min_value=0.0,
                    step=0.001, format="%.4f",
                    key=f"noec_val_{i}", label_visibility="collapsed")
            with cols[3]:
                degrad = st.selectbox("분해성", ["이분해성", "난분해성", "자료없음"],
                    key=f"noec_degrad_{i}", label_visibility="collapsed")

            noec_data.append({'name': comp['name'], 'pct': pct, 'noec': noec, 'degrad': degrad})

        st.markdown("---")
        if st.button("📊 만성 EqNOECmix 계산", key="calc_ecmix_chronic"):
            readily = [d for d in noec_data if d['pct'] > 0 and d['noec'] > 0 and d['degrad'] == '이분해성']
            not_readily = [d for d in noec_data if d['pct'] > 0 and d['noec'] > 0 and d['degrad'] == '난분해성']
            unknown = [d for d in noec_data if d['pct'] > 0 and (d['noec'] == 0 or d['degrad'] == '자료없음')]

            if not readily and not not_readily:
                st.error("⚠️ NOEC값과 분해성을 입력해주세요.")
            else:
                sum_readily = sum(d['pct'] / d['noec'] for d in readily)
                sum_not_readily = sum(d['pct'] * 2 / d['noec'] for d in not_readily)
                total_sum = sum_readily + sum_not_readily

                if total_sum > 0:
                    eq_noec = 100 / total_sum
                    classification = classify_chronic_aquatic(eq_noec)

                    st.markdown("**계산 과정:**")
                    lines = []
                    for d in readily:
                        lines.append(f"  {d['name']} (이분해성): {d['pct']}% / {d['noec']:.4f} = {d['pct']/d['noec']:.4f}")
                    for d in not_readily:
                        lines.append(f"  {d['name']} (난분해성): {d['pct']}% × 2 / {d['noec']:.4f} = {d['pct']*2/d['noec']:.4f}")
                    code_text = '\n'.join(lines)
                    code_text += f"\n\n  Σ(이분해) = {sum_readily:.4f}"
                    code_text += f"\n  Σ(난분해×2) = {sum_not_readily:.4f}"
                    code_text += f"\n  합계 = {total_sum:.4f}"
                    code_text += f"\n  EqNOECmix = 100 / {total_sum:.4f} = {eq_noec:.4f} mg/L"
                    if unknown:
                        code_text += f"\n  ⚠ 자료없음: {', '.join(d['name'] for d in unknown)}"
                    st.code(code_text)

                    st.markdown(f'<div class="result-box">📌 <b>EqNOECmix = {eq_noec:.4f} mg/L</b> → <b>{classification}</b></div>', unsafe_allow_html=True)
                    st.session_state['ecmix_chronic_result'] = f"EqNOECmix = {eq_noec:.4f} mg/L → {classification}"

        if 'ecmix_chronic_result' in st.session_state:
            st.markdown("---")
            st.markdown("**최종 판정 결과** (수정 가능):")
            edited_chronic = st.text_input(
                "판정 결과", value=st.session_state['ecmix_chronic_result'],
                key="edit_ecmix_chronic", label_visibility="collapsed")
            if st.button("✅ 만성 수생독성 결과를 확정합니다", key="confirm_ecmix_chronic"):
                st.session_state.confirmed_env_classifications['만성_수생독성'] = edited_chronic
                st.success("✅ 만성 수생독성 확정!")
                st.rerun()

        # ── 직접 분류 (계산 없이) ──
        st.markdown("---")
        st.markdown("**또는 직접 분류 선택:**")
        chronic_options = ["선택 안 함", "만성 구분 1 (H410)", "만성 구분 2 (H411)",
                           "만성 구분 3 (H412)", "만성 구분 4 (H413)", "분류되지 않음", "자료없음"]
        direct_chronic = st.selectbox("만성 수생독성 직접 분류", chronic_options,
            key="direct_chronic_cls", label_visibility="collapsed")
        if direct_chronic != "선택 안 함":
            if st.button("✅ 직접 분류를 확정합니다", key="confirm_direct_chronic"):
                st.session_state.confirmed_env_classifications['만성_수생독성'] = direct_chronic
                st.success(f"✅ 만성 수생독성: {direct_chronic} 확정!")
                st.rerun()


# ============================================================
# 5. 나머지 항목 (잔류성, 농축성, 토양이동성, 기타)
# ============================================================
st.markdown("---")
for key, label, _, ph in ENV_FIELDS[4:]:
    cur = st.session_state.section12_data.get(key, '')
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=cur, height=100, placeholder=ph,
        key=f"s12_{key}", label_visibility="collapsed")
    st.session_state.section12_data[key] = val


# ============================================================
# 6. 확정 분류 요약 + 저장
# ============================================================
st.markdown("---")
st.markdown("### 📋 확정 분류 요약")

confirmed = st.session_state.confirmed_env_classifications
if confirmed:
    for ck, cv in list(confirmed.items()):
        cc1, cc2 = st.columns([4, 1])
        with cc1:
            st.markdown(f"  ✅ **{ck}**: {cv}")
        with cc2:
            if st.button("↩ 해제", key=f"reset_env_{ck}"):
                del st.session_state.confirmed_env_classifications[ck]
                st.rerun()
else:
    st.caption("아직 확정된 분류가 없습니다. 위 ECmix 계산 후 [확정] 버튼을 눌러주세요.")

st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 12 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 12가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.json(st.session_state.section12_data)
    st.json(st.session_state.confirmed_env_classifications)
