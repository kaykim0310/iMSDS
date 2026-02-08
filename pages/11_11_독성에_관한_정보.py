import streamlit as st
import pandas as pd
from datetime import datetime
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
    .kosha-box { background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50; margin: 5px 0; font-size: 0.9em; }
    .echa-box { background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 5px 0; font-size: 0.9em; }
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

TOXICITY_FIELDS = [
    ('급성독성_경구', '급성독성 (경구)', ['경구'], "예: LD50 = 5800 mg/kg (Rat)"),
    ('급성독성_경피', '급성독성 (경피)', ['경피'], "예: LD50 > 2000 mg/kg (Rabbit)"),
    ('급성독성_흡입', '급성독성 (흡입)', ['흡입'], "예: LC50 = 76 mg/L (Rat, 4hr)"),
    ('피부_부식성_또는_자극성', '피부 부식성/자극성', ['피부부식', '피부 부식', '피부자극', '피부 자극'], "예: 구분 2"),
    ('심한_눈_손상_또는_자극성', '심한 눈 손상/자극성', ['눈손상', '눈 손상', '눈자극', '눈 자극'], "예: 구분 2A"),
    ('호흡기_과민성', '호흡기 과민성', ['호흡기과민', '호흡기 과민'], "예: 자료없음"),
    ('피부_과민성', '피부 과민성', ['피부과민', '피부 과민'], "예: 자료없음"),
    ('발암성', '발암성', ['발암'], "예: IARC Group 3"),
    ('생식세포_변이원성', '생식세포 변이원성', ['변이원', '돌연변이'], "예: 자료없음"),
    ('생식독성', '생식독성', ['생식독성', '생식'], "예: 자료없음"),
    ('특정_표적장기_독성_1회노출', '특정 표적장기 독성 (1회 노출)', ['1회', '단회'], "예: 구분 3"),
    ('특정_표적장기_독성_반복노출', '특정 표적장기 독성 (반복 노출)', ['반복'], "예: 자료없음"),
    ('흡인_유해성', '흡인 유해성', ['흡인'], "예: 자료없음"),
]

def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


def query_kosha(cas_no):
    """KOSHA API 섹션 11 조회"""
    try:
        import requests
        import xml.etree.ElementTree as ET
        API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
        BASE = "https://msds.kosha.or.kr/openapi/service/msdschem"
        resp = requests.get(f"{BASE}/chemlist", params={"serviceKey": API_KEY, "searchWrd": cas_no, "searchCnd": 1, "numOfRows": 5}, timeout=20)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        if not items: return {"success": False, "error": "KOSHA 미등록", "raw_items": []}
        chem_id = items[0].findtext("chemId", "")
        chem_name = items[0].findtext("chemNameKor", cas_no)
        time.sleep(0.3)
        resp2 = requests.get(f"{BASE}/chemdetail11", params={"serviceKey": API_KEY, "chemId": chem_id}, timeout=20)
        root2 = ET.fromstring(resp2.content)
        raw = [{"name": it.findtext("msdsItemNameKor","").strip(), "detail": it.findtext("itemDetail","").strip(), "source": "KOSHA"} for it in root2.findall(".//item") if it.findtext("itemDetail","").strip()]
        return {"success": True, "name": chem_name, "raw_items": raw}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def query_echa(cas_no):
    """PubChem API 섹션 11 조회"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from echa_api import get_toxicity_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        tox = get_toxicity_info(cas_no, sub_id)
        return {"success": bool(tox.get("raw_items")), "name": name, "raw_items": tox.get("raw_items", []), "error": tox.get("error", "")}
    except ImportError:
        return {"success": False, "error": "echa_api.py 모듈이 프로젝트 루트에 없습니다.", "raw_items": []}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name):
    """항목명을 독성 필드 키로 매핑"""
    n = item_name.strip()
    for key, label, keywords, _ in TOXICITY_FIELDS:
        for kw in keywords:
            if kw in n: return key
    return None


def organize_results(raw_items, material_name=""):
    """원본 항목을 필드별로 정리"""
    organized = {key: [] for key, _, _, _ in TOXICITY_FIELDS}
    for item in raw_items:
        detail = item.get("detail", "")
        if not _is_valid(detail): continue
        fk = classify_item(item.get("name", ""))
        if fk and fk in organized:
            prefix = f"[{material_name}] " if material_name else ""
            organized[fk].append(f"{prefix}{item['name']}: {detail}")
    return organized


# ============================================================
# API 연동 UI
# ============================================================
with st.expander("🔍 KOSHA + 국제DB 동시 조회 (클릭)", expanded=False):
    st.markdown("섹션 3의 CAS 번호로 **🟢KOSHA(한국)**와 **🔵 국제DB(PubChem)** 데이터를 동시 조회합니다.")
    
    cas_list, mat_info = [], []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                cas_list.append(comp['CAS번호'])
                mat_info.append({'name': comp['물질명'], 'cas': comp['CAS번호']})
    
    if cas_list:
        st.success(f"✅ {len(cas_list)}개 물질 발견")
        for m in mat_info: st.write(f"  • **{m['name']}** (CAS: {m['cas']})")
        
        if st.button("🔍 KOSHA + 국제DB 동시 조회", type="primary", key="dual_query"):
            k_results, e_results = [], []
            prog = st.progress(0)
            total = len(cas_list) * 2
            step = 0
            for m in mat_info:
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas']); kr['mat'] = m['name']; k_results.append(kr)
                step += 1; time.sleep(0.3)
                prog.progress(step / total, f"🔵 국제DB: {m['name']}...")
                er = query_echa(m['cas']); er['mat'] = m['name']; e_results.append(er)
                step += 1; time.sleep(0.3)
            prog.progress(1.0, "✅ 완료!")
            st.session_state['s11_k'] = k_results
            st.session_state['s11_e'] = e_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")
    
    # === 결과 비교 및 선택 ===
    if 's11_k' in st.session_state and 's11_e' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 항목별 비교 및 선택")
        st.info("각 항목마다 원하는 출처를 선택 → 아래 \'반영\' 버튼 클릭")
        
        # 전체 결과 필드별 집계
        k_all = {key: [] for key, _, _, _ in TOXICITY_FIELDS}
        e_all = {key: [] for key, _, _, _ in TOXICITY_FIELDS}
        for kr in st.session_state['s11_k']:
            if kr.get('success'):
                org = organize_results(kr['raw_items'], kr.get('mat',''))
                for k in k_all: k_all[k].extend(org.get(k, []))
        for er in st.session_state['s11_e']:
            if er.get('success'):
                org = organize_results(er['raw_items'], er.get('mat',''))
                for k in e_all: e_all[k].extend(org.get(k, []))
        
        if 's11_sel' not in st.session_state: st.session_state['s11_sel'] = {}
        
        for fk, fl, _, _ in TOXICITY_FIELDS:
            kt = chr(10).join(k_all.get(fk, [])) or ""
            et = chr(10).join(e_all.get(fk, [])) or ""
            if not kt and not et: continue
            
            st.markdown(f"**{fl}**")
            c1, c2 = st.columns(2)
            with c1:
                if kt: st.markdown(f'<div class="kosha-box">🟢 KOSHA<br>{kt.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                else: st.caption("🟢 KOSHA: 데이터 없음")
            with c2:
                if et: st.markdown(f'<div class="echa-box">🔵 국제DB<br>{et.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                else: st.caption("🔵 국제DB: 데이터 없음")
            
            opts = []
            if kt: opts.append("🟢 KOSHA")
            if et: opts.append("🔵 국제DB")
            if kt and et: opts.append("🟡 병합")
            opts.append("✏️ 직접입력")
            
            sel = st.radio(f"sel_{fl}", opts, horizontal=True, key=f"sel11_{fk}", label_visibility="collapsed")
            st.session_state['s11_sel'][fk] = {'choice': sel, 'k': kt, 'e': et}
            st.markdown("---")
        
        if st.button("✅ 선택한 데이터 반영", type="primary", key="apply11"):
            for fk, fl, _, _ in TOXICITY_FIELDS:
                s = st.session_state.get('s11_sel', {}).get(fk, {})
                ch = s.get('choice', '')
                if '직접' in ch: continue
                if 'KOSHA' in ch: val = s.get('k', '')
                elif '국제DB' in ch: val = s.get('e', '')
                elif '병합' in ch:
                    parts = []
                    if s.get('k'): parts.append(f"[KOSHA] {s['k']}")
                    if s.get('e'): parts.append(f"[PubChem] {s['e']}")
                    val = chr(10).join(parts)
                else: continue
                if val:
                    st.session_state.section11_data['나_건강_유해성_정보'][fk] = val
                    wk = f"s11_{fk}"
                    if wk in st.session_state: st.session_state[wk] = val
            st.success("✅ 반영 완료!")
            st.rerun()


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
        if "[KOSHA]" in cur: tag = " 🟢"
        elif "국제DB" in cur: tag = " 🔵"
        elif cur.strip() not in ("", "자료없음"): tag = " ✏️"
    st.markdown(f"**{label}{tag}**")
    val = st.text_area(label, value=cur, height=80, placeholder=ph, key=f"s11_{key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][key] = val

st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 노출경로**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', '') or '(미입력)')
    for key, label, _, _ in TOXICITY_FIELDS:
        val = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        if val: st.write(f"  • **{label}**: {val[:100]}")
    st.json(st.session_state.section11_data)
