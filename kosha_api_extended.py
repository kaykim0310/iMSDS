#!/usr/bin/env python3
"""
KOSHA MSDS API 확장 스크립트
안전보건공단 화학물질정보시스템 Open API - 11, 12, 15번 항목 조회
"""

import requests
import xml.etree.ElementTree as ET
import time
from typing import Optional, Dict, List, Any

# ============================================================
# API 설정
# ============================================================
API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
BASE_URL = "https://msds.kosha.or.kr/openapi/service/msdschem"
TIMEOUT = 30
DELAY = 0.3  # API 호출 간격 (초)


def set_api_key(key: str):
    """API 키 설정"""
    global API_KEY
    API_KEY = key


# ============================================================
# 기본 API 호출 함수
# ============================================================
def _call_api(endpoint: str, params: Dict[str, Any]) -> Optional[ET.Element]:
    """API 호출 후 XML 파싱하여 반환"""
    url = f"{BASE_URL}/{endpoint}"
    params["serviceKey"] = API_KEY
    
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
def search_by_cas(cas_no: str) -> Dict[str, Any]:
    """
    CAS 번호로 화학물질 검색
    
    Args:
        cas_no: CAS 번호 (예: "67-64-1")
    
    Returns:
        {'success': True, 'chemId': '...', 'chemNameKor': '...', ...} 또는
        {'success': False, 'error': '...'}
    """
    root = _call_api("chemlist", {
        "searchWrd": cas_no,
        "searchCnd": 1,  # CAS No 검색
        "numOfRows": 10,
        "pageNo": 1
    })
    
    if root is None:
        return {"success": False, "error": "API 호출 실패"}
    
    items = root.findall(".//item")
    if not items:
        return {"success": False, "error": "물질 미등록"}
    
    item = items[0]
    return {
        "success": True,
        "chemId": _get_text(item, "chemId"),
        "chemNameKor": _get_text(item, "chemNameKor"),
        "casNo": _get_text(item, "casNo"),
        "keNo": _get_text(item, "keNo"),
        "unNo": _get_text(item, "unNo"),
        "enNo": _get_text(item, "enNo"),
        "lastDate": _get_text(item, "lastDate")
    }


# ============================================================
# 11번 항목: 독성에 관한 정보
# ============================================================
def get_toxicity_info(chem_id: str) -> Dict[str, Any]:
    """
    독성에 관한 정보 조회 (11번 항목)
    
    Args:
        chem_id: 화학물질 ID (6자리)
    
    Returns:
        {
            'exposure_routes': '...',       # 가능성이 높은 노출 경로에 관한 정보
            'health_hazard_info': '...',    # 건강 유해성 정보
            'acute_toxicity': {...},        # 급성 독성 (경구, 경피, 흡입)
            'irritation': {...},            # 자극성/부식성/민감성
            'chronic_toxicity': {...},      # 만성 독성 및 발암성
            'raw_items': [...]              # 원본 데이터
        }
    """
    root = _call_api("chemdetail11", {"chemId": chem_id})
    
    result = {
        "exposure_routes": "",
        "health_hazard_info": "",
        "acute_toxicity": {
            "oral": "",      # 경구
            "dermal": "",    # 경피
            "inhalation": "" # 흡입
        },
        "irritation": {
            "skin": "",           # 피부 자극성
            "eye": "",            # 눈 자극성
            "respiratory": "",    # 호흡기 자극성
            "sensitization": ""   # 피부 민감성
        },
        "chronic_toxicity": {
            "carcinogenicity": "",      # 발암성
            "mutagenicity": "",         # 생식세포 변이원성
            "reproductive": "",         # 생식독성
            "specific_single": "",      # 특정표적장기독성(1회노출)
            "specific_repeated": "",    # 특정표적장기독성(반복노출)
            "aspiration": ""            # 흡인유해성
        },
        "raw_items": []
    }
    
    if root is None:
        return result
    
    items = root.findall(".//item")
    
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")
        
        if not detail or detail in ["자료없음", "", "-"]:
            continue
        
        # 원본 저장
        result["raw_items"].append({
            "name": name_kor,
            "detail": detail
        })
        
        name_lower = name_kor.lower()
        
        # 노출 경로
        if "노출" in name_kor and "경로" in name_kor:
            result["exposure_routes"] = detail
        
        # 건강 유해성
        elif "건강" in name_kor and "유해성" in name_kor:
            result["health_hazard_info"] = detail
        
        # 급성 독성
        elif "급성" in name_kor and "독성" in name_kor:
            if "경구" in name_kor:
                result["acute_toxicity"]["oral"] = detail
            elif "경피" in name_kor:
                result["acute_toxicity"]["dermal"] = detail
            elif "흡입" in name_kor:
                result["acute_toxicity"]["inhalation"] = detail
            else:
                # 일반 급성독성 (LD50, LC50 포함 가능)
                if "LD50" in detail or "경구" in detail:
                    result["acute_toxicity"]["oral"] = detail
                elif "LC50" in detail or "흡입" in detail:
                    result["acute_toxicity"]["inhalation"] = detail
        
        # 피부 자극성/부식성
        elif "피부" in name_kor and ("자극" in name_kor or "부식" in name_kor):
            result["irritation"]["skin"] = detail
        
        # 눈 자극성
        elif "눈" in name_kor and ("자극" in name_kor or "손상" in name_kor):
            result["irritation"]["eye"] = detail
        
        # 호흡기 자극성
        elif "호흡" in name_kor and "자극" in name_kor:
            result["irritation"]["respiratory"] = detail
        
        # 피부 민감성
        elif "민감" in name_kor or "과민" in name_kor:
            result["irritation"]["sensitization"] = detail
        
        # 발암성
        elif "발암" in name_kor:
            result["chronic_toxicity"]["carcinogenicity"] = detail
        
        # 생식세포 변이원성
        elif "변이원성" in name_kor or "변이" in name_kor and "유전" in name_kor:
            result["chronic_toxicity"]["mutagenicity"] = detail
        
        # 생식독성
        elif "생식" in name_kor and "독성" in name_kor:
            result["chronic_toxicity"]["reproductive"] = detail
        
        # 특정표적장기독성
        elif "특정" in name_kor and "표적" in name_kor:
            if "1회" in name_kor or "단회" in name_kor:
                result["chronic_toxicity"]["specific_single"] = detail
            elif "반복" in name_kor:
                result["chronic_toxicity"]["specific_repeated"] = detail
        
        # 흡인 유해성
        elif "흡인" in name_kor:
            result["chronic_toxicity"]["aspiration"] = detail
    
    return result


# ============================================================
# 12번 항목: 환경에 미치는 영향
# ============================================================
def get_environmental_info(chem_id: str) -> Dict[str, Any]:
    """
    환경에 미치는 영향 조회 (12번 항목)
    
    Args:
        chem_id: 화학물질 ID (6자리)
    
    Returns:
        {
            'aquatic_toxicity': {...},     # 수생/환경 유해성
            'persistence': '...',           # 잔류성 및 분해성
            'bioaccumulation': '...',       # 생물 농축성
            'soil_mobility': '...',         # 토양 이동성
            'other_effects': '...',         # 기타 유해 영향
            'raw_items': [...]              # 원본 데이터
        }
    """
    root = _call_api("chemdetail12", {"chemId": chem_id})
    
    result = {
        "aquatic_toxicity": {
            "fish": "",           # 어류 LC50
            "daphnia": "",        # 물벼룩 EC50
            "algae": "",          # 조류 EC50
            "chronic": ""         # 만성 수생독성
        },
        "persistence": "",
        "bioaccumulation": "",
        "soil_mobility": "",
        "other_effects": "",
        "raw_items": []
    }
    
    if root is None:
        return result
    
    items = root.findall(".//item")
    
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")
        
        if not detail or detail in ["자료없음", "", "-"]:
            continue
        
        # 원본 저장
        result["raw_items"].append({
            "name": name_kor,
            "detail": detail
        })
        
        # 수생/환경 유해성
        if "수생" in name_kor or "환경" in name_kor and "유해" in name_kor:
            if "어류" in name_kor or "어독성" in name_kor:
                result["aquatic_toxicity"]["fish"] = detail
            elif "물벼룩" in name_kor or "갑각류" in name_kor:
                result["aquatic_toxicity"]["daphnia"] = detail
            elif "조류" in name_kor:
                result["aquatic_toxicity"]["algae"] = detail
            elif "만성" in name_kor:
                result["aquatic_toxicity"]["chronic"] = detail
            else:
                # 일반적인 수생독성 데이터 파싱
                if "어류" in detail or "fish" in detail.lower():
                    result["aquatic_toxicity"]["fish"] = detail
                elif "물벼룩" in detail or "Daphnia" in detail:
                    result["aquatic_toxicity"]["daphnia"] = detail
                elif "조류" in detail or "algae" in detail.lower():
                    result["aquatic_toxicity"]["algae"] = detail
        
        # 잔류성 및 분해성
        elif "잔류" in name_kor or "분해" in name_kor:
            result["persistence"] = detail
        
        # 생물 농축성
        elif "농축" in name_kor or "생물축적" in name_kor:
            result["bioaccumulation"] = detail
        
        # 토양 이동성
        elif "토양" in name_kor and "이동" in name_kor:
            result["soil_mobility"] = detail
        
        # 기타 유해 영향
        elif "기타" in name_kor and "영향" in name_kor:
            result["other_effects"] = detail
    
    return result


# ============================================================
# 15번 항목: 법적 규제현황
# ============================================================
def get_legal_regulations(chem_id: str) -> Dict[str, Any]:
    """
    법적 규제현황 조회 (15번 항목)
    
    Args:
        chem_id: 화학물질 ID (6자리)
    
    Returns:
        {
            'occupational_safety': {...},   # 산업안전보건법
            'chemical_control': {...},      # 화학물질관리법
            'dangerous_goods': '...',       # 위험물안전관리법
            'waste_management': '...',      # 폐기물관리법
            'other_regulations': {...},     # 기타 국내 및 외국법
            'raw_items': [...]              # 원본 데이터
        }
    """
    root = _call_api("chemdetail15", {"chemId": chem_id})
    
    result = {
        "occupational_safety": {
            "measurement": "",       # 작업환경측정대상물질
            "managed_hazard": "",    # 관리대상유해물질
            "health_check": "",      # 특수건강진단대상물질
            "exposure_limit": "",    # 노출기준설정물질
            "permission_limit": "",  # 허용기준설정물질
            "permission_required": "",  # 허가대상물질
            "prohibited": "",        # 제조금지물질
            "raw_text": ""
        },
        "chemical_control": {
            "toxic": "",             # 유독물질
            "permission": "",        # 허가물질
            "restricted": "",        # 제한물질
            "prohibited": "",        # 금지물질
            "accident_preparedness": "",  # 사고대비물질
            "raw_text": ""
        },
        "dangerous_goods": "",
        "waste_management": "",
        "other_regulations": {
            "domestic": "",          # 국내 (잔류성유기오염물질 등)
            "us_osha": "",           # 미국 OSHA
            "us_cercla": "",         # 미국 CERCLA
            "us_epcra": "",          # 미국 EPCRA
            "eu_classification": "", # EU 분류
            "rotterdam": "",         # 로테르담협약
            "stockholm": "",         # 스톡홀름협약
            "montreal": ""           # 몬트리올의정서
        },
        "raw_items": []
    }
    
    if root is None:
        return result
    
    items = root.findall(".//item")
    
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")
        
        if not detail or detail in ["해당없음", "자료없음", "", "-"]:
            continue
        
        # 원본 저장
        result["raw_items"].append({
            "name": name_kor,
            "detail": detail
        })
        
        # 산업안전보건법
        if "산업안전보건법" in name_kor or "산안법" in name_kor:
            result["occupational_safety"]["raw_text"] += detail + " | "
            
            if "작업환경측정" in detail or "측정대상" in detail:
                result["occupational_safety"]["measurement"] = "해당"
            if "관리대상" in detail:
                result["occupational_safety"]["managed_hazard"] = "해당"
            if "특수건강진단" in detail or "건강진단" in detail:
                result["occupational_safety"]["health_check"] = "해당"
            if "노출기준" in detail:
                result["occupational_safety"]["exposure_limit"] = "해당"
            if "허용기준" in detail:
                result["occupational_safety"]["permission_limit"] = "해당"
            if "허가대상" in detail:
                result["occupational_safety"]["permission_required"] = "해당"
            if "제조금지" in detail:
                result["occupational_safety"]["prohibited"] = "해당"
        
        # 화학물질관리법
        elif "화학물질관리법" in name_kor or "화관법" in name_kor or "유해화학물질" in name_kor:
            result["chemical_control"]["raw_text"] += detail + " | "
            
            if "유독물질" in detail:
                result["chemical_control"]["toxic"] = "해당"
            if "허가물질" in detail:
                result["chemical_control"]["permission"] = "해당"
            if "제한물질" in detail:
                result["chemical_control"]["restricted"] = "해당"
            if "금지물질" in detail:
                result["chemical_control"]["prohibited"] = "해당"
            if "사고대비" in detail:
                result["chemical_control"]["accident_preparedness"] = "해당"
        
        # 위험물안전관리법
        elif "위험물" in name_kor:
            result["dangerous_goods"] = detail
        
        # 폐기물관리법
        elif "폐기물" in name_kor:
            result["waste_management"] = detail
        
        # 기타 규제
        elif "기타" in name_kor or "외국" in name_kor:
            if "잔류성" in detail or "POPs" in detail:
                result["other_regulations"]["domestic"] = detail
            elif "OSHA" in detail:
                result["other_regulations"]["us_osha"] = detail
            elif "CERCLA" in detail:
                result["other_regulations"]["us_cercla"] = detail
            elif "EPCRA" in detail:
                result["other_regulations"]["us_epcra"] = detail
            elif "EU" in detail or "유럽" in detail:
                result["other_regulations"]["eu_classification"] = detail
            elif "로테르담" in detail:
                result["other_regulations"]["rotterdam"] = detail
            elif "스톡홀름" in detail:
                result["other_regulations"]["stockholm"] = detail
            elif "몬트리올" in detail:
                result["other_regulations"]["montreal"] = detail
    
    return result


# ============================================================
# 통합 조회 함수 (11, 12, 15번 항목)
# ============================================================
def get_msds_sections_11_12_15(cas_no: str) -> Dict[str, Any]:
    """
    CAS 번호로 MSDS 11, 12, 15번 항목 통합 조회
    
    Args:
        cas_no: CAS 번호
    
    Returns:
        통합된 정보 딕셔너리
    """
    # 1. 물질 검색
    search_result = search_by_cas(cas_no)
    
    if not search_result.get("success"):
        return {
            "success": False,
            "casNo": cas_no,
            "name": "미등록",
            "error": search_result.get("error", "검색 실패")
        }
    
    chem_id = search_result["chemId"]
    chem_name = search_result.get("chemNameKor", cas_no)
    
    # 2. 11번 항목 조회 (독성)
    time.sleep(DELAY)
    toxicity = get_toxicity_info(chem_id)
    
    # 3. 12번 항목 조회 (환경)
    time.sleep(DELAY)
    environmental = get_environmental_info(chem_id)
    
    # 4. 15번 항목 조회 (법적규제)
    time.sleep(DELAY)
    regulations = get_legal_regulations(chem_id)
    
    return {
        "success": True,
        "casNo": cas_no,
        "chemId": chem_id,
        "name": chem_name,
        "keNo": search_result.get("keNo", ""),
        "section11_toxicity": toxicity,
        "section12_environmental": environmental,
        "section15_regulations": regulations
    }


def batch_query_sections(cas_list: List[str]) -> List[Dict[str, Any]]:
    """
    여러 CAS 번호에 대해 11, 12, 15번 항목 일괄 조회
    
    Args:
        cas_list: CAS 번호 리스트
    
    Returns:
        조회 결과 리스트
    """
    results = []
    total = len(cas_list)
    
    for i, cas in enumerate(cas_list):
        print(f"[{i+1}/{total}] {cas} 조회 중...")
        
        info = get_msds_sections_11_12_15(cas)
        results.append(info)
        
        if i < total - 1:
            time.sleep(DELAY)
    
    return results


# ============================================================
# 테스트
# ============================================================
if __name__ == "__main__":
    import json
    
    # 테스트 CAS 번호 (아세톤)
    test_cas = "67-64-1"
    
    print(f"=== {test_cas} 조회 테스트 ===\n")
    
    result = get_msds_sections_11_12_15(test_cas)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
