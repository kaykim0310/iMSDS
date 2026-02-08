#!/usr/bin/env python3
"""
국제 화학물질 독성/환경 데이터 조회 모듈 (PubChem PUG View 기반)
═══════════════════════════════════════════════════════════════════

MSDS 11번(독성)과 12번(환경) 항목에 필요한 **실제 동물실험 수치**를
PubChem에서 조회하여 출처와 함께 반환한다.

※ GHS 분류(구분1,2 등)는 MSDS 2번 항목용이므로 이 모듈에서 제외.
※ 이 모듈이 반환하는 데이터 예시:
   - 급성독성 (경구): LD50 = 5800 mg/kg (Rat) |출처: ChemIDplus
   - 어류 독성: LC50 = 8.3 mg/L (96hr, Rainbow trout) |출처: ECOTOX

인터페이스:
  search_substance(cas_no)       → 물질 검색
  get_toxicity_info(cas_no, ..)  → 독성 실험 데이터 (11번용)
  get_environmental_info(cas_no) → 환경 실험 데이터 (12번용)
"""

import requests
import json
import re
import time
from typing import Optional, Dict, List, Any

# ============================================================
# 설정
# ============================================================
TIMEOUT = 25
DELAY = 0.3
PUBCHEM_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUBCHEM_VIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"

HEADERS = {
    "User-Agent": "MSDS-Writer/1.0 (Chemical Safety Application)",
    "Accept": "application/json",
}


# ============================================================
# 유틸리티
# ============================================================
def _cas_to_cid(cas_no: str) -> Optional[int]:
    """CAS 번호 → PubChem CID"""
    try:
        url = f"{PUBCHEM_PUG}/compound/name/{cas_no}/cids/JSON"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            cids = resp.json().get("IdentifierList", {}).get("CID", [])
            return cids[0] if cids else None
    except Exception:
        pass
    return None


def _get_pug_view_full(cid: int, heading: str) -> dict:
    """PUG View에서 특정 헤딩의 전체 데이터(Reference 포함)를 가져온다."""
    try:
        url = f"{PUBCHEM_VIEW}/data/compound/{cid}/JSON"
        resp = requests.get(url, params={"heading": heading}, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def _build_ref_map(record: dict) -> Dict[int, str]:
    """
    Record의 Reference 배열에서 {ReferenceNumber: 출처명} 맵을 만든다.
    PubChem은 각 데이터에 ReferenceNumber를 달아서 출처를 추적할 수 있게 한다.
    """
    ref_map = {}
    for ref in record.get("Reference", []):
        ref_num = ref.get("ReferenceNumber", 0)
        source_name = ref.get("SourceName", "")
        source_id = ref.get("SourceID", "")
        name = ref.get("Name", "")
        
        # 출처명 결정 (우선순위: SourceName > Name)
        display = source_name or name or ""
        if source_id and source_id != display:
            display = f"{display}"
        
        if display:
            ref_map[ref_num] = display
    
    return ref_map


def _extract_data_with_refs(section: dict, ref_map: dict, depth: int = 0) -> List[Dict[str, str]]:
    """
    섹션에서 실험 데이터를 출처와 함께 추출한다.
    
    Returns:
        [{'name': '항목명', 'detail': '실험값', 'source': '출처명'}, ...]
    """
    results = []
    heading = section.get("TOCHeading", "")
    
    for info in section.get("Information", []):
        name = info.get("Name", "") or heading
        ref_num = info.get("ReferenceNumber", 0)
        source = ref_map.get(ref_num, "PubChem")
        
        val_obj = info.get("Value", {})
        
        # ── 문자열 값 추출 ──
        for swm in val_obj.get("StringWithMarkup", []):
            text = swm.get("String", "").strip()
            if text and len(text) > 2:
                # "Not available" 같은 무의미한 값 필터
                if text.lower() in ("not available", "n/a", "none", "not classified", "no data"):
                    continue
                results.append({"name": name, "detail": text, "source": source})
        
        # ── 숫자 값 추출 ──
        nums = val_obj.get("Number", [])
        unit = val_obj.get("Unit", "")
        if nums:
            num_str = ", ".join(str(n) for n in nums)
            if unit:
                num_str += f" {unit}"
            results.append({"name": name, "detail": num_str, "source": source})
    
    # 하위 섹션 재귀
    for sub in section.get("Section", []):
        results.extend(_extract_data_with_refs(sub, ref_map, depth + 1))
    
    return results


# ============================================================
# 물질 검색
# ============================================================
def search_substance(cas_no: str) -> Dict[str, Any]:
    """CAS 번호로 PubChem 물질 검색"""
    try:
        cid = _cas_to_cid(cas_no)
        if cid is None:
            return {"success": False, "error": f"PubChem에서 CAS {cas_no} 미등록", "cas_number": cas_no}
        
        # 기본 정보
        url = f"{PUBCHEM_PUG}/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight/JSON"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        name = cas_no
        if resp.status_code == 200:
            props = resp.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            name = props.get("IUPACName", cas_no)
        
        return {
            "success": True,
            "substance_id": str(cid),
            "name": name,
            "ec_number": "",
            "cas_number": cas_no,
            "source": "PubChem (NIH)"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "cas_number": cas_no}


# ============================================================
# 독성 정보 조회 (섹션 11용) - 실제 동물실험 수치 + 출처
# ============================================================
def get_toxicity_info(cas_no: str, substance_id: str = "") -> Dict[str, Any]:
    """
    PubChem에서 **실제 독성 실험 데이터**를 조회한다.
    
    가져오는 데이터:
      - Acute Effects: LD50(경구/경피), LC50(흡입) 등 실험값
      - Non-Human Toxicity Values: 추가 동물실험 독성값
      - Skin/Eye/Respiratory Irritations: 자극성 시험 결과
      - IARC Carcinogenicity Classifications: 발암성 등급
      - Reproductive Toxicity: 생식독성 시험
      - Genotoxicity: 변이원성 시험
    
    ※ GHS 분류(H-statement)는 가져오지 않음 (2번 항목용)
    
    Returns:
        {
            'raw_items': [
                {'name': '경구 급성독성', 'detail': 'LD50 = 5800 mg/kg (Rat)', 'source': 'ChemIDplus'},
                ...
            ],
            'error': ''
        }
    """
    result = {"raw_items": [], "error": ""}
    
    try:
        cid = int(substance_id) if substance_id else _cas_to_cid(cas_no)
        if not cid:
            result["error"] = f"PubChem에서 CAS {cas_no}을 찾을 수 없습니다."
            return result
        
        # ── Toxicological Information 전체 조회 ──
        time.sleep(DELAY)
        tox_full = _get_pug_view_full(cid, "Toxicological Information")
        
        if not tox_full:
            # 대체: Safety and Hazards 시도
            time.sleep(DELAY)
            tox_full = _get_pug_view_full(cid, "Safety and Hazards")
        
        if not tox_full:
            result["error"] = "PubChem에서 독성 데이터를 가져올 수 없습니다."
            return result
        
        record = tox_full.get("Record", {})
        ref_map = _build_ref_map(record)
        sections = record.get("Section", [])
        
        # ── 독성 관련 하위 섹션만 선별 추출 ──
        # PubChem 독성 섹션 구조:
        #   Toxicological Information
        #     ├─ Toxicity Summary
        #     ├─ Acute Effects (★ LD50/LC50)
        #     ├─ Non-Human Toxicity Values (★ 동물실험)
        #     ├─ Skin, Eye, and Respiratory Irritations (★ 자극성)
        #     ├─ IARC Carcinogenicity Classifications (★ 발암성)
        #     ├─ Reproductive Toxicity (★ 생식독성)
        #     ├─ Genotoxicity (★ 변이원성)
        #     ├─ Chronic Toxicity (★ 반복독성)
        #     └─ ...
        
        TARGET_HEADINGS_TOX = {
            # PubChem 헤딩명: (MSDS 독성 항목 매핑, 최대 추출 개수)
            "Acute Effects": ("급성독성", 10),
            "Non-Human Toxicity Values": ("급성독성", 10),
            "Non-Human Toxicity Excerpts": ("급성독성", 8),
            "Acute Toxicity": ("급성독성", 10),
            "Skin, Eye, and Respiratory Irritations": ("피부/눈 자극성", 8),
            "Skin Irritation": ("피부 부식성/자극성", 5),
            "Eye Irritation": ("심한 눈 손상/자극성", 5),
            "Respiratory Sensitization": ("호흡기 과민성", 5),
            "Skin Sensitization": ("피부 과민성", 5),
            "IARC Carcinogenicity Classifications": ("발암성", 5),
            "NTP Carcinogenicity Classifications": ("발암성", 5),
            "Carcinogenicity": ("발암성", 5),
            "Reproductive Toxicity": ("생식독성", 8),
            "Developmental Toxicity": ("생식독성", 5),
            "Genotoxicity": ("생식세포 변이원성", 8),
            "Mutagenicity": ("생식세포 변이원성", 5),
            "Chronic Toxicity": ("특정 표적장기 독성 (반복 노출)", 5),
            "Repeated Dose Toxicity": ("특정 표적장기 독성 (반복 노출)", 5),
            "Target Organ Toxicity": ("특정 표적장기 독성", 5),
            "Aspiration Hazard": ("흡인 유해성", 3),
            "Inhalation Risk": ("흡인 유해성", 3),
            "Toxicity Summary": ("독성 요약", 5),
            "Health Hazard": ("건강 유해성", 5),
        }
        
        def _process_section(sec, depth=0):
            heading = sec.get("TOCHeading", "")
            
            # 타겟 헤딩이면 데이터 추출
            for target_heading, (msds_name, max_items) in TARGET_HEADINGS_TOX.items():
                if target_heading.lower() in heading.lower():
                    items = _extract_data_with_refs(sec, ref_map)
                    
                    count = 0
                    for item in items:
                        if count >= max_items:
                            break
                        
                        detail = item["detail"]
                        source = item["source"]
                        
                        # 너무 짧거나 무의미한 값 스킵
                        if len(detail) < 5:
                            continue
                        
                        # 출처를 detail에 포함
                        detail_with_src = f"{detail} |출처: {source}" if source else detail
                        
                        # 항목명 결정: PubChem 원본 이름 + MSDS 매핑
                        item_name = item["name"] if item["name"] != heading else msds_name
                        
                        # LD50/LC50 같은 핵심 키워드가 있으면 더 구체적 이름
                        detail_lower = detail.lower()
                        if "ld50" in detail_lower:
                            if "oral" in detail_lower or "경구" in detail_lower:
                                item_name = "급성독성 (경구)"
                            elif "dermal" in detail_lower or "경피" in detail_lower:
                                item_name = "급성독성 (경피)"
                            elif "inhal" in detail_lower or "흡입" in detail_lower:
                                item_name = "급성독성 (흡입)"
                            else:
                                item_name = "급성독성"
                        elif "lc50" in detail_lower:
                            item_name = "급성독성 (흡입)"
                        
                        result["raw_items"].append({
                            "name": item_name,
                            "detail": detail_with_src[:400],
                            "source": source
                        })
                        count += 1
                    
                    return  # 이 섹션 처리 완료
            
            # 타겟이 아니면 하위 섹션 재귀
            for sub in sec.get("Section", []):
                _process_section(sub, depth + 1)
        
        for sec in sections:
            _process_section(sec)
        
        # ── 중복 제거 ──
        seen = set()
        unique_items = []
        for item in result["raw_items"]:
            key = item["detail"][:60]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        result["raw_items"] = unique_items
        
        if not result["raw_items"]:
            result["error"] = "PubChem에서 독성 실험 데이터를 찾을 수 없습니다."
    
    except Exception as e:
        result["error"] = f"PubChem 독성 조회 오류: {str(e)}"
    
    return result


# ============================================================
# 환경 정보 조회 (섹션 12용) - 실제 생태독성 수치 + 출처
# ============================================================
def get_environmental_info(cas_no: str, substance_id: str = "") -> Dict[str, Any]:
    """
    PubChem에서 **실제 환경독성 실험 데이터**를 조회한다.
    
    가져오는 데이터:
      - Ecotoxicity Values: 어류/갑각류/조류 LC50, EC50
      - Environmental Fate/Transport: 분해성, 잔류성
      - Bioconcentration Factor: BCF 값
      - Soil Adsorption/Mobility: Koc 값
      - Biodegradation: 생분해도
    
    Returns:
        {
            'raw_items': [
                {'name': '어류 독성', 'detail': 'LC50 = 8.3 mg/L (96hr, Rainbow trout)', 'source': 'ECOTOX'},
                ...
            ],
            'error': ''
        }
    """
    result = {"raw_items": [], "error": ""}
    
    try:
        cid = int(substance_id) if substance_id else _cas_to_cid(cas_no)
        if not cid:
            result["error"] = f"PubChem에서 CAS {cas_no}을 찾을 수 없습니다."
            return result
        
        # ── Ecological Information 조회 ──
        time.sleep(DELAY)
        eco_full = _get_pug_view_full(cid, "Ecological Information")
        
        if not eco_full:
            # 대체 시도
            time.sleep(DELAY)
            eco_full = _get_pug_view_full(cid, "Ecotoxicity")
        
        if not eco_full:
            result["error"] = "PubChem에서 환경 데이터를 가져올 수 없습니다."
            return result
        
        record = eco_full.get("Record", {})
        ref_map = _build_ref_map(record)
        sections = record.get("Section", [])
        
        TARGET_HEADINGS_ENV = {
            # PubChem 헤딩명: (MSDS 환경 항목 매핑, 최대 추출 개수)
            "Ecotoxicity Values": ("생태독성", 15),
            "Ecotoxicity Excerpts": ("생태독성", 10),
            "Ecotoxicity": ("생태독성", 10),
            "Non-Human Toxicity Values": ("생태독성", 5),
            "Fish Toxicity": ("생태독성 (어류)", 5),
            "Aquatic Toxicity": ("생태독성 (수생)", 8),
            "Environmental Biodegradation": ("잔류성 및 분해성", 8),
            "Biodegradation": ("잔류성 및 분해성", 5),
            "Abiotic Degradation": ("잔류성 및 분해성", 3),
            "Environmental Fate/Exposure Summary": ("잔류성 및 분해성", 5),
            "Environmental Fate": ("잔류성 및 분해성", 5),
            "Bioconcentration Factor": ("생물 농축성", 5),
            "Bioaccumulation": ("생물 농축성", 5),
            "Octanol/Water Partition Coefficient": ("생물 농축성", 3),
            "Soil Adsorption/Mobility": ("토양 이동성", 5),
            "Soil Adsorption Coefficient": ("토양 이동성", 3),
            "Mobility in Soil": ("토양 이동성", 3),
            "Atmospheric Fate": ("기타 유해 영향", 3),
            "Other Coverage": ("기타 유해 영향", 3),
        }
        
        def _process_section(sec, depth=0):
            heading = sec.get("TOCHeading", "")
            
            for target_heading, (msds_name, max_items) in TARGET_HEADINGS_ENV.items():
                if target_heading.lower() in heading.lower():
                    items = _extract_data_with_refs(sec, ref_map)
                    
                    count = 0
                    for item in items:
                        if count >= max_items:
                            break
                        
                        detail = item["detail"]
                        source = item["source"]
                        
                        if len(detail) < 5:
                            continue
                        
                        detail_with_src = f"{detail} |출처: {source}" if source else detail
                        
                        # 생태독성 세부 분류
                        item_name = item["name"] if item["name"] != heading else msds_name
                        detail_lower = detail.lower()
                        
                        if any(k in detail_lower for k in ["fish", "어류", "rainbow", "fathead", "bluegill", "oncorhynchus", "pimephales"]):
                            item_name = "생태독성 (어류)"
                        elif any(k in detail_lower for k in ["daphn", "갑각류", "crustacea", "mysid", "ceriodaphnia"]):
                            item_name = "생태독성 (갑각류)"
                        elif any(k in detail_lower for k in ["alga", "조류", "selenastrum", "desmodesmus", "pseudokirchneriella"]):
                            item_name = "생태독성 (조류)"
                        elif "bcf" in detail_lower or "bioconcentrat" in detail_lower:
                            item_name = "생물 농축성"
                        elif "koc" in detail_lower or "soil" in detail_lower or "adsorption" in detail_lower:
                            item_name = "토양 이동성"
                        elif any(k in detail_lower for k in ["biodeg", "bod", "cod", "half-life", "반감기"]):
                            item_name = "잔류성 및 분해성"
                        
                        result["raw_items"].append({
                            "name": item_name,
                            "detail": detail_with_src[:400],
                            "source": source
                        })
                        count += 1
                    
                    return
            
            for sub in sec.get("Section", []):
                _process_section(sub, depth + 1)
        
        for sec in sections:
            _process_section(sec)
        
        # 중복 제거
        seen = set()
        unique_items = []
        for item in result["raw_items"]:
            key = item["detail"][:60]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        result["raw_items"] = unique_items
        
        if not result["raw_items"]:
            result["error"] = "PubChem에서 환경 실험 데이터를 찾을 수 없습니다."
    
    except Exception as e:
        result["error"] = f"PubChem 환경 조회 오류: {str(e)}"
    
    return result


# ============================================================
# 통합 조회
# ============================================================
def get_substance_full_info(cas_no: str) -> Dict[str, Any]:
    """CAS 번호로 독성 + 환경 전체 조회"""
    search = search_substance(cas_no)
    sub_id = search.get("substance_id", "") if search.get("success") else ""
    
    time.sleep(DELAY)
    toxicity = get_toxicity_info(cas_no, sub_id)
    
    time.sleep(DELAY)
    environmental = get_environmental_info(cas_no, sub_id)
    
    return {
        "success": search.get("success", False),
        "cas_no": cas_no,
        "name": search.get("name", cas_no),
        "toxicity": toxicity,
        "environmental": environmental,
        "source": "PubChem (NIH)"
    }


# ============================================================
# CLI 테스트
# ============================================================
if __name__ == "__main__":
    import sys
    
    cas = sys.argv[1] if len(sys.argv) > 1 else "67-64-1"
    print(f"{'='*60}")
    print(f"  PubChem 독성/환경 데이터 조회: {cas}")
    print(f"{'='*60}\n")
    
    print("1️⃣  물질 검색...")
    s = search_substance(cas)
    if s["success"]:
        print(f"   ✅ CID: {s['substance_id']}, 이름: {s['name']}\n")
    else:
        print(f"   ❌ {s['error']}\n")
        sys.exit(1)
    
    sid = s["substance_id"]
    
    print("2️⃣  독성 실험 데이터 (MSDS 11번)...")
    tox = get_toxicity_info(cas, sid)
    if tox["raw_items"]:
        for item in tox["raw_items"]:
            print(f"   🔹 [{item['name']}] {item['detail'][:100]}")
    else:
        print(f"   ⚠️ {tox.get('error', '데이터 없음')}")
    
    print(f"\n3️⃣  환경 실험 데이터 (MSDS 12번)...")
    env = get_environmental_info(cas, sid)
    if env["raw_items"]:
        for item in env["raw_items"]:
            print(f"   🔹 [{item['name']}] {item['detail'][:100]}")
    else:
        print(f"   ⚠️ {env.get('error', '데이터 없음')}")
