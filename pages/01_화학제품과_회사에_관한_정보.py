import streamlit as st
import pandas as pd
from datetime import datetime, date

# 페이지 설정
st.set_page_config(
    page_title="MSDS 섹션 1 - 화학제품과 회사정보",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화 (가장 먼저 실행)
if 'section1_data' not in st.session_state:
    st.session_state.section1_data = {
        'company_logo': None,
        'management_number': '',
        'initial_date': date.today(),
        'revision_date': date.today(),
        'product_name': '',
        'other_names': '',
        'recommended_use': [],
        'use_restrictions': '상기 용도외 사용금지',
        'manufacturer_info': {
            'company_name': '',
            'address': '',
            'emergency_phone': ''
        },
        'supplier_info': {
            'company_name': '',
            'address': '',
            'emergency_phone': ''
        },
        'is_different_supplier': False
    }

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
    .small-text {
        font-size: 0.8em;
        color: #666;
    }
    /* multiselect 내부 텍스트도 나눔고딕 적용 */
    .stMultiSelect > div {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    /* 드롭다운 옵션에도 적용 */
    div[data-baseweb="select"] {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

# 용도 분류 데이터 (PDF 별표5 기준)
usage_data = {
    "1": ("원료 및 중간체", "새로운 물질의 합성, 혼합물의 배합 등에 사용되는 원료 및 그 과정에서 발생되는 중간체"),
    "2": ("접착제 및 실런트", "두 물체의 접촉면을 접합시키거나 두 개의 개체를 결합시키는 물질"),
    "3": ("흡착제", "가스나 액체를 흡착하는 물질"),
    "4": ("방향제 및 탈취제 등", "실내 공기 중에 냄새를 발생시키거나 의류 등의 냄새를 제거하는데 사용되는 물질"),
    "5": ("냉동방지 및 결빙제거제", "냉각에 의하여 고화되는 것을 방지하거나 얼음을 제거하는 물질"),
    "6": ("금속(금속 광물 포함) 및 합금", "납, 구리 등 하나의 원소로 이루어진 금속 및 하나의 금속에 한 종류 이상의 금속을 첨가하여 만든 금속"),
    "7": ("살생물제", "농작물 이외의 대상에 대하여 유해생물을 제거, 무해화 또는 억제하기 위해 사용되는 물질(농약 제외)"),
    "8": ("코팅, 페인트, 신너, 페인트 제거제", "표면에 피막을 입히거나 제거하는데 사용되는 물질"),
    "8.1": ("유성 페인트", "신너에 희석하여 사용하는 페인트"),
    "8.2": ("수성 페인트", "물에 희석하여 사용하는 페인트"),
    "8.3": ("신너", "페인트 등을 희석하는데 사용하는 용제"),
    "8.4": ("페인트 제거제", "도색된 페인트를 표면으로부터 제거하는데 사용하는 물질"),
    "8.5": ("경화제", "경도를 높이거나 경화를 촉진시키기 위하여 첨가하는 물질"),
    "8.6": ("기타 코팅 및 도장 관련 제품", "표면에 피막을 입히거나 제거하는데 사용되는 물질 중에서 8.1부터 8.5에 해당되지 않는 물질"),
    "9": ("필러, 퍼티, 점토 등", "빈 틈이나 공간을 메꾸거나 연결하기 위하여 사용되는 물질"),
    "10": ("화약 및 폭발물", "화학적 안전성이 있으나 화학적 변화를 거침으로써 폭발 또는 팽창을 동반한 다량의 에너지 및 가스를 매우 빠르게 발생시키는 물질"),
    "11": ("비료", "식물에 영양을 주거나 식물의 재배를 돕기 위해 흙에서 화학적 변화를 가져오게 하는 물질"),
    "12": ("연료 및 연료 첨가제", "연소반응을 통해 에너지를 얻을 수 있는 물질 및 연소 효율이나 에너지 효율을 높이기 위하여 연료에 첨가하는 물질(플라스틱 원료는 제외)"),
    "13": ("금속 표면 처리제", "금속표면의 세척 및 세정을 위해서 쓰이는 물질 및 도금공정에서 도금강도를 증가시키기 위해 첨가하는 물질"),
    "14": ("비금속 표면 처리제", "금속 이외의 표면의 세척 및 세정을 위해서 쓰이는 물질 및 도금공정에서 도금강도를 증가시키기 위해 첨가하는 물질"),
    "15": ("열전달제", "열을 전달하고 열을 제거하는 물질"),
    "16": ("유압유 및 첨가제", "각종 압축기에 넣는 액체(기름류) 및 압력 전달 효율을 높이기 위해 첨가하는 물질"),
    "17": ("잉크 및 토너", "프린터나 전자복사기 등에 쓰여 영구적인 이미지 생성에 사용하는 물질"),
    "18": ("다양한 공정 보조제", "공정의 안정성과 효율을 높이기 위하여 사용되는 각종 물질"),
    "18.1": ("부식방지제", "공기를 비롯한 화학물질, 옥외노출 등으로 생기는 부식을 방지하기 위해 첨가하는 물질"),
    "18.2": ("부유제", "광물질의 제련 공정 중에서 광물질을 농축·수거하기 위해 사용하는 물질"),
    "18.3": ("주물용 융제", "광물질을 녹이는 공정에서 산화물이 형성되는 것을 방지하기 위해 첨가하는 물질"),
    "18.4": ("발포제 및 기포제", "주로 플라스틱이나 고무 등에 첨가해서 작업공정 중 가스를 발생시켜 기포를 형성하게 하는 물질"),
    "18.5": ("산화제", "특수한 조건에서 산소를 쉽게 발생시켜 다른 물질을 산화시키는 물질, 수소를 제거하는 물질 또는 화학반응에서 전자를 쉽게 받아들이는 물질"),
    "18.6": ("pH조절제", "수소이온농도(pH)를 조절하거나 안정화하는데 사용하는 물질"),
    "18.7": ("공정속도 조절제", "화학반응 속도를 조절함으로써 공정속도를 제어할 목적으로 사용하는 물질"),
    "18.8": ("환원제", "주어진 조건에서 산소를 제거하거나 또는 화학반응에서 전자를 제공하는 물질"),
    "18.9": ("안정제", "제조공정이나 사용 중에 열, 빛, 산소, 오존 등에 의해서 열화가 일어나 모양, 색깔, 물성이 변하는 것을 방지할 목적으로 사용하는 물질"),
    "18.10": ("계면활성제 및 표면활성제", "한 분자 내에 친수기와 소수기를 지닌 화합물로서 액체의 표면에 부착해서 표면장력을 크게 저하시켜 활성화해주는 물질"),
    "18.11": ("점도 조정제", "수지 등 고분자화합물을 용해한 점성재료의 농도를 안정화시켜 사용하기 쉽도록 해주는 물질"),
    "18.12": ("응집제 및 침전제", "물 등의 액체에 존재하는 여러 입자를 모여서 덩어리가 되도록 하거나 덩어리로 만들어 가라앉게 하는 물질"),
    "18.13": ("소포제", "거품의 형성을 억제하는 물질"),
    "18.14": ("촉매", "다른 물질의 화학반응을 매개하여 반응 속도를 빠르게 하거나 늦추는 물질"),
    "18.15": ("착화제", "주로 중금속 이온인 다른 물질에 배위자로서 배위되어 착물(복합체)을 형성하는 물질"),
    "18.16": ("기타 공정 보조제", "공정의 안정성과 효율을 높이기 위하여 사용되는 각종 물질로서 18.1부터 18.16에 해당하지 않는 물질"),
    "19": ("실험용 화학물질(시약)", "실험실에서 기기분석 등에 사용되는 화학물질"),
    "20": ("가죽 처리제", "가죽을 부드럽게 하는 등 다양한 목적을 위하여 가죽처리에 사용되는 물질"),
    "21": ("윤활용제품", "기계의 마찰 부분의 발열이나 마모를 방지하거나 탈부착을 원활하게 하기 위해 사용되는 기름"),
    "21.1": ("윤활유", "기계의 마찰 부분의 발열이나 마모를 방지하기 위해 사용되는 기름"),
    "21.2": ("그리스", "기계의 마찰 부분의 발열이나 마모를 방지하기 위해 사용되는 점도가 높은 기름"),
    "21.3": ("이형제", "성형품을 거푸집으로부터 꺼낼 때 벗겨지기 쉽게하는 등 탈부착이 용이하도록 바르는 액체"),
    "21.4": ("기타 윤활용 제품", "기계의 마찰 부분의 발열이나 마모를 방지하거나 탈부착을 원활하게 하기 위해 사용되는 기름류 중에서 21.1부터 21.3에 해당하지 않는 물질"),
    "22": ("금속 가공유", "금속재료의 천공, 절삭, 연마 등을 할 때 발생하는 마찰 저항과 온도 및 금속찌꺼기의 제거 등을 목적으로 사용되는 물질"),
    "22.1": ("수용성 및 합성 금속가공유", "원유에서 정제한 윤활기유가 없거나 일부 있더라도 물과 섞이도록 만든 금속가공유"),
    "22.2": ("비수용성 금속가공유", "원유에서 정제한 윤활기유가 주성분인 금속가공유로서 물이 함유되지 않은 것"),
    "22.3": ("프레스오일 등 포밍유", "프레스 등 막대한 압력을 가해지는 금속가공으로부터 장비와 모재를 보호하기 위한 금속가공유"),
    "22.4": ("방청유", "금속의 가공 전후에 녹으로부터 보호하기 위하여 사용하는 물질"),
    "22.5": ("기타 금속 가공유", "금속가공유 중에서 22.1부터 22.4에 해당하지 않는 물질"),
    "23": ("종이 및 보드 처리제", "종이 등의 제조 과정에서 사용되는 각종 물질"),
    "24": ("식물보호제(농약)", "농작물을 균, 곤충, 응애, 선충, 바이러스, 잡초, 그 밖의 병해충으로부터 방제하는데 사용하는 물질. 다만, 비료는 제외한다."),
    "25": ("향수 및 향료", "향을 내는 물질"),
    "26": ("의약품", "병의 치료나 증상의 완화 등을 목적으로 의료에 사용되는 물질"),
    "27": ("광화학제품", "영구적인 사진 이미지를 만드는 데 사용하는 물질"),
    "28": ("광택제 및 왁스", "표면의 윤기를 내기 위하여 사용하는 물질"),
    "29": ("폴리머(고무 및 플라스틱) 재료(단량체 제외)", "플라스틱과 고무를 제조하는데 사용되는 원료 및 첨가제 중 단량체물질을 제외한 모든 제품(플라스틱 및 고무제품에 사용되는 세척제나 이형제는 제외)"),
    "30": ("반도체", "규소단결정체처럼 절연체와 금속의 중간 정도의 전기저항을 갖는 물질로서 빛, 열 또는 전자기장에 의해 기전력을 발생하는 물질"),
    "31": ("섬유용 염료 등 섬유 처리제", "섬유에 색을 입히거나 섬유의 질을 개선하기 위해 첨가하는 물질"),
    "32": ("세정 및 세척제", "표면의 오염을 제거하는데 사용되는 액체로서 물이나 용제를 포함"),
    "33": ("경수 연화제", "물 속의 칼슘이나 마그네슘 등을 제거하여 경수를 연수로 변화시키는 물질"),
    "34": ("수처리제", "오염된 물을 정수 또는 소독하기 위하여 사용되는 물질"),
    "35": ("용접, 납땜 재료 및 플럭스", "금속류의 용접 및 납땜질을 할 때 사용하는 물질"),
    "36": ("화장품 및 개인위생용품", "인체를 청결 미화하는 등의 목적으로 사용되는 물질"),
    "37": ("용제 및 추출제", "녹이거나 희석시키거나 추출, 탈지를 위해 사용하는 물질"),
    "38": ("배터리 전해제", "배터리의 전기 전달을 돕는 물질"),
    "39": ("색소", "페인트나 잉크 등의 색을 내는 데 사용되는 물질"),
    "40": ("단열재 및 건축용 재료", "열의 소실을 막기 위하여 사용되는 재료 등 건축에 사용되는 재료"),
    "41": ("전기 절연제", "전기가 통하지 않도록 차단하는 물질"),
    "42": ("에어로졸 추진체", "압축가스 또는 액화가스로서 용기에서 가스를 분사함으로써 내용물을 분출시키는 물질"),
    "43": ("응축방지제", "물체의 표면에서 액체가 응축되는 것을 방지할 목적으로 사용하는 물질"),
    "44": ("접착방지제", "두 개체 접촉면의 접착을 방지할 목적으로 사용하는 물질"),
    "45": ("정전기방지제", "정전기 발생을 방지하거나 저감하는 물질"),
    "46": ("분진결합제", "분진의 발생·분산을 방지하기 위해 첨가하는 물질"),
    "47": ("식품 및 식품첨가물", "식품(의약으로 섭취하는 것은 제외한다) 및 식품을 제조·가공 또는 보존하는 과정에서 식품에 넣거나 첨가하는 물질"),
    "48": ("기타", "1부터 47에 해당하지 않는 그 밖의 물질")
}

# 로고 및 관리정보 섹션 (최상단)
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # 로고 업로드
    uploaded_logo = st.file_uploader(
        "회사 로고 업로드",
        type=['png', 'jpg', 'jpeg'],
        help="회사 로고 이미지를 업로드하세요 (PNG, JPG 형식)"
    )
    
    if uploaded_logo is not None:
        st.image(uploaded_logo, width=200)
        # 세션 상태에 로고 저장
        st.session_state.section1_data['company_logo'] = uploaded_logo
    elif st.session_state.section1_data.get('company_logo'):
        st.image(st.session_state.section1_data['company_logo'], width=200)

with col2:
    st.markdown("**관리번호**")
    management_number = st.text_input(
        "관리번호",
        value=st.session_state.section1_data.get('management_number', ''),
        placeholder="예: MSDS-001",
        label_visibility="collapsed"
    )
    st.session_state.section1_data['management_number'] = management_number

with col3:
    # 작성일 테이블 형식으로 표시
    st.markdown("**작성일**")
    date_data = {
        '구분': ['최초작성일', '최종개정일'],
        '날짜': [
            st.session_state.section1_data.get('initial_date', date.today()).strftime('%Y년 %m월 %d일'),
            st.session_state.section1_data.get('revision_date', date.today()).strftime('%Y년 %m월 %d일')
        ]
    }
    st.table(pd.DataFrame(date_data).set_index('구분'))
    
    # 날짜 입력 (숨김)
    with st.expander("날짜 수정", expanded=False):
        initial_date = st.date_input(
            "최초작성일",
            value=st.session_state.section1_data.get('initial_date', date.today()),
            key="initial_date_input"
        )
        revision_date = st.date_input(
            "최종개정일",
            value=st.session_state.section1_data.get('revision_date', date.today()),
            key="revision_date_input"
        )
        st.session_state.section1_data['initial_date'] = initial_date
        st.session_state.section1_data['revision_date'] = revision_date

st.markdown("---")  # 구분선

# 제목
st.markdown('<div class="section-header"><h2>1. 화학제품과 회사에 관한 정보</h2></div>', unsafe_allow_html=True)

# 가. 제품명
st.subheader("가. 제품명")
product_name = st.text_input("제품명", key="product_name", value=st.session_state.section1_data['product_name'])
st.session_state.section1_data['product_name'] = product_name

# 나. 제품의 권고 용도와 사용상의 제한
st.subheader("나. 제품의 권고 용도와 사용상의 제한")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**제품의 권고 용도**")
    
    # 드롭다운용 옵션 생성 (용도명과 설명을 함께 표시)
    usage_options = {}
    for code, (name, desc) in usage_data.items():
        # 전체 설명을 포함한 옵션 텍스트 생성
        option_text = f"{code}. {name} - {desc}"
        usage_options[code] = option_text
    
    # 선택된 용도
    selected_uses = st.multiselect(
        "용도 선택 (복수 선택 가능)",
        options=list(usage_options.keys()),
        format_func=lambda x: usage_options[x],
        default=st.session_state.section1_data.get('recommended_use', []),
        help="드롭다운에서 용도와 설명을 함께 확인하실 수 있습니다."
    )
    # 선택 즉시 세션 상태에 저장
    st.session_state.section1_data['recommended_use'] = selected_uses

with col2:
    st.markdown("**제품의 사용상의 제한**")
    st.text_input(
        "사용상의 제한사항",
        value="상기 용도외 사용금지",
        disabled=True,
        key="use_restrictions"
    )
    st.session_state.section1_data['use_restrictions'] = "상기 용도외 사용금지"

# 다. 제조자 정보
st.subheader("다. 제조자/수입자/유통업자 정보")

# 제조자와 공급자가 다른지 체크
is_different = st.checkbox(
    "제조자와 공급자가 다른 경우", 
    value=st.session_state.section1_data['is_different_supplier']
)
st.session_state.section1_data['is_different_supplier'] = is_different

# 제조자 정보
st.markdown("#### 제조자 정보")
col1, col2, col3 = st.columns(3)

with col1:
    mfr_company = st.text_input(
        "회사명", 
        key="mfr_company",
        value=st.session_state.section1_data['manufacturer_info']['company_name']
    )
    st.session_state.section1_data['manufacturer_info']['company_name'] = mfr_company

with col2:
    mfr_phone = st.text_input(
        "긴급전화번호", 
        key="mfr_phone",
        value=st.session_state.section1_data['manufacturer_info']['emergency_phone']
    )
    st.session_state.section1_data['manufacturer_info']['emergency_phone'] = mfr_phone

mfr_address = st.text_input(
    "주소", 
    key="mfr_address",
    value=st.session_state.section1_data['manufacturer_info']['address']
)
st.session_state.section1_data['manufacturer_info']['address'] = mfr_address

# 공급자 정보 (제조자와 다른 경우에만 표시)
if is_different:
    st.markdown("#### 공급자 정보")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sup_company = st.text_input(
            "회사명", 
            key="sup_company",
            value=st.session_state.section1_data['supplier_info']['company_name']
        )
        st.session_state.section1_data['supplier_info']['company_name'] = sup_company
    
    with col2:
        sup_phone = st.text_input(
            "긴급전화번호", 
            key="sup_phone",
            value=st.session_state.section1_data['supplier_info']['emergency_phone']
        )
        st.session_state.section1_data['supplier_info']['emergency_phone'] = sup_phone
    
    sup_address = st.text_input(
        "주소", 
        key="sup_address",
        value=st.session_state.section1_data['supplier_info']['address']
    )
    st.session_state.section1_data['supplier_info']['address'] = sup_address

# 저장 버튼
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("섹션 1 저장", type="primary", use_container_width=True):
        st.success("섹션 1이 저장되었습니다!")
        # 여기에 데이터베이스 저장 로직 추가
        
# 데이터 미리보기 (디버깅용 - 나중에 제거 가능)
with st.expander("저장된 데이터 확인"):
    # 선택된 용도 표시
    if st.session_state.section1_data['recommended_use']:
        st.write("**선택된 용도:**")
        for code in st.session_state.section1_data['recommended_use']:
            if code in usage_data:
                name, _ = usage_data[code]
                st.write(f"- {code}. {name}")
    
    # 전체 데이터 JSON 표시
    st.json(st.session_state.section1_data)