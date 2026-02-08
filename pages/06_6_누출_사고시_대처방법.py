import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 6 - 누출 사고시 대처방법", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="section-header"><h2>6. 누출 사고시 대처방법</h2></div>', unsafe_allow_html=True)

if 'section6_data' not in st.session_state:
    st.session_state.section6_data = {
        '가_인체를_보호하기_위해_필요한_조치사항_및_보호구': '',
        '나_환경을_보호하기_위해_필요한_조치사항': '',
        '다_정화_또는_제거_방법': ''
    }

items = [
    ('가_인체를_보호하기_위해_필요한_조치사항_및_보호구', '가. 인체를 보호하기 위해 필요한 조치사항 및 보호구', "예: 적절한 보호장비를 착용하지 않은 작업자는 누출지역 접근을 금할 것", "personal_precautions"),
    ('나_환경을_보호하기_위해_필요한_조치사항', '나. 환경을 보호하기 위해 필요한 조치사항', "예: 하수구, 수계 또는 토양으로 유입되지 않도록 할 것", "environmental_precautions"),
    ('다_정화_또는_제거_방법', '다. 정화 또는 제거 방법', "예: 누출물을 적절한 흡착제로 흡수시킬 것", "cleanup_methods"),
]

for key, label, placeholder, widget_key in items:
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=st.session_state.section6_data.get(key, ''), height=120, placeholder=placeholder, key=widget_key, label_visibility="collapsed")
    st.session_state.section6_data[key] = val

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 6 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 6이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for key, label, _, _ in items:
        내용 = st.session_state.section6_data.get(key, '')
        if 내용:
            st.write(f"**{label}**")
            st.text(내용)
    st.json(st.session_state.section6_data)
