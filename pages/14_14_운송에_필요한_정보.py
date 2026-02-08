import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSDS 섹션 14 - 운송에 필요한 정보", layout="wide", initial_sidebar_state="collapsed")

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
    .transport-section { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>14. 운송에 필요한 정보</h2></div>', unsafe_allow_html=True)

if 'section14_data' not in st.session_state:
    st.session_state.section14_data = {
        '가_유엔번호': '', '나_적정선적명': '', '다_운송에서의_위험성_등급': '',
        '라_용기등급': '', '마_해양오염물질': '',
        '바_사용자가_운송_또는_운송수단에_관련해_알_필요가_있거나_필요한_특별한_안전대책': {
            '화재시_비상조치': '', '유출시_비상조치': ''
        }
    }

st.markdown('<div class="subsection-header">가. 유엔번호(UN No.)</div>', unsafe_allow_html=True)
un_number = st.text_input("유엔번호", value=st.session_state.section14_data.get('가_유엔번호', ''), placeholder="예: UN1234 또는 해당없음", key="un_number", label_visibility="collapsed")
st.session_state.section14_data['가_유엔번호'] = un_number

st.markdown('<div class="subsection-header">나. 적정선적명</div>', unsafe_allow_html=True)
proper_shipping_name = st.text_input("적정선적명", value=st.session_state.section14_data.get('나_적정선적명', ''), placeholder="예: FLAMMABLE LIQUID, N.O.S. 또는 해당없음", key="proper_shipping_name", label_visibility="collapsed")
st.session_state.section14_data['나_적정선적명'] = proper_shipping_name

st.markdown('<div class="subsection-header">다. 운송에서의 위험성 등급</div>', unsafe_allow_html=True)
transport_hazard_class = st.text_input("위험성 등급", value=st.session_state.section14_data.get('다_운송에서의_위험성_등급', ''), placeholder="예: Class 3 (인화성 액체) 또는 해당없음", key="transport_hazard_class", label_visibility="collapsed")
st.session_state.section14_data['다_운송에서의_위험성_등급'] = transport_hazard_class

st.markdown('<div class="subsection-header">라. 용기등급</div>', unsafe_allow_html=True)
packing_group = st.text_input("용기등급", value=st.session_state.section14_data.get('라_용기등급', ''), placeholder="예: II 또는 III 또는 해당없음", key="packing_group", label_visibility="collapsed")
st.session_state.section14_data['라_용기등급'] = packing_group

st.markdown('<div class="subsection-header">마. 해양오염물질</div>', unsafe_allow_html=True)
marine_pollutant = st.radio("해양오염물질 여부", options=["자료없음", "해당없음", "해당됨"], horizontal=True, key="marine_pollutant", label_visibility="collapsed")
st.session_state.section14_data['마_해양오염물질'] = marine_pollutant

st.markdown('<div class="subsection-header">바. 사용자가 운송 또는 운송수단에 관련해 알 필요가 있거나 필요한 특별한 안전대책</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown("**화재시 비상조치**")
    fire_emergency = st.text_input("화재시 비상조치", value=st.session_state.section14_data['바_사용자가_운송_또는_운송수단에_관련해_알_필요가_있거나_필요한_특별한_안전대책'].get('화재시_비상조치', ''), placeholder="예: F-E", key="fire_emergency", label_visibility="collapsed")
with col2:
    st.markdown("**유출시 비상조치**")
    spill_emergency = st.text_input("유출시 비상조치", value=st.session_state.section14_data['바_사용자가_운송_또는_운송수단에_관련해_알_필요가_있거나_필요한_특별한_안전대책'].get('유출시_비상조치', ''), placeholder="예: S-D", key="spill_emergency", label_visibility="collapsed")
st.session_state.section14_data['바_사용자가_운송_또는_운송수단에_관련해_알_필요가_있거나_필요한_특별한_안전대책'] = {'화재시_비상조치': fire_emergency, '유출시_비상조치': spill_emergency}

st.info("💡 **참고사항**\n- UN번호, 적정선적명 등은 UN 위험물 운송 권고안(Orange Book)을 참조하세요.\n- 해당사항이 없는 경우 \"해당없음\"으로 기재하세요.")

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 14 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 14가 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    for 제목, 키 in [("가. 유엔번호", '가_유엔번호'), ("나. 적정선적명", '나_적정선적명'), ("다. 운송에서의 위험성 등급", '다_운송에서의_위험성_등급'), ("라. 용기등급", '라_용기등급'), ("마. 해양오염물질", '마_해양오염물질')]:
        내용 = st.session_state.section14_data.get(키, '')
        if 내용:
            st.write(f"**{제목}**: {내용}")
    st.json(st.session_state.section14_data)
