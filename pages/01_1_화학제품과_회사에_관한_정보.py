import streamlit as st
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="MSDS 섹션 1 - 화학제품과 회사에 관한 정보", layout="wide", initial_sidebar_state="collapsed")

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

st.markdown('<div class="section-header"><h2>1. 화학제품과 회사에 관한 정보</h2></div>', unsafe_allow_html=True)

if 'section1_data' not in st.session_state:
    st.session_state.section1_data = {
        'product_name': '', 'product_code': '', 'management_number': '',
        'recommended_use': '', 'restrictions_on_use': '',
        'manufacturer_info': {
            'company_name': '', 'address': '', 'phone': '', 'fax': '', 'emergency_phone': ''
        },
        'supplier_info': {
            'company_name': '', 'address': '', 'phone': '', 'fax': '', 'emergency_phone': ''
        },
        'initial_date': date.today(),
        'revision_date': date.today()
    }

st.markdown('<div class="subsection-header">가. 제품명(제품번호)</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    product_name = st.text_input("제품명", value=st.session_state.section1_data.get('product_name', ''), placeholder="예: 아세톤", key="product_name")
    st.session_state.section1_data['product_name'] = product_name
with col2:
    product_code = st.text_input("제품번호", value=st.session_state.section1_data.get('product_code', ''), placeholder="예: CHM-001", key="product_code")
    st.session_state.section1_data['product_code'] = product_code
with col3:
    management_number = st.text_input("관리번호", value=st.session_state.section1_data.get('management_number', ''), placeholder="예: MSDS-2025-001", key="management_number")
    st.session_state.section1_data['management_number'] = management_number

st.markdown('<div class="subsection-header">나. 제품의 권고 용도와 사용상의 제한</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    recommended_use = st.text_area("제품의 권고 용도", value=st.session_state.section1_data.get('recommended_use', ''), height=80, placeholder="예: 용제, 세정제, 화학합성 중간체", key="recommended_use")
    st.session_state.section1_data['recommended_use'] = recommended_use
with col2:
    restrictions = st.text_area("사용상의 제한", value=st.session_state.section1_data.get('restrictions_on_use', ''), height=80, placeholder="예: 공업용 외 사용 금지", key="restrictions_on_use")
    st.session_state.section1_data['restrictions_on_use'] = restrictions

st.markdown('<div class="subsection-header">다. 공급자 정보 (제조자/수입자/유통업자)</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏭 제조자/공급자", "🚚 수입자/유통업자"])

with tab1:
    mfr = st.session_state.section1_data['manufacturer_info']
    col1, col2 = st.columns(2)
    with col1:
        mfr['company_name'] = st.text_input("회사명 (제조자)", value=mfr.get('company_name', ''), placeholder="예: ○○화학(주)", key="mfr_company")
        mfr['address'] = st.text_input("주소 (제조자)", value=mfr.get('address', ''), placeholder="예: 서울특별시 강남구 ○○로 123", key="mfr_address")
    with col2:
        mfr['phone'] = st.text_input("전화번호 (제조자)", value=mfr.get('phone', ''), placeholder="예: 02-1234-5678", key="mfr_phone")
        mfr['fax'] = st.text_input("팩스번호 (제조자)", value=mfr.get('fax', ''), placeholder="예: 02-1234-5679", key="mfr_fax")
    mfr['emergency_phone'] = st.text_input("긴급 연락번호 (제조자)", value=mfr.get('emergency_phone', ''), placeholder="예: 02-1234-9999 (24시간)", key="mfr_emergency")

with tab2:
    sup = st.session_state.section1_data['supplier_info']
    col1, col2 = st.columns(2)
    with col1:
        sup['company_name'] = st.text_input("회사명 (공급자)", value=sup.get('company_name', ''), placeholder="예: △△무역(주)", key="sup_company")
        sup['address'] = st.text_input("주소 (공급자)", value=sup.get('address', ''), placeholder="예: 인천광역시 ○○구 ○○로 456", key="sup_address")
    with col2:
        sup['phone'] = st.text_input("전화번호 (공급자)", value=sup.get('phone', ''), placeholder="예: 032-1234-5678", key="sup_phone")
        sup['fax'] = st.text_input("팩스번호 (공급자)", value=sup.get('fax', ''), placeholder="예: 032-1234-5679", key="sup_fax")
    sup['emergency_phone'] = st.text_input("긴급 연락번호 (공급자)", value=sup.get('emergency_phone', ''), placeholder="예: 032-1234-9999 (24시간)", key="sup_emergency")

st.markdown('<div class="subsection-header">라. 작성일자</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    initial_date = st.date_input("최초 작성일", value=st.session_state.section1_data.get('initial_date', date.today()), key="initial_date")
    st.session_state.section1_data['initial_date'] = initial_date
with col2:
    revision_date = st.date_input("개정일자", value=st.session_state.section1_data.get('revision_date', date.today()), key="revision_date")
    st.session_state.section1_data['revision_date'] = revision_date

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 1 저장", type="primary", use_container_width=True):
        if product_name:
            st.success("✅ 섹션 1이 저장되었습니다!")
        else:
            st.warning("⚠️ 제품명을 입력해주세요.")

with st.expander("저장된 데이터 확인"):
    st.write("### 1. 화학제품과 회사에 관한 정보")
    st.write(f"**제품명**: {st.session_state.section1_data.get('product_name', '')}")
    st.write(f"**제품번호**: {st.session_state.section1_data.get('product_code', '')}")
    st.write(f"**관리번호**: {st.session_state.section1_data.get('management_number', '')}")
    st.write(f"**권고 용도**: {st.session_state.section1_data.get('recommended_use', '')}")
    st.write(f"**사용상의 제한**: {st.session_state.section1_data.get('restrictions_on_use', '')}")
    st.write("---")
    st.write("**제조자 정보**")
    for k, v in st.session_state.section1_data['manufacturer_info'].items():
        if v: st.write(f"  • {k}: {v}")
    st.write("**공급자 정보**")
    for k, v in st.session_state.section1_data['supplier_info'].items():
        if v: st.write(f"  • {k}: {v}")
    st.json(st.session_state.section1_data)
