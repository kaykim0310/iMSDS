#!/usr/bin/env python3
"""
KOSHA MSDS API 확장 모듈
11. 독성에 관한 정보
12. 환경에 미치는 영향
15. 법적 규제현황
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
        root = ET.fromstring(response.content)

        # 응답 코드 및 아이템 수 로깅
        result_code = _get_text(root, ".//resultCode")
        result_msg = _get_text(root, ".//resultMsg")
        total_count = _get_text(root, ".//totalCount")
        items = root.findall(".//item")
        print(f"[API] {endpoint}: resultCode={result_code}, resultMsg={result_msg}, totalCount={total_count}, items={len(items)}")

        return root
    except requests.RequestException as e:
        print(f"[ERROR] API 호출 실패 ({endpoint}): {e}")
        return None
    except ET.ParseError as e:
        print(f"[ERROR] XML 파싱 실패 ({endpoint}): {e}")
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
            'exposure_routes': '...',           # 가. 노출 경로
            'acute_toxicity': {...},            # 나. 급성 독성
            'skin_corrosion': '...',            # 피부 부식성/자극성
            'eye_damage': '...',                # 눈 손상/자극성
            'respiratory_sensitization': '...', # 호흡기 과민성
            'skin_sensitization': '...',        # 피부 과민성
            'carcinogenicity': '...',           # 발암성
            'germ_cell_mutagenicity': '...',    # 생식세포 변이원성
            'reproductive_toxicity': '...',     # 생식독성
            'stot_single': '...',               # 특정표적장기독성(1회)
            'stot_repeated': '...',             # 특정표적장기독성(반복)
            'aspiration_hazard': '...',         # 흡인 유해성
            'raw_items': [...]                  # 원본 데이터
        }
    """
    root = _call_api("chemdetail11", {
        "chemId": chem_id,
        "numOfRows": 100,
        "pageNo": 1
    })

    # 디버깅: 원본 XML 저장
    raw_xml = ""
    if root is not None:
        raw_xml = ET.tostring(root, encoding='unicode')

    result = {
        "exposure_routes": "",
        "acute_toxicity": {"oral": "", "dermal": "", "inhalation": ""},
        "skin_corrosion": "",
        "eye_damage": "",
        "respiratory_sensitization": "",
        "skin_sensitization": "",
        "carcinogenicity": "",
        "germ_cell_mutagenicity": "",
        "reproductive_toxicity": "",
        "stot_single": "",
        "stot_repeated": "",
        "aspiration_hazard": "",
        "raw_items": [],
        "_debug_xml": raw_xml,
        "_debug_chemId": chem_id
    }
    
    if root is None:
        return result
    
    items = root.findall(".//item")
    
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")
        
        if not detail or detail in ["자료없음", ""]:
            detail = "자료없음"
        
        # 원본 데이터 저장
        result["raw_items"].append({
            "name": name_kor,
            "detail": detail
        })
        
        # 항목별 파싱
        name_lower = name_kor.lower() if name_kor else ""
        
        if "노출" in name_kor and "경로" in name_kor:
            result["exposure_routes"] = detail
        elif "급성" in name_kor and "독성" in name_kor:
            if "경구" in name_kor:
                result["acute_toxicity"]["oral"] = detail
            elif "경피" in name_kor:
                result["acute_toxicity"]["dermal"] = detail
            elif "흡입" in name_kor:
                result["acute_toxicity"]["inhalation"] = detail
            else:
                # 통합 급성독성
                if result["acute_toxicity"]["oral"] == "":
                    result["acute_toxicity"]["oral"] = detail
        elif "피부" in name_kor and ("부식" in name_kor or "자극" in name_kor):
            if "과민" not in name_kor:
                result["skin_corrosion"] = detail
        elif "눈" in name_kor and ("손상" in name_kor or "자극" in name_kor):
            result["eye_damage"] = detail
        elif "호흡기" in name_kor and "과민" in name_kor:
            result["respiratory_sensitization"] = detail
        elif "피부" in name_kor and "과민" in name_kor:
            result["skin_sensitization"] = detail
        elif "발암" in name_kor:
            result["carcinogenicity"] = detail
        elif "생식세포" in name_kor and "변이" in name_kor:
            result["germ_cell_mutagenicity"] = detail
        elif "생식독성" in name_kor:
            result["reproductive_toxicity"] = detail
        elif "특정" in name_kor and "표적" in name_kor and "장기" in name_kor:
            if "1회" in name_kor or "단일" in name_kor:
                result["stot_single"] = detail
            elif "반복" in name_kor:
                result["stot_repeated"] = detail
        elif "흡인" in name_kor and "유해" in name_kor:
            result["aspiration_hazard"] = detail
    
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
            'ecological_toxicity': {...},    # 가. 생태독성
            'persistence': '...',            # 나. 잔류성 및 분해성
            'bioaccumulation': '...',        # 다. 생물 농축성
            'soil_mobility': '...',          # 라. 토양 이동성
            'other_effects': '...',          # 마. 기타 유해 영향
            'raw_items': [...]               # 원본 데이터
        }
    """
    root = _call_api("chemdetail12", {
        "chemId": chem_id,
        "numOfRows": 100,
        "pageNo": 1
    })
    
    result = {
        "ecological_toxicity": {
            "fish": "",
            "daphnia": "",
            "algae": "",
            "other": ""
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
        
        if not detail or detail in ["자료없음", ""]:
            detail = "자료없음"
        
        # 원본 데이터 저장
        result["raw_items"].append({
            "name": name_kor,
            "detail": detail
        })
        
        # 항목별 파싱
        if "생태독성" in name_kor or "수생" in name_kor:
            if "어류" in name_kor or "fish" in name_kor.lower():
                result["ecological_toxicity"]["fish"] = detail
            elif "물벼룩" in name_kor or "daphnia" in name_kor.lower():
                result["ecological_toxicity"]["daphnia"] = detail
            elif "조류" in name_kor or "algae" in name_kor.lower():
                result["ecological_toxicity"]["algae"] = detail
            else:
                result["ecological_toxicity"]["other"] = detail
        elif "잔류" in name_kor or "분해" in name_kor:
            result["persistence"] = detail
        elif "농축" in name_kor or "생물농축" in name_kor:
            result["bioaccumulation"] = detail
        elif "토양" in name_kor and "이동" in name_kor:
            result["soil_mobility"] = detail
        elif "기타" in name_kor and "유해" in name_kor:
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
            'occupational_safety': {...},    # 가. 산업안전보건법
            'chemical_control': {...},       # 나. 화학물질관리법
            'chemical_registration': '...',  # 다. 화평법
            'hazardous_materials': '...',    # 라. 위험물안전관리법
            'waste_management': '...',       # 마. 폐기물관리법
            'other_regulations': '...',      # 바. 기타 국내 및 외국법
            'raw_items': [...]               # 원본 데이터
        }
    """
    root = _call_api("chemdetail15", {
        "chemId": chem_id,
        "numOfRows": 100,
        "pageNo": 1
    })
    
    result = {
        "occupational_safety": {
            "measurement": "X",      # 작업환경측정대상
            "health_check": "X",     # 특수건강진단대상
            "managed_hazard": "X",   # 관리대상유해물질
            "special_managed": "X",  # 특별관리물질
            "exposure_limit": "X",   # 노출기준설정물질
            "permission": "X",       # 허가대상물질
            "prohibited": "X",       # 제조금지물질
            "raw_text": ""
        },
        "chemical_control": {
            "toxic": "X",           # 유독물질
            "permitted": "X",       # 허가물질
            "restricted": "X",      # 제한물질
            "prohibited": "X",      # 금지물질
            "accident": "X",        # 사고대비물질
            "raw_text": ""
        },
        "chemical_registration": "",
        "hazardous_materials": "",
        "waste_management": "",
        "other_regulations": "",
        "raw_items": []
    }
    
    if root is None:
        return result
    
    items = root.findall(".//item")
    
    for item in items:
        name_kor = _get_text(item, "msdsItemNameKor")
        detail = _get_text(item, "itemDetail")
        
        if not detail or detail in ["자료없음", "해당없음", ""]:
            detail = "해당없음"
        
        # 원본 데이터 저장
        result["raw_items"].append({
            "name": name_kor,
            "detail": detail
        })
        
        # 항목별 파싱
        if "산업안전보건법" in name_kor:
            result["occupational_safety"]["raw_text"] = detail
            
            if "작업환경측정" in detail:
                result["occupational_safety"]["measurement"] = "O"
            if "특수건강진단" in detail or "건강진단" in detail:
                result["occupational_safety"]["health_check"] = "O"
            if "관리대상" in detail:
                result["occupational_safety"]["managed_hazard"] = "O"
            if "특별관리" in detail:
                result["occupational_safety"]["special_managed"] = "O"
            if "노출기준" in detail:
                result["occupational_safety"]["exposure_limit"] = "O"
            if "허가대상" in detail:
                result["occupational_safety"]["permission"] = "O"
            if "제조금지" in detail or "금지물질" in detail:
                result["occupational_safety"]["prohibited"] = "O"
                
        elif "화학물질관리법" in name_kor or "유해화학물질" in name_kor:
            result["chemical_control"]["raw_text"] = detail
            
            if "유독물질" in detail:
                result["chemical_control"]["toxic"] = "O"
            if "허가물질" in detail:
                result["chemical_control"]["permitted"] = "O"
            if "제한물질" in detail:
                result["chemical_control"]["restricted"] = "O"
            if "금지물질" in detail:
                result["chemical_control"]["prohibited"] = "O"
            if "사고대비" in detail:
                result["chemical_control"]["accident"] = "O"
                
        elif "등록" in name_kor and "평가" in name_kor:
            result["chemical_registration"] = detail
        elif "위험물" in name_kor:
            result["hazardous_materials"] = detail
        elif "폐기물" in name_kor:
            result["waste_management"] = detail
        elif "기타" in name_kor and ("국내" in name_kor or "외국" in name_kor):
            result["other_regulations"] = detail
    
    return result


# ============================================================
# 통합 조회 함수
# ============================================================
def get_msds_sections_11_12_15(cas_no: str) -> Dict[str, Any]:
    """
    CAS 번호로 MSDS 11, 12, 15번 항목 통합 조회
    
    Args:
        cas_no: CAS 번호
    
    Returns:
        통합된 MSDS 정보 딕셔너리
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
    name = search_result.get("chemNameKor", cas_no)
    
    # 2. 11번 항목 - 독성 정보
    time.sleep(DELAY)
    toxicity = get_toxicity_info(chem_id)
    
    # 3. 12번 항목 - 환경 영향
    time.sleep(DELAY)
    environmental = get_environmental_info(chem_id)
    
    # 4. 15번 항목 - 법적 규제
    time.sleep(DELAY)
    regulations = get_legal_regulations(chem_id)
    
    return {
        "success": True,
        "casNo": cas_no,
        "chemId": chem_id,
        "name": name,
        "keNo": search_result.get("keNo", ""),
        "section11_toxicity": toxicity,
        "section12_environmental": environmental,
        "section15_regulations": regulations
    }


def batch_query_sections(cas_list: List[str]) -> List[Dict[str, Any]]:
    """
    여러 CAS 번호 일괄 조회 (11, 12, 15번 항목)
    
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
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="KOSHA MSDS API 확장 조회 (11, 12, 15번 항목)")
    parser.add_argument("--cas", help="조회할 CAS 번호")
    parser.add_argument("--cas-list", help="조회할 CAS 번호 목록 (쉼표 구분)")
    parser.add_argument("--output", "-o", help="결과 저장 파일 (JSON)")
    
    args = parser.parse_args()
    
    results = []
    
    if args.cas:
        results = [get_msds_sections_11_12_15(args.cas)]
    elif args.cas_list:
        cas_list = [c.strip() for c in args.cas_list.split(",")]
        results = batch_query_sections(cas_list)
    else:
        parser.print_help()
        exit(1)
    
    # 출력
    output = json.dumps(results, ensure_ascii=False, indent=2)
    print(output)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n결과 저장: {args.output}")
