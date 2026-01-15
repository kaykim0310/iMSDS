"""
KOSHA (한국산업안전보건공단) MSDS API 연동 모듈

이 모듈은 KOSHA MSDS 공개 API를 연동합니다.
https://msds.kosha.or.kr/openapi/service/msdschem
"""

import requests
import os
import streamlit as st
from typing import Optional, Dict, List, Any
import xml.etree.ElementTree as ET
import time
import re


# ============================================================
# API 설정
# ============================================================
DEFAULT_API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
BASE_URL = "https://msds.kosha.or.kr/openapi/service/msdschem"
TIMEOUT = 30
DELAY = 0.3  # API 호출 간격 (초)


# ============================================================
# 기본 API 호출 함수
# ============================================================
def _call_api(endpoint: str, params: Dict[str, Any], api_key: str = "") -> Optional[ET.Element]:
    """API 호출 후 XML 파싱하여 반환"""
    url = f"{BASE_URL}/{endpoint}"
    params["serviceKey"] = api_key or DEFAULT_API_KEY

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"[ERROR] API 호출 실패: {e}")
        return None
    except ET.ParseError as e:
        print(f"[ERROR] XML 파싱 실패: {e}")
        return None


def _get_text(element: Optional[ET.Element], tag: str) -> str:
    """XML 요소에서 텍스트 추출"""
    if element is None:
        return ""
    child = element.find(tag)
    return child.text if child is not None and child.text else ""


# ============================================================
# 화학물질 검색
# ============================================================
def get_chemical_by_cas(cas_number: str, api_key: str = "") -> dict:
    """
    CAS 번호로 화학물질 정보 조회

    Args:
        cas_number: CAS 번호 (예: "67-64-1")
        api_key: API 키 (선택)

    Returns:
        {'success': True, 'data': [...]} 또는 {'success': False, 'error': '...'}
    """
    root = _call_api("chemlist", {
        "searchWrd": cas_number,
        "searchCnd": 1,  # 1 = CAS No 검색
        "numOfRows": 10,
        "pageNo": 1
    }, api_key)

    if root is None:
        return {"success": False, "error": "API 호출 실패"}

    items = root.findall(".//item")
    if not items:
        return {"success": False, "error": "물질 미등록", "data": []}

    results = []
    for item in items:
        result = {
            "chemId": _get_text(item, "chemId"),
            "chemNameKor": _get_text(item, "chemNameKor"),
            "casNo": _get_text(item, "casNo"),
            "keNo": _get_text(item, "keNo"),
            "unNo": _get_text(item, "unNo"),
            "enNo": _get_text(item, "enNo"),
            "lastDate": _get_text(item, "lastDate")
        }
        results.append(result)

    return {"success": True, "data": results}


def get_chemical_by_name(chem_name: str, api_key: str = "") -> dict:
    """
    화학물질명으로 정보 조회

    Args:
        chem_name: 물질명 (예: "아세톤")
        api_key: API 키 (선택)
    """
    root = _call_api("chemlist", {
        "searchWrd": chem_name,
        "searchCnd": 0,  # 0 = 국문명 검색
        "numOfRows": 10,
        "pageNo": 1
    }, api_key)

    if root is None:
        return {"success": False, "error": "API 호출 실패"}

    items = root.findall(".//item")
    if not items:
        return {"success": False, "error": "물질 미등록", "data": []}

    results = []
    for item in items:
        result = {
            "chemId": _get_text(item, "chemId"),
            "chemNameKor": _get_text(item, "chemNameKor"),
            "casNo": _get_text(item, "casNo"),
            "keNo": _get_text(item, "keNo"),
            "unNo": _get_text(item, "unNo")
        }
        results.append(result)

    return {"success": True, "data": results}


# ============================================================
# 상세 정보 조회
# ============================================================
def get_hazard_classification(chem_id: str, api_key: str = "") -> Dict[str, Any]:
    """
    유해성·위험성 분류 조회 (2번 항목)

    Args:
        chem_id: 화학물질 ID (6자리)

    Returns:
        {'classification': '...', 'signal': '...', 'pictograms': [...]}
    """
    root = _call_api("chemdetail02", {"chemId": chem_id}, api_key)

    result = {
        "classification": "",
        "signal": "",
        "pictograms": [],
        "hazardStatements": [],
        "precautionStatements": []
    }

    if root is None:
        return result

    items = root.findall(".//item")
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")

        if not detail or detail in ["자료없음", ""]:
            continue

        if "유해성" in name_kor and "위험성" in name_kor and "분류" in name_kor:
            result["classification"] = detail
        elif "신호어" in name_kor:
            result["signal"] = detail
        elif "그림문자" in name_kor:
            result["pictograms"].append(detail)
        elif "유해" in name_kor and "위험문구" in name_kor:
            result["hazardStatements"].append(detail)
        elif "예방조치문구" in name_kor:
            result["precautionStatements"].append(detail)

    return result


def get_exposure_limits(chem_id: str, api_key: str = "") -> Dict[str, str]:
    """
    노출기준 조회 (8번 항목: 노출방지 및 개인보호구)

    Args:
        chem_id: 화학물질 ID (6자리)

    Returns:
        {'twa': '...', 'stel': '...', 'acgih_twa': '...', 'acgih_stel': '...'}
    """
    root = _call_api("chemdetail08", {"chemId": chem_id}, api_key)

    result = {"twa": "-", "stel": "-", "acgih_twa": "-", "acgih_stel": "-"}

    if root is None:
        return result

    items = root.findall(".//item")
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")

        if not detail or detail in ["자료없음", ""]:
            continue

        # 국내규정 TWA/STEL 파싱
        if "국내규정" in name_kor:
            if "TWA" in detail.upper():
                twa_match = re.search(r'TWA[:\s]*([^\s,;]+(?:\s*[a-zA-Z/³]+)?)', detail, re.I)
                if twa_match:
                    result["twa"] = twa_match.group(1).strip()
            if "STEL" in detail.upper():
                stel_match = re.search(r'STEL[:\s]*([^\s,;]+(?:\s*[a-zA-Z/³]+)?)', detail, re.I)
                if stel_match:
                    result["stel"] = stel_match.group(1).strip()
            # TWA/STEL 구분 없이 값만 있는 경우
            if result["twa"] == "-" and ("ppm" in detail or "mg/m" in detail):
                result["twa"] = detail.split(",")[0].strip()

        # ACGIH 규정
        if "ACGIH" in name_kor:
            if "TWA" in detail.upper():
                twa_match = re.search(r'TWA[:\s]*([^\s,;]+(?:\s*[a-zA-Z/³]+)?)', detail, re.I)
                if twa_match:
                    result["acgih_twa"] = twa_match.group(1).strip()
            if "STEL" in detail.upper():
                stel_match = re.search(r'STEL[:\s]*([^\s,;]+(?:\s*[a-zA-Z/³]+)?)', detail, re.I)
                if stel_match:
                    result["acgih_stel"] = stel_match.group(1).strip()

    return result


def get_physical_properties(chem_id: str, api_key: str = "") -> Dict[str, str]:
    """
    물리화학적 특성 조회 (9번 항목)

    Args:
        chem_id: 화학물질 ID

    Returns:
        {'appearance': '...', 'odor': '...', 'pH': '...', ...}
    """
    root = _call_api("chemdetail09", {"chemId": chem_id}, api_key)

    result = {}

    if root is None:
        return result

    # 항목명 → 키 매핑
    key_map = {
        "외관": "appearance",
        "냄새": "odor",
        "pH": "pH",
        "녹는점": "meltingPoint",
        "끓는점": "boilingPoint",
        "인화점": "flashPoint",
        "증기압": "vaporPressure",
        "비중": "specificGravity",
        "용해도": "solubility",
        "분자량": "molecularWeight"
    }

    items = root.findall(".//item")
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")

        if not detail or detail in ["자료없음", ""]:
            continue

        for kor_name, eng_key in key_map.items():
            if kor_name in name_kor:
                result[eng_key] = detail
                break

    return result


def get_legal_regulations(chem_id: str, api_key: str = "") -> Dict[str, str]:
    """
    법적 규제현황 조회 (15번 항목)

    Args:
        chem_id: 화학물질 ID (6자리)

    Returns:
        {
            'measurement': 'O/X',      # 작업환경측정 대상
            'healthCheck': 'O/X',      # 특수건강진단 대상
            'managedHazard': 'O/X',    # 관리대상유해물질
            'specialManaged': 'O/X',   # 특별관리물질
            'rawText': '...'           # 원본 텍스트
        }
    """
    root = _call_api("chemdetail15", {"chemId": chem_id}, api_key)

    result = {
        "measurement": "X",
        "healthCheck": "X",
        "managedHazard": "X",
        "specialManaged": "X",
        "rawText": ""
    }

    if root is None:
        return result

    items = root.findall(".//item")
    raw_texts = []

    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")

        if not detail or detail in ["해당없음", "자료없음", ""]:
            continue

        if "산업안전보건법" in name_kor:
            raw_texts.append(detail)

            # 규제 항목 파싱
            if any(k in detail for k in ["작업환경측정", "측정대상"]):
                result["measurement"] = "O"
            if any(k in detail for k in ["특수건강진단", "건강진단"]):
                result["healthCheck"] = "O"
            if any(k in detail for k in ["관리대상", "유해물질"]):
                result["managedHazard"] = "O"
            if any(k in detail for k in ["특별관리", "발암성", "CMR"]):
                result["specialManaged"] = "O"

            # 일반 규제 표시가 있으면 기본 항목 O
            if detail and result["measurement"] == "X":
                result["measurement"] = "O"
                result["healthCheck"] = "O"

    result["rawText"] = " | ".join(raw_texts)
    return result


def get_toxicity_info(chem_id: str, api_key: str = "") -> Dict[str, Any]:
    """
    독성정보 조회 (11번 항목)

    Args:
        chem_id: 화학물질 ID

    Returns:
        급성독성, 피부자극성 등 독성 정보
    """
    root = _call_api("chemdetail11", {"chemId": chem_id}, api_key)

    result = {
        "acute_oral": "",
        "acute_dermal": "",
        "acute_inhalation": "",
        "skin_corrosion": "",
        "eye_damage": "",
        "sensitization": "",
        "carcinogenicity": "",
        "mutagenicity": "",
        "reproductive_toxicity": "",
        "raw_items": []
    }

    if root is None:
        return result

    items = root.findall(".//item")
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")

        if not detail or detail in ["자료없음", ""]:
            continue

        result["raw_items"].append({"name": name_kor, "detail": detail})

        # 급성독성
        if "급성" in name_kor and "경구" in name_kor:
            result["acute_oral"] = detail
        elif "급성" in name_kor and "경피" in name_kor:
            result["acute_dermal"] = detail
        elif "급성" in name_kor and "흡입" in name_kor:
            result["acute_inhalation"] = detail
        # 기타 독성
        elif "피부" in name_kor and ("부식" in name_kor or "자극" in name_kor):
            result["skin_corrosion"] = detail
        elif "눈" in name_kor and ("손상" in name_kor or "자극" in name_kor):
            result["eye_damage"] = detail
        elif "과민" in name_kor:
            result["sensitization"] = detail
        elif "발암" in name_kor:
            result["carcinogenicity"] = detail
        elif "변이원" in name_kor or "돌연변이" in name_kor:
            result["mutagenicity"] = detail
        elif "생식" in name_kor:
            result["reproductive_toxicity"] = detail

    return result


def get_ecological_info(chem_id: str, api_key: str = "") -> Dict[str, Any]:
    """
    환경정보 조회 (12번 항목)

    Args:
        chem_id: 화학물질 ID

    Returns:
        수생독성, 잔류성 등 환경 정보
    """
    root = _call_api("chemdetail12", {"chemId": chem_id}, api_key)

    result = {
        "aquatic_acute": "",
        "aquatic_chronic": "",
        "persistence": "",
        "bioaccumulation": "",
        "raw_items": []
    }

    if root is None:
        return result

    items = root.findall(".//item")
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")

        if not detail or detail in ["자료없음", ""]:
            continue

        result["raw_items"].append({"name": name_kor, "detail": detail})

        if "수생" in name_kor and "급성" in name_kor:
            result["aquatic_acute"] = detail
        elif "수생" in name_kor and "만성" in name_kor:
            result["aquatic_chronic"] = detail
        elif "잔류" in name_kor or "분해" in name_kor:
            result["persistence"] = detail
        elif "생물" in name_kor and "농축" in name_kor:
            result["bioaccumulation"] = detail

    return result


# ============================================================
# 통합 조회 함수
# ============================================================
def get_chemical_info(cas_no: str, api_key: str = "") -> Dict[str, Any]:
    """
    CAS 번호로 화학물질 정보 통합 조회 (기본)

    Args:
        cas_no: CAS 번호
        api_key: API 키 (선택)

    Returns:
        통합된 화학물질 정보 딕셔너리
    """
    # 1. 물질 검색
    search_result = get_chemical_by_cas(cas_no, api_key)

    if not search_result.get("success") or not search_result.get("data"):
        return {
            "success": False,
            "casNo": cas_no,
            "name": "미등록",
            "error": search_result.get("error", "검색 실패")
        }

    chem_data = search_result["data"][0]
    chem_id = chem_data["chemId"]

    # 2. 노출기준 조회
    time.sleep(DELAY)
    exposure = get_exposure_limits(chem_id, api_key)

    # 3. 법적규제 조회
    time.sleep(DELAY)
    regulations = get_legal_regulations(chem_id, api_key)

    return {
        "success": True,
        "casNo": cas_no,
        "chemId": chem_id,
        "name": chem_data.get("chemNameKor", cas_no),
        "keNo": chem_data.get("keNo", ""),
        "unNo": chem_data.get("unNo", ""),
        "twa": exposure.get("twa", "-"),
        "stel": exposure.get("stel", "-"),
        "acgih_twa": exposure.get("acgih_twa", "-"),
        "acgih_stel": exposure.get("acgih_stel", "-"),
        "measurement": regulations.get("measurement", "X"),
        "healthCheck": regulations.get("healthCheck", "X"),
        "managedHazard": regulations.get("managedHazard", "X"),
        "specialManaged": regulations.get("specialManaged", "X"),
        "regulations_raw": regulations.get("rawText", "")
    }


def get_chemical_info_full(cas_no: str, api_key: str = "") -> Dict[str, Any]:
    """
    CAS 번호로 화학물질 전체 정보 조회 (MSDS 작성용)
    유해성, 물리적 특성, 독성정보, 환경정보 포함

    Args:
        cas_no: CAS 번호
        api_key: API 키 (선택)

    Returns:
        전체 화학물질 정보 딕셔너리
    """
    basic = get_chemical_info(cas_no, api_key)

    if not basic.get("success"):
        return basic

    chem_id = basic["chemId"]

    # 추가 정보 조회
    time.sleep(DELAY)
    hazard = get_hazard_classification(chem_id, api_key)

    time.sleep(DELAY)
    physical = get_physical_properties(chem_id, api_key)

    time.sleep(DELAY)
    toxicity = get_toxicity_info(chem_id, api_key)

    time.sleep(DELAY)
    ecological = get_ecological_info(chem_id, api_key)

    return {
        **basic,
        # 2번 유해위험성
        "hazardClassification": hazard.get("classification", ""),
        "signal": hazard.get("signal", ""),
        "pictograms": hazard.get("pictograms", []),
        "hazardStatements": hazard.get("hazardStatements", []),
        "precautionStatements": hazard.get("precautionStatements", []),
        # 9번 물리화학적 특성
        "physicalProperties": physical,
        # 11번 독성정보
        "toxicityInfo": toxicity,
        # 12번 환경정보
        "ecologicalInfo": ecological
    }


# ============================================================
# Streamlit 통합 함수
# ============================================================
def parse_regulation_for_section15(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    API 조회 결과를 섹션 15 형식으로 변환

    Args:
        info: get_chemical_info 또는 get_chemical_info_full 결과

    Returns:
        섹션 15에서 사용할 수 있는 형식의 딕셔너리
    """
    if not info.get("success"):
        return {
            "success": False,
            "error": info.get("error", "조회 실패")
        }

    return {
        "success": True,
        "물질명": info.get("name", ""),
        "CAS번호": info.get("casNo", ""),
        "산업안전보건법": {
            "작업환경측정대상물질": "해당" if info.get("measurement") == "O" else "해당없음",
            "관리대상유해물질": "해당" if info.get("managedHazard") == "O" else "해당없음",
            "특수건강진단대상물질": "해당" if info.get("healthCheck") == "O" else "해당없음",
            "노출기준설정물질": f"해당 (TWA: {info.get('twa', '-')}, STEL: {info.get('stel', '-')})" if info.get("twa", "-") != "-" else "해당없음",
            "허용기준설정물질": "해당없음",
            "허가대상물질": "해당없음",
            "제조금지물질": "해당없음",
        },
        "화학물질관리법": {
            "유독물질": "해당없음",
            "허가물질": "해당없음",
            "제한물질": "해당없음",
            "금지물질": "해당없음",
            "사고대비물질": "해당없음",
        },
        "raw_regulations": info.get("regulations_raw", ""),
        "노출기준": {
            "TWA": info.get("twa", "-"),
            "STEL": info.get("stel", "-"),
            "ACGIH_TWA": info.get("acgih_twa", "-"),
            "ACGIH_STEL": info.get("acgih_stel", "-"),
        }
    }


# Streamlit 캐시를 활용한 API 호출
@st.cache_data(ttl=3600, show_spinner=False)
def cached_regulation_lookup(cas_number: str, api_key: str = "") -> Dict[str, Any]:
    """
    규제물질 정보를 캐싱하여 조회

    Args:
        cas_number: CAS 등록번호
        api_key: API 키 (선택, 기본값 사용 가능)

    Returns:
        규제물질 정보
    """
    info = get_chemical_info(cas_number, api_key)
    return parse_regulation_for_section15(info)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_full_lookup(cas_number: str, api_key: str = "") -> Dict[str, Any]:
    """
    전체 화학물질 정보를 캐싱하여 조회

    Args:
        cas_number: CAS 등록번호
        api_key: API 키 (선택)

    Returns:
        전체 화학물질 정보
    """
    return get_chemical_info_full(cas_number, api_key)


# ============================================================
# CAS 번호 검증
# ============================================================
def validate_cas_number(cas_number: str) -> bool:
    """
    CAS 번호 형식 검증

    CAS 번호는 XXX-XX-X 또는 XXXXXX-XX-X 형식입니다.
    마지막 숫자는 체크섬입니다.

    Args:
        cas_number: 검증할 CAS 번호

    Returns:
        유효한 CAS 번호인지 여부
    """
    # 기본 형식 검증
    pattern = r'^(\d{2,7})-(\d{2})-(\d)$'
    match = re.match(pattern, cas_number.strip())

    if not match:
        return False

    # 체크섬 검증
    full_number = cas_number.replace('-', '')
    check_digit = int(full_number[-1])
    digits = full_number[:-1][::-1]  # 역순으로

    total = sum(int(d) * (i + 1) for i, d in enumerate(digits))

    return total % 10 == check_digit


# ============================================================
# 일괄 조회 함수
# ============================================================
def collect_all_chemical_info(cas_numbers: list, api_key: str = "", full_info: bool = False) -> list:
    """
    여러 CAS 번호에 대한 화학물질 정보 일괄 수집

    Args:
        cas_numbers: CAS 번호 리스트
        api_key: API 키 (선택)
        full_info: True면 전체 정보 조회

    Returns:
        조회 결과 리스트
    """
    results = []
    total = len(cas_numbers)

    for i, cas in enumerate(cas_numbers):
        if full_info:
            info = get_chemical_info_full(cas, api_key)
        else:
            info = get_chemical_info(cas, api_key)

        results.append(info)

        if i < total - 1:
            time.sleep(DELAY)

    return results
