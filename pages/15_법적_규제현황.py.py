import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 15 - 법적 규제현황",
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
    .regulation-category {
        background-color: #f5f5f5;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        font-weight: bold;
    }
    .material-selection-box {
        border: 2px solid #ff0000;
        padding: 15px;
        border-radius: 5px;
        background-color: #fff5f5;
        margin: 10px 0;
    }
    .conclusion-box {
        background-color: #e8f4ff;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>15. 법적 규제현황</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section15_data' not in st.session_state:
    st.session_state.section15_data = {
        '가_산업안전보건법': {
            '작업환경측정대상물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '관리대상유해물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '특수건강진단대상물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '노출기준설정물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '허용기준설정물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '허가대상물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '제조금지물질': {'결론': '', '선택물질': {}, '상세내용': ''}
        },
        '나_화학물질관리법': {
            '유독물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '허가물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '제한물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '금지물질': {'결론': '', '선택물질': {}, '상세내용': ''},
            '사고대비물질': {'결론': '', '선택물질': {}, '상세내용': ''}
        },
        '다_위험물안전관리법': '',
        '라_폐기물관리법': '',
        '마_기타_국내_및_외국법': ''
    }

# 섹션 3에서 물질명 가져오기
materials = []
if 'section3_data' in st.session_state:
    for comp in st.session_state.get('section3_data', {}).get('components', []):
        if comp.get('물질명'):
            materials.append({
                '물질명': comp.get('물질명'),
                'CAS번호': comp.get('CAS번호', ''),
                '함유량': comp.get('함유량(%)', '')
            })

if not materials:
    st.warning("⚠️ 섹션 3에서 구성성분 정보를 먼저 입력해주세요.")
    materials = [{'물질명': '예시물질', 'CAS번호': '1234-56-7', '함유량': '10-20'}]  # 예시용

# 가. 산업안전보건법에 의한 규제
st.markdown('<div class="subsection-header">가. 산업안전보건법에 의한 규제</div>', unsafe_allow_html=True)

산안법_항목들 = [
    '작업환경측정대상물질',
    '관리대상유해물질',
    '특수건강진단대상물질',
    '노출기준설정물질',
    '허용기준설정물질',
    '허가대상물질',
    '제조금지물질'
]

for 항목 in 산안법_항목들:
    st.markdown(f'<div class="regulation-category">{항목}</div>', unsafe_allow_html=True)
    
    # 결론 입력 필드
    col1, col2 = st.columns([1, 3])
    with col1:
        결론 = st.text_input(
            "결론",
            value=st.session_state.section15_data['가_산업안전보건법'][항목].get('결론', ''),
            placeholder="예: 해당됨/해당없음",
            key=f"산안법_{항목}_결론",
            label_visibility="collapsed"
        )
        st.session_state.section15_data['가_산업안전보건법'][항목]['결론'] = 결론
    
    # 물질 선택 박스
    st.markdown('<div class="material-selection-box">', unsafe_allow_html=True)
    st.markdown("**해당물질 선택**")
    
    선택된_물질 = {}
    cols = st.columns(2)
    for idx, material in enumerate(materials):
        with cols[idx % 2]:
            col_a, col_b = st.columns([3, 2])
            with col_a:
                if st.checkbox(
                    f"{material['물질명']} (CAS: {material['CAS번호']}, 함유량: {material['함유량']}%)",
                    key=f"산안법_{항목}_{material['물질명']}"
                ):
                    with col_b:
                        규제함유량 = st.text_input(
                            "규제대상 함유량",
                            placeholder="예: 1% 이상",
                            key=f"산안법_{항목}_{material['물질명']}_함유량",
                            label_visibility="collapsed"
                        )
                        선택된_물질[material['물질명']] = {
                            'CAS번호': material['CAS번호'],
                            '함유량': material['함유량'],
                            '규제함유량': 규제함유량
                        }
    
    st.session_state.section15_data['가_산업안전보건법'][항목]['선택물질'] = 선택된_물질
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 추가 설명
    상세내용 = st.text_area(
        "추가 설명",
        value=st.session_state.section15_data['가_산업안전보건법'][항목].get('상세내용', ''),
        height=70,
        placeholder="필요시 추가 설명을 입력하세요",
        key=f"산안법_{항목}_상세",
        label_visibility="collapsed"
    )
    st.session_state.section15_data['가_산업안전보건법'][항목]['상세내용'] = 상세내용

# 나. 화학물질관리법에 의한 규제
st.markdown('<div class="subsection-header">나. 화학물질관리법에 의한 규제</div>', unsafe_allow_html=True)

화관법_항목들 = [
    '유독물질',
    '허가물질',
    '제한물질',
    '금지물질',
    '사고대비물질'
]

for 항목 in 화관법_항목들:
    st.markdown(f'<div class="regulation-category">{항목}</div>', unsafe_allow_html=True)
    
    # 결론 입력 필드
    col1, col2 = st.columns([1, 3])
    with col1:
        결론 = st.text_input(
            "결론",
            value=st.session_state.section15_data['나_화학물질관리법'][항목].get('결론', ''),
            placeholder="예: 해당됨/해당없음",
            key=f"화관법_{항목}_결론",
            label_visibility="collapsed"
        )
        st.session_state.section15_data['나_화학물질관리법'][항목]['결론'] = 결론
    
    # 물질 선택 박스
    st.markdown('<div class="material-selection-box">', unsafe_allow_html=True)
    st.markdown("**해당물질 선택**")
    
    선택된_물질 = {}
    cols = st.columns(2)
    for idx, material in enumerate(materials):
        with cols[idx % 2]:
            col_a, col_b = st.columns([3, 2])
            with col_a:
                if st.checkbox(
                    f"{material['물질명']} (CAS: {material['CAS번호']}, 함유량: {material['함유량']}%)",
                    key=f"화관법_{항목}_{material['물질명']}"
                ):
                    with col_b:
                        규제함유량 = st.text_input(
                            "규제대상 함유량",
                            placeholder="예: 0.1% 이상",
                            key=f"화관법_{항목}_{material['물질명']}_함유량",
                            label_visibility="collapsed"
                        )
                        선택된_물질[material['물질명']] = {
                            'CAS번호': material['CAS번호'],
                            '함유량': material['함유량'],
                            '규제함유량': 규제함유량
                        }
    
    st.session_state.section15_data['나_화학물질관리법'][항목]['선택물질'] = 선택된_물질
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 추가 설명
    상세내용 = st.text_area(
        "추가 설명",
        value=st.session_state.section15_data['나_화학물질관리법'][항목].get('상세내용', ''),
        height=70,
        placeholder="필요시 추가 설명을 입력하세요",
        key=f"화관법_{항목}_상세",
        label_visibility="collapsed"
    )
    st.session_state.section15_data['나_화학물질관리법'][항목]['상세내용'] = 상세내용

# 다. 위험물안전관리법에 의한 규제
st.markdown('<div class="subsection-header">다. 위험물안전관리법에 의한 규제</div>', unsafe_allow_html=True)
위험물_value = st.text_area(
    "위험물안전관리법",
    value=st.session_state.section15_data.get('다_위험물안전관리법', ''),
    height=80,
    placeholder="예: 제4류 인화성액체, 제1석유류(비수용성액체), 200ℓ",
    key="위험물안전관리법"
)
st.session_state.section15_data['다_위험물안전관리법'] = 위험물_value

# 라. 폐기물관리법에 의한 규제
st.markdown('<div class="subsection-header">라. 폐기물관리법에 의한 규제</div>', unsafe_allow_html=True)
폐기물_value = st.text_area(
    "폐기물관리법",
    value=st.session_state.section15_data.get('라_폐기물관리법', ''),
    height=80,
    placeholder="예: 지정폐기물(폐유기용제)",
    key="폐기물관리법"
)
st.session_state.section15_data['라_폐기물관리법'] = 폐기물_value

# 마. 기타 국내 및 외국법에 의한 규제
st.markdown('<div class="subsection-header">마. 기타 국내 및 외국법에 의한 규제</div>', unsafe_allow_html=True)

# 세부 항목들 정의
기타법규_항목들 = {
    '국내규제': {
        '잔류성유기오염물질관리법': {'결론': '', '선택물질': {}, '상세내용': ''}
    },
    '국외규제': {
        '미국관리정보(OSHA 규정)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(CERCLA 규정)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(EPCRA 302 규정)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(EPCRA 304 규정)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(EPCRA 313 규정)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(로테르담협약물질)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(스톡홀름협약물질)': {'결론': '', '선택물질': {}, '상세내용': ''},
        '미국관리정보(몬트리올의정서물질)': {'결론': '', '선택물질': {}, '상세내용': ''},
        'EU 분류정보(확정분류결과)': {'결론': '', '선택물질': {}, '상세내용': ''},
        'EU 분류정보(위험문구)': {'결론': '', '선택물질': {}, '상세내용': ''},
        'EU 분류정보(안전문구)': {'결론': '', '선택물질': {}, '상세내용': ''}
    }
}

# 세션 상태에 없으면 초기화
if '마_기타_국내_및_외국법' not in st.session_state.section15_data or isinstance(st.session_state.section15_data['마_기타_국내_및_외국법'], str):
    st.session_state.section15_data['마_기타_국내_및_외국법'] = 기타법규_항목들

# 국내규제
st.markdown("**국내규제**")
for 항목, 데이터 in 기타법규_항목들['국내규제'].items():
    st.markdown(f'<div class="regulation-category">{항목}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        결론 = st.text_input(
            f"{항목} 결론",
            value=st.session_state.section15_data['마_기타_국내_및_외국법']['국내규제'][항목].get('결론', ''),
            placeholder="해당됨/해당없음",
            key=f"국내규제_{항목}_결론",
            label_visibility="collapsed"
        )
        st.session_state.section15_data['마_기타_국내_및_외국법']['국내규제'][항목]['결론'] = 결론
    
    # 물질 선택
    st.markdown('<div class="material-selection-box">', unsafe_allow_html=True)
    st.markdown("**해당물질 선택**")
    
    선택된_물질 = {}
    cols = st.columns(2)
    for idx, material in enumerate(materials):
        with cols[idx % 2]:
            if st.checkbox(
                f"{material['물질명']} (CAS: {material['CAS번호']}, 함유량: {material['함유량']}%)",
                key=f"국내규제_{항목}_{material['물질명']}"
            ):
                선택된_물질[material['물질명']] = {
                    'CAS번호': material['CAS번호'],
                    '함유량': material['함유량']
                }
    
    st.session_state.section15_data['마_기타_국내_및_외국법']['국내규제'][항목]['선택물질'] = 선택된_물질
    st.markdown('</div>', unsafe_allow_html=True)

# 국외규제
st.markdown("**국외규제**")

# 미국관리정보
st.markdown("*미국관리정보*")
미국규정_목록 = [
    '미국관리정보(OSHA 규정)',
    '미국관리정보(CERCLA 규정)',
    '미국관리정보(EPCRA 302 규정)',
    '미국관리정보(EPCRA 304 규정)',
    '미국관리정보(EPCRA 313 규정)',
    '미국관리정보(로테르담협약물질)',
    '미국관리정보(스톡홀름협약물질)',
    '미국관리정보(몬트리올의정서물질)'
]

for 항목 in 미국규정_목록:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(항목)
    with col2:
        결론 = st.text_input(
            f"{항목} 결론",
            value=st.session_state.section15_data['마_기타_국내_및_외국법']['국외규제'][항목].get('결론', ''),
            placeholder="해당됨/해당없음",
            key=f"국외규제_{항목}_결론",
            label_visibility="collapsed"
        )
        st.session_state.section15_data['마_기타_국내_및_외국법']['국외규제'][항목]['결론'] = 결론

# EU 분류정보
st.markdown("*EU 분류정보*")
EU규정_목록 = [
    'EU 분류정보(확정분류결과)',
    'EU 분류정보(위험문구)',
    'EU 분류정보(안전문구)'
]

for 항목 in EU규정_목록:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(항목)
    with col2:
        결론 = st.text_input(
            f"{항목} 결론",
            value=st.session_state.section15_data['마_기타_국내_및_외국법']['국외규제'][항목].get('결론', ''),
            placeholder="해당됨/해당없음",
            key=f"국외규제_{항목}_결론",
            label_visibility="collapsed"
        )
        st.session_state.section15_data['마_기타_국내_및_외국법']['국외규제'][항목]['결론'] = 결론

# 추가 정보 안내
st.info("""
💡 **참고사항**
- 각 법규별 해당 여부는 관련 부처 고시를 확인하세요.
- 해당사항이 없는 경우 "해당없음"으로 기재하세요.
- 화학물질정보시스템(https://icis.me.go.kr) 등을 참조할 수 있습니다.
- 추후 데이터베이스 연동을 통해 자동 조회 기능이 추가될 예정입니다.
""")

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 15 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 15가 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 15. 법적 규제현황")
    
    st.write("**가. 산업안전보건법에 의한 규제**")
    for 항목, 데이터 in st.session_state.section15_data['가_산업안전보건법'].items():
        if 데이터.get('결론') or 데이터.get('선택물질'):
            st.write(f"\n  **{항목}**: {데이터.get('결론', '')}")
            if 데이터.get('선택물질'):
                for 물질명, 물질정보 in 데이터['선택물질'].items():
                    st.write(f"    - {물질명} (규제대상 함유량: {물질정보.get('규제함유량', '')})")
            if 데이터.get('상세내용'):
                st.write(f"    {데이터['상세내용']}")
    
    st.write("\n**나. 화학물질관리법에 의한 규제**")
    for 항목, 데이터 in st.session_state.section15_data['나_화학물질관리법'].items():
        if 데이터.get('결론') or 데이터.get('선택물질'):
            st.write(f"\n  **{항목}**: {데이터.get('결론', '')}")
            if 데이터.get('선택물질'):
                for 물질명, 물질정보 in 데이터['선택물질'].items():
                    st.write(f"    - {물질명} (규제대상 함유량: {물질정보.get('규제함유량', '')})")
            if 데이터.get('상세내용'):
                st.write(f"    {데이터['상세내용']}")
    
    if st.session_state.section15_data.get('다_위험물안전관리법'):
        st.write(f"\n**다. 위험물안전관리법에 의한 규제**")
        st.write(f"  {st.session_state.section15_data['다_위험물안전관리법']}")
    
    if st.session_state.section15_data.get('라_폐기물관리법'):
        st.write(f"\n**라. 폐기물관리법에 의한 규제**")
        st.write(f"  {st.session_state.section15_data['라_폐기물관리법']}")
    
    if st.session_state.section15_data.get('마_기타_국내_및_외국법'):
        st.write(f"\n**마. 기타 국내 및 외국법에 의한 규제**")
        
        # 국내규제
        st.write("  *국내규제*")
        for 항목, 데이터 in st.session_state.section15_data['마_기타_국내_및_외국법']['국내규제'].items():
            if 데이터.get('결론'):
                st.write(f"    - {항목}: {데이터['결론']}")
                if 데이터.get('선택물질'):
                    for 물질명 in 데이터['선택물질']:
                        st.write(f"      • {물질명}")
        
        # 국외규제
        st.write("\n  *국외규제*")
        for 항목, 데이터 in st.session_state.section15_data['마_기타_국내_및_외국법']['국외규제'].items():
            if 데이터.get('결론'):
                st.write(f"    - {항목}: {데이터['결론']}")
    
    # JSON 데이터
    st.write("\n### 원본 데이터")
    st.json(st.session_state.section15_data)