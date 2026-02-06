import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 11 - 독성에 관한 정보",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 스타일 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');

    * {
        font-family: 'Nanum Gothic', sans-serif !important;
    }

    .stTextInput > div > div > input {
        background-color: #f0f0f0;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #f0f0f0;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .section-header {
        background-color: #d3e3f3;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .subsection-header {
        background-color: #e8f0f7;
        padding: 8px;
        border-radius: 3px;
        margin: 15px 0;
        font-weight: bold;
    }
    .sub-item {
        background-color: #f5f5f5;
        padding: 5px 10px;
        margin: 5px 0;
        border-left: 3px solid #1976d2;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화 (공식 양식 기준)
if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출_경로에_관한_정보': '',
        '나_건강_유해성_정보': {
            '급성_독성': '',
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

# 기존 데이터가 문자열 형태인 경우 새 형식으로 변환
if isinstance(st.session_state.section11_data.get('나_건강_유해성_정보'), str):
    old_value = st.session_state.section11_data.get('나_건강_유해성_정보', '')
    st.session_state.section11_data['나_건강_유해성_정보'] = {
        '급성_독성': old_value,
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

# ============================================================
# KOSHA API 연동 섹션
# ============================================================
import requests
import xml.etree.ElementTree as ET
import time

KOSHA_API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
KOSHA_BASE_URL = "https://msds.kosha.or.kr/openapi/service/msdschem"

with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 독성 정보를 자동 조회합니다.")

    # 섹션 3에서 CAS 번호 가져오기
    cas_list = []
    materials_info = []

    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                cas_list.append(comp['CAS번호'])
                materials_info.append({
                    'name': comp['물질명'],
                    'cas': comp['CAS번호'],
                    'content': comp.get('함유량(%)', '')
                })

    if cas_list:
        st.success(f"✅ 섹션 3에서 {len(cas_list)}개의 CAS 번호를 찾았습니다.")
        for mat in materials_info:
            st.write(f"  • **{mat['name']}** (CAS: {mat['cas']})")

        if st.button("🔍 KOSHA API에서 독성 정보 조회", type="primary", key="api_query_btn"):
            try:
                progress = st.empty()
                api_results = []

                for idx, cas in enumerate(cas_list):
                    progress.info(f"[{idx+1}/{len(cas_list)}] CAS {cas} 조회 중...")

                    # 1단계: chemlist로 물질 검색
                    resp1 = requests.get(f"{KOSHA_BASE_URL}/chemlist", params={
                        "serviceKey": KOSHA_API_KEY,
                        "searchWrd": cas,
                        "searchCnd": 1,
                        "numOfRows": 10,
                        "pageNo": 1
                    }, timeout=30)

                    root1 = ET.fromstring(resp1.content)
                    search_items = root1.findall(".//item")

                    if not search_items:
                        api_results.append({'cas': cas, 'name': cas, 'error': '물질 미등록'})
                        continue

                    chem_id = search_items[0].findtext("chemId", "")
                    chem_name = search_items[0].findtext("chemNameKor", cas)

                    time.sleep(0.3)

                    # 2단계: chemdetail11로 독성정보 조회
                    resp2 = requests.get(f"{KOSHA_BASE_URL}/chemdetail11", params={
                        "serviceKey": KOSHA_API_KEY,
                        "chemId": chem_id,
                        "numOfRows": 100,
                        "pageNo": 1
                    }, timeout=30)

                    raw_xml = resp2.text[:3000]
                    root2 = ET.fromstring(resp2.content)
                    detail_items = root2.findall(".//item")

                    # 항목 파싱
                    parsed = {
                        'exposure_routes': '', 'skin_corrosion': '', 'eye_damage': '',
                        'respiratory_sensitization': '', 'skin_sensitization': '',
                        'carcinogenicity': '', 'germ_cell_mutagenicity': '',
                        'reproductive_toxicity': '', 'stot_single': '', 'stot_repeated': '',
                        'aspiration_hazard': '',
                        'acute_oral': '', 'acute_dermal': '', 'acute_inhalation': '',
                    }
                    raw_items = []

                    for it in detail_items:
                        name_kor = it.findtext("msdsItemNameKor", "")
                        detail = it.findtext("itemDetail", "")
                        if not detail or detail == "자료없음":
                            detail = "자료없음"
                        raw_items.append({"name": name_kor, "detail": detail})

                        if "노출" in name_kor and "경로" in name_kor:
                            parsed['exposure_routes'] = detail
                        elif "급성" in name_kor and "독성" in name_kor:
                            if "경구" in name_kor: parsed['acute_oral'] = detail
                            elif "경피" in name_kor: parsed['acute_dermal'] = detail
                            elif "흡입" in name_kor: parsed['acute_inhalation'] = detail
                            elif not parsed['acute_oral']: parsed['acute_oral'] = detail
                        elif "피부" in name_kor and ("부식" in name_kor or "자극" in name_kor) and "과민" not in name_kor:
                            parsed['skin_corrosion'] = detail
                        elif "눈" in name_kor and ("손상" in name_kor or "자극" in name_kor):
                            parsed['eye_damage'] = detail
                        elif "호흡기" in name_kor and "과민" in name_kor:
                            parsed['respiratory_sensitization'] = detail
                        elif "피부" in name_kor and "과민" in name_kor:
                            parsed['skin_sensitization'] = detail
                        elif "발암" in name_kor:
                            parsed['carcinogenicity'] = detail
                        elif "생식세포" in name_kor and "변이" in name_kor:
                            parsed['germ_cell_mutagenicity'] = detail
                        elif "생식독성" in name_kor:
                            parsed['reproductive_toxicity'] = detail
                        elif "특정" in name_kor and "표적" in name_kor and "장기" in name_kor:
                            if "1회" in name_kor or "단일" in name_kor: parsed['stot_single'] = detail
                            elif "반복" in name_kor: parsed['stot_repeated'] = detail
                        elif "흡인" in name_kor and "유해" in name_kor:
                            parsed['aspiration_hazard'] = detail

                    api_results.append({
                        'cas': cas, 'name': chem_name, 'chemId': chem_id,
                        'parsed': parsed, 'raw_items': raw_items, 'raw_xml': raw_xml,
                        'item_count': len(detail_items)
                    })
                    time.sleep(0.3)

                st.session_state['section11_api_results'] = api_results

                # 즉시 폼에 반영
                widget_fill = {
                    'exposure_routes': '', 'acute_toxicity': '', 'skin_corrosion': '',
                    'eye_damage': '', 'respiratory_sensitization': '', 'skin_sensitization': '',
                    'carcinogenicity': '', 'germ_cell_mutagenicity': '', 'reproductive_toxicity': '',
                    'stot_single': '', 'stot_repeated': '', 'aspiration_hazard': '',
                }

                for r in api_results:
                    if 'error' in r:
                        continue
                    p = r['parsed']
                    n = r['name']

                    def _add(key, val):
                        if val and val != "자료없음":
                            widget_fill[key] += (f"[{n}] {val}\n" if widget_fill[key] else f"[{n}] {val}")

                    _add('exposure_routes', p['exposure_routes'])
                    acute_line = " / ".join(filter(None, [
                        f"경구: {p['acute_oral']}" if p['acute_oral'] and p['acute_oral'] != "자료없음" else "",
                        f"경피: {p['acute_dermal']}" if p['acute_dermal'] and p['acute_dermal'] != "자료없음" else "",
                        f"흡입: {p['acute_inhalation']}" if p['acute_inhalation'] and p['acute_inhalation'] != "자료없음" else "",
                    ]))
                    _add('acute_toxicity', acute_line)
                    _add('skin_corrosion', p['skin_corrosion'])
                    _add('eye_damage', p['eye_damage'])
                    _add('respiratory_sensitization', p['respiratory_sensitization'])
                    _add('skin_sensitization', p['skin_sensitization'])
                    _add('carcinogenicity', p['carcinogenicity'])
                    _add('germ_cell_mutagenicity', p['germ_cell_mutagenicity'])
                    _add('reproductive_toxicity', p['reproductive_toxicity'])
                    _add('stot_single', p['stot_single'])
                    _add('stot_repeated', p['stot_repeated'])
                    _add('aspiration_hazard', p['aspiration_hazard'])

                # 위젯 키 + 데이터 딕셔너리 동시 업데이트
                for wkey, val in widget_fill.items():
                    st.session_state[wkey] = val or "자료없음"

                d = st.session_state.section11_data
                d['가_가능성이_높은_노출_경로에_관한_정보'] = widget_fill['exposure_routes'] or "자료없음"
                h = d['나_건강_유해성_정보']
                h['급성_독성'] = widget_fill['acute_toxicity'] or "자료없음"
                h['피부_부식성_또는_자극성'] = widget_fill['skin_corrosion'] or "자료없음"
                h['심한_눈_손상_또는_자극성'] = widget_fill['eye_damage'] or "자료없음"
                h['호흡기_과민성'] = widget_fill['respiratory_sensitization'] or "자료없음"
                h['피부_과민성'] = widget_fill['skin_sensitization'] or "자료없음"
                h['발암성'] = widget_fill['carcinogenicity'] or "자료없음"
                h['생식세포_변이원성'] = widget_fill['germ_cell_mutagenicity'] or "자료없음"
                h['생식독성'] = widget_fill['reproductive_toxicity'] or "자료없음"
                h['특정_표적장기_독성_1회_노출'] = widget_fill['stot_single'] or "자료없음"
                h['특정_표적장기_독성_반복_노출'] = widget_fill['stot_repeated'] or "자료없음"
                h['흡인_유해성'] = widget_fill['aspiration_hazard'] or "자료없음"

                progress.success("✅ 조회 완료! 폼에 자동 반영되었습니다.")
                st.rerun()

            except requests.RequestException as e:
                st.error(f"❌ API 연결 오류: {e}")
            except ET.ParseError as e:
                st.error(f"❌ XML 파싱 오류: {e}")
            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # API 결과 표시
    if 'section11_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과:**")

        for result in st.session_state['section11_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                cnt = result.get('item_count', 0)
                with st.expander(f"**{result['name']}** (CAS: {result['cas']}, chemId: {result.get('chemId','?')}) - {cnt}개 항목"):
                    raw_items = result.get('raw_items', [])
                    if raw_items:
                        for item in raw_items:
                            st.markdown(f"- **{item['name']}**: {item['detail']}")
                    else:
                        st.error(f"chemdetail11에서 반환된 항목이 0개입니다.")
                    with st.expander("원본 XML"):
                        st.code(result.get('raw_xml', '(없음)'), language="xml")

st.markdown("---")

# ============================================================
# 공식 양식 기준 입력 필드
# ============================================================

# 가. 가능성이 높은 노출 경로에 관한 정보
st.markdown('<div class="subsection-header">가. 가능성이 높은 노출 경로에 관한 정보</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "가능성이 높은 노출 경로에 관한 정보",
    value=st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', ''),
    height=100,
    placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구",
    key="exposure_routes",
    label_visibility="collapsed"
)
st.session_state.section11_data['가_가능성이_높은_노출_경로에_관한_정보'] = 가_내용

# 나. 건강 유해성 정보
st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

# 나-1. 급성 독성
st.markdown('<div class="sub-item">○ 급성 독성 (노출 가능한 모든 경로에 대해 기재)</div>', unsafe_allow_html=True)
급성독성 = st.text_area(
    "급성 독성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('급성_독성', ''),
    height=100,
    placeholder="예: 경구 LD50 (랫드): > 2000 mg/kg\n경피 LD50 (토끼): > 2000 mg/kg\n흡입 LC50 (랫드, 4hr): > 5 mg/L",
    key="acute_toxicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['급성_독성'] = 급성독성

# 나-2. 피부 부식성 또는 자극성
st.markdown('<div class="sub-item">○ 피부 부식성 또는 자극성</div>', unsafe_allow_html=True)
피부자극성 = st.text_area(
    "피부 부식성 또는 자극성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('피부_부식성_또는_자극성', ''),
    height=80,
    placeholder="예: 자료없음 / 피부에 자극을 일으킴 (구분 2)",
    key="skin_corrosion",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['피부_부식성_또는_자극성'] = 피부자극성

# 나-3. 심한 눈 손상 또는 자극성
st.markdown('<div class="sub-item">○ 심한 눈 손상 또는 자극성</div>', unsafe_allow_html=True)
눈자극성 = st.text_area(
    "심한 눈 손상 또는 자극성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('심한_눈_손상_또는_자극성', ''),
    height=80,
    placeholder="예: 자료없음 / 눈에 심한 자극을 일으킴 (구분 2A)",
    key="eye_damage",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['심한_눈_손상_또는_자극성'] = 눈자극성

# 나-4. 호흡기 과민성
st.markdown('<div class="sub-item">○ 호흡기 과민성</div>', unsafe_allow_html=True)
호흡기과민성 = st.text_area(
    "호흡기 과민성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('호흡기_과민성', ''),
    height=80,
    placeholder="예: 자료없음 / 흡입 시 알레르기성 반응, 천식 또는 호흡 곤란을 일으킬 수 있음",
    key="respiratory_sensitization",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['호흡기_과민성'] = 호흡기과민성

# 나-5. 피부 과민성
st.markdown('<div class="sub-item">○ 피부 과민성</div>', unsafe_allow_html=True)
피부과민성 = st.text_area(
    "피부 과민성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('피부_과민성', ''),
    height=80,
    placeholder="예: 자료없음 / 알레르기성 피부 반응을 일으킬 수 있음",
    key="skin_sensitization",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['피부_과민성'] = 피부과민성

# 나-6. 발암성
st.markdown('<div class="sub-item">○ 발암성</div>', unsafe_allow_html=True)
발암성 = st.text_area(
    "발암성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('발암성', ''),
    height=80,
    placeholder="예: 자료없음 / IARC: Group 1 (인체 발암성 물질)\nACGIH: A1 (확인된 인체 발암성 물질)",
    key="carcinogenicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['발암성'] = 발암성

# 나-7. 생식세포 변이원성
st.markdown('<div class="sub-item">○ 생식세포 변이원성</div>', unsafe_allow_html=True)
변이원성 = st.text_area(
    "생식세포 변이원성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('생식세포_변이원성', ''),
    height=80,
    placeholder="예: 자료없음 / 유전적인 결함을 일으킬 수 있음 (구분 1B)",
    key="germ_cell_mutagenicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['생식세포_변이원성'] = 변이원성

# 나-8. 생식독성
st.markdown('<div class="sub-item">○ 생식독성</div>', unsafe_allow_html=True)
생식독성 = st.text_area(
    "생식독성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('생식독성', ''),
    height=80,
    placeholder="예: 자료없음 / 태아 또는 생식능력에 손상을 일으킬 수 있음 (구분 1A)",
    key="reproductive_toxicity",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['생식독성'] = 생식독성

# 나-9. 특정 표적장기 독성 (1회 노출)
st.markdown('<div class="sub-item">○ 특정 표적장기 독성 (1회 노출)</div>', unsafe_allow_html=True)
표적장기1회 = st.text_area(
    "특정 표적장기 독성 (1회 노출)",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('특정_표적장기_독성_1회_노출', ''),
    height=80,
    placeholder="예: 자료없음 / 호흡기계 자극을 일으킬 수 있음 (구분 3)",
    key="stot_single",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['특정_표적장기_독성_1회_노출'] = 표적장기1회

# 나-10. 특정 표적장기 독성 (반복 노출)
st.markdown('<div class="sub-item">○ 특정 표적장기 독성 (반복 노출)</div>', unsafe_allow_html=True)
표적장기반복 = st.text_area(
    "특정 표적장기 독성 (반복 노출)",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('특정_표적장기_독성_반복_노출', ''),
    height=80,
    placeholder="예: 자료없음 / 장기간 또는 반복 노출되면 간에 손상을 일으킬 수 있음 (구분 2)",
    key="stot_repeated",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['특정_표적장기_독성_반복_노출'] = 표적장기반복

# 나-11. 흡인 유해성
st.markdown('<div class="sub-item">○ 흡인 유해성</div>', unsafe_allow_html=True)
흡인유해성 = st.text_area(
    "흡인 유해성",
    value=st.session_state.section11_data['나_건강_유해성_정보'].get('흡인_유해성', ''),
    height=80,
    placeholder="예: 자료없음 / 삼켜서 기도로 유입되면 치명적일 수 있음 (구분 1)",
    key="aspiration_hazard",
    label_visibility="collapsed"
)
st.session_state.section11_data['나_건강_유해성_정보']['흡인_유해성'] = 흡인유해성

# 참고 안내
st.info("💡 **참고**: 가.항 및 나.항을 합쳐서 노출 경로와 건강 유해성 정보를 함께 기재할 수 있습니다.")

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 11. 독성에 관한 정보")
    
    st.write("**가. 가능성이 높은 노출 경로에 관한 정보**")
    st.text(st.session_state.section11_data.get('가_가능성이_높은_노출_경로에_관한_정보', '') or '(미입력)')
    
    st.write("\n**나. 건강 유해성 정보**")
    
    건강유해성_항목 = [
        ('급성_독성', '급성 독성'),
        ('피부_부식성_또는_자극성', '피부 부식성 또는 자극성'),
        ('심한_눈_손상_또는_자극성', '심한 눈 손상 또는 자극성'),
        ('호흡기_과민성', '호흡기 과민성'),
        ('피부_과민성', '피부 과민성'),
        ('발암성', '발암성'),
        ('생식세포_변이원성', '생식세포 변이원성'),
        ('생식독성', '생식독성'),
        ('특정_표적장기_독성_1회_노출', '특정 표적장기 독성 (1회 노출)'),
        ('특정_표적장기_독성_반복_노출', '특정 표적장기 독성 (반복 노출)'),
        ('흡인_유해성', '흡인 유해성')
    ]
    
    for key, label in 건강유해성_항목:
        value = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        st.write(f"  ○ **{label}**: {value or '(미입력)'}")
    
    st.write("\n### 원본 데이터")
    st.json(st.session_state.section11_data)
