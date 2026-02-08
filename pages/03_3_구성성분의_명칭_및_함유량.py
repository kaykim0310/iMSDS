import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="MSDS 섹션 3 - 구성성분의 명칭 및 함유량", layout="wide", initial_sidebar_state="collapsed")

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
    .dataframe { font-family: 'Nanum Gothic', sans-serif !important; }
    .stDataFrame { font-family: 'Nanum Gothic', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>3. 구성성분의 명칭 및 함유량</h2></div>', unsafe_allow_html=True)

if 'section3_data' not in st.session_state:
    st.session_state.section3_data = {
        'components': [
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''},
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''},
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''},
        ]
    }

num_components = len(st.session_state.section3_data['components'])

button_col1, button_col2, button_col3 = st.columns([1, 1, 8])
with button_col1:
    if st.button("➕ 성분 추가", type="primary"):
        st.session_state.section3_data['components'].append({'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''})
        st.rerun()
with button_col2:
    if st.button("➖ 성분 삭제") and num_components > 1:
        st.session_state.section3_data['components'].pop()
        st.rerun()

st.markdown("### 구성성분 정보")
header_cols = st.columns([2, 2, 2, 1])
with header_cols[0]: st.markdown("**물질명**")
with header_cols[1]: st.markdown("**관용명(이명)**")
with header_cols[2]: st.markdown("**CAS번호**")
with header_cols[3]: st.markdown("**함유량(%)**")
st.markdown("---")

for idx, component in enumerate(st.session_state.section3_data['components']):
    cols = st.columns([2, 2, 2, 1])
    with cols[0]:
        component['물질명'] = st.text_input(f"물질명 {idx+1}", value=component['물질명'], key=f"material_{idx}", label_visibility="collapsed")
    with cols[1]:
        component['관용명(이명)'] = st.text_input(f"관용명 {idx+1}", value=component['관용명(이명)'], key=f"common_name_{idx}", label_visibility="collapsed")
    with cols[2]:
        component['CAS번호'] = st.text_input(f"CAS번호 {idx+1}", value=component['CAS번호'], key=f"cas_{idx}", placeholder="예: 7732-18-5", label_visibility="collapsed")
    with cols[3]:
        component['함유량(%)'] = st.text_input(f"함유량 {idx+1}", value=component['함유량(%)'], key=f"content_{idx}", placeholder="예: 10-20", label_visibility="collapsed")

st.markdown("---")
try:
    total = 0
    valid_percentages = []
    for comp in st.session_state.section3_data['components']:
        if comp['함유량(%)'] and '-' not in comp['함유량(%)']:
            try:
                val = float(comp['함유량(%)'])
                valid_percentages.append(val)
                total += val
            except: pass
    if valid_percentages:
        st.info(f"📊 입력된 함유량 합계: {total:.1f}%")
        if abs(total - 100) > 0.1:
            st.warning(f"⚠️ 함유량 합계가 100%가 아닙니다. 확인이 필요합니다.")
except: pass

st.markdown("### 엑셀 파일로 가져오기")
col1, col2 = st.columns([1, 3])
with col1:
    template_df = pd.DataFrame({
        '물질명': ['물질명을 입력하세요', '예: 에탄올', '예: 메탄올'],
        '관용명(이명)': ['관용명 또는 이명', '예: 에틸알코올', '예: 메틸알코올'],
        'CAS번호': ['CAS 번호 입력', '64-17-5', '67-56-1'],
        '함유량(%)': ['함유량 또는 범위', '40-50', '10-20']
    })
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, sheet_name='구성성분', index=False)
        worksheet = writer.sheets['구성성분']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 25
        worksheet.column_dimensions['C'].width = 20
        worksheet.column_dimensions['D'].width = 15
    buffer.seek(0)
    st.download_button(label="📥 템플릿 다운로드", data=buffer, file_name="MSDS_구성성분_템플릿.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col2:
    uploaded_file = st.file_uploader("구성성분 정보가 포함된 엑셀 파일을 업로드하세요", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        required_cols = ['물질명', '관용명(이명)', 'CAS번호', '함유량(%)']
        df.columns = df.columns.str.strip()
        if all(col in df.columns for col in required_cols):
            components_list = []
            for _, row in df.iterrows():
                components_list.append({
                    '물질명': str(row['물질명']) if pd.notna(row['물질명']) else '',
                    '관용명(이명)': str(row['관용명(이명)']) if pd.notna(row['관용명(이명)']) else '',
                    'CAS번호': str(row['CAS번호']) if pd.notna(row['CAS번호']) else '',
                    '함유량(%)': str(row['함유량(%)']) if pd.notna(row['함유량(%)']) else ''
                })
            if st.button("엑셀 데이터 적용"):
                old_count = len(st.session_state.section3_data.get('components', []))
                for old_idx in range(old_count):
                    for wk in [f"material_{old_idx}", f"common_name_{old_idx}", f"cas_{old_idx}", f"content_{old_idx}"]:
                        if wk in st.session_state: del st.session_state[wk]
                st.session_state.section3_data['components'] = components_list
                for i, comp in enumerate(components_list):
                    st.session_state[f"material_{i}"] = comp['물질명']
                    st.session_state[f"common_name_{i}"] = comp['관용명(이명)']
                    st.session_state[f"cas_{i}"] = comp['CAS번호']
                    st.session_state[f"content_{i}"] = comp['함유량(%)']
                st.success(f"✅ {len(components_list)}개의 성분 정보를 가져왔습니다!")
                st.rerun()
        else:
            st.error("❌ 엑셀 파일에 필요한 컬럼이 없습니다.")
    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 오류가 발생했습니다: {str(e)}")

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 3 저장", type="primary", use_container_width=True):
        cleaned_components = [comp for comp in st.session_state.section3_data['components'] if any(comp.values())]
        if cleaned_components:
            st.session_state.section3_data['components'] = cleaned_components
            st.success("✅ 섹션 3이 저장되었습니다!")
        else:
            st.warning("⚠️ 최소 하나 이상의 성분 정보를 입력해주세요.")

with st.expander("저장된 데이터 확인"):
    if st.session_state.section3_data['components']:
        df_display = pd.DataFrame(st.session_state.section3_data['components'])
        st.table(df_display)
