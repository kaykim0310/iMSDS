import streamlit as st
import sys
import os
import time
import re
import math

st.set_page_config(page_title="MSDS 섹션 11 - 독성에 관한 정보", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    * { font-family: 'Nanum Gothic', sans-serif !important; }
    [data-testid="stIconMaterial"], .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stTextInput > div > div > input { background-color: #f0f0f0; }
    .stTextArea > div > div > textarea { background-color: #f0f0f0; }
    .section-header { background-color: #d3e3f3; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    .subsection-header { background-color: #e8f0f7; padding: 8px; border-radius: 3px; margin: 15px 0; font-weight: bold; }
    .field-header { background-color: #f5f5f5; padding: 10px; border-radius: 5px; border-left: 4px solid #1976d2; margin: 15px 0 5px 0; font-weight: bold; font-size: 1.05em; }
    .calc-box { background: #fff3e0; padding: 12px; border-radius: 8px; border: 1px solid #ffb74d; margin: 8px 0; }
    .result-box { background: #e8f5e9; padding: 12px; border-radius: 8px; border: 1px solid #66bb6a; margin: 8px 0; }
    .warn-box { background: #fce4ec; padding: 12px; border-radius: 8px; border: 1px solid #ef5350; margin: 8px 0; }
    .confirm-badge { background: #4caf50; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>11. 독성에 관한 정보</h2></div>', unsafe_allow_html=True)

# ============================================================
# GHS 혼합물 분류 기준 (고용노동부 고시 별표 1)
# ============================================================

# ATEmix 구분 기준
ATE_CRITERIA = {
    '경구': [(5, '구분 1'), (50, '구분 2'), (300, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
    '경피': [(50, '구분 1'), (200, '구분 2'), (1000, '구분 3'), (2000, '구분 4'), (5000, '구분 5')],
    '흡입_증기': [(0.5, '구분 1'), (2.0, '구분 2'), (10, '구분 3'), (20, '구분 4')],
    '흡입_분진': [(0.05, '구분 1'), (0.5, '구분 2'), (1.0, '구분 3'), (5, '구분 4')],
}

# ATE 변환표 (구분 → 점추정치)
ATE_CONVERSION = {
    '경구': {'구분 1': 0.5, '구분 2': 5, '구분 3': 100, '구분 4': 500, '구분 5': 2500},
    '경피': {'구분 1': 5, '구분 2': 50, '구분 3': 300, '구분 4': 1100, '구분 5': 2500},
}

# 항목별 드롭다운 구분 옵션 + 혼합물 판정 로직
FIELD_CONFIG = {
    '피부_부식성_또는_자극성': {
        'desc': '피부 부식성/자극성',
        'options': ["해당없음", "구분 1 (부식성)", "구분 2 (자극성)", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1 (부식성): 구분1 성분 합계 ≥ 5%',
            '구분 2 (자극성): 구분1 1~5% 또는 구분2 ≥ 10% 또는 (구분1×10)+구분2 ≥ 10%',
        ],
    },
    '심한_눈_손상_또는_자극성': {
        'desc': '심한 눈 손상/자극성',
        'options': ["해당없음", "구분 1 (심한 눈 손상)", "구분 2A (자극성)", "구분 2B (경미)", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1: (눈 구분1 + 피부 구분1) 합계 ≥ 3%',
            '구분 2: (눈 구분1 + 피부 구분1) 1~3% 또는 눈 구분2 ≥ 10%',
        ],
    },
    '호흡기_과민성': {
        'desc': '호흡기 과민성',
        'options': ["해당없음", "구분 1", "구분 1A", "구분 1B", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1A: 호흡기 과민성 구분1 성분 ≥ 0.1%',
            '구분 1B: 고체/액체 ≥ 1.0%, 가스 ≥ 0.2%',
        ],
    },
    '피부_과민성': {
        'desc': '피부 과민성',
        'options': ["해당없음", "구분 1", "구분 1A", "구분 1B", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1A: 피부 과민성 구분1 성분 ≥ 0.1%',
            '구분 1B: 피부 과민성 구분1 성분 ≥ 1.0%',
        ],
    },
    '발암성': {
        'desc': '발암성',
        'options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1A/1B: 발암성 구분1A/1B 성분 ≥ 0.1%',
            '구분 2: 발암성 구분2 성분 ≥ 1.0%',
        ],
    },
    '생식세포_변이원성': {
        'desc': '생식세포 변이원성',
        'options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1A/1B: 변이원성 구분1A/1B 성분 ≥ 0.1%',
            '구분 2: 변이원성 구분2 성분 ≥ 1.0%',
        ],
    },
    '생식독성': {
        'desc': '생식독성',
        'options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "수유독성", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1A/1B: 생식독성 구분1A/1B 성분 ≥ 0.3%',
            '구분 2: 생식독성 구분2 성분 ≥ 3.0%',
            '수유독성: 수유독성 성분 ≥ 0.3%',
        ],
    },
    '특정_표적장기_독성_1회노출': {
        'desc': '특정 표적장기 독성 (1회 노출)',
        'options': ["해당없음", "구분 1", "구분 2", "구분 3 (호흡기자극/마취)", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1: STOT-1회 구분1 성분 ≥ 10%',
            '구분 2: 구분1 1~10% 또는 구분2 ≥ 10%',
            '구분 3: 구분3 성분 ≥ 20%',
        ],
    },
    '특정_표적장기_독성_반복노출': {
        'desc': '특정 표적장기 독성 (반복 노출)',
        'options': ["해당없음", "구분 1", "구분 2", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1: STOT-반복 구분1 성분 ≥ 10%',
            '구분 2: 구분1 1~10% 또는 구분2 ≥ 10%',
        ],
    },
    '흡인_유해성': {
        'desc': '흡인 유해성',
        'options': ["해당없음", "구분 1", "구분 2", "분류되지 않음", "자료없음"],
        'rules_text': [
            '구분 1: 구분1 성분 ≥ 10% + 동점도 ≤ 20.5 mm²/s (40℃)',
            '구분 2: 구분2 성분 ≥ 10% + 동점도 ≤ 14 mm²/s (40℃)',
        ],
    },
}


# ============================================================
# 발암성 기관별 분류체계
# ============================================================
CARCINOGEN_AGENCIES = {
    '산업안전보건법': {
        'label': '산업안전보건법',
        'options': ["해당없음", "구분 1A (알려진 인체 발암성 물질)", "구분 1B (인체 발암성 추정 물질)", "구분 2 (인체 발암성 의심 물질)", "분류되지 않음", "자료없음"],
        'short_options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "분류되지 않음", "자료없음"],
    },
    '고용노동부고시': {
        'label': '고용노동부 고시',
        'options': ["해당없음", "구분 1A (알려진 인체 발암성 물질)", "구분 1B (인체 발암성 추정 물질)", "구분 2 (인체 발암성 의심 물질)", "분류되지 않음", "자료없음"],
        'short_options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "분류되지 않음", "자료없음"],
    },
    'IARC': {
        'label': 'IARC (국제암연구소)',
        'options': ["해당없음", "Group 1 (인체 발암성 확인)", "Group 2A (인체 발암성 추정)", "Group 2B (인체 발암성 가능)", "Group 3 (인체 발암성 미분류)", "자료없음"],
        'short_options': ["해당없음", "Group 1", "Group 2A", "Group 2B", "Group 3", "자료없음"],
    },
    'OSHA': {
        'label': 'OSHA (미국산업안전보건청)',
        'options': ["해당없음", "Listed (발암성 물질 목록)", "Not Listed", "자료없음"],
        'short_options': ["해당없음", "Listed", "Not Listed", "자료없음"],
    },
    'ACGIH': {
        'label': 'ACGIH (미국산업위생전문가협의회)',
        'options': ["해당없음", "A1 (인체 발암성 확인)", "A2 (인체 발암성 의심)", "A3 (동물 발암성 확인)", "A4 (인체 발암성 미분류)", "A5 (인체 발암성 의심 안됨)", "자료없음"],
        'short_options': ["해당없음", "A1", "A2", "A3", "A4", "A5", "자료없음"],
    },
    'NTP': {
        'label': 'NTP (미국독성프로그램)',
        'options': ["해당없음", "Known (인체 발암성 물질)", "RAHC (합리적으로 인체 발암성 예상)", "Not Listed", "자료없음"],
        'short_options': ["해당없음", "Known", "RAHC", "Not Listed", "자료없음"],
    },
    'EU_CLP': {
        'label': 'EU CLP',
        'options': ["해당없음", "Carc. 1A (알려진 인체 발암성)", "Carc. 1B (추정 인체 발암성)", "Carc. 2 (의심되는 인체 발암성)", "분류되지 않음", "자료없음"],
        'short_options': ["해당없음", "Carc. 1A", "Carc. 1B", "Carc. 2", "분류되지 않음", "자료없음"],
    },
    '환경부': {
        'label': '환경부 (화학물질등록평가법)',
        'options': ["해당없음", "구분 1A (알려진 인체 발암성 물질)", "구분 1B (인체 발암성 추정 물질)", "구분 2 (인체 발암성 의심 물질)", "분류되지 않음", "자료없음"],
        'short_options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "분류되지 않음", "자료없음"],
    },
    'NITE': {
        'label': 'NITE (일본기술종합연구소)',
        'options': ["해당없음", "구분 1A (알려진 인체 발암성 물질)", "구분 1B (인체 발암성 추정 물질)", "구분 2 (인체 발암성 의심 물질)", "분류되지 않음", "자료없음"],
        'short_options': ["해당없음", "구분 1A", "구분 1B", "구분 2", "분류되지 않음", "자료없음"],
    },
}

# 기관별 발암성 → GHS 구분 매핑 (혼합물 분류 판정용)
CARCINOGEN_TO_GHS = {
    # 산업안전보건법 / 고용노동부 고시
    "구분 1A (알려진 인체 발암성 물질)": "구분 1A", "구분 1A": "구분 1A",
    "구분 1B (인체 발암성 추정 물질)": "구분 1B", "구분 1B": "구분 1B",
    "구분 2 (인체 발암성 의심 물질)": "구분 2", "구분 2": "구분 2",
    # IARC
    "Group 1 (인체 발암성 확인)": "구분 1A", "Group 1": "구분 1A",
    "Group 2A (인체 발암성 추정)": "구분 1B", "Group 2A": "구분 1B",
    "Group 2B (인체 발암성 가능)": "구분 2", "Group 2B": "구분 2",
    "Group 3 (인체 발암성 미분류)": "해당없음",
    # OSHA
    "Listed (발암성 물질 목록)": "구분 1A",
    "Listed": "구분 1A",
    # ACGIH
    "A1 (인체 발암성 확인)": "구분 1A", "A1": "구분 1A",
    "A2 (인체 발암성 의심)": "구분 1B", "A2": "구분 1B",
    "A3 (동물 발암성 확인)": "구분 2", "A3": "구분 2",
    "A4 (인체 발암성 미분류)": "해당없음",
    "A5 (인체 발암성 의심 안됨)": "해당없음",
    # NTP
    "Known (인체 발암성 물질)": "구분 1A", "Known": "구분 1A",
    "RAHC (합리적으로 인체 발암성 예상)": "구분 1B", "RAHC": "구분 1B",
    # EU CLP
    "Carc. 1A (알려진 인체 발암성)": "구분 1A", "Carc. 1A": "구분 1A",
    "Carc. 1B (추정 인체 발암성)": "구분 1B", "Carc. 1B": "구분 1B",
    "Carc. 2 (의심되는 인체 발암성)": "구분 2", "Carc. 2": "구분 2",
}

# GHS 구분 → 보수성 순위 (높을수록 보수적)
GHS_CARCINOGEN_RANK = {"구분 1A": 4, "구분 1B": 3, "구분 2": 2, "분류되지 않음": 1, "해당없음": 0, "자료없음": -1}


def get_most_conservative_ghs(agency_selections):
    """물질 1개의 기관별 선택값에서 가장 보수적인 GHS 구분 반환"""
    best_ghs = "해당없음"
    best_rank = -1
    for agency_key, sel_val in agency_selections.items():
        ghs = CARCINOGEN_TO_GHS.get(sel_val, "해당없음")
        rank = GHS_CARCINOGEN_RANK.get(ghs, 0)
        if rank > best_rank:
            best_rank = rank
            best_ghs = ghs
    return best_ghs


def parse_carcinogen_text(text):
    """발암성 관련 텍스트에서 기관별 분류를 자동 파싱하여 딕셔너리로 반환.
    KOSHA API 결과 예시:
      'IARC: 1(Group 1), 산업안전보건법: 구분 1A, ACGIH: A1, NTP: Known to be Human Carcinogen'
      'IARC 그룹 2B / NTP RAHC / ACGIH A3'
    반환: {'IARC': 'Group 2B (인체 발암성 가능)', 'NTP': 'RAHC (...)', ...}
    """
    if not text:
        return {}

    result = {}
    tl = text.lower().replace('\n', ' ').replace('|', ' ')

    # ── IARC ──
    iarc_patterns = [
        (r'iarc\s*[:\-]?\s*(?:group\s*)?1(?:\s|\b|[^0-9ab])', 'Group 1 (인체 발암성 확인)'),
        (r'iarc\s*[:\-]?\s*(?:group\s*)?2\s*a', 'Group 2A (인체 발암성 추정)'),
        (r'iarc\s*[:\-]?\s*(?:group\s*)?2\s*b', 'Group 2B (인체 발암성 가능)'),
        (r'iarc\s*[:\-]?\s*(?:group\s*)?3(?:\s|\b)', 'Group 3 (인체 발암성 미분류)'),
        (r'1\s*군', 'Group 1 (인체 발암성 확인)'),
        (r'2a\s*군', 'Group 2A (인체 발암성 추정)'),
        (r'2b\s*군', 'Group 2B (인체 발암성 가능)'),
        (r'group\s*1(?:\s|\b|[^0-9ab])', 'Group 1 (인체 발암성 확인)'),
        (r'group\s*2\s*a', 'Group 2A (인체 발암성 추정)'),
        (r'group\s*2\s*b', 'Group 2B (인체 발암성 가능)'),
        (r'group\s*3', 'Group 3 (인체 발암성 미분류)'),
    ]
    for pat, val in iarc_patterns:
        if re.search(pat, tl):
            result['IARC'] = val
            break

    # ── ACGIH ──
    acgih_patterns = [
        (r'acgih\s*[:\-]?\s*a\s*1', 'A1 (인체 발암성 확인)'),
        (r'acgih\s*[:\-]?\s*a\s*2', 'A2 (인체 발암성 의심)'),
        (r'acgih\s*[:\-]?\s*a\s*3', 'A3 (동물 발암성 확인)'),
        (r'acgih\s*[:\-]?\s*a\s*4', 'A4 (인체 발암성 미분류)'),
        (r'acgih\s*[:\-]?\s*a\s*5', 'A5 (인체 발암성 의심 안됨)'),
        (r'(?<!\w)a1\s*\(', 'A1 (인체 발암성 확인)'),
        (r'(?<!\w)a2\s*\(', 'A2 (인체 발암성 의심)'),
        (r'(?<!\w)a3\s*\(', 'A3 (동물 발암성 확인)'),
        (r'(?<!\w)a4\s*\(', 'A4 (인체 발암성 미분류)'),
        (r'(?<!\w)a5\s*\(', 'A5 (인체 발암성 의심 안됨)'),
    ]
    for pat, val in acgih_patterns:
        if re.search(pat, tl):
            result['ACGIH'] = val
            break

    # ── NTP ──
    ntp_patterns = [
        (r'ntp\s*[:\-]?\s*known', 'Known (인체 발암성 물질)'),
        (r'ntp\s*[:\-]?\s*r(?:ahc|easonab)', 'RAHC (합리적으로 인체 발암성 예상)'),
        (r'known\s*(?:to\s*be\s*)?(?:human\s*)?carcinogen', 'Known (인체 발암성 물질)'),
        (r'reasonably\s*anticipated', 'RAHC (합리적으로 인체 발암성 예상)'),
    ]
    for pat, val in ntp_patterns:
        if re.search(pat, tl):
            result['NTP'] = val
            break

    # ── OSHA ──
    osha_patterns = [
        (r'osha\s*[:\-]?\s*(?:listed|규제)', 'Listed (발암성 물질 목록)'),
    ]
    for pat, val in osha_patterns:
        if re.search(pat, tl):
            result['OSHA'] = val
            break

    # ── 산업안전보건법 ──
    osh_act_patterns = [
        (r'산업안전보건법\s*[:\-]?\s*구분\s*1\s*a', '구분 1A (알려진 인체 발암성 물질)'),
        (r'산업안전보건법\s*[:\-]?\s*구분\s*1\s*b', '구분 1B (인체 발암성 추정 물질)'),
        (r'산업안전보건법\s*[:\-]?\s*구분\s*2', '구분 2 (인체 발암성 의심 물질)'),
    ]
    for pat, val in osh_act_patterns:
        if re.search(pat, tl):
            result['산업안전보건법'] = val
            break

    # ── 고용노동부 고시 ──
    moel_patterns = [
        (r'고용노동부\s*(?:고시)?\s*[:\-]?\s*구분\s*1\s*a', '구분 1A (알려진 인체 발암성 물질)'),
        (r'고용노동부\s*(?:고시)?\s*[:\-]?\s*구분\s*1\s*b', '구분 1B (인체 발암성 추정 물질)'),
        (r'고용노동부\s*(?:고시)?\s*[:\-]?\s*구분\s*2', '구분 2 (인체 발암성 의심 물질)'),
    ]
    for pat, val in moel_patterns:
        if re.search(pat, tl):
            result['고용노동부고시'] = val
            break

    # ── EU CLP ──
    eu_patterns = [
        (r'(?:eu\s*clp|clp)\s*[:\-]?\s*(?:carc\.?\s*)?1\s*a', 'Carc. 1A (알려진 인체 발암성)'),
        (r'(?:eu\s*clp|clp)\s*[:\-]?\s*(?:carc\.?\s*)?1\s*b', 'Carc. 1B (추정 인체 발암성)'),
        (r'(?:eu\s*clp|clp)\s*[:\-]?\s*(?:carc\.?\s*)?2', 'Carc. 2 (의심되는 인체 발암성)'),
        (r'carc\.\s*1a', 'Carc. 1A (알려진 인체 발암성)'),
        (r'carc\.\s*1b', 'Carc. 1B (추정 인체 발암성)'),
        (r'carc\.\s*2', 'Carc. 2 (의심되는 인체 발암성)'),
    ]
    for pat, val in eu_patterns:
        if re.search(pat, tl):
            result['EU_CLP'] = val
            break

    # ── 환경부 ──
    env_patterns = [
        (r'환경부\s*[:\-]?\s*구분\s*1\s*a', '구분 1A (알려진 인체 발암성 물질)'),
        (r'환경부\s*[:\-]?\s*구분\s*1\s*b', '구분 1B (인체 발암성 추정 물질)'),
        (r'환경부\s*[:\-]?\s*구분\s*2', '구분 2 (인체 발암성 의심 물질)'),
    ]
    for pat, val in env_patterns:
        if re.search(pat, tl):
            result['환경부'] = val
            break

    # ── NITE ──
    nite_patterns = [
        (r'nite\s*[:\-]?\s*(?:구분\s*)?1\s*a', '구분 1A (알려진 인체 발암성 물질)'),
        (r'nite\s*[:\-]?\s*(?:구분\s*)?1\s*b', '구분 1B (인체 발암성 추정 물질)'),
        (r'nite\s*[:\-]?\s*(?:구분\s*)?2', '구분 2 (인체 발암성 의심 물질)'),
    ]
    for pat, val in nite_patterns:
        if re.search(pat, tl):
            result['NITE'] = val
            break

    # ── 일반 GHS 구분 (기관 미특정 → 산업안전보건법으로 간주) ──
    if '산업안전보건법' not in result and '고용노동부고시' not in result:
        ghs_generic = [
            (r'(?:발암성\s*)?구분\s*1\s*a', '구분 1A (알려진 인체 발암성 물질)'),
            (r'(?:발암성\s*)?구분\s*1\s*b', '구분 1B (인체 발암성 추정 물질)'),
            (r'(?:발암성\s*)?구분\s*2(?!\s*[ab])', '구분 2 (인체 발암성 의심 물질)'),
        ]
        for pat, val in ghs_generic:
            if re.search(pat, tl):
                result['산업안전보건법'] = val
                result['고용노동부고시'] = val
                break

    return result


def _is_cls1(cls_str):
    """구분 1 계열인지 판정"""
    return cls_str in ['구분 1', '구분 1A', '구분 1B', '구분 1C',
                       '구분 1 (부식성)', '구분 1 (심한 눈 손상)']


def _is_cls2(cls_str):
    return cls_str in ['구분 2', '구분 2 (자극성)', '구분 2A (자극성)', '구분 2A', '구분 2B', '구분 2B (경미)']


def _is_cls3(cls_str):
    return '구분 3' in cls_str


def judge_classification(key, comp_data):
    """항목별 정확한 혼합물 분류 판정 (고용노동부 고시 별표 1)"""
    cls1_sum = sum(d['pct'] for d in comp_data if _is_cls1(d['cls']))
    cls2_sum = sum(d['pct'] for d in comp_data if _is_cls2(d['cls']))
    cls3_sum = sum(d['pct'] for d in comp_data if _is_cls3(d['cls']))
    cls1a_sum = sum(d['pct'] for d in comp_data if d['cls'] == '구분 1A')
    cls1b_sum = sum(d['pct'] for d in comp_data if d['cls'] == '구분 1B')
    nursing_sum = sum(d['pct'] for d in comp_data if d['cls'] == '수유독성')
    unknown = sum(d['pct'] for d in comp_data if d['cls'] == '자료없음')

    result = "분류되지 않음"
    details = []

    if key == '피부_부식성_또는_자극성':
        if cls1_sum >= 5:
            result = "구분 1 (부식성)"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 5%")
        elif cls1_sum >= 1 and cls1_sum < 5:
            result = "구분 2 (자극성)"; details.append(f"구분1 합계 {cls1_sum:.2f}% (1~5%)")
        elif cls2_sum >= 10:
            result = "구분 2 (자극성)"; details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 10%")
        else:
            combined = cls1_sum * 10 + cls2_sum
            if combined >= 10:
                result = "구분 2 (자극성)"; details.append(f"(구분1×10)+구분2 = {combined:.2f}% ≥ 10%")

    elif key == '심한_눈_손상_또는_자극성':
        if cls1_sum >= 3:
            result = "구분 1 (심한 눈 손상)"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 3%")
        elif cls1_sum >= 1 and cls1_sum < 3:
            result = "구분 2A (자극성)"; details.append(f"구분1 합계 {cls1_sum:.2f}% (1~3%)")
        elif cls2_sum >= 10:
            result = "구분 2A (자극성)"; details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 10%")
        else:
            combined = cls1_sum * 10 + cls2_sum
            if combined >= 10:
                result = "구분 2A (자극성)"; details.append(f"(구분1×10)+구분2 = {combined:.2f}% ≥ 10%")

    elif key == '호흡기_과민성':
        if cls1a_sum >= 0.1 or (cls1_sum >= 0.1):
            result = "구분 1"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 0.1%")
        elif cls1b_sum >= 1.0:
            result = "구분 1"; details.append(f"구분1B 합계 {cls1b_sum:.2f}% ≥ 1.0%")

    elif key == '피부_과민성':
        if cls1a_sum >= 0.1 or (cls1_sum >= 0.1):
            result = "구분 1"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 0.1%")
        elif cls1b_sum >= 1.0:
            result = "구분 1"; details.append(f"구분1B 합계 {cls1b_sum:.2f}% ≥ 1.0%")

    elif key in ('발암성', '생식세포_변이원성'):
        if cls1_sum >= 0.1:
            result = "구분 1A/1B"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 0.1%")
        elif cls2_sum >= 1.0:
            result = "구분 2"; details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 1.0%")

    elif key == '생식독성':
        if cls1_sum >= 0.3:
            result = "구분 1A/1B"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 0.3%")
        elif cls2_sum >= 3.0:
            result = "구분 2"; details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 3.0%")
        if nursing_sum >= 0.3:
            if result != "분류되지 않음":
                result += " + 수유독성"
            else:
                result = "수유독성"
            details.append(f"수유독성 합계 {nursing_sum:.2f}% ≥ 0.3%")

    elif key == '특정_표적장기_독성_1회노출':
        if cls1_sum >= 10:
            result = "구분 1"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 10%")
        elif cls1_sum >= 1 or cls2_sum >= 10:
            result = "구분 2"
            if cls1_sum >= 1: details.append(f"구분1 합계 {cls1_sum:.2f}% (1~10%)")
            if cls2_sum >= 10: details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 10%")
        elif cls3_sum >= 20:
            result = "구분 3 (호흡기자극/마취)"; details.append(f"구분3 합계 {cls3_sum:.2f}% ≥ 20%")

    elif key == '특정_표적장기_독성_반복노출':
        if cls1_sum >= 10:
            result = "구분 1"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 10%")
        elif cls1_sum >= 1 or cls2_sum >= 10:
            result = "구분 2"
            if cls1_sum >= 1: details.append(f"구분1 합계 {cls1_sum:.2f}% (1~10%)")
            if cls2_sum >= 10: details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 10%")

    elif key == '흡인_유해성':
        if cls1_sum >= 10:
            result = "구분 1"; details.append(f"구분1 합계 {cls1_sum:.2f}% ≥ 10% (동점도 ≤ 20.5 mm²/s 확인 필요)")
        elif cls2_sum >= 10:
            result = "구분 2"; details.append(f"구분2 합계 {cls2_sum:.2f}% ≥ 10% (동점도 ≤ 14 mm²/s 확인 필요)")

    if not details:
        details.append("모든 기준 미달 → 분류되지 않음")

    return result, details, {
        'cls1': cls1_sum, 'cls2': cls2_sum, 'cls3': cls3_sum, 'unknown': unknown
    }

# ============================================================
# 세션 초기화
# ============================================================
if 'section11_data' not in st.session_state:
    st.session_state.section11_data = {
        '가_가능성이_높은_노출경로에_관한_정보': '',
        '나_건강_유해성_정보': {
            '급성독성_경구': '', '급성독성_경피': '', '급성독성_흡입': '',
            '피부_부식성_또는_자극성': '', '심한_눈_손상_또는_자극성': '',
            '호흡기_과민성': '', '피부_과민성': '', '발암성': '', '생식세포_변이원성': '',
            '생식독성': '', '특정_표적장기_독성_1회노출': '', '특정_표적장기_독성_반복노출': '',
            '흡인_유해성': ''
        }
    }

if 'confirmed_classifications' not in st.session_state:
    st.session_state.confirmed_classifications = {}

# 발암성 기관별 물질별 데이터 초기화
if 'carcinogen_agency_data' not in st.session_state:
    st.session_state.carcinogen_agency_data = {}  # {물질명: {기관key: 선택값}}

TOXICITY_FIELDS = [
    ('급성독성_경구', '급성독성 (경구)', ['경구', 'oral', 'Acute Oral', 'ingestion'], "예: LD50 = 5800 mg/kg (Rat)"),
    ('급성독성_경피', '급성독성 (경피)', ['경피', 'dermal', 'Acute Dermal', 'skin absorption'], "예: LD50 > 2000 mg/kg (Rabbit)"),
    ('급성독성_흡입', '급성독성 (흡입)', ['흡입', 'inhalation', 'Acute Inhalation'], "예: LC50 = 76 mg/L (Rat, 4hr)"),
    ('피부_부식성_또는_자극성', '피부 부식성/자극성', ['피부부식', '피부 부식', '피부자극', '피부 자극', 'Skin Corrosion', 'Skin Irritation', 'skin irrit'], ""),
    ('심한_눈_손상_또는_자극성', '심한 눈 손상/자극성', ['눈손상', '눈 손상', '눈자극', '눈 자극', 'Eye Damage', 'Eye Irritation', 'Serious Eye', 'eye irrit'], ""),
    ('호흡기_과민성', '호흡기 과민성', ['호흡기과민', '호흡기 과민', 'Respiratory Sensitiz', 'respiratory sensit'], ""),
    ('피부_과민성', '피부 과민성', ['피부과민', '피부 과민', 'Skin Sensitiz', 'skin sensit'], ""),
    ('발암성', '발암성', ['발암', 'Carcinogen', 'IARC', 'NTP', 'carcino'], ""),
    ('생식세포_변이원성', '생식세포 변이원성', ['변이원', '돌연변이', 'Genotoxic', 'Mutagen', 'mutageni', 'genotox', 'Ames'], ""),
    ('생식독성', '생식독성', ['생식독성', '생식', 'Reproductive Toxic', 'Developmental Toxic', 'reproduct', 'teratogen'], ""),
    ('특정_표적장기_독성_1회노출', '특정 표적장기 독성 (1회 노출)', ['1회', '단회', 'single exposure'], ""),
    ('특정_표적장기_독성_반복노출', '특정 표적장기 독성 (반복 노출)', ['반복', 'Chronic Toxic', 'Repeated Dose', 'chronic', 'repeated', 'subchronic'], ""),
    ('흡인_유해성', '흡인 유해성', ['흡인', 'Aspiration', 'aspiration'], ""),
]


def _is_valid(detail):
    if not detail: return False
    return detail.strip() not in ("자료없음", "해당없음", "(없음)", "", "자료 없음")


def extract_numeric(text):
    """텍스트에서 LD50/LC50 수치를 추출한다.
    예: 'LD50 270 mg/kg' → 270.0
        'LD50 = 5800 mg/kg' → 5800.0
        'LD50 >5000 mg/kg' → 5000.0
        'LC50 76 mg/L (4hr)' → 76.0
    """
    if not text:
        return None
    # &gt; → >, &lt; → < 변환
    text = text.replace('&gt;', '>').replace('&lt;', '<')
    # LD50/LC50 뒤의 숫자를 우선 추출
    m = re.search(r'(?:LD50|LC50|EC50|ATE)\s*[=:>< ]*\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass
    # 일반 숫자 추출 (단위 mg/kg, mg/L 앞의 숫자)
    m = re.search(r'([\d,]+\.?\d*)\s*(?:mg/kg|mg/L|ppm|mg/m)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass
    # 최후: 아무 숫자나
    m = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return None


def classify_ate(ate_value, route='경구'):
    """ATE값으로 급성독성 구분 판정"""
    criteria = ATE_CRITERIA.get(route, ATE_CRITERIA['경구'])
    for threshold, label in criteria:
        if ate_value <= threshold:
            return label
    return '분류되지 않음'


def conservative_score(detail, field_key=''):
    """보수적(독성↑) 순으로 점수 부여. 점수가 높을수록 보수적.
    ★ 핵심 원칙: 정량 데이터(수치) > 정성 데이터(키워드)
    - 정량 데이터: +500 보너스 → 항상 정성보다 우선
    - 정량 내 비교: 값이 낮을수록 독성↑ → 역수
    - 정성 데이터: 구분/키워드 기반 (최대 ~100)
    """
    if not detail or detail.strip() in ('자료없음', '해당없음', '(없음)', ''):
        return -9999  # 자료없음은 최하위

    dl = detail.lower()

    # 1) 정량 데이터 (LD50/LC50/EC50/NOEC 등 수치) → 최우선
    num = extract_numeric(detail)
    if num and num > 0:
        # 정량 보너스(500) + 역수 → 항상 정성(최대100)보다 높음
        return 500.0 + (10000.0 / num)

    # ── 이하 정성 데이터 (최대 ~100점) ──

    # 2) 구분(Category) 기반 판정
    cat_scores = {
        '구분 1a': 100, '구분1a': 100, 'category 1a': 100, 'cat 1a': 100,
        '구분 1b': 95, '구분1b': 95, 'category 1b': 95, 'cat 1b': 95,
        '구분 1c': 90, '구분1c': 90, 'category 1c': 90,
        '구분 1': 85, '구분1': 85, 'category 1': 85, 'cat 1': 85,
        '구분 2a': 75, '구분2a': 75, 'category 2a': 75,
        '구분 2b': 72, '구분2b': 72, 'category 2b': 72,
        '구분 2': 70, '구분2': 70, 'category 2': 70, 'cat 2': 70,
        '구분 3': 60, '구분3': 60, 'category 3': 60,
        '구분 4': 50, '구분4': 50, 'category 4': 50,
        '구분 5': 40, '구분5': 40, 'category 5': 40,
    }
    best_cat = -1
    for pat, sc in cat_scores.items():
        if pat in dl:
            best_cat = max(best_cat, sc)
    if best_cat > 0:
        return best_cat

    # 3) IARC/NTP 발암성 등급
    iarc_scores = {
        'group 1': 100, 'iarc 1': 100, '1군': 100,
        'group 2a': 90, 'iarc 2a': 90, '2a군': 90,
        'group 2b': 80, 'iarc 2b': 80, '2b군': 80,
        'group 3': 50, 'iarc 3': 50,
    }
    for pat, sc in iarc_scores.items():
        if pat in dl:
            return sc

    # 4) 독성 표현 키워드 (비수치)
    severe_kw = {
        'corrosive': 80, '부식': 80, 'irreversible': 80, '비가역': 80,
        'fatal': 90, '치명': 90, 'lethal': 90,
        'toxic': 70, '독성': 70, 'harmful': 60, '유해': 60,
        'irritat': 50, '자극': 50,
        'sensitiz': 60, '과민': 60,
        'not classified': 10, '분류되지': 10, '해당없음': 5,
        'positive': 65, '양성': 65,
        'negative': 15, '음성': 15,
    }
    best_kw = 0
    for kw, sc in severe_kw.items():
        if kw in dl:
            best_kw = max(best_kw, sc)
    if best_kw > 0:
        return best_kw

    # 5) 기본: 내용이 있으면 약간의 점수
    return 1


def auto_select_conservative(all_results, prefix="chk11"):
    """물질별·항목별로 가장 보수적인(독성↑) 결과 1개씩 자동 선택.
    이미 사용자가 체크한 것이 있으면 건드리지 않음.
    """
    from collections import defaultdict

    # 사용자가 이미 수동 체크한 게 있는지 확인
    any_manual = any(
        st.session_state.get(f"{prefix}_{r['idx']}", False)
        for r in all_results if not r.get('no_data')
    )
    if any_manual:
        return  # 사용자가 이미 선택함 → 자동선택 안 함

    # (물질, 항목) 그룹별로 최고 보수점수 결과 찾기
    groups = defaultdict(list)
    for r in all_results:
        if r.get('no_data'):
            continue
        if r['field'] == '발암성':
            continue  # 발암성은 자동 반영 → 보수적 선택 제외
        groups[(r['mat'], r['field'])].append(r)

    for (mat, fk), items in groups.items():
        if not items:
            continue
        scored = [(conservative_score(r['detail'], fk), r) for r in items]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_r = scored[0][1]
        st.session_state[f"{prefix}_{best_r['idx']}"] = True


# ============================================================
# API 조회 함수
# ============================================================
def query_kosha(cas_no):
    try:
        import requests
        import xml.etree.ElementTree as ET
        API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
        BASE = "https://msds.kosha.or.kr/openapi/service/msdschem"
        resp = requests.get(f"{BASE}/chemlist", params={"serviceKey": API_KEY, "searchWrd": cas_no, "searchCnd": 1, "numOfRows": 5}, timeout=20)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        if not items: return {"success": False, "raw_items": []}
        chem_id = items[0].findtext("chemId", "")
        chem_name = items[0].findtext("chemNameKor", cas_no)
        time.sleep(0.3)
        resp2 = requests.get(f"{BASE}/chemdetail11", params={"serviceKey": API_KEY, "chemId": chem_id}, timeout=20)
        root2 = ET.fromstring(resp2.content)
        raw = []
        for it in root2.findall(".//item"):
            name = it.findtext("msdsItemNameKor", "").strip()
            detail = it.findtext("itemDetail", "").strip()
            if name and detail and _is_valid(detail):
                raw.append({"name": name, "detail": detail, "source": "KOSHA"})
        return {"success": True, "name": chem_name, "raw_items": raw}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def query_pubchem(cas_no):
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from echa_api import get_toxicity_info, search_substance
        search = search_substance(cas_no)
        sub_id = search.get("substance_id", "") if search.get("success") else ""
        name = search.get("name", cas_no)
        time.sleep(0.3)
        tox = get_toxicity_info(cas_no, sub_id)
        return {"success": bool(tox.get("raw_items")), "name": name, "raw_items": tox.get("raw_items", []), "error": tox.get("error", "")}
    except Exception as e:
        return {"success": False, "error": str(e), "raw_items": []}


def classify_item(item_name, detail=""):
    combined = (item_name + " " + detail).strip()
    cl = combined.lower()
    if "ld50" in cl:
        if "oral" in cl or "경구" in cl: return "급성독성_경구"
        if "dermal" in cl or "경피" in cl: return "급성독성_경피"
        if "inhal" in cl or "흡입" in cl: return "급성독성_흡입"
        return "급성독성_경구"
    if "lc50" in cl: return "급성독성_흡입"
    for key, label, keywords, _ in TOXICITY_FIELDS:
        for kw in keywords:
            if kw.lower() in cl: return key
    return None


# ============================================================
# 섹션 3에서 성분 정보 가져오기
# ============================================================
def get_components():
    """섹션 3에서 물질명, CAS, 함유량(%) 가져오기"""
    comps = []
    if 'section3_data' in st.session_state:
        for comp in st.session_state.get('section3_data', {}).get('components', []):
            if comp.get('CAS번호') and comp.get('물질명'):
                pct_str = comp.get('함유량', comp.get('함유량(%)', ''))
                pct = None
                if pct_str:
                    m = re.search(r'[\d.]+', str(pct_str))
                    if m:
                        try: pct = float(m.group())
                        except: pass
                comps.append({'name': comp['물질명'], 'cas': comp['CAS번호'], 'pct': pct})
    return comps

components = get_components()

# ============================================================
# 1. API 조회 + 데이터 선택
# ============================================================
with st.expander("🔍 KOSHA + 국제DB(PubChem) 동시 조회", expanded=False):
    st.markdown("섹션 3의 CAS 번호로 **🟢 KOSHA** 와 **🔵 국제DB(PubChem)** 독성 데이터를 동시 조회합니다.")

    if components:
        st.success(f"✅ {len(components)}개 물질 발견")
        for m in components:
            pct_txt = f", 함유량: {m['pct']}%" if m['pct'] is not None else ""
            st.write(f"  • **{m['name']}** (CAS: {m['cas']}{pct_txt})")

        if st.button("🔍 KOSHA + 국제DB 동시 조회", type="primary", key="dual_query_s11"):
            all_results = []
            mat_field_found = {m['name']: set() for m in components}
            prog = st.progress(0)
            total = len(components) * 2
            step = 0

            for m in components:
                prog.progress(step / total, f"🟢 KOSHA: {m['name']}...")
                kr = query_kosha(m['cas'])
                if kr.get('success'):
                    for item in kr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk:
                            all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m['pct'],
                                'src': 'KOSHA', 'field': fk, 'label': item['name'], 'detail': item['detail']})
                            mat_field_found[m['name']].add(fk)
                step += 1; time.sleep(0.3)

                prog.progress(step / total, f"🔵 국제DB: {m['name']}...")
                pr = query_pubchem(m['cas'])
                if pr.get('success'):
                    KOSHA_ONLY_FIELDS = {'발암성'}
                    for item in pr['raw_items']:
                        fk = classify_item(item['name'], item.get('detail', ''))
                        if fk and fk not in KOSHA_ONLY_FIELDS:
                            all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m['pct'],
                                'src': 'PubChem', 'field': fk, 'label': item['name'], 'detail': item['detail']})
                            mat_field_found[m['name']].add(fk)
                step += 1; time.sleep(0.3)

            for m in components:
                for fk, fl, _, _ in TOXICITY_FIELDS:
                    if fk not in mat_field_found[m['name']]:
                        all_results.append({'mat': m['name'], 'cas': m['cas'], 'pct': m['pct'],
                            'src': '-', 'field': fk, 'label': fl, 'detail': '자료없음', 'no_data': True})

            prog.progress(1.0, "✅ 조회 완료!")
            for i, r in enumerate(all_results): r['idx'] = i

            # ── 발암성: KOSHA 데이터 전부 자동 반영 (선택 없이) ──
            carc_by_mat = {}  # {물질명: [detail, ...]}
            for r in all_results:
                if r['field'] == '발암성' and not r.get('no_data') and r.get('detail'):
                    mat_name = r['mat']
                    if mat_name not in carc_by_mat:
                        carc_by_mat[mat_name] = []
                    carc_by_mat[mat_name].append(r['detail'])

            # 텍스트 영역에 자동 반영
            if carc_by_mat:
                carc_lines = []
                for mat_name, details in carc_by_mat.items():
                    for d in details:
                        carc_lines.append(f"{mat_name}: {d}")
                combined_carc = "\n".join(carc_lines)
                st.session_state.section11_data['나_건강_유해성_정보']['발암성'] = combined_carc
                if 's11_발암성' in st.session_state:
                    st.session_state['s11_발암성'] = combined_carc

            # 기관별 파싱
            for mat_name, details in carc_by_mat.items():
                merged_text = " ".join(details)
                parsed = parse_carcinogen_text(merged_text)
                if parsed:
                    existing = st.session_state.carcinogen_agency_data.get(mat_name, {})
                    for ag_key, ag_val in parsed.items():
                        if existing.get(ag_key, "해당없음") == "해당없음":
                            existing[ag_key] = ag_val
                    st.session_state.carcinogen_agency_data[mat_name] = existing

            st.session_state['s11_all'] = all_results
            st.rerun()
    else:
        st.warning("⚠️ 섹션 3에 CAS 번호가 등록된 구성성분이 없습니다.")

    # 결과 체크박스
    if 's11_all' in st.session_state and st.session_state['s11_all']:
        all_results = st.session_state['s11_all']

        # ── 자동 보수적 선택 (최초 1회) ──
        auto_select_conservative(all_results, prefix="chk11")

        st.markdown("---")
        st.markdown("### 📊 항목별 데이터 선택")
        st.info("⚡ **가장 보수적인 값**(독성↑)이 자동 선택되었습니다. 필요 시 수정하세요.")

        for fk, fl, _, _ in TOXICITY_FIELDS:
            items_in_field = [r for r in all_results if r['field'] == fk]
            if not items_in_field: continue

            # ── 발암성: 선택 없이 자동 반영 표시 ──
            if fk == '발암성':
                st.markdown(f'<div class="field-header">📋 {fl} <span style="color:#4caf50; font-size:0.85em;">✅ KOSHA 데이터 자동 반영됨</span></div>', unsafe_allow_html=True)
                for r in items_in_field:
                    if r.get('no_data'):
                        st.markdown(f"  ⬜ {r['mat']}: 자료없음")
                    else:
                        st.markdown(f"  🟢 **KOSHA** | {r['mat']}: {r['detail'][:160]}")
                st.markdown("")
                continue

            st.markdown(f'<div class="field-header">📋 {fl}</div>', unsafe_allow_html=True)
            for r in items_in_field:
                idx = r['idx']
                if r.get('no_data'):
                    display = f"⬜ {r['mat']}: 자료없음"
                else:
                    emoji = "🟢" if r['src'] == 'KOSHA' else "🔵"
                    score = conservative_score(r['detail'], fk)
                    if score >= 500:
                        score_tag = f" `📊 정량 [{score:.0f}]`"
                    elif score > 0:
                        score_tag = f" `📝 정성 [{score:.0f}]`"
                    else:
                        score_tag = ""
                    display = f"{emoji} **{r['src']}** | {r['mat']}: {r['detail'][:160]}{score_tag}"
                c1, c2 = st.columns([0.05, 0.95])
                with c1: st.checkbox("선택", key=f"chk11_{idx}", label_visibility="collapsed")
                with c2: st.markdown(display)
            st.markdown("")

        st.markdown("---")
        if st.button("✅ 선택한 데이터를 입력란에 반영", type="primary", key="apply_s11"):
            selected_by_field = {fk: [] for fk, _, _, _ in TOXICITY_FIELDS}
            for r in all_results:
                # 발암성은 이미 자동 반영됨 → 스킵
                if r['field'] == '발암성':
                    continue
                if st.session_state.get(f"chk11_{r['idx']}", False):
                    selected_by_field[r['field']].append(f"{r['mat']}: {r['detail']}")

            applied = 0
            for fk, _, _, _ in TOXICITY_FIELDS:
                if fk == '발암성':
                    continue  # 발암성은 조회 시 이미 반영
                if selected_by_field[fk]:
                    combined = "\n".join(selected_by_field[fk])
                    st.session_state.section11_data['나_건강_유해성_정보'][fk] = combined
                    wk = f"s11_{fk}"
                    if wk in st.session_state: st.session_state[wk] = combined
                    applied += len(selected_by_field[fk])

            if applied > 0:
                st.success(f"✅ {applied}개 값 반영!")
                st.rerun()
            else:
                st.warning("⚠️ 선택된 값이 없습니다.")

# ============================================================
# 2. 독성 정보 입력 + ATEmix/분류 계산
# ============================================================
st.markdown("---")
st.markdown("### ✍️ 독성 정보 입력 및 혼합물 분류 판정")

st.markdown('<div class="subsection-header">가. 가능성이 높은 노출경로에 관한 정보</div>', unsafe_allow_html=True)
v = st.text_area("노출경로", value=st.session_state.section11_data.get('가_가능성이_높은_노출경로에_관한_정보', ''),
    height=80, placeholder="예: 흡입, 피부 접촉, 눈 접촉, 경구", key="exposure_routes", label_visibility="collapsed")
st.session_state.section11_data['가_가능성이_높은_노출경로에_관한_정보'] = v

st.markdown('<div class="subsection-header">나. 건강 유해성 정보</div>', unsafe_allow_html=True)

# ── 급성독성 (경구/경피/흡입) : ATEmix 계산 ──
for route_key, route_label, route_kws, route_ph in TOXICITY_FIELDS[:3]:
    route_type = route_key.split('_')[-1]  # 경구, 경피, 흡입

    st.markdown(f'<div class="field-header">📋 {route_label}</div>', unsafe_allow_html=True)
    cur = st.session_state.section11_data['나_건강_유해성_정보'].get(route_key, '')
    val = st.text_area(route_label, value=cur, height=100,
        placeholder=f"조회 결과가 여기에 표시됩니다. 예: LD50 = 5800 mg/kg (Rat)",
        key=f"s11_{route_key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][route_key] = val

    # ── ATEmix 계산 패널 ──
    is_confirmed = st.session_state.confirmed_classifications.get(route_key)
    if is_confirmed:
        st.markdown(f'<div class="result-box">✅ <b>확정 분류:</b> {is_confirmed} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

    with st.expander(f"🧮 ATEmix 계산 ({route_label})", expanded=False):
        st.markdown(f"""
        <div class="calc-box">
        <b>ATEmix 공식:</b> 100/ATEmix = Σ(Ci/ATEi)<br>
        <small>Ci = 성분 함유량(%), ATEi = 성분의 ATE값 (실험 LD50/LC50 또는 구분별 변환값)</small>
        </div>
        """, unsafe_allow_html=True)

        if not components:
            st.warning("섹션 3에 성분이 없습니다.")
        else:
            # ── 텍스트 영역에서 성분별 독성값 자동 추출 ──
            auto_ate = {}
            if val:
                for line in val.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    for comp in components:
                        if comp['name'] in line:
                            # 전체 라인에서 LD50/LC50 수치 추출
                            # 예: "포름알데히드: LD50 270 mg/kg 실험종 : Rabbit|..."
                            num = extract_numeric(line)
                            if num and num > 0:
                                auto_ate[comp['name']] = num

            # 자동추출값을 session_state에 미리 세팅 (아직 0이거나 없을 때만)
            for i, comp in enumerate(components):
                ss_key = f"ate_val_{route_key}_{i}"
                if comp['name'] in auto_ate:
                    if ss_key not in st.session_state or st.session_state[ss_key] == 0.0:
                        st.session_state[ss_key] = auto_ate[comp['name']]

            st.markdown("**성분별 ATE 입력:**")
            # 컬럼 헤더
            hc1, hc2, hc3, hc4 = st.columns([2, 1, 2, 1.5])
            with hc1: st.caption("성분명")
            with hc2: st.caption("함유량(%)")
            with hc3: st.caption("ATE값 (LD50/LC50)")
            with hc4: st.caption("구분변환")

            ate_data = []
            for i, comp in enumerate(components):
                c1, c2, c3, c4 = st.columns([2, 1, 2, 1.5])

                ss_key = f"ate_val_{route_key}_{i}"

                with c1:
                    ate_badge = ""
                    if comp['name'] in auto_ate:
                        ate_badge = f" ← **{auto_ate[comp['name']]}** 자동추출"
                    st.markdown(f"{comp['name']}{ate_badge}")
                with c2:
                    pct = st.number_input("함유량(%)", value=comp['pct'] or 0.0,
                        min_value=0.0, max_value=100.0, step=0.1,
                        key=f"ate_pct_{route_key}_{i}", label_visibility="collapsed")
                with c3:
                    ate_val = st.number_input("ATE값",
                        value=0.0, min_value=0.0, step=0.1, format="%.2f",
                        key=ss_key, label_visibility="collapsed")
                with c4:
                    conv_options = ["직접입력"] + list(ATE_CONVERSION.get(route_type, {}).keys())
                    conv_sel = st.selectbox("구분변환", conv_options,
                        key=f"ate_conv_{route_key}_{i}", label_visibility="collapsed")

                    final_ate = ate_val
                    if conv_sel != "직접입력" and route_type in ATE_CONVERSION:
                        final_ate = ATE_CONVERSION[route_type].get(conv_sel, ate_val)

                ate_data.append({'name': comp['name'], 'pct': pct, 'ate': final_ate})

            # 계산 실행
            st.markdown("---")
            if st.button(f"📊 ATEmix 계산", key=f"calc_ate_{route_key}"):
                valid_entries = [d for d in ate_data if d['pct'] > 0 and d['ate'] > 0]
                if not valid_entries:
                    st.error("⚠️ 함유량(%)과 ATE값을 모두 입력해주세요.")
                else:
                    sum_ci_atei = sum(d['pct'] / d['ate'] for d in valid_entries)
                    unknown_pct = sum(d['pct'] for d in ate_data if d['pct'] > 0 and d['ate'] == 0)

                    if sum_ci_atei > 0:
                        ate_mix = 100 / sum_ci_atei
                        classification = classify_ate(ate_mix, route_type)

                        st.markdown("**계산 과정:**")
                        calc_lines = []
                        for d in valid_entries:
                            calc_lines.append(f"  {d['name']}: {d['pct']}% / {d['ate']} = {d['pct']/d['ate']:.4f}")
                        st.code('\n'.join(calc_lines) +
                            f"\n\n  Σ(Ci/ATEi) = {sum_ci_atei:.4f}" +
                            f"\n  ATEmix = 100 / {sum_ci_atei:.4f} = {ate_mix:.2f}" +
                            (f"\n  ⚠ ATE 미확인 성분: {unknown_pct:.1f}%" if unknown_pct > 0 else ""))

                        st.markdown(f'<div class="result-box">📌 <b>ATEmix = {ate_mix:.2f}</b> → <b>{classification}</b></div>', unsafe_allow_html=True)

                        st.session_state[f'ate_result_{route_key}'] = f"ATEmix = {ate_mix:.2f} → {classification}"

            # ATEmix 결과가 있으면 수정 + 확정
            if f'ate_result_{route_key}' in st.session_state:
                st.markdown("---")
                st.markdown("**최종 판정 결과** (수정 가능):")
                edited_ate = st.text_input(
                    "판정 결과", value=st.session_state[f'ate_result_{route_key}'],
                    key=f"edit_ate_{route_key}", label_visibility="collapsed")
                if st.button(f"✅ 이 결과를 확정합니다", key=f"confirm_ate_{route_key}"):
                    st.session_state.confirmed_classifications[route_key] = edited_ate
                    st.success(f"✅ {route_label}: {edited_ate} 확정!")
                    st.rerun()


# ── 나머지 항목: 함유량 기준 분류 ──
for key, label, kws, ph in TOXICITY_FIELDS[3:]:

    # ============================================================
    # 발암성 항목: 물질별 기관별 분류 결과 입력 UI
    # ============================================================
    if key == '발암성':
        st.markdown(f'<div class="field-header">📋 {label}</div>', unsafe_allow_html=True)
        cur = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
        val = st.text_area(label, value=cur, height=80, placeholder=ph or "조회 결과가 여기에 표시됩니다.",
            key=f"s11_{key}", label_visibility="collapsed")
        st.session_state.section11_data['나_건강_유해성_정보'][key] = val

        is_confirmed = st.session_state.confirmed_classifications.get(key)
        if is_confirmed:
            st.markdown(f'<div class="result-box">✅ <b>확정 분류:</b> {is_confirmed} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

        # ── 기관별 발암성 분류 입력 패널 ──
        if components:
            with st.expander(f"🏛️ 기관별 발암성 분류 결과 입력 ({len(components)}개 물질)", expanded=False):
                st.markdown("""
                <div class="calc-box">
                <b>물질별 기관별 발암성 분류</b><br>
                <small>각 성분의 발암성 분류를 7개 기관 기준으로 입력합니다.<br>
                가장 보수적인(위험한) 기관 결과가 혼합물 분류에 자동 반영됩니다.</small>
                </div>
                """, unsafe_allow_html=True)

                # 물질별 탭 생성
                comp_tabs = st.tabs([f"🔬 {comp['name']}" for comp in components])

                for ci, (comp, tab) in enumerate(zip(components, comp_tabs)):
                    with tab:
                        pct_display = f"{comp['pct']}%" if comp['pct'] is not None else "미입력"
                        st.markdown(f"**{comp['name']}** (CAS: {comp['cas']}, 함유량: {pct_display})")

                        # 기관별 선택 영역
                        agency_selections = {}
                        for ag_key, ag_cfg in CARCINOGEN_AGENCIES.items():
                            ss_key = f"carc_{ci}_{ag_key}"

                            # carcinogen_agency_data에 파싱된 값이 있으면 우선 반영
                            parsed_val = st.session_state.carcinogen_agency_data.get(comp['name'], {}).get(ag_key, None)

                            if parsed_val and parsed_val in ag_cfg['options']:
                                # API 파싱 결과가 있으면 위젯 key도 강제 업데이트
                                if ss_key not in st.session_state or st.session_state.get(ss_key) == "해당없음":
                                    st.session_state[ss_key] = parsed_val
                                idx = ag_cfg['options'].index(st.session_state.get(ss_key, parsed_val))
                            elif ss_key in st.session_state and st.session_state[ss_key] in ag_cfg['options']:
                                idx = ag_cfg['options'].index(st.session_state[ss_key])
                            else:
                                idx = 0

                            c_label, c_sel = st.columns([1.5, 3])
                            with c_label:
                                st.markdown(f"**{ag_cfg['label']}**")
                            with c_sel:
                                sel = st.selectbox(
                                    ag_cfg['label'],
                                    ag_cfg['options'],
                                    index=idx,
                                    key=ss_key,
                                    label_visibility="collapsed"
                                )
                            agency_selections[ag_key] = sel

                        # session_state에 저장
                        st.session_state.carcinogen_agency_data[comp['name']] = agency_selections

                        # 이 물질의 가장 보수적 GHS 구분 표시
                        best_ghs = get_most_conservative_ghs(agency_selections)

                        # 기관별 결과 요약 테이블
                        st.markdown("---")
                        active_agencies = []
                        for ag_key, sel_val in agency_selections.items():
                            if sel_val not in ("해당없음", "자료없음"):
                                ghs = CARCINOGEN_TO_GHS.get(sel_val, "-")
                                active_agencies.append(f"**{CARCINOGEN_AGENCIES[ag_key]['label']}**: {sel_val} → GHS {ghs}")

                        if active_agencies:
                            summary_text = " / ".join(active_agencies)
                            if best_ghs in ("구분 1A", "구분 1B"):
                                st.markdown(f'<div class="warn-box">⚠️ {summary_text}<br>→ 최보수 판정: <b>{best_ghs}</b></div>', unsafe_allow_html=True)
                            elif best_ghs == "구분 2":
                                st.markdown(f'<div class="calc-box">📌 {summary_text}<br>→ 최보수 판정: <b>{best_ghs}</b></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="result-box">✅ {summary_text}<br>→ 판정: <b>{best_ghs}</b></div>', unsafe_allow_html=True)
                        else:
                            st.caption("아직 선택된 기관별 분류가 없습니다.")

                # ── 전체 물질 요약 + 혼합물 분류 자동 판정 ──
                st.markdown("---")
                st.markdown("### 📊 발암성 혼합물 분류 자동 판정")

                comp_class_data_carc = []
                summary_rows = []
                for ci, comp in enumerate(components):
                    ag_sels = st.session_state.carcinogen_agency_data.get(comp['name'], {})
                    best_ghs = get_most_conservative_ghs(ag_sels)
                    pct = comp['pct'] or 0.0

                    # 기관별 비해당 제외 요약 생성
                    active_list = []
                    for ag_key, sel_val in ag_sels.items():
                        if sel_val not in ("해당없음", "자료없음"):
                            active_list.append(f"{CARCINOGEN_AGENCIES[ag_key]['label']}: {sel_val}")

                    agency_detail = " | ".join(active_list) if active_list else "발암성 분류 없음"
                    summary_rows.append({
                        'name': comp['name'], 'pct': pct, 'ghs': best_ghs, 'detail': agency_detail
                    })
                    comp_class_data_carc.append({'name': comp['name'], 'pct': pct, 'cls': best_ghs})

                # 요약 테이블 표시
                for row in summary_rows:
                    ghs_emoji = "🔴" if "1" in row['ghs'] else ("🟡" if "2" in row['ghs'] else "⚪")
                    st.markdown(f"  {ghs_emoji} **{row['name']}** ({row['pct']}%) → **{row['ghs']}** — {row['detail']}")

                # 자동 판정 버튼
                st.markdown("---")
                if st.button("📊 발암성 혼합물 분류 판정", key="calc_carc_agency"):
                    recommendation, details, sums = judge_classification('발암성', comp_class_data_carc)

                    st.markdown("**함유량 합산:**")
                    code = f"  구분1 (1A+1B) 합계: {sums['cls1']:.2f}%\n  구분2 합계: {sums['cls2']:.2f}%"
                    if sums['unknown'] > 0: code += f"\n  ⚠ 자료없음: {sums['unknown']:.2f}%"
                    st.code(code)

                    for d in details:
                        st.write(f"  → {d}")

                    if recommendation != "분류되지 않음":
                        st.markdown(f'<div class="result-box">📌 <b>판정: {recommendation}</b></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="calc-box">📌 <b>판정: 분류되지 않음</b></div>', unsafe_allow_html=True)

                    st.session_state[f'conc_result_{key}'] = recommendation

                    # 텍스트 영역에 기관별 결과 자동 반영
                    carc_text_lines = []
                    for row in summary_rows:
                        if row['ghs'] not in ("해당없음", "자료없음"):
                            carc_text_lines.append(f"{row['name']}: {row['detail']}")
                    if carc_text_lines:
                        combined_text = "\n".join(carc_text_lines)
                        st.session_state.section11_data['나_건강_유해성_정보']['발암성'] = combined_text
                        wk = f"s11_발암성"
                        if wk in st.session_state:
                            st.session_state[wk] = combined_text

                # ── 결과 수정 + 확정 ──
                if f'conc_result_{key}' in st.session_state:
                    st.markdown("---")
                    st.markdown("**최종 판정 결과** (수정 가능):")
                    edited_result = st.text_input(
                        "판정 결과", value=st.session_state[f'conc_result_{key}'],
                        key=f"edit_conc_{key}", label_visibility="collapsed")

                    if st.button(f"✅ 이 결과를 확정합니다", key=f"confirm_conc_{key}"):
                        st.session_state.confirmed_classifications[key] = edited_result
                        st.success(f"✅ {label}: {edited_result} 확정!")
                        st.rerun()

        # ── 기존 함유량 기준 분류 패널도 유지 (성분이 없거나 대체 사용 시) ──
        if key in FIELD_CONFIG and components:
            cfg = FIELD_CONFIG[key]
            with st.expander(f"📐 함유량 기준 수동 분류 ({label}) — 기관별 입력을 사용하지 않을 경우", expanded=False):
                st.markdown(f"""
                <div class="calc-box">
                <b>{cfg['desc']}</b> - 혼합물 분류 (수동 구분 선택)<br>
                <small>위 기관별 입력 대신 직접 GHS 구분을 선택합니다.</small>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**분류 기준:**")
                for rt in cfg['rules_text']:
                    st.write(f"  • {rt}")

                st.markdown("---")
                st.markdown("**성분별 해당 구분 정보 입력:**")

                comp_class_data = []
                for i, comp in enumerate(components):
                    c1, c2, c3 = st.columns([2, 1.5, 2])
                    with c1:
                        pct_display = f"{comp['pct']}%" if comp['pct'] is not None else "미입력"
                        st.markdown(f"**{comp['name']}** ({pct_display})")
                    with c2:
                        pct = st.number_input("함유량(%)", value=comp['pct'] or 0.0,
                            min_value=0.0, max_value=100.0, step=0.1,
                            key=f"conc_pct_manual_{key}_{i}", label_visibility="collapsed")
                    with c3:
                        cls = st.selectbox(f"{comp['name']} 구분", cfg['options'],
                            key=f"conc_cls_manual_{key}_{i}", label_visibility="collapsed")

                    comp_class_data.append({'name': comp['name'], 'pct': pct, 'cls': cls})

                st.markdown("---")
                if st.button(f"📊 분류 판정", key=f"calc_conc_manual_{key}"):
                    recommendation, details, sums = judge_classification(key, comp_class_data)

                    st.markdown("**함유량 합산:**")
                    code = f"  구분1 합계: {sums['cls1']:.2f}%\n  구분2 합계: {sums['cls2']:.2f}%"
                    if sums['unknown'] > 0: code += f"\n  ⚠ 자료없음: {sums['unknown']:.2f}%"
                    st.code(code)

                    for d in details:
                        st.write(f"  → {d}")

                    if recommendation != "분류되지 않음":
                        st.markdown(f'<div class="result-box">📌 <b>판정: {recommendation}</b></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="calc-box">📌 <b>판정: 분류되지 않음</b></div>', unsafe_allow_html=True)

                    st.session_state[f'conc_result_{key}'] = recommendation

                if f'conc_result_{key}' in st.session_state:
                    st.markdown("---")
                    st.markdown("**최종 판정 결과** (수정 가능):")
                    edited_result = st.text_input(
                        "판정 결과", value=st.session_state[f'conc_result_{key}'],
                        key=f"edit_conc_manual_{key}", label_visibility="collapsed")

                    if st.button(f"✅ 이 결과를 확정합니다", key=f"confirm_conc_manual_{key}"):
                        st.session_state.confirmed_classifications[key] = edited_result
                        st.success(f"✅ {label}: {edited_result} 확정!")
                        st.rerun()

        continue  # 발암성은 여기서 처리 완료, 아래 일반 로직 건너뜀
    # ============================================================
    # 발암성 이외 나머지 항목: 기존 로직 유지
    # ============================================================
    st.markdown(f'<div class="field-header">📋 {label}</div>', unsafe_allow_html=True)
    cur = st.session_state.section11_data['나_건강_유해성_정보'].get(key, '')
    val = st.text_area(label, value=cur, height=80, placeholder=ph or "조회 결과가 여기에 표시됩니다.",
        key=f"s11_{key}", label_visibility="collapsed")
    st.session_state.section11_data['나_건강_유해성_정보'][key] = val

    is_confirmed = st.session_state.confirmed_classifications.get(key)
    if is_confirmed:
        st.markdown(f'<div class="result-box">✅ <b>확정 분류:</b> {is_confirmed} <span class="confirm-badge">CONFIRMED</span></div>', unsafe_allow_html=True)

    if key in FIELD_CONFIG and components:
        cfg = FIELD_CONFIG[key]

        with st.expander(f"📐 함유량 기준 분류 판정 ({label})", expanded=False):
            st.markdown(f"""
            <div class="calc-box">
            <b>{cfg['desc']}</b> - 혼합물 분류 (함유량 기준)<br>
            <small>각 성분의 해당 구분 함유량 합계로 혼합물 구분 판정</small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**분류 기준:**")
            for rt in cfg['rules_text']:
                st.write(f"  • {rt}")

            st.markdown("---")
            st.markdown("**성분별 해당 구분 정보 입력:**")

            comp_class_data = []
            for i, comp in enumerate(components):
                c1, c2, c3 = st.columns([2, 1.5, 2])
                with c1:
                    pct_display = f"{comp['pct']}%" if comp['pct'] is not None else "미입력"
                    st.markdown(f"**{comp['name']}** ({pct_display})")
                with c2:
                    pct = st.number_input("함유량(%)", value=comp['pct'] or 0.0,
                        min_value=0.0, max_value=100.0, step=0.1,
                        key=f"conc_pct_{key}_{i}", label_visibility="collapsed")
                with c3:
                    cls = st.selectbox(f"{comp['name']} 구분", cfg['options'],
                        key=f"conc_cls_{key}_{i}", label_visibility="collapsed")

                comp_class_data.append({'name': comp['name'], 'pct': pct, 'cls': cls})

            # 자동 판정
            st.markdown("---")
            if st.button(f"📊 분류 판정", key=f"calc_conc_{key}"):
                recommendation, details, sums = judge_classification(key, comp_class_data)

                st.markdown("**함유량 합산:**")
                code = f"  구분1 합계: {sums['cls1']:.2f}%\n  구분2 합계: {sums['cls2']:.2f}%"
                if sums['cls3'] > 0: code += f"\n  구분3 합계: {sums['cls3']:.2f}%"
                if sums['unknown'] > 0: code += f"\n  ⚠ 자료없음: {sums['unknown']:.2f}%"
                st.code(code)

                for d in details:
                    st.write(f"  → {d}")

                if recommendation != "분류되지 않음":
                    st.markdown(f'<div class="result-box">📌 <b>판정: {recommendation}</b></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="calc-box">📌 <b>판정: 분류되지 않음</b></div>', unsafe_allow_html=True)

                if sums['unknown'] > 0:
                    st.markdown(f'<div class="warn-box">⚠️ 자료없음 성분 {sums["unknown"]:.2f}% — 추가 조사 권장</div>', unsafe_allow_html=True)

                st.session_state[f'conc_result_{key}'] = recommendation

            # ── 결과 수정 + 확정 ──
            if f'conc_result_{key}' in st.session_state:
                st.markdown("---")
                st.markdown("**최종 판정 결과** (수정 가능):")
                edited_result = st.text_input(
                    "판정 결과", value=st.session_state[f'conc_result_{key}'],
                    key=f"edit_conc_{key}", label_visibility="collapsed")

                if st.button(f"✅ 이 결과를 확정합니다", key=f"confirm_conc_{key}"):
                    st.session_state.confirmed_classifications[key] = edited_result
                    st.success(f"✅ {label}: {edited_result} 확정!")
                    st.rerun()

# ============================================================
# 3. 확정 분류 요약 + 저장
# ============================================================
st.markdown("---")
st.markdown("### 📋 확정 분류 요약")

confirmed = st.session_state.confirmed_classifications
if confirmed:
    for fk, fl, _, _ in TOXICITY_FIELDS:
        if fk in confirmed:
            cc1, cc2 = st.columns([4, 1])
            with cc1:
                st.markdown(f"  ✅ **{fl}**: {confirmed[fk]}")
            with cc2:
                if st.button("↩ 해제", key=f"reset_{fk}"):
                    del st.session_state.confirmed_classifications[fk]
                    st.rerun()
else:
    st.caption("아직 확정된 분류가 없습니다. 위 각 항목에서 계산 후 [확정] 버튼을 눌러주세요.")

st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("섹션 11 저장", type="primary", use_container_width=True):
        st.success("✅ 섹션 11이 저장되었습니다!")

with st.expander("저장된 데이터 확인"):
    st.json(st.session_state.section11_data)
    st.json(st.session_state.confirmed_classifications)
    if st.session_state.carcinogen_agency_data:
        st.markdown("**🏛️ 기관별 발암성 분류 데이터:**")
        st.json(st.session_state.carcinogen_agency_data)
