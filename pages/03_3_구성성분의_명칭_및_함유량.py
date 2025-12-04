import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 3 - 구성성분의 명칭 및 함유량",
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
    .section-header {
        background-color: #d3e3f3;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    /* 테이블 스타일 */
    .dataframe {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    .stDataFrame {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="section-header"><h2>3. 구성성분의 명칭 및 함유량</h2></div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'section3_data' not in st.session_state:
    st.session_state.section3_data = {
        'components': [
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''},
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''},
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''},
        ]
    }

# 현재 성분 개수
num_components = len(st.session_state.section3_data['components'])

# 버튼 컨테이너
button_col1, button_col2, button_col3 = st.columns([1, 1, 8])
with button_col1:
    if st.button("➕ 성분 추가", type="primary"):
        st.session_state.section3_data['components'].append(
            {'물질명': '', '관용명(이명)': '', 'CAS번호': '', '함유량(%)': ''}
        )
        st.rerun()

with button_col2:
    if st.button("➖ 성분 삭제") and num_components > 1:
        st.session_state.section3_data['components'].pop()
        st.rerun()

# 구성성분 입력 테이블
st.markdown("### 구성성분 정보")

# 헤더
header_cols = st.columns([2, 2, 2, 1])
with header_cols[0]:
    st.markdown("**물질명**")
with header_cols[1]:
    st.markdown("**관용명(이명)**")
with header_cols[2]:
    st.markdown("**CAS번호**")
with header_cols[3]:
    st.markdown("**함유량(%)**")

# 구분선
st.markdown("---")

# 각 성분에 대한 입력 필드
for idx, component in enumerate(st.session_state.section3_data['components']):
    cols = st.columns([2, 2, 2, 1])
    
    with cols[0]:
        component['물질명'] = st.text_input(
            f"물질명 {idx+1}",
            value=component['물질명'],
            key=f"material_{idx}",
            label_visibility="collapsed"
        )
    
    with cols[1]:
        component['관용명(이명)'] = st.text_input(
            f"관용명 {idx+1}",
            value=component['관용명(이명)'],
            key=f"common_name_{idx}",
            label_visibility="collapsed"
        )
    
    with cols[2]:
        component['CAS번호'] = st.text_input(
            f"CAS번호 {idx+1}",
            value=component['CAS번호'],
            key=f"cas_{idx}",
            placeholder="예: 7732-18-5",
            label_visibility="collapsed"
        )
    
    with cols[3]:
        component['함유량(%)'] = st.text_input(
            f"함유량 {idx+1}",
            value=component['함유량(%)'],
            key=f"content_{idx}",
            placeholder="예: 10-20",
            label_visibility="collapsed"
        )

# 합계 계산 (함유량이 단일 숫자인 경우에만)
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
            except:
                pass
    
    if valid_percentages:
        st.info(f"📊 입력된 함유량 합계: {total:.1f}%")
        if abs(total - 100) > 0.1:
            st.warning(f"⚠️ 함유량 합계가 100%가 아닙니다. 확인이 필요합니다.")
except:
    pass

# 엑셀 업로드 기능
st.markdown("### 엑셀 파일로 가져오기")

# 템플릿 다운로드 버튼
col1, col2 = st.columns([1, 3])
with col1:
    # 템플릿 생성
    template_df = pd.DataFrame({
        '물질명': ['물질명을 입력하세요', '예: 에탄올', '예: 메탄올'],
        '관용명(이명)': ['관용명 또는 이명', '예: 에틸알코올', '예: 메틸알코올'],
        'CAS번호': ['CAS 번호 입력', '64-17-5', '67-56-1'],
        '함유량(%)': ['함유량 또는 범위', '40-50', '10-20']
    })
    
    # 엑셀 파일 생성
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, sheet_name='구성성분', index=False)
        
        # 워크시트 가져오기
        worksheet = writer.sheets['구성성분']
        
        # 컬럼 너비 조정
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 25
        worksheet.column_dimensions['C'].width = 20
        worksheet.column_dimensions['D'].width = 15
    
    buffer.seek(0)
    
    st.download_button(
        label="📥 템플릿 다운로드",
        data=buffer,
        file_name="MSDS_구성성분_템플릿.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="구성성분 정보를 입력할 수 있는 엑셀 템플릿을 다운로드합니다."
    )

with col2:
    uploaded_file = st.file_uploader(
        "구성성분 정보가 포함된 엑셀 파일을 업로드하세요",
        type=['xlsx', 'xls'],
        help="엑셀 파일은 '물질명', '관용명(이명)', 'CAS번호', '함유량(%)' 열을 포함해야 합니다."
    )

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        # 필요한 컬럼이 있는지 확인
        required_cols = ['물질명', '관용명(이명)', 'CAS번호', '함유량(%)']
        
        # 컬럼명 정규화 (공백 제거 등)
        df.columns = df.columns.str.strip()
        
        if all(col in df.columns for col in required_cols):
            # 데이터를 세션 상태로 변환
            components_list = []
            for _, row in df.iterrows():
                components_list.append({
                    '물질명': str(row['물질명']) if pd.notna(row['물질명']) else '',
                    '관용명(이명)': str(row['관용명(이명)']) if pd.notna(row['관용명(이명)']) else '',
                    'CAS번호': str(row['CAS번호']) if pd.notna(row['CAS번호']) else '',
                    '함유량(%)': str(row['함유량(%)']) if pd.notna(row['함유량(%)']) else ''
                })
            
            if st.button("엑셀 데이터 적용"):
                st.session_state.section3_data['components'] = components_list
                st.success(f"✅ {len(components_list)}개의 성분 정보를 가져왔습니다!")
                st.rerun()
        else:
            st.error("❌ 엑셀 파일에 필요한 컬럼이 없습니다. '물질명', '관용명(이명)', 'CAS번호', '함유량(%)' 컬럼이 필요합니다.")
            st.info("현재 엑셀 파일의 컬럼: " + ", ".join(df.columns.tolist()))
    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 오류가 발생했습니다: {str(e)}")

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 3 저장", type="primary", use_container_width=True):
        # 빈 행 제거
        cleaned_components = [
            comp for comp in st.session_state.section3_data['components'] 
            if any(comp.values())
        ]
        
        if cleaned_components:
            st.session_state.section3_data['components'] = cleaned_components
            st.success("✅ 섹션 3이 저장되었습니다!")
        else:
            st.warning("⚠️ 최소 하나 이상의 성분 정보를 입력해주세요.")

# 데이터 미리보기
with st.expander("저장된 데이터 확인"):
    if st.session_state.section3_data['components']:
        # DataFrame으로 표시
        df_display = pd.DataFrame(st.session_state.section3_data['components'])
        st.table(df_display)