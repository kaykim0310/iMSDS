import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 13 - 폐기시 주의사항", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    * { font-family: 'Nanum Gothic', sans-serif !important; }
    /* Streamlit 아이콘 폰트 복원 */
    [data-testid="stIconMaterial"],
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stTextInput > div > div > input { background-color: #f0f0f0; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>13. 폐기시 주의사항</h2></div>', unsafe_allow_html=True)

if 'section13_data' not in st.session_state:
    st.session_state.section13_data = {
        '가_폐기방법': '',
        '나_폐기시_주의사항': ''
    }

st.markdown('<div class="subsection-header">가. 폐기방법</div>', unsafe_allow_html=True)
폐기방법 = st.text_area("폐기방법", value=st.session_state.section13_data.get('가_폐기방법', ''), height=150,
    placeholder="예:\n- 폐기물관리법에 의거하여 지정폐기물로 처리할 것\n- 허가된 폐기물 처리업체에 의뢰하여 소각 또는 안전하게 매립할 것\n- 하수구, 수계 또는 토양에 방류하지 말 것",
    key="disposal_method", label_visibility="collapsed")
st.session_state.section13_data['가_폐기방법'] = 폐기방법

st.markdown('<div class="subsection-header">나. 폐기시 주의사항 (오염된 용기 및 포장의 폐기 방법 포함)</div>', unsafe_allow_html=True)
폐기주의 = st.text_area("폐기시 주의사항", value=st.session_state.section13_data.get('나_폐기시_주의사항', ''), height=150,
    placeholder="예:\n- 오염된 용기는 잔류물이 남지 않도록 세척 후 폐기할 것\n- 빈 용기에도 제품 잔류물이 남아있을 수 있으므로 취급에 주의할 것\n- 관련 법규에 따라 적절히 처리할 것",
    key="disposal_precautions", label_visibility="collapsed")
st.session_state.section13_data['나_폐기시_주의사항'] = 폐기주의

st.info("💡 **참고사항**\n- 폐기물관리법에 따른 지정폐기물 해당 여부를 확인하세요.\n- 지역별 폐기물 처리 규정이 다를 수 있으므로 관할 지자체에 확인하세요.")

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 13 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 13이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.write("**가. 폐기방법**")
    st.text(st.session_state.section13_data.get('가_폐기방법', '') or '(미입력)')
    st.write("**나. 폐기시 주의사항**")
    st.text(st.session_state.section13_data.get('나_폐기시_주의사항', '') or '(미입력)')
    st.json(st.session_state.section13_data)
