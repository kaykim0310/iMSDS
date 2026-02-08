import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 9 - 물리화학적 특성", layout="wide", initial_sidebar_state="collapsed")

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
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-family: 'Nanum Gothic', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>9. 물리화학적 특성</h2></div>', unsafe_allow_html=True)

if 'section9_data' not in st.session_state:
    st.session_state.section9_data = {
        '가_외관': {'성상': '', '색상': '', '출처': ''},
        '나_냄새': {'값': '', '출처': ''}, '다_냄새역치': {'값': '', '출처': ''},
        '라_pH': {'값': '', '출처': ''}, '마_녹는점_어는점': {'값': '', '출처': ''},
        '바_초기끓는점과_끓는점범위': {'값': '', '출처': ''}, '사_인화점': {'값': '', '출처': ''},
        '아_증발속도': {'값': '', '출처': ''}, '자_인화성_고체_기체': {'값': '', '출처': ''},
        '차_인화_또는_폭발범위의_상한_하한': {'값': '', '출처': ''}, '카_증기압': {'값': '', '출처': ''},
        '타_용해도': {'값': '', '출처': ''}, '파_증기밀도': {'값': '', '출처': ''},
        '하_비중': {'값': '', '출처': ''}, '거_n옥탄올_물분배계수': {'값': '', '출처': ''},
        '너_자연발화온도': {'값': '', '출처': ''}, '더_분해온도': {'값': '', '출처': ''},
        '러_점도': {'값': '', '출처': ''}, '머_분자량': {'값': '', '출처': ''}
    }

st.markdown("### 물리화학적 특성 정보")

st.markdown("#### 가. 외관")
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    성상 = st.text_input("성상", value=st.session_state.section9_data['가_외관'].get('성상', ''), placeholder="예: 액체", key="appearance_state")
with col2:
    색상 = st.text_input("색상", value=st.session_state.section9_data['가_외관'].get('색상', ''), placeholder="예: 무색투명", key="appearance_color")
with col3:
    외관_출처 = st.text_input("출처", value=st.session_state.section9_data['가_외관'].get('출처', ''), placeholder="출처 입력 (선택사항)", key="appearance_source")
st.session_state.section9_data['가_외관'] = {'성상': 성상, '색상': 색상, '출처': 외관_출처}

properties = [
    ('나_냄새', '나. 냄새', '예: 무취'), ('다_냄새역치', '다. 냄새역치', '예: 자료없음'),
    ('라_pH', '라. pH', '예: 7.0'), ('마_녹는점_어는점', '마. 녹는점/어는점', '예: 0℃'),
    ('바_초기끓는점과_끓는점범위', '바. 초기 끓는점과 끓는점 범위', '예: 100℃'),
    ('사_인화점', '사. 인화점', '예: 자료없음'), ('아_증발속도', '아. 증발속도', '예: 자료없음'),
    ('자_인화성_고체_기체', '자. 인화성(고체, 기체)', '예: 해당없음'),
    ('차_인화_또는_폭발범위의_상한_하한', '차. 인화 또는 폭발 범위의 상한/하한', '예: 자료없음'),
    ('카_증기압', '카. 증기압', '예: 23.8 mmHg (25℃)'), ('타_용해도', '타. 용해도', '예: 물에 가용'),
    ('파_증기밀도', '파. 증기밀도', '예: 자료없음'), ('하_비중', '하. 비중', '예: 1.0'),
    ('거_n옥탄올_물분배계수', '거. n-옥탄올/물분배계수', '예: 자료없음'),
    ('너_자연발화온도', '너. 자연발화온도', '예: 자료없음'), ('더_분해온도', '더. 분해온도', '예: 자료없음'),
    ('러_점도', '러. 점도', '예: 자료없음'), ('머_분자량', '머. 분자량', '예: 18.015')
]

for key, label, placeholder in properties:
    st.markdown(f"#### {label}")
    col1, col2 = st.columns([2, 1])
    with col1:
        value = st.text_input(label, value=st.session_state.section9_data[key].get('값', ''), placeholder=placeholder, key=f"{key}_value", label_visibility="collapsed")
    with col2:
        source = st.text_input(f"{label} 출처", value=st.session_state.section9_data[key].get('출처', ''), placeholder="출처 입력 (선택사항)", key=f"{key}_source", label_visibility="collapsed")
    st.session_state.section9_data[key] = {'값': value, '출처': source}

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 9 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 9가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    preview_data = []
    외관_값 = f"성상: {st.session_state.section9_data['가_외관']['성상']}, 색상: {st.session_state.section9_data['가_외관']['색상']}"
    preview_data.append(["가. 외관", 외관_값])
    for key, label, _ in properties:
        값 = st.session_state.section9_data[key]['값']
        출처 = st.session_state.section9_data[key]['출처']
        표시값 = f"{값} [{출처}]" if 출처 else 값
        preview_data.append([label, 표시값])
    st.table(pd.DataFrame(preview_data, columns=['항목', '값']).set_index('항목'))
    st.json(st.session_state.section9_data)
