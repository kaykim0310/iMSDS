#!/usr/bin/env python3
"""
국제 화학물질 독성/환경 데이터 조회 모듈 (PubChem PUG View 기반)
═══════════════════════════════════════════════════════════════════
MSDS 11번(독성)과 12번(환경) 항목에 필요한 **실제 동물실험 수치**를
PubChem에서 조회하여 출처와 함께 반환한다.

※ GHS 분류(구분1,2 등)는 MSDS 2번 항목용이므로 이 모듈에서 제외.
"""

import requests
import json
import re
import time
from typing import Optional, Dict, List, Any

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
    try:
        url = f"{PUBCHEM_VIEW}/data/compound/{cid}/JSON"
        resp = requests.get(url, params={"heading": heading}, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def _build_ref_map(record: dict) -> Dict[int, str]:
    ref_map = {}
    for ref in record.get("Reference", []):
        ref_num = ref.get("ReferenceNumber", 0)
        source_name = ref.get("SourceName", "") or ref.get("Name", "")
        if source_name:
            ref_map[ref_num] = source_name
    return ref_map


def _extract_leaf_data(section: dict, ref_map: dict) -> List[Dict[str, str]]:
    """현재 섹션의 Information 블록에서만 데이터 추출 (하위 재귀 안함)"""
    results = []
    heading = section.get("TOCHeading", "")
    for info in section.get("Information", []):
        name = info.get("Name", "") or heading
        ref_num = info.get("ReferenceNumber", 0)
        source = ref_map.get(ref_num, "PubChem")
        val_obj = info.get("Value", {})

        for swm in val_obj.get("StringWithMarkup", []):
            text = swm.get("String", "").strip()
            if text and len(text) > 3:
                if text.lower() not in ("not available", "n/a", "none", "not classified", "no data"):
                    results.append({"name": name, "detail": text, "source": source})

        nums = val_obj.get("Number", [])
        unit = val_obj.get("Unit", "")
        if nums:
            num_str = ", ".join(str(n) for n in nums)
            if unit:
                num_str += f" {unit}"
            results.append({"name": name, "detail": num_str, "source": source})
    return results


# ============================================================
# 물질 검색
# ============================================================
def search_substance(cas_no: str) -> Dict[str, Any]:
    try:
        cid = _cas_to_cid(cas_no)
        if cid is None:
            return {"success": False, "error": f"PubChem에서 CAS {cas_no} 미등록", "cas_number": cas_no}
        url = f"{PUBCHEM_PUG}/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight/JSON"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        name = cas_no
        if resp.status_code == 200:
            props = resp.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            name = props.get("IUPACName", cas_no)
        return {"success": True, "substance_id": str(cid), "name": name, "ec_number": "", "cas_number": cas_no, "source": "PubChem"}
    except Exception as e:
        return {"success": False, "error": str(e), "cas_number": cas_no}


# ============================================================
# 독성 정보 조회 (섹션 11용) - 실제 동물실험 수치 + 출처
# ============================================================

# PubChem 헤딩 → MSDS 항목명 매핑
_TOX_HEADING_MAP = {
    "acute effects": "급성독성",
    "non-human toxicity values": "급성독성",
    "non-human toxicity excerpts": "급성독성",
    "acute toxicity": "급성독성",
    "skin, eye, and respiratory irritations": "피부/눈/호흡기 자극성",
    "skin irritation": "피부 부식성/자극성",
    "eye irritation": "심한 눈 손상/자극성",
    "respiratory sensitization": "호흡기 과민성",
    "respiratory irritation": "호흡기 과민성",
    "skin sensitization": "피부 과민성",
    "iarc carcinogenicity classifications": "발암성",
    "ntp carcinogenicity classifications": "발암성",
    "carcinogenicity": "발암성",
    "carcinogen classification": "발암성",
    "reproductive toxicity": "생식독성",
    "developmental toxicity": "생식독성",
    "teratogenicity": "생식독성",
    "genotoxicity": "생식세포 변이원성",
    "mutagenicity": "생식세포 변이원성",
    "genetic toxicology": "생식세포 변이원성",
    "chronic toxicity": "특정 표적장기 독성 (반복 노출)",
    "repeated dose toxicity": "특정 표적장기 독성 (반복 노출)",
    "subchronic toxicity": "특정 표적장기 독성 (반복 노출)",
    "target organ toxicity": "특정 표적장기 독성",
    "aspiration hazard": "흡인 유해성",
    "inhalation risk": "흡인 유해성",
    "toxicity summary": "독성 요약",
    "health hazard": "건강 유해성",
    "hepatotoxicity": "특정 표적장기 독성 (반복 노출)",
    "neurotoxicity": "특정 표적장기 독성 (반복 노출)",
    "nephrotoxicity": "특정 표적장기 독성 (반복 노출)",
    "immunotoxicity": "특정 표적장기 독성 (반복 노출)",
}

MAX_PER_HEADING = 8


def _match_tox_heading(heading: str) -> Optional[str]:
    """PubChem 헤딩을 MSDS 항목명으로 매핑"""
    h = heading.lower().strip()
    # 정확 매칭 먼저
    if h in _TOX_HEADING_MAP:
        return _TOX_HEADING_MAP[h]
    # 부분 매칭
    for key, val in _TOX_HEADING_MAP.items():
        if key in h or h in key:
            return val
    return None


def _refine_tox_name(msds_name: str, detail: str) -> str:
    """LD50/LC50 등 키워드로 더 구체적 항목명 결정"""
    dl = detail.lower()
    if "ld50" in dl:
        if "oral" in dl: return "급성독성 (경구)"
        if "dermal" in dl: return "급성독성 (경피)"
        if "inhal" in dl: return "급성독성 (흡입)"
        return "급성독성 (경구)"
    if "lc50" in dl:
        return "급성독성 (흡입)"
    if "skin" in dl and "irrit" in dl: return "피부 부식성/자극성"
    if "eye" in dl and ("irrit" in dl or "damage" in dl): return "심한 눈 손상/자극성"
    if "skin" in dl and "sensit" in dl: return "피부 과민성"
    if "respiratory" in dl and "sensit" in dl: return "호흡기 과민성"
    return msds_name


def get_toxicity_info(cas_no: str, substance_id: str = "") -> Dict[str, Any]:
    """PubChem에서 실제 독성 실험 데이터를 조회한다."""
    result = {"raw_items": [], "error": ""}
    try:
        cid = int(substance_id) if substance_id else _cas_to_cid(cas_no)
        if not cid:
            result["error"] = f"PubChem에서 CAS {cas_no}을 찾을 수 없습니다."
            return result

        time.sleep(DELAY)
        tox_full = _get_pug_view_full(cid, "Toxicological Information")
        if not tox_full:
            time.sleep(DELAY)
            tox_full = _get_pug_view_full(cid, "Safety and Hazards")
        if not tox_full:
            result["error"] = "PubChem에서 독성 데이터를 가져올 수 없습니다."
            return result

        record = tox_full.get("Record", {})
        ref_map = _build_ref_map(record)
        heading_count = {}  # 헤딩별 추출 개수 제한

        def _walk_sections(sec, depth=0):
            """모든 섹션을 재귀 탐색하며, 매칭되는 헤딩의 데이터를 추출"""
            heading = sec.get("TOCHeading", "")
            msds_name = _match_tox_heading(heading)

            if msds_name:
                # 이 헤딩의 데이터 추출
                items = _extract_leaf_data(sec, ref_map)
                hkey = msds_name
                if hkey not in heading_count:
                    heading_count[hkey] = 0

                for item in items:
                    if heading_count[hkey] >= MAX_PER_HEADING:
                        break
                    detail = item["detail"]
                    if len(detail) < 5:
                        continue

                    source = item["source"]
                    detail_with_src = f"{detail} |출처: {source}" if source else detail
                    final_name = _refine_tox_name(msds_name, detail)

                    result["raw_items"].append({
                        "name": final_name,
                        "detail": detail_with_src[:400],
                        "source": source
                    })
                    heading_count[hkey] += 1

            # ★ 핵심 수정: 매칭 여부와 무관하게 항상 하위 섹션도 탐색
            for sub in sec.get("Section", []):
                _walk_sections(sub, depth + 1)

        for sec in record.get("Section", []):
            _walk_sections(sec)

        # 중복 제거
        seen = set()
        unique = []
        for item in result["raw_items"]:
            key = item["detail"][:60]
            if key not in seen:
                seen.add(key)
                unique.append(item)
        result["raw_items"] = unique

        if not result["raw_items"]:
            result["error"] = "PubChem에서 독성 실험 데이터를 찾을 수 없습니다."

    except Exception as e:
        result["error"] = f"PubChem 독성 조회 오류: {str(e)}"
    return result


# ============================================================
# 환경 정보 조회 (섹션 12용)
# ============================================================
_ENV_HEADING_MAP = {
    "ecotoxicity values": "생태독성",
    "ecotoxicity excerpts": "생태독성",
    "ecotoxicity": "생태독성",
    "fish toxicity": "생태독성 (어류)",
    "aquatic toxicity": "생태독성",
    "environmental biodegradation": "잔류성 및 분해성",
    "biodegradation": "잔류성 및 분해성",
    "abiotic degradation": "잔류성 및 분해성",
    "environmental fate/exposure summary": "잔류성 및 분해성",
    "environmental fate": "잔류성 및 분해성",
    "bioconcentration factor": "생물 농축성",
    "bioaccumulation": "생물 농축성",
    "octanol/water partition coefficient": "생물 농축성",
    "octanol-water partition coefficient": "생물 농축성",
    "soil adsorption/mobility": "토양 이동성",
    "soil adsorption coefficient": "토양 이동성",
    "mobility in soil": "토양 이동성",
    "atmospheric fate": "기타 유해 영향",
    "other environmental information": "기타 유해 영향",
}


def _match_env_heading(heading: str) -> Optional[str]:
    h = heading.lower().strip()
    if h in _ENV_HEADING_MAP:
        return _ENV_HEADING_MAP[h]
    for key, val in _ENV_HEADING_MAP.items():
        if key in h or h in key:
            return val
    return None


def _refine_env_name(msds_name: str, detail: str) -> str:
    dl = detail.lower()

    # ── 만성 수생독성 키워드 (NOEC, LOEC, chronic, 21d, 28d 등) ──
    is_chronic = any(k in dl for k in [
        "noec", "loec", "chronic", "long-term", "21 day", "28 day",
        "21d", "28d", "reproduction", "growth rate", "maturation"
    ])

    # ── 어류 ──
    if any(k in dl for k in ["fish", "rainbow", "fathead", "bluegill",
                              "oncorhynchus", "pimephales", "danio",
                              "oryzias", "lepomis", "salmo"]):
        return "만성 수생독성" if is_chronic else "급성 수생독성 (어류)"
    # ── 갑각류 ──
    if any(k in dl for k in ["daphn", "crustacea", "mysid", "ceriodaphnia",
                              "americamysis", "gammarus", "hyalella"]):
        return "만성 수생독성" if is_chronic else "급성 수생독성 (갑각류)"
    # ── 조류 ──
    if any(k in dl for k in ["alga", "selenastrum", "desmodesmus",
                              "pseudokirchneriella", "chlorella",
                              "scenedesmus", "skeletonema", "navicula"]):
        return "만성 수생독성" if is_chronic else "급성 수생독성 (조류)"
    # ── 수생 일반 (종 미분류) ──
    if any(k in dl for k in ["lc50", "ec50", "ic50", "aquatic"]):
        return "만성 수생독성" if is_chronic else "급성 수생독성"
    if is_chronic:
        return "만성 수생독성"

    if "bcf" in dl or "bioconcentrat" in dl:
        return "생물 농축성"
    if any(k in dl for k in ["koc", "soil adsorption"]):
        return "토양 이동성"
    if any(k in dl for k in ["biodeg", "bod", "cod", "half-life"]):
        return "잔류성 및 분해성"
    return msds_name


def get_environmental_info(cas_no: str, substance_id: str = "") -> Dict[str, Any]:
    """PubChem에서 실제 환경독성 실험 데이터를 조회한다."""
    result = {"raw_items": [], "error": ""}
    try:
        cid = int(substance_id) if substance_id else _cas_to_cid(cas_no)
        if not cid:
            result["error"] = f"PubChem에서 CAS {cas_no}을 찾을 수 없습니다."
            return result

        time.sleep(DELAY)
        eco_full = _get_pug_view_full(cid, "Ecological Information")
        if not eco_full:
            time.sleep(DELAY)
            eco_full = _get_pug_view_full(cid, "Ecotoxicity")
        if not eco_full:
            result["error"] = "PubChem에서 환경 데이터를 가져올 수 없습니다."
            return result

        record = eco_full.get("Record", {})
        ref_map = _build_ref_map(record)
        heading_count = {}

        def _walk_sections(sec, depth=0):
            heading = sec.get("TOCHeading", "")
            msds_name = _match_env_heading(heading)

            if msds_name:
                items = _extract_leaf_data(sec, ref_map)
                hkey = msds_name
                if hkey not in heading_count:
                    heading_count[hkey] = 0

                for item in items:
                    if heading_count[hkey] >= MAX_PER_HEADING:
                        break
                    detail = item["detail"]
                    if len(detail) < 5:
                        continue

                    source = item["source"]
                    detail_with_src = f"{detail} |출처: {source}" if source else detail
                    final_name = _refine_env_name(msds_name, detail)

                    result["raw_items"].append({
                        "name": final_name,
                        "detail": detail_with_src[:400],
                        "source": source
                    })
                    heading_count[hkey] += 1

            # ★ 항상 하위 탐색
            for sub in sec.get("Section", []):
                _walk_sections(sub, depth + 1)

        for sec in record.get("Section", []):
            _walk_sections(sec)

        seen = set()
        unique = []
        for item in result["raw_items"]:
            key = item["detail"][:60]
            if key not in seen:
                seen.add(key)
                unique.append(item)
        result["raw_items"] = unique

        if not result["raw_items"]:
            result["error"] = "PubChem에서 환경 실험 데이터를 찾을 수 없습니다."

    except Exception as e:
        result["error"] = f"PubChem 환경 조회 오류: {str(e)}"
    return result


# ============================================================
# 통합 조회
# ============================================================
def get_substance_full_info(cas_no: str) -> Dict[str, Any]:
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


if __name__ == "__main__":
    import sys
    cas = sys.argv[1] if len(sys.argv) > 1 else "67-64-1"
    print(f"{'='*60}")
    print(f"  PubChem 독성/환경 데이터 조회: {cas}")
    print(f"{'='*60}\n")

    s = search_substance(cas)
    if not s["success"]:
        print(f"❌ {s['error']}")
    else:
        print(f"✅ CID: {s['substance_id']}\n")
        sid = s["substance_id"]

        print("── 독성 (11번) ──")
        tox = get_toxicity_info(cas, sid)
        for item in tox["raw_items"]:
            print(f"  [{item['name']}] {item['detail'][:100]}")
        if tox["error"]: print(f"  ⚠️ {tox['error']}")

        print("\n── 환경 (12번) ──")
        env = get_environmental_info(cas, sid)
        for item in env["raw_items"]:
            print(f"  [{item['name']}] {item['detail'][:100]}")
        if env["error"]: print(f"  ⚠️ {env['error']}")
