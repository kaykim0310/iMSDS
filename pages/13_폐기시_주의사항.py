import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 13 - 폐기시 주의사항",
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
    .disposal-method {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        border-left: 4px solid #0066cc;
    }
    .state-checkbox {
        margin: 10px 0;
        padding: 10px;
        background-color: #f0f7ff;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>13. 폐기시 주의사항</h2></div>', unsafe_allow_html=True)

# 폐기물 종류 및 처리방법 데이터
waste_disposal_data = {
    "1. 폐산이나 폐알칼리": {
        "액체상태": [
            "중화·산화·환원의 반응을 이용하여 처분한 후 응집·침전·여과·탈수의 방법으로 처분하여야 한다.",
            "증발·농축의 방법으로 처분하여야 한다.",
            "분리·증류·추출·여과의 방법으로 정제처분하여야 한다."
        ],
        "고체상태": [
            "수산화칼륨 및 수산화나트륨은 액체상태의 방법으로 처분하거나 매립하는 경우에는 지정폐기물을 매립할 수 있는 관리형 매립시설의 차수시설 및 침출수 처리시설의 성능에 지장을 초래하지 않도록 중화 등의 방법으로 중간처분한 후 매립하여야 한다."
        ],
        "폐산이나 폐알칼리와 폐유·폐유기용제 등 다른 폐기물이 혼합되어 있는 액체상태": [
            "소각시설에 지장이 생기지 아니하도록 중화 등으로 처분하여 소각(할로겐족 폐유기용제 등 고온소각대상 폐기물이 혼합되어 있는 경우에는 고온소각)한 후 매립하여야 한다."
        ]
    },
    "2. 폐유": {
        "액체상태": [
            "1) 기름과 물을 분리하여 분리된 기름성분은 소각하여야 하고, 기름과 물을 분리한 후 남은 물은 「물환경보전법」 제2조제12호에 따른 수질오염방지시설에서 처리하여야 한다.",
            "2) 증발·농축방법으로 처리한 후 그 잔재물은 소각하거나 안정화처분하여야 한다.",
            "3) 응집·침전방법으로 처리한 후 그 잔재물은 소각하여야 한다.",
            "4) 분리·증류·추출·여과·열분해의 방법으로 정제처분하여야 한다.",
            "5) 소각하거나 안정화처분하여야 한다."
        ],
        "고체상태(타르·피치류는 제외)": [
            "소각하거나 안정화처분하여야 한다."
        ],
        "타르·피치(pitch)류": [
            "소각하거나 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다."
        ]
    },
    "3. 폐유기용제": {
        "기름과 물 분리가 가능한 것": [
            "기름과 물 분리방법으로 사전처분하여야 한다."
        ],
        "할로겐족으로 액체상태": [
            "1) 고온소각하여야 한다.",
            "2) 증발·농축방법으로 처분한 후 그 잔재물은 고온소각하여야 한다.",
            "3) 분리·증류·추출·여과의 방법으로 정제한 후 그 잔재물은 고온소각하여야 한다.",
            "4) 중화·산화·환원·중합·축합(縮合)의 반응을 이용하여 처분하여야 하며, 처분 후 발생하는 잔재물은 고온소각하거나, 응집·침전·여과·탈수의 방법으로 다시 처분한 후 그 잔재물은 고온소각하여야 한다."
        ],
        "할로겐족으로 고체상태": [
            "고온소각하여야 한다."
        ],
        "그 밖의 폐유기용제로서 액체상태": [
            "1) 소각하여야 한다.",
            "2) 증발·농축방법으로 처분한 후 그 잔재물은 소각하여야 한다.",
            "3) 분리·증류·추출·여과의 방법으로 정제한 후 그 잔재물은 소각하여야 한다.",
            "4) 중화·산화·환원·중합·축합의 반응을 이용하여 처분하여야 하며, 처분 후 발생하는 잔재물은 소각하거나, 응집·침전·여과·탈수의 방법으로 다시 처분한 후 그 잔재물은 소각하여야 한다."
        ],
        "폐유기용제로서 고체상태": [
            "소각하여야 한다."
        ]
    },
    "4. 폐합성고분자화합물": {
        "플라스틱": [
            "소각하여야 한다. 다만, 소각이 곤란한 경우에는 최대지름 15센티미터 이하의 크기로 파쇄·절단 또는 용융한 후 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립할 수 있다."
        ]
    },
    "5. 폐페인트와 폐래커": {
        "고형화된 유기화합물": [
            "고온소각하거나 유기용제 등 재활용 대상 물질을 회수한 후 그 잔재물은 고온소각하여야 한다."
        ]
    },
    "6. 폐석면": {
        "고체상": [
            "(1) 분진이나 부스러기는 고온용융처분하거나 고형화처분하여야 한다.",
            "(2) 고형화되어 있어 흩날릴 우려가 없는 것은 폴리에틸렌 그 밖에 이와 유사한 재질의 포대로 포장하여 지정폐기물매립시설에 매립하되, 매립과정에서 석면 분진이 날리지 아니하도록 충분히 물을 뿌리고 수시로 복토를 실시하여야 하며, 장비 등을 이용한 다짐·압축작업은 복토 후에 하여야 한다.",
            "(3) 석면의 해체·제거작업에 사용된 바닥비닐시트, 방진마스크, 작업복 등은 고밀도 내수성재질의 포대에 2중으로 포장하거나 견고한 용기에 밀봉하여 지정폐기물매립시설에 매립하거나 고온용융처분 또는 고형화처분하여야 한다.",
            "(4) 매립시설내 일정구역을 정하여 매립하고, 매립구역임을 알리는 표지판을 설치"
        ]
    },
    "7. 광재·폐주물사·폐사·폐내화물·도자기조각·폐촉매": {
        "고체상": [
            "안정화처분 또는 시멘트·합성고분자화합물의 이용 그 밖에 이와 비슷한 방법으로 고형화처분하거나 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다. 다만, 가연성 물질을 포함한 폐촉매는 소각할 수 있고, 할로겐족에 해당하는 물질을 포함한 폐촉매를 소각하는 경우에는 고온 소각하여야 한다."
        ]
    },
    "8. 폐흡수제와 폐흡착제": {
        "고체상": [
            "1) 고온소각 처분대상물질을 흡수하거나 흡착한 것 중 가연성은 고온소각하여야 하고, 불연성은 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다.",
            "2) 일반소각 처분대상물질을 흡수하거나 흡착한 것 중 가연성은 일반소각하여야 하며, 불연성은 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다.",
            "3) 안정화처분하거나 시멘트·합성고분자화합물을 이용하여 고형화처분하거나 이와 비슷한 방법으로 고형화처분하여야 한다.",
            "4) 광물유·동물유 또는 식물유가 포함된 것은 포함된 기름을 추출 등으로 재활용하여야 한다."
        ]
    },
    "9. 분진": {
        "분진": [
            "(1) 폴리에틸렌이나 그 밖에 이와 비슷한 재질의 포대에 담아 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다.",
            "(2) 안정화처분하여야 한다.",
            "(3) 시멘트·합성고분자화합물을 이용하여 고형화처분하거나 이와 비슷한 방법으로 고형화처분하여야 한다."
        ]
    },
    "10. 소각재": {
        "연방사성제품폐기물 소각재가 아닌 소각재": [
            "1) 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립해야 한다.",
            "2) 안정화처분해야 한다.",
            "3) 시멘트ㆍ합성고분자화합물을 이용하여 고형화처분하거나 이와 비슷한 방법으로 고형화처분해야 한다."
        ],
        "천연방사성제품폐기물 소각재": [
            "1) 작업자는 방진복, 보호안경, 장갑 및 1급 이상의 방진마스크를 착용해야 한다.",
            "2) 천연방사성제품폐기물 소각재가 비산, 유출 또는 방출되지 않도록 밀폐된 상태로 운반하여 지체 없이 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립해야 한다.",
            "3) 하나의 매립시설의 사용이 종료될 때까지 천연방사성제품폐기물 소각재와 불연성 천연방사성제품폐기물을 합하여 1,200톤 이하로 매립해야 한다."
        ]
    },
    "11. 폐농약": {
        "액체상태": [
            "고온소각하거나 고온용융처분하여야 한다."
        ],
        "고체상태": [
            "고온소각 또는 고온용융처분하거나 차단형 매립시설에 매립하여야 한다."
        ]
    },
    "12. 폴리클로리네이티드비페닐 함유폐기물": {
        "고형화된 유기화합물": [
            "고온소각하거나 고온용융처분하여야 한다."
        ]
    },
    "13. 오니": {
        "오니": [
            "1) 소각하여야 한다.",
            "2) 시멘트·합성고분자화합물을 이용하여 고형화처분하거나 이와 비슷한 방법으로 고형화처분하여야 한다.",
            "3) 수분함량 85퍼센트 이하로 하여 안정화처분하여야 한다.",
            "4) 수분함량 85퍼센트 이하로 하여 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다.",
            "5) 폐수배출량 2천세제곱미터 이상인 배출업소의 유기성 오니는 바로 매립하여서는 아니되며, 소각하거나 시멘트·합성고분자화합물의 이용이나 그 밖에 이와 비슷한 방법으로 고형화처분하여야 한다.",
            "6) 1일 폐수배출량 700세제곱미터 이상 2천세제곱미터 미만인 배출업소의 유기성 오니도 (5)와 같이 처분하여야 한다."
        ]
    },
    "14. 안정화·고형화·고화처리물": {
        "안정화·고형화·고화처리물": [
            "1) 지정폐기물을 매립할 수 있는 관리형 매립시설에 매립하여야 한다.",
            "2) 석면을 1퍼센트 이상 함유한 고형화처리물을 매립하는 경우에는 매립시설 내 일정구역을 정하여 매립하고, 매립구역임을 알리는 표지판을 설치하여야 한다."
        ]
    },
    "15. 폐유독물질": {
        "고체상": [
            "1) 중화·가수분해·산화·환원으로 처분하여야 한다.",
            "2) 고온소각하거나 고온용융처분하여야 한다.",
            "3) 고형화처분하여야 한다."
        ]
    },
    "16. 폐오일 필터": {
        "고체상": [
            "(1) 소각하여야 한다.",
            "(2) 파쇄처분하여 재활용할 경우 고철·여과지·고무 및 폐윤활유를 각각 분리할 수 있도록 폐오일 필터를 파쇄처분한 후 폐유·고철은 별도로 회수·선별하여 재활용하고, 여과지·고무 등 재활용이 어려운 파쇄물은 소각하거나 매립하여야 한다.",
            "(3) 증류처분하여 재활용할 경우 증류시설에서 폐유와 고철을 분리·회수하여 각각 재활용하여야 한다."
        ]
    },
    "기타 (해당사항 없음)": {
        "해당사항 없음": [
            "폐기물관리법에 명시된 경우 규정에 따라 내용물 및 용기를 폐기하시오."
        ]
    }
}

# 세션 상태 초기화
if 'section13_data' not in st.session_state:
    st.session_state.section13_data = {
        '가_폐기방법': '',
        '나_폐기시_주의사항': '',
        '선택된_폐기물_종류': '',
        '선택된_상태': [],
        '기타_폐기시_주의사항': ''
    }

# 가. 폐기방법
st.markdown('<div class="subsection-header">가. 폐기방법</div>', unsafe_allow_html=True)

# 폐기물 종류 선택 (드롭다운)
col1, col2 = st.columns([1, 2])

with col1:
    selected_waste = st.selectbox(
        "폐기물 종류",
        options=list(waste_disposal_data.keys()),
        key="waste_type_dropdown",
        help="해당하는 폐기물 종류를 선택하세요"
    )
    st.session_state.section13_data['선택된_폐기물_종류'] = selected_waste

with col2:
    if selected_waste and selected_waste != "기타 (해당사항 없음)":
        st.markdown("**폐기물 상태 선택 (복수 선택 가능)**")
        
        # 선택된 폐기물의 상태 옵션들
        states = list(waste_disposal_data[selected_waste].keys())
        
        # 체크박스로 상태 선택
        selected_states = []
        cols = st.columns(2)
        for idx, state in enumerate(states):
            with cols[idx % 2]:
                if st.checkbox(state, key=f"state_{state}"):
                    selected_states.append(state)
        
        st.session_state.section13_data['선택된_상태'] = selected_states

# 선택에 따른 폐기방법 자동 표시
if st.session_state.section13_data['선택된_폐기물_종류'] and st.session_state.section13_data['선택된_상태']:
    st.markdown("#### 폐기방법")
    
    disposal_methods = []
    for state in st.session_state.section13_data['선택된_상태']:
        methods = waste_disposal_data[st.session_state.section13_data['선택된_폐기물_종류']][state]
        for method in methods:
            disposal_methods.append(method)
    
    # 폐기방법 표시
    disposal_text = "\n".join(disposal_methods)
    st.text_area(
        "폐기방법",
        value=disposal_text,
        height=200,
        key="disposal_methods_display",
        disabled=True,
        label_visibility="collapsed"
    )
    
    st.session_state.section13_data['가_폐기방법'] = disposal_text

elif st.session_state.section13_data['선택된_폐기물_종류'] == "기타 (해당사항 없음)":
    # 기타 선택시 자동으로 기본 문구 표시
    disposal_text = "폐기물관리법에 명시된 경우 규정에 따라 내용물 및 용기를 폐기하시오."
    st.text_area(
        "폐기방법",
        value=disposal_text,
        height=60,
        key="disposal_methods_default",
        disabled=True,
        label_visibility="collapsed"
    )
    st.session_state.section13_data['가_폐기방법'] = disposal_text

# 나. 폐기시 주의사항
st.markdown('<div class="subsection-header">나. 폐기시 주의사항</div>', unsafe_allow_html=True)

# 기본 주의사항 (고정)
default_caution_text = """폐기물 관리법에 따라 내용물 용기를 폐기하시오.
본 폐기물은 지정폐기물이므로 법규에 명시한 내용에 따라 처리 하시오."""

st.text_area(
    "폐기시 주의사항",
    value=default_caution_text,
    height=80,
    key="default_caution_display",
    disabled=True,
    label_visibility="collapsed"
)
st.session_state.section13_data['나_폐기시_주의사항'] = default_caution_text

# 추가 주의사항
additional_caution = st.text_area(
    "추가 주의사항 (선택사항)",
    value=st.session_state.section13_data.get('기타_폐기시_주의사항', ''),
    height=100,
    placeholder="추가적인 폐기시 주의사항이 있으면 입력하세요",
    key="additional_caution_input"
)
st.session_state.section13_data['기타_폐기시_주의사항'] = additional_caution

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 13 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 13이 저장되었습니다!")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    st.write("### 13. 폐기시 주의사항")
    
    st.write("**가. 폐기방법**")
    if st.session_state.section13_data.get('가_폐기방법'):
        st.text(st.session_state.section13_data['가_폐기방법'])
    else:
        st.text("폐기물 종류와 상태를 선택해주세요.")
    
    st.write("\n**나. 폐기시 주의사항**")
    st.text(st.session_state.section13_data.get('나_폐기시_주의사항', ''))
    
    if st.session_state.section13_data.get('기타_폐기시_주의사항'):
        st.write("\n**추가 주의사항**")
        st.text(st.session_state.section13_data['기타_폐기시_주의사항'])
    
    # JSON 데이터
    st.write("\n### 원본 데이터")
    st.json(st.session_state.section13_data)