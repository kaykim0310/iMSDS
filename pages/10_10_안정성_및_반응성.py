import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 10 - 안정성 및 반응성", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="section-header"><h2>10. 안정성 및 반응성</h2></div>', unsafe_allow_html=True)

if 'section10_data' not in st.session_state:
    st.session_state.section10_data = {
        '가_화학적_안정성_및_유해_반응의_가능성': '', '나_피해야_할_조건': '',
        '다_피해야_할_물질': '', '라_분해시_생성되는_유해물질': ''
    }

items = [
    ('가_화학적_안정성_및_유해_반응의_가능성', '가. 화학적 안정성 및 유해 반응의 가능성', "예: 상온상압에서 안정함", "stability_reactivity", 150),
    ('나_피해야_할_조건', '나. 피해야 할 조건', "예: 열, 스파크, 화염 등 점화원", "conditions_to_avoid", 100),
    ('다_피해야_할_물질', '다. 피해야 할 물질', "예: 강산화제, 강산, 강염기", "materials_to_avoid", 100),
    ('라_분해시_생성되는_유해물질', '라. 분해시 생성되는 유해물질', "예: 열분해시 유독가스 발생 가능", "hazardous_decomposition", 100),
]

for key, label, placeholder, widget_key, height in items:
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=st.session_state.section10_data.get(key, ''), height=height, placeholder=placeholder, key=widget_key, label_visibility="collapsed")
    st.session_state.section10_data[key] = val

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 10 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 10이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for key, label, _, _, _ in items:
        내용 = st.session_state.section10_data.get(key, '')
        if 내용:
            st.write(f"**{label}**")
            st.text(내용)
    st.json(st.session_state.section10_data)
