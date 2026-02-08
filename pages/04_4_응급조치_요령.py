import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 4 - 응급조치 요령", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="section-header"><h2>4. 응급조치 요령</h2></div>', unsafe_allow_html=True)

if 'section4_data' not in st.session_state:
    st.session_state.section4_data = {
        '가_눈에_들어갔을_때': '', '나_피부에_접촉했을_때': '',
        '다_흡입했을_때': '', '라_먹었을_때': '', '마_기타_의사의_주의사항': ''
    }

items = [
    ('가_눈에_들어갔을_때', '가. 눈에 들어갔을 때', "예: 즉시 다량의 물로 15분 이상 씻어내고 의사의 진료를 받을 것", "eye_contact"),
    ('나_피부에_접촉했을_때', '나. 피부에 접촉했을 때', "예: 오염된 의복을 벗기고 피부를 물과 비누로 씻을 것", "skin_contact"),
    ('다_흡입했을_때', '다. 흡입했을 때', "예: 신선한 공기가 있는 곳으로 옮기고 호흡하기 쉬운 자세로 안정을 취할 것", "inhalation"),
    ('라_먹었을_때', '라. 먹었을 때', "예: 입을 씻어내고 즉시 의사의 진료를 받을 것", "ingestion"),
    ('마_기타_의사의_주의사항', '마. 기타 의사의 주의사항', "예: 증상에 따라 치료할 것", "physician_notes"),
]

for key, label, placeholder, widget_key in items:
    st.markdown(f'<div class="subsection-header">{label}</div>', unsafe_allow_html=True)
    val = st.text_area(label, value=st.session_state.section4_data.get(key, ''), height=100, placeholder=placeholder, key=widget_key, label_visibility="collapsed")
    st.session_state.section4_data[key] = val

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 4 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 4가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for key, label, _, _ in items:
        내용 = st.session_state.section4_data.get(key, '')
        if 내용:
            st.write(f"**{label}**")
            st.text(내용)
    st.json(st.session_state.section4_data)
