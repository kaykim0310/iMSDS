import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 12 - 환경에 미치는 영향",
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
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>12. 환경에 미치는 영향</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화 (공식 양식 기준)
if 'section12_data' not in st.session_state:
    st.session_state.section12_data = {
        '가_생태독성': '',
        '나_잔류성_및_분해성': '',
        '다_생물_농축성': '',
        '라_토양_이동성': '',
        '마_기타_유해_영향': ''
    }


# ============================================================
# API 결과 → 입력 필드 자동 매핑 헬퍼 함수
# ============================================================
def _val(text):
    """자료없음이면 빈 문자열 반환"""
    if not text or text.strip() in ("자료없음", ""):
        return ""
    return text.strip()


def apply_api_results_to_section12(api_results):
    """
    API 조회 결과를 section12_data 세션 상태에 매핑합니다.
    여러 물질이면 물질명 앞에 붙여서 합칩니다.
    """
    eco_lines = []
    persistence_lines = []
    bioaccum_lines = []
    soil_lines = []
    other_lines = []

    for result in api_results:
        if 'error' in result:
            continue

        name = result.get('name', result.get('cas', ''))
        env = result.get('environmental', {})

        # 가. 생태독성 — 어류/갑각류/조류를 합쳐서 기재
        eco_parts = []
        eco_tox = env.get('ecological_toxicity', {})
        fish = _val(eco_tox.get('fish', ''))
        daphnia = _val(eco_tox.get('daphnia', ''))
        algae = _val(eco_tox.get('algae', ''))
        other_eco = _val(eco_tox.get('other', ''))

        if fish:
            eco_parts.append(f"어류: {fish}")
        if daphnia:
            eco_parts.append(f"갑각류(물벼룩): {daphnia}")
        if algae:
            eco_parts.append(f"조류: {algae}")
        if other_eco:
            eco_parts.append(other_eco)
        if eco_parts:
            eco_lines.append(f"[{name}]\n" + "\n".join(eco_parts))

        # 나. 잔류성 및 분해성
        v = _val(env.get('persistence', ''))
        if v:
            persistence_lines.append(f"[{name}] {v}")

        # 다. 생물 농축성
        v = _val(env.get('bioaccumulation', ''))
        if v:
            bioaccum_lines.append(f"[{name}] {v}")

        # 라. 토양 이동성
        v = _val(env.get('soil_mobility', ''))
        if v:
            soil_lines.append(f"[{name}] {v}")

        # 마. 기타 유해 영향
        v = _val(env.get('other_effects', ''))
        if v:
            other_lines.append(f"[{name}] {v}")

    # 세션 상태에 반영
    s12 = st.session_state.section12_data

    if eco_lines:
        s12['가_생태독성'] = "\n".join(eco_lines)
    if persistence_lines:
        s12['나_잔류성_및_분해성'] = "\n".join(persistence_lines)
    if bioaccum_lines:
        s12['다_생물_농축성'] = "\n".join(bioaccum_lines)
    if soil_lines:
        s12['라_토양_이동성'] = "\n".join(soil_lines)
    if other_lines:
        s12['마_기타_유해_영향'] = "\n".join(other_lines)


# ============================================================
# KOSHA API 연동 섹션
# ============================================================
with st.expander("🔗 KOSHA API 연동 (클릭하여 열기)", expanded=False):
    st.markdown("섹션 3에 등록된 CAS 번호로 환경 영향 정보를 자동 조회합니다.")

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

        if st.button("🔍 KOSHA API에서 환경 영향 정보 조회", type="primary", key="api_query_btn"):
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from kosha_api_extended import get_environmental_info, search_by_cas
                import time

                with st.spinner("KOSHA API에서 데이터를 조회 중입니다..."):
                    api_results = []

                    for cas in cas_list:
                        search_result = search_by_cas(cas)
                        if search_result.get('success'):
                            chem_id = search_result['chemId']
                            name = search_result.get('chemNameKor', cas)
                            time.sleep(0.3)
                            env_info = get_environmental_info(chem_id)
                            api_results.append({
                                'cas': cas,
                                'name': name,
                                'environmental': env_info
                            })
                        else:
                            api_results.append({
                                'cas': cas,
                                'name': cas,
                                'error': search_result.get('error', '조회 실패')
                            })
                        time.sleep(0.3)

                    st.session_state['section12_api_results'] = api_results

                    # ★ 핵심 수정: API 결과를 입력 필드에 자동 매핑
                    apply_api_results_to_section12(api_results)

                    st.rerun()

            except ImportError:
                st.error("❌ kosha_api_extended.py 모듈을 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"❌ API 조회 중 오류: {e}")
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # API 결과 표시
    if 'section12_api_results' in st.session_state:
        st.markdown("---")
        st.markdown("**📊 조회 결과:**")

        for result in st.session_state['section12_api_results']:
            if 'error' in result:
                st.warning(f"⚠️ {result['cas']}: {result['error']}")
            else:
                env = result.get('environmental', {})
                with st.expander(f"✅ **{result['name']}** (CAS: {result['cas']}) - 상세 보기"):
                    raw = env.get('raw_items', [])
                    if raw:
                        for item in raw:
                            st.write(f"  • **{item['name']}**: {item['detail']}")
                    else:
                        st.write("  (raw_items 없음)")

        # 수동 재적용 버튼
        if st.button("📥 조회 결과를 입력란에 다시 적용", key="reapply_btn"):
            apply_api_results_to_section12(st.session_state['section12_api_results'])
            st.success("✅ API 조회 결과가 아래 입력란에 반영되었습니다.")
            st.rerun()

st.markdown("---")

# ============================================================
# 공식 양식 기준 입력 필드
# ============================================================

# 가. 생태독성
st.markdown('<div class="subsection-header">가. 생태독성</div>', unsafe_allow_html=True)

가_내용 = st.text_area(
    "생태독성",
    value=st.session_state.section12_data.get('가_생태독성', ''),
    height=150,
    placeholder="예:\n어류: LC50 = 10 mg/L (96hr, 송사리)\n수생무척추동물: EC50 = 5 mg/L (48hr, 물벼룩)\n조류: EC50 = 2 mg/L (72hr, 녹조류)",
    key="ecological_toxicity",
    label_visibility="collapsed"
)
st.session_state.section12_data['가_생태독성'] = 가_내용

# 나. 잔류성 및 분해성
st.markdown('<div class="subsection-header">나. 잔류성 및 분해성</div>', unsafe_allow_html=True)

나_내용 = st.text_area(
    "잔류성 및 분해성",
    value=st.session_state.section12_data.get('나_잔류성_및_분해성', ''),
    height=100,
    placeholder="예:\n생분해성: 이분해성 (28일 내 60% 이상 분해)\n비생물적 분해: 자료없음",
    key="persistence_degradability",
    label_visibility="collapsed"
)
st.session_state.section12_data['나_잔류성_및_분해성'] = 나_내용

# 다. 생물 농축성
st.markdown('<div class="subsection-header">다. 생물 농축성</div>', unsafe_allow_html=True)

다_내용 = st.text_area(
    "생물 농축성",
    value=st.session_state.section12_data.get('다_생물_농축성', ''),
    height=100,
    placeholder="예:\n생물농축계수(BCF): < 100\nlog Kow: 2.5\n생물농축 가능성 낮음",
    key="bioaccumulation",
    label_visibility="collapsed"
)
st.session_state.section12_data['다_생물_농축성'] = 다_내용

# 라. 토양 이동성
st.markdown('<div class="subsection-header">라. 토양 이동성</div>', unsafe_allow_html=True)

라_내용 = st.text_area(
    "토양 이동성",
    value=st.session_state.section12_data.get('라_토양_이동성', ''),
    height=100,
    placeholder="예:\n토양 흡착 계수(Koc): 자료없음\n이동성: 자료없음",
    key="soil_mobility",
    label_visibility="collapsed"
)
st.session_state.section12_data['라_토양_이동성'] = 라_내용

# 마. 기타 유해 영향
st.markdown('<div class="subsection-header">마. 기타 유해 영향</div>', unsafe_allow_html=True)

마_내용 = st.text_area(
    "기타 유해 영향",
    value=st.session_state.section12_data.get('마_기타_유해_영향', ''),
    height=100,
    placeholder="예:\n오존층 파괴 물질: 해당없음\n지구 온난화 지수(GWP): 해당없음\n기타: 자료없음",
    key="other_adverse_effects",
    label_visibility="collapsed"
)
st.session_state.section12_data['마_기타_유해_영향'] = 마_내용

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 12 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 12가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 12. 환경에 미치는 영향")

    항목들 = [
        ("가. 생태독성", '가_생태독성'),
        ("나. 잔류성 및 분해성", '나_잔류성_및_분해성'),
        ("다. 생물 농축성", '다_생물_농축성'),
        ("라. 토양 이동성", '라_토양_이동성'),
        ("마. 기타 유해 영향", '마_기타_유해_영향')
    ]

    for 제목, 키 in 항목들:
        내용 = st.session_state.section12_data.get(키, '')
        st.write(f"**{제목}**")
        st.text(내용 or '(미입력)')
        st.write("")

    st.write("### 원본 데이터")
    st.json(st.session_state.section12_data)
