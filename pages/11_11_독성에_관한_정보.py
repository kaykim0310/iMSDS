import streamlit as st
import sys
import os
import time

st.set_page_config(page_title="MSDS 섹션 11 - 독성에 관한 정보", layout="wide", initial_sidebar_state="collapsed")

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
    .kosha-tag { background-color: #4caf50; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-right: 5px; }
    .pubchem-tag { background-color: #2196f3; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

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

# 독성 항목 정의: (키, 한글명, KOSHA 매칭 키워드, placeholder)
TOXICITY_FIELDS = [
    ('급성독성_경구', '급성독성 (경구)', ['경구'], "예: LD50 = 5800 mg/kg (Rat)"),
    ('급성독성_경피', '급성독성 (경피)', ['경피'], "예: LD50 > 2000 mg/kg (Rabbit)"),
    ('급성독성_흡입', '급성독성 (흡입)', ['흡입'], "예: LC50 = 76 mg/L (Rat, 4hr)"),
    ('피부_부식성_또는_자극성', '피부 부식성/자극성', ['피부부식', '피부 부식', '피부자극', '피부 자극'], "예: 구분 2"),
    ('심한_눈_손상_또는_자극성', '심한 눈 손상/자극성', ['눈손상', '눈 손상', '눈자극', '눈 자극'], "예: 구분 2A"),
    ('호흡기_과민성', '호흡기 과민성', ['호흡기과민', '호흡기 과민'], "예: 자료없음"),
    ('피부_과민성', '피부 과민성', ['피부과민', '피부 과민'], "예: 자료없음"),
    ('발암성', '발암성', ['발암'], "예: IARC Group 3"),
    ('생식세포_변이원성', '생식세포 변이원성', ['변이원', '돌연변이'], "예: Ames test 음성"),
    ('생식독성', '생식독성', ['생식독성', '생식'], "예: 자료없음"),
    ('특정_표적장기_독성_1회노출', '특정 표적장기 독성 (1회 노출)', ['1회', '단회'], "예: 구분 3 (마취작용)"),
    ('특정_표적장기_독성_반복노출', '특정 표적장기 독성 (반복 노출)', ['반복'], "예: 자료없음"),
    ('흡인_유해성', '흡인 유해성', ['흡인'], "예: 자료없음"),
]


def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


# ============================================================
# API 조회 함수
# ============================================================
def query_kosha(cas_no):
    """KOSHA API 섹션 11 조회"""
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
        resp2 = requests.get(f"{BASE}/chemdetail11", params={
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
    """PubChem API 섹션 11 조회"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from echa_api import get_toxicity_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        tox = get_toxicity_info(cas_no, sub_id)
        return {
            "success": bool(tox.get("raw_items")),
            "name": name,
            "raw_items": tox.get("raw_items", []),
            "error": tox.get("error", "")
        }
    except ImportError:
        return {"success": False, "error": "echa_api.py 모듈이 프로젝트 루트에 없습니다.", "raw_items": []}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name):
    """항목명을 독성 필드 키로 매핑"""
    n = item_name.strip().lower()
    # LD50/LC50 키워드 우선
    if "ld50" in n:
        if "oral" in n or "경구" in n: return "급성독성_경구"
        if "dermal" in n or "경피" in n: return "급성독성_경피"
        if "inhal" in n or "흡입" in n: return "급성독성_흡입"
    if "lc50" in n: return "급성독성_흡입"
    
    for key, label, keywords, _ in TOXICITY_FIELDS:
        for kw in keywords:
            if kw in item_name: return key
    return None


# ============================================================
# API 연동 UI
# ============================================================
with st.expander("🔍 KOSHA + 국제DB(PubChem) 동시 조회", expanded=False):
    st.markdown("""
    섹션 3의 CAS 번호로 **🟢 KOSHA(한국)** 와 **🔵 국제DB(PubChem)** 독성 데이터를 동시 조회합니다.  
    각 항목별로 조회된 **개별 독성값에 체크(☑)** 하면 입력란에 반영됩니다.
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

        if st.button("🔍 KOSHA + 국제DB 동시 조회", type="primary", key="dual_query_s11"):
            all_results = []  # [{mat, cas, source, field_key, detail, idx}, ...]
            prog = st.progress(0)
            total = len(cas_list) * 2
            step = 0

            for m in mat_info:
                # KOSHA
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas'])
                if kr.get('success'):
                    for item in kr['raw_items']:
                        fk = classify_item(item['name'])
                        if fk:
                            all_results.append({
                                'mat': m['name'], 'cas': m['cas'],
                                'src': 'KOSHA', 'field': fk,
                                'label': item['name'], 'detail': item['detail']
                            })
                step += 1
                time.sleep(0.3)

                # PubChem
                prog.progress(step / total, f"🔵 국제DB: {m['name']}...")
                pr = query_pubchem(m['cas'])
                if pr.get('success'):
                    for item in pr['raw_items']:
                        fk = classify_item(item['name'])
                        if fk:
                            all_results.append({
                                'mat': m['name'], 'cas': m['cas'],
                                'src': 'PubChem', 'field': fk,
                                'label': item['name'], 'detail': item['detail']
                            })
                step += 1
                time.sleep(0.3)

            prog.progress(1.0, "✅ 조회 완료!")

            # 인덱스 부여
            for i, r in enumerate(all_results):
                r['idx'] = i

            st.session_state['s11_all'] = all_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # ===== 결과 표시: 항목별 → 개별 값 체크박스 =====
    if 's11_all' in st.session_state and st.session_state['s11_all']:
        all_results = st.session_state['s11_all']

        st.markdown("---")
        st.markdown("### 📊 항목별 데이터 선택")
        st.info("☑ 원하는 독성값을 체크한 후 아래 **[선택 반영]** 버튼을 누르세요.")

        # 항목별로 그룹핑
        for fk, fl, _, _ in TOXICITY_FIELDS:
            items_in_field = [r for r in all_results if r['field'] == fk]
            if not items_in_field:
                continue

            st.markdown(f'<div class="field-header">📋 {fl}</div>', unsafe_allow_html=True)

            for r in items_in_field:
                idx = r['idx']
                src_emoji = "🟢" if r['src'] == 'KOSHA' else "🔵"
                src_label = r['src']
                mat_name = r['mat']
                detail = r['detail']

                # 표시 텍스트: [출처] 물질명 - 상세값
                display_text = f"{src_emoji} **[{src_label}]** {mat_name}: {detail[:150]}"

                col_chk, col_txt = st.columns([0.05, 0.95])
                with col_chk:
                    checked = st.checkbox(
                        "선택", key=f"chk11_{idx}",
                        label_visibility="collapsed"
                    )
                with col_txt:
                    st.markdown(display_text)

            st.markdown("")  # 여백

        # ===== 선택 반영 버튼 =====
        st.markdown("---")
        if st.button("✅ 선택한 데이터를 입력란에 반영", type="primary", key="apply_s11"):
            # 체크된 항목 수집 → 필드별로 묶어서 반영
            selected_by_field = {fk: [] for fk, _, _, _ in TOXICITY_FIELDS}

            for r in all_results:
                idx = r['idx']
                if st.session_state.get(f"chk11_{idx}", False):
                    fk = r['field']
                    src = r['src']
                    mat = r['mat']
                    detail = r['detail']
                    selected_by_field[fk].append(f"[{src}] {mat}: {detail}")

            applied_count = 0
            for fk, _, _, _ in TOXICITY_FIELDS:
                if selected_by_field[fk]:
                    combined = "\n".join(selected_by_field[fk])
                    st.session_state.section11_data['나_건강_유해성_정보'][fk] = combined
                    wk = f"s11_{fk}"
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
st.markdown("### ✍️ 독성 정보 입력")

st.markdown('<div class="subsection-header">가. 가능성이 높은 노출경로에 관한 정보</div>', unsafe_allow_html=True)
v = st.text_area("노출경로", value=st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', ''),
    height=100, placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구", key="exposure_routes", label_visibility="collapsed")
st.session_state.section11_data['가_가능성이_높은_노출경로에_관한_정보'] = v

st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

for key, label, _, ph in TOXICITY_FIELDS:
    cur = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
    tag = ""
    if cur:
        if "[KOSHA]" in cur and "[PubChem]" in cur: tag = " 🟢🔵"
        elif "[KOSHA]" in cur: tag = " 🟢"
        elif "[PubChem]" in cur: tag = " 🔵"
        elif cur.strip() not in ("", "자료없음"): tag = " ✏️"
    st.markdown(f"**{label}{tag}**")
    val = st.text_area(label, value=cur, height=80, placeholder=ph, key=f"s11_{key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][key] = val

# ============================================================
# 저장
# ============================================================
st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 노출경로**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', '') or '(미입력)')
    st.write("**나. 건강 유해성 정보**")
    for key, label, _, _ in TOXICITY_FIELDS:
        val = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        if val: st.write(f"  • **{label}**: {val[:120]}{'...' if len(val) > 120 else ''}")
    st.json(st.session_state.section11_data)
