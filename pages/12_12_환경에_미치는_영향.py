import streamlit as st
import sys
import os
import time

st.set_page_config(page_title="MSDS 섹션 12 - 환경에 미치는 영향", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    * { font-family: 'Nanum Gothic', sans-serif !important; }
    [data-testid="stIconMaterial"],
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stTextInput > div > div > input { background-color: #f0f0f0; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
    .field-header { background-color: #f5f5f5; padding: 10px; border-radius: 5px; border-left: 4px solid #1976d2; margin: 15px 0 5px 0; font-weight: bold; font-size: 1.05em; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

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

# 환경 항목: (키, 한글명, 매칭 키워드(한글+영문), placeholder)
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
     ['만성', 'chronic', 'NOEC', 'LOEC', 'long-term',
      '만성 수생독성'],
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


def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


# ============================================================
# API 조회 함수
# ============================================================
def query_kosha(cas_no):
    """KOSHA API 섹션 12 조회"""
    try:
        import requests
        import xml.etree.ElementTree as ET
        API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
        BASE = "https://msds.kosha.or.kr/openapi/service/msdschem"
        resp = requests.get(f"{BASE}/chemlist", params={
            "serviceKey": API_KEY, "searchWrd": cas_no, "searchCnd": 1, "numOfRows": 5
        }, timeout=20)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        if not items:
            return {"success": False, "error": "KOSHA 미등록", "raw_items": []}
        chem_id = items[0].findtext("chemId", "")
        chem_name = items[0].findtext("chemNameKor", cas_no)
        time.sleep(0.3)
        resp2 = requests.get(f"{BASE}/chemdetail12", params={
            "serviceKey": API_KEY, "chemId": chem_id
        }, timeout=20)
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
    """PubChem API 섹션 12 조회"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from echa_api import get_environmental_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        env = get_environmental_info(cas_no, sub_id)
        return {
            "success": bool(env.get("raw_items")),
            "name": name,
            "raw_items": env.get("raw_items", []),
            "error": env.get("error", "")
        }
    except ImportError:
        return {"success": False, "error": "echa_api.py 모듈이 프로젝트 루트에 없습니다.", "raw_items": []}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name, detail=""):
    """항목명+내용을 환경 필드 키로 매핑 (급성/만성 수생독성 구분)"""
    combined = (item_name + " " + detail).strip()
    cl = combined.lower()

    # ── 1단계: 수생독성 판별 (급성/만성 + 종 구분) ──
    is_aquatic = any(k in cl for k in [
        "어류", "갑각류", "조류", "수생", "생태", "ecotox",
        "lc50", "ec50", "ic50", "noec", "loec",
        "fish", "daphn", "alga", "crustacea", "aquatic",
        "rainbow", "fathead", "bluegill", "mysid", "selenastrum",
        "oncorhynchus", "pimephales", "danio", "oryzias",
        "ceriodaphnia", "americamysis", "desmodesmus", "chlorella",
    ])

    if is_aquatic:
        # 만성 여부 판별
        is_chronic = any(k in cl for k in [
            "만성", "chronic", "noec", "loec", "long-term",
            "21 day", "28 day", "21d", "28d", "reproduction",
        ])
        if is_chronic:
            return '가4_만성_수생독성'

        # 급성 - 종 구분
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
        # 종 불명확 → 급성 어류(기본)
        return '가1_급성_수생독성_어류'

    # ── 2단계: 나머지 항목 키워드 매칭 ──
    for key, label, keywords, _ in ENV_FIELDS:
        if key.startswith('가'):  # 수생독성은 위에서 이미 처리
            continue
        for kw in keywords:
            if kw.lower() in cl:
                return key
    return None


# ============================================================
# API 연동 UI
# ============================================================
with st.expander("🔍 KOSHA + 국제DB(PubChem) 동시 조회", expanded=False):
    st.markdown("""
    섹션 3의 CAS 번호로 **🟢 KOSHA(한국)** 와 **🔵 국제DB(PubChem)** 환경 데이터를 동시 조회합니다.  
    각 항목별로 조회된 **개별 환경값에 체크(☑)** 하면 입력란에 반영됩니다.
    """)

    cas_list, mat_info = [], []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                cas_list.append(comp['CAS번호'])
                mat_info.append({'name': comp['물질명'], 'cas': comp['CAS번호']})

    if cas_list:
        st.success(f"✅ {len(cas_list)}개 물질 발견")
        for m in mat_info:
            st.write(f"  • **{m['name']}** (CAS: {m['cas']})")

        if st.button("🔍 KOSHA + 국제DB 동시 조회", type="primary", key="dual_query_s12"):
            all_results = []
            mat_field_found = {m['name']: set() for m in mat_info}

            prog = st.progress(0)
            total = len(cas_list) * 2
            step = 0

            for m in mat_info:
                # KOSHA
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas'])
                if kr.get('success'):
                    for item in kr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk:
                            all_results.append({
                                'mat': m['name'], 'cas': m['cas'],
                                'src': 'KOSHA', 'field': fk,
                                'label': item['name'], 'detail': item['detail']
                            })
                            mat_field_found[m['name']].add(fk)
                step += 1
                time.sleep(0.3)

                # PubChem
                prog.progress(step / total, f"🔵 국제DB: {m['name']}...")
                pr = query_pubchem(m['cas'])
                if pr.get('success'):
                    for item in pr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk:
                            all_results.append({
                                'mat': m['name'], 'cas': m['cas'],
                                'src': 'PubChem', 'field': fk,
                                'label': item['name'], 'detail': item['detail']
                            })
                            mat_field_found[m['name']].add(fk)
                step += 1
                time.sleep(0.3)

            # ── 수정3: 데이터가 없는 물질+항목에 "자료없음" 추가 ──
            for m in mat_info:
                for fk, fl, _, _ in ENV_FIELDS:
                    if fk not in mat_field_found[m['name']]:
                        all_results.append({
                            'mat': m['name'], 'cas': m['cas'],
                            'src': '-', 'field': fk,
                            'label': fl, 'detail': '자료없음',
                            'no_data': True
                        })

            prog.progress(1.0, "✅ 조회 완료!")

            for i, r in enumerate(all_results):
                r['idx'] = i

            st.session_state['s12_all'] = all_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # ===== 결과 표시: 항목별 → 개별 값 체크박스 =====
    if 's12_all' in st.session_state and st.session_state['s12_all']:
        all_results = st.session_state['s12_all']

        st.markdown("---")
        st.markdown("### 📊 항목별 데이터 선택")
        st.info("☑ 원하는 환경값을 체크한 후 아래 **[선택 반영]** 버튼을 누르세요.")

        for fk, fl, _, _ in ENV_FIELDS:
            items_in_field = [r for r in all_results if r['field'] == fk]
            if not items_in_field:
                continue

            st.markdown(f'<div class="field-header">📋 {fl}</div>', unsafe_allow_html=True)

            for r in items_in_field:
                idx = r['idx']
                is_no_data = r.get('no_data', False)
                mat_name = r['mat']
                detail = r['detail']

                if is_no_data:
                    display_text = f"⬜ {mat_name}: 자료없음"
                else:
                    src_emoji = "🟢" if r['src'] == 'KOSHA' else "🔵"
                    src_label = r['src']
                    display_text = f"{src_emoji} **{src_label}** | {mat_name}: {detail[:200]}"

                col_chk, col_txt = st.columns([0.05, 0.95])
                with col_chk:
                    st.checkbox("선택", key=f"chk12_{idx}", label_visibility="collapsed")
                with col_txt:
                    st.markdown(display_text)

            st.markdown("")

        # ===== 선택 반영 버튼 =====
        st.markdown("---")
        if st.button("✅ 선택한 데이터를 입력란에 반영", type="primary", key="apply_s12"):
            selected_by_field = {fk: [] for fk, _, _, _ in ENV_FIELDS}

            for r in all_results:
                idx = r['idx']
                if st.session_state.get(f"chk12_{idx}", False):
                    fk = r['field']
                    mat = r['mat']
                    detail = r['detail']
                    # ── 수정1: [PubChem], [KOSHA] 태그 없이 반영 ──
                    selected_by_field[fk].append(f"{mat}: {detail}")

            applied_count = 0
            for fk, _, _, _ in ENV_FIELDS:
                if selected_by_field[fk]:
                    combined = "\n".join(selected_by_field[fk])
                    st.session_state.section12_data[fk] = combined
                    wk = f"s12_{fk}"
                    if wk in st.session_state:
                        st.session_state[wk] = combined
                    applied_count += len(selected_by_field[fk])

            if applied_count > 0:
                st.success(f"✅ {applied_count}개 값이 반영되었습니다!")
                st.rerun()
            else:
                st.warning("⚠️ 선택된 값이 없습니다. 체크박스를 먼저 선택해주세요.")


# ============================================================
# 수동 입력 영역
# ============================================================
st.markdown("---")
st.markdown("### ✍️ 환경 영향 정보 입력")

for key, label, _, ph in ENV_FIELDS:
    cur = st.session_state.section12_data.get(key, '')
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=cur, height=120 if '생태독성' in label else 100,
        placeholder=ph, key=f"s12_{key}", label_visibility="collapsed")
    st.session_state.section12_data[key] = val

# ============================================================
# 저장
# ============================================================
st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 12 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 12가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for key, label, _, _ in ENV_FIELDS:
        st.write(f"**{label}**")
        st.text(st.session_state.section12_data.get(key, '') or '(미입력)')
    st.json(st.session_state.section12_data)
