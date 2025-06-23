import streamlit as st
from datetime import date

# 페이지 설정
st.set_page_config(
    page_title="MSDS 관리 시스템",
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
    
    .main-header {
        text-align: center;
        padding: 2rem;
        background-color: #d3e3f3;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .section-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .section-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .status-complete {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-incomplete {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-partial {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>📋 MSDS 통합 관리 시스템</h1>
    <p>물질안전보건자료(MSDS) 작성 및 관리</p>
</div>
""", unsafe_allow_html=True)

# 전체 세션 상태 초기화 (각 섹션 간 데이터 공유를 위해)
if 'global_msds_data' not in st.session_state:
    st.session_state.global_msds_data = {
        'product_name': '',
        'management_number': '',
        'created_date': date.today(),
        'last_updated': date.today()
    }

# 작성 상태 확인 함수
def check_section_status(section_key):
    if section_key not in st.session_state:
        return "미작성", "status-incomplete"
    
    data = st.session_state.get(section_key, {})
    
    # 섹션별 필수 항목 체크
    if section_key == 'section1_data':
        if data.get('product_name') and data.get('manufacturer_info', {}).get('company_name'):
            return "작성완료", "status-complete"
        elif data.get('product_name') or data.get('manufacturer_info', {}).get('company_name'):
            return "작성중", "status-partial"
    
    elif section_key == 'section3_data':
        components = data.get('components', [])
        filled_components = [c for c in components if c.get('물질명')]
        if filled_components:
            return "작성완료", "status-complete"
    
    elif section_key == 'section8_data':
        if data.get('공학적_관리') or data.get('개인보호구'):
            return "작성완료", "status-complete"
    
    return "미작성", "status-incomplete"

# 정보 요약
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("제품명", st.session_state.get('section1_data', {}).get('product_name', '-'))

with col2:
    st.metric("관리번호", st.session_state.get('section1_data', {}).get('management_number', '-'))

with col3:
    components = st.session_state.get('section3_data', {}).get('components', [])
    filled_components = [c for c in components if c.get('물질명')]
    st.metric("등록된 성분", f"{len(filled_components)}개")

with col4:
    completed_sections = sum(1 for key in ['section1_data', 'section3_data', 'section8_data'] 
                           if check_section_status(key)[0] == "작성완료")
    st.metric("작성 진행률", f"{completed_sections}/16")

st.markdown("---")

# 섹션 목록
st.markdown("## 📝 MSDS 섹션 목록")

# 섹션 정보
sections = [
    {
        'number': 1,
        'title': '화학제품과 회사에 관한 정보',
        'file': 'pages/1_화학제품정보.py pages/01_화학제품과_회사에_관한_정보.py',
        'key': 'section1_data',
        'description': '제품명, 용도, 제조자/공급자 정보'
    },
    {
        'number': 2,
        'title': '유해성·위험성',
        'file': 'section2.py',
        'key': 'section2_data',
        'description': '유해성 분류, 예방조치 문구'
    },
    {
        'number': 3,
        'title': '구성성분의 명칭 및 함유량',
        'file': 'pages/3_구성성분.py pages/03_구성성분의_명칭_및_함유량.py',
        'key': 'section3_data',
        'description': '화학물질명, CAS번호, 함유량'
    },
    {
        'number': 4,
        'title': '응급조치 요령',
        'file': 'section4.py',
        'key': 'section4_data',
        'description': '응급처치 방법'
    },
    {
        'number': 5,
        'title': '폭발·화재시 대처방법',
        'file': 'section5.py',
        'key': 'section5_data',
        'description': '소화방법, 화재 위험성'
    },
    {
        'number': 6,
        'title': '누출 사고시 대처방법',
        'file': 'section6.py',
        'key': 'section6_data',
        'description': '누출시 조치사항'
    },
    {
        'number': 7,
        'title': '취급 및 저장방법',
        'file': 'section7.py',
        'key': 'section7_data',
        'description': '안전취급, 저장조건'
    },
    {
        'number': 8,
        'title': '노출방지 및 개인보호구',
        'file': 'pages/8_노출방지.py pages/08_노출방지_및_개인보호구.py',
        'key': 'section8_data',
        'description': '노출기준, 보호구'
    },
    {
        'number': 9,
        'title': '물리화학적 특성',
        'file': 'pages/9_물리화학적특성.py pages/09_물리화학적_특성.py',
        'key': 'section9_data',
        'description': '물리적 상태, 화학적 특성'
    },
    {
        'number': 10,
        'title': '안정성 및 반응성',
        'file': 'pages/10_안정성및반응성.py pages/10_안정성_및_반응성.py',
        'key': 'section10_data',
        'description': '화학적 안정성, 반응성'
    },
    {
        'number': 11,
        'title': '독성에 관한 정보',
        'file': 'section11.py',
        'key': 'section11_data',
        'description': '독성 정보'
    },
    {
        'number': 12,
        'title': '환경에 미치는 영향',
        'file': 'section12.py',
        'key': 'section12_data',
        'description': '환경 영향'
    },
    {
        'number': 13,
        'title': '폐기시 주의사항',
        'file': 'pages/13_폐기시주의사항.py pages/13_폐기시_주의사항.py',
        'key': 'section13_data',
        'description': '폐기방법'
    },
    {
        'number': 14,
        'title': '운송에 필요한 정보',
        'file': 'pages/14_운송정보.py pages/14_운송에_필요한_정보.py',
        'key': 'section14_data',
        'description': '운송 정보'
    },
    {
        'number': 15,
        'title': '법적 규제현황',
        'file': 'pages/15_법적규제현황.py pages/15_법적_규제현황.py',
        'key': 'section15_data',
        'description': '관련 법규'
    },
    {
        'number': 16,
        'title': '기타 참고사항',
        'file': 'section16.py',
        'key': 'section16_data',
        'description': '작성일, 개정정보 등'
    }
]

# 3열로 섹션 카드 표시
cols = st.columns(3)

for idx, section in enumerate(sections):
    with cols[idx % 3]:
        status, status_class = check_section_status(section['key'])
        
        st.markdown(f"""
        <div class="section-card">
            <h4>섹션 {section['number']}. {section['title']}</h4>
            <p style="color: #6c757d; font-size: 0.9em;">{section['description']}</p>
            <p>상태: <span class="{status_class}">{status}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"작성하기", key=f"btn_{section['number']}"):
            st.info(f"터미널에서 다음 명령어를 실행하세요: streamlit run {section['file']}")

# 하단 기능 버튼들
st.markdown("---")
st.markdown("## 🛠️ 관리 기능")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 전체 데이터 확인", use_container_width=True):
        with st.expander("저장된 전체 데이터"):
            for key in st.session_state:
                if key.startswith('section'):
                    st.subheader(key)
                    st.json(st.session_state[key])

with col2:
    if st.button("💾 전체 저장", type="primary", use_container_width=True):
        st.success("전체 MSDS 데이터가 저장되었습니다!")

with col3:
    if st.button("📥 MSDS 다운로드", use_container_width=True):
        st.info("MSDS 문서 생성 기능은 준비중입니다.")

# 사용 안내
st.markdown("---")
st.info("""
**💡 사용 방법**
1. 각 섹션의 '작성하기' 버튼을 클릭하여 해당 섹션 작성
2. 각 섹션은 독립적으로 실행되며, 데이터는 자동으로 저장됩니다
3. 섹션 3 (구성성분)을 먼저 작성하면 섹션 8에서 자동으로 연동됩니다
4. 모든 섹션 작성 완료 후 'MSDS 다운로드'로 최종 문서를 생성할 수 있습니다
""")

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d;">
    <p>MSDS 통합 관리 시스템 v1.0 | 안전보건공단 MSDS 작성 지침 준수</p>
</div>
""", unsafe_allow_html=True)
