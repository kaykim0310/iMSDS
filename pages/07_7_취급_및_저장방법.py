import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 7 - 취급 및 저장방법", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');

    * {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    /* Streamlit 아이콘 폰트 복원 */
    [data-testid="stIconMaterial"],
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }

    .stTextInput > div > div > input { background-color: #f0f0f0; font-family: 'Nanum Gothic', sans-serif !important; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; font-family: 'Nanum Gothic', sans-serif !important; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-family: 'Nanum Gothic', sans-serif !important; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>7. 취급 및 저장방법</h2></div>', unsafe_allow_html=True)

if 'section7_data' not in st.session_state:
    st.session_state.section7_data = {'가_안전취급요령': '', '나_안전한_저장방법': ''}

st.markdown('<div class="subsection-header">가. 안전취급요령</div>', unsafe_allow_html=True)
가_내용 = st.text_area("안전취급요령", value=st.session_state.section7_data.get('가_안전취급요령', ''), height=150, placeholder="예: 모든 안전주의사항을 읽고 이해하기 전에는 취급하지 말 것", key="handling_precautions", label_visibility="collapsed")
st.session_state.section7_data['가_안전취급요령'] = 가_내용

st.markdown('<div class="subsection-header">나. 안전한 저장방법 (피해야 할 조건을 포함함)</div>', unsafe_allow_html=True)
나_내용 = st.text_area("안전한 저장방법", value=st.session_state.section7_data.get('나_안전한_저장방법', ''), height=150, placeholder="예: 용기를 단단히 밀폐하여 환기가 잘 되는 곳에 저장할 것", key="storage_conditions", label_visibility="collapsed")
st.session_state.section7_data['나_안전한_저장방법'] = 나_내용

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 7 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 7이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for 제목, 키 in [("가. 안전취급요령", '가_안전취급요령'), ("나. 안전한 저장방법", '나_안전한_저장방법')]:
        내용 = st.session_state.section7_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**")
            st.text(내용)
    st.json(st.session_state.section7_data)
