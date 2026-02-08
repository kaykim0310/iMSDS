import streamlit as st
import pandas as pd
from datetime import datetime
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
    .kosha-box { background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50; margin: 5px 0; font-size: 0.9em; }
    .echa-box { background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 5px 0; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

if 'section12_data' not in st.session_state:
    st.session_state.section12_data = {
        '가_생태독성': '', '나_잔류성_및_분해성': '', '다_생물_농축성': '',
        '라_토양_이동성': '', '마_기타_유해_영향': ''
    }

ENV_FIELDS = [
    ('가_생태독성', '가. 생태독성', ['어류', '갑각류', '조류', '수생', '생태', 'LC50', 'EC50'], "예: 어류 LC50=10mg/L, 갑각류 EC50=5mg/L"),
    ('나_잔류성_및_분해성', '나. 잔류성 및 분해성', ['잔류', '분해', 'log Kow', 'BOD', 'COD'], "예: log Kow=2.73, 이분해성"),
    ('다_생물_농축성', '다. 생물 농축성', ['농축', 'BCF', '생분해'], "예: BCF=90, 생분해성 80%"),
    ('라_토양_이동성', '라. 토양 이동성', ['토양', '이동', 'Koc'], "예: Koc=자료없음"),
    ('마_기타_유해_영향', '마. 기타 유해 영향', ['기타', '오존', '만성'], "예: 오존층파괴물질: 해당없음"),
]

def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


def query_kosha(cas_no):
    """KOSHA API 섹션 12 조회"""
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
        resp2 = requests.get(f"{BASE}/chemdetail12", params={"serviceKey": API_KEY, "chemId": chem_id}, timeout=20)
        root2 = ET.fromstring(resp2.content)
        raw = [{"name": it.findtext("msdsItemNameKor","").strip(), "detail": it.findtext("itemDetail","").strip(), "source": "KOSHA"} for it in root2.findall(".//item") if it.findtext("itemDetail","").strip()]
        return {"success": True, "name": chem_name, "raw_items": raw}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def query_echa(cas_no):
    """ECHA API 섹션 12 조회"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from echa_api import get_environmental_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        env = get_environmental_info(cas_no, sub_id)
        return {"success": bool(env.get("raw_items")), "name": name, "raw_items": env.get("raw_items", []), "error": env.get("error", "")}
    except ImportError:
        return {"success": False, "error": "echa_api.py 모듈이 프로젝트 루트에 없습니다.", "raw_items": []}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name):
    """항목명을 환경 필드 키로 매핑"""
    n = item_name.strip()
    for key, label, keywords, _ in ENV_FIELDS:
        for kw in keywords:
            if kw in n: return key
    return None


def organize_results(raw_items, material_name=""):
    organized = {key: [] for key, _, _, _ in ENV_FIELDS}
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
with st.expander("🔍 KOSHA + ECHA 동시 조회 (클릭)", expanded=False):
    st.markdown("섹션 3의 CAS 번호로 **🟢KOSHA(한국)**와 **🔵ECHA(유럽)** 환경 데이터를 동시 조회합니다.")
    
    cas_list, mat_info = [], []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                cas_list.append(comp['CAS번호'])
                mat_info.append({'name': comp['물질명'], 'cas': comp['CAS번호']})
    
    if cas_list:
        st.success(f"✅ {len(cas_list)}개 물질 발견")
        for m in mat_info: st.write(f"  • **{m['name']}** (CAS: {m['cas']})")
        
        if st.button("🔍 KOSHA + ECHA 동시 조회", type="primary", key="dual_query"):
            k_results, e_results = [], []
            prog = st.progress(0)
            total = len(cas_list) * 2
            step = 0
            for m in mat_info:
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas']); kr['mat'] = m['name']; k_results.append(kr)
                step += 1; time.sleep(0.3)
                prog.progress(step / total, f"🔵 ECHA: {m['name']}...")
                er = query_echa(m['cas']); er['mat'] = m['name']; e_results.append(er)
                step += 1; time.sleep(0.3)
            prog.progress(1.0, "✅ 완료!")
            st.session_state['s12_k'] = k_results
            st.session_state['s12_e'] = e_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")
    
    if 's12_k' in st.session_state and 's12_e' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 항목별 비교 및 선택")
        st.info("각 항목마다 원하는 출처를 선택 → 아래 \'반영\' 버튼 클릭")
        
        k_all = {key: [] for key, _, _, _ in ENV_FIELDS}
        e_all = {key: [] for key, _, _, _ in ENV_FIELDS}
        for kr in st.session_state['s12_k']:
            if kr.get('success'):
                org = organize_results(kr['raw_items'], kr.get('mat',''))
                for k in k_all: k_all[k].extend(org.get(k, []))
        for er in st.session_state['s12_e']:
            if er.get('success'):
                org = organize_results(er['raw_items'], er.get('mat',''))
                for k in e_all: e_all[k].extend(org.get(k, []))
        
        if 's12_sel' not in st.session_state: st.session_state['s12_sel'] = {}
        
        for fk, fl, _, _ in ENV_FIELDS:
            kt = chr(10).join(k_all.get(fk, [])) or ""
            et = chr(10).join(e_all.get(fk, [])) or ""
            if not kt and not et: continue
            
            st.markdown(f"**{fl}**")
            c1, c2 = st.columns(2)
            with c1:
                if kt: st.markdown(f'<div class="kosha-box">🟢 KOSHA<br>{kt.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                else: st.caption("🟢 KOSHA: 데이터 없음")
            with c2:
                if et: st.markdown(f'<div class="echa-box">🔵 ECHA<br>{et.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                else: st.caption("🔵 ECHA: 데이터 없음")
            
            opts = []
            if kt: opts.append("🟢 KOSHA")
            if et: opts.append("🔵 ECHA")
            if kt and et: opts.append("🟡 병합")
            opts.append("✏️ 직접입력")
            
            sel = st.radio(f"sel_{fl}", opts, horizontal=True, key=f"sel12_{fk}", label_visibility="collapsed")
            st.session_state['s12_sel'][fk] = {'choice': sel, 'k': kt, 'e': et}
            st.markdown("---")
        
        if st.button("✅ 선택한 데이터 반영", type="primary", key="apply12"):
            for fk, fl, _, _ in ENV_FIELDS:
                s = st.session_state.get('s12_sel', {}).get(fk, {})
                ch = s.get('choice', '')
                if '직접' in ch: continue
                if 'KOSHA' in ch: val = s.get('k', '')
                elif 'ECHA' in ch: val = s.get('e', '')
                elif '병합' in ch:
                    parts = []
                    if s.get('k'): parts.append(f"[KOSHA] {s['k']}")
                    if s.get('e'): parts.append(f"[ECHA] {s['e']}")
                    val = chr(10).join(parts)
                else: continue
                if val:
                    st.session_state.section12_data[fk] = val
                    wk = f"s12_{fk}"
                    if wk in st.session_state: st.session_state[wk] = val
            st.success("✅ 반영 완료!")
            st.rerun()


# ============================================================
# 수동 입력 영역
# ============================================================
st.markdown("---")
st.markdown("### ✍️ 환경 영향 정보 입력")

for key, label, _, ph in ENV_FIELDS:
    cur = st.session_state.section12_data.get(key, '')
    tag = ""
    if cur:
        if "[KOSHA]" in cur: tag = " 🟢"
        elif "ECHA" in cur: tag = " 🔵"
        elif cur.strip() not in ("", "자료없음"): tag = " ✏️"
    st.markdown(f'<div class="subsection-header">{label}{tag}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=cur, height=120 if '생태독성' in label else 100, placeholder=ph, key=f"s12_{key}", label_visibility="collapsed")
    st.session_state.section12_data[key] = val

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
