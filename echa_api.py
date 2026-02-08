#!/usr/bin/env python3
"""
국제 화학물질 DB 조회 모듈 (PubChem 기반)
──────────────────────────────────────────
ECHA(유럽화학물질청)는 Cloudflare 봇 차단으로 API 접근 불가.
대안으로 미국 NIH PubChem API를 사용하여 동일한 데이터를 제공한다.

PubChem 데이터 출처:
  - GHS 분류 (EU CLP, 일본 NITE, 한국 NIER 등 국제 기관 통합)
  - REACH 등록 독성 데이터
  - EPA 생태독성 데이터
  - HSDB (Hazardous Substances Data Bank)

인터페이스는 기존 echa_api.py와 동일하므로
섹션 11, 12 코드 변경 불필요.

사용법:
  from echa_api import search_substance, get_toxicity_info, get_environmental_info
"""

import requests
import json
import re
import time
from typing import Optional, Dict, List, Any

# ============================================================
# 설정
# ============================================================
TIMEOUT = 20
DELAY = 0.25  # PubChem 권장: 초당 5회 이하
PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest"

HEADERS = {
    "User-Agent": "MSDS-Writer/1.0 (Streamlit App; Chemical Safety)",
    "Accept": "application/json",
}


# ============================================================
# CAS → PubChem CID 변환
# ============================================================
def _cas_to_cid(cas_no: str) -> Optional[int]:
    """CAS 번호로 PubChem CID를 찾는다."""
    try:
        url = f"{PUBCHEM_BASE}/pug/compound/name/{cas_no}/cids/JSON"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            return cids[0] if cids else None
    except Exception:
        pass
    return None


def _get_pug_view(cid: int, heading: str) -> dict:
    """PUG View API로 특정 섹션 데이터를 가져온다."""
    try:
        url = f"{PUBCHEM_BASE}/pug_view/data/compound/{cid}/JSON"
        params = {"heading": heading}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def _extract_strings(section: dict, depth: int = 0) -> List[Dict[str, str]]:
    """PUG View 섹션에서 이름-값 쌍을 재귀적으로 추출한다."""
    results = []
    heading = section.get("TOCHeading", "")

    # Information 블록에서 값 추출
    for info in section.get("Information", []):
        name = info.get("Name", heading)
        value_obj = info.get("Value", {})

        # StringWithMarkup
        for swm in value_obj.get("StringWithMarkup", []):
            text = swm.get("String", "").strip()
            if text:
                results.append({"name": name, "detail": text})

        # Number + Unit
        nums = value_obj.get("Number", [])
        unit = value_obj.get("Unit", "")
        if nums:
            num_str = ", ".join(str(n) for n in nums)
            if unit:
                num_str += f" {unit}"
            results.append({"name": name, "detail": num_str})

    # 하위 섹션 재귀
    for sub in section.get("Section", []):
        results.extend(_extract_strings(sub, depth + 1))

    return results


# ============================================================
# 물질 검색 (인터페이스 유지)
# ============================================================
def search_substance(cas_no: str) -> Dict[str, Any]:
    """
    CAS 번호로 PubChem에서 물질 검색.
    기존 ECHA 인터페이스와 동일한 반환 형식.
    """
    try:
        cid = _cas_to_cid(cas_no)
        if cid is None:
            return {"success": False, "error": f"PubChem에서 CAS {cas_no} 검색 실패", "cas_number": cas_no}

        # 기본 정보 조회
        url = f"{PUBCHEM_BASE}/pug/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight/JSON"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        name = cas_no
        mw = ""
        if resp.status_code == 200:
            props = resp.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            name = props.get("IUPACName", cas_no)
            mw = str(props.get("MolecularWeight", ""))

        return {
            "success": True,
            "substance_id": str(cid),
            "name": name,
            "ec_number": "",
            "cas_number": cas_no,
            "molecular_weight": mw,
            "source": "PubChem (NIH)"
        }

    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "PubChem 서버 연결 실패 (인터넷 연결 확인)", "cas_number": cas_no}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "PubChem 응답 시간 초과", "cas_number": cas_no}
    except Exception as e:
        return {"success": False, "error": f"PubChem 조회 오류: {str(e)}", "cas_number": cas_no}


# ============================================================
# H-statement → 독성 항목 매핑
# ============================================================
H_TOXICITY_MAP = {
    "H300": ("급성독성 (경구)", "구분 1 - 삼키면 치명적임"),
    "H301": ("급성독성 (경구)", "구분 3 - 삼키면 유독함"),
    "H302": ("급성독성 (경구)", "구분 4 - 삼키면 유해함"),
    "H304": ("흡인 유해성", "구분 1 - 삼켜서 기도로 유입되면 치명적일 수 있음"),
    "H310": ("급성독성 (경피)", "구분 1 - 피부와 접촉하면 치명적임"),
    "H311": ("급성독성 (경피)", "구분 3 - 피부와 접촉하면 유독함"),
    "H312": ("급성독성 (경피)", "구분 4 - 피부와 접촉하면 유해함"),
    "H314": ("피부 부식성", "구분 1 - 피부에 심한 화상과 눈에 손상을 일으킴"),
    "H315": ("피부 자극성", "구분 2 - 피부에 자극을 일으킴"),
    "H317": ("피부 과민성", "구분 1 - 알레르기성 피부 반응을 일으킬 수 있음"),
    "H318": ("심한 눈 손상", "구분 1 - 눈에 심한 손상을 일으킴"),
    "H319": ("눈 자극성", "구분 2A - 눈에 심한 자극을 일으킴"),
    "H330": ("급성독성 (흡입)", "구분 1 - 흡입하면 치명적임"),
    "H331": ("급성독성 (흡입)", "구분 3 - 흡입하면 유독함"),
    "H332": ("급성독성 (흡입)", "구분 4 - 흡입하면 유해함"),
    "H334": ("호흡기 과민성", "구분 1 - 흡입 시 알레르기성 반응, 천식 또는 호흡곤란"),
    "H335": ("특정 표적장기 독성 (1회 노출)", "구분 3 - 호흡기계 자극을 일으킬 수 있음"),
    "H336": ("특정 표적장기 독성 (1회 노출)", "구분 3 - 졸음 또는 현기증을 일으킬 수 있음"),
    "H340": ("생식세포 변이원성", "구분 1 - 유전적인 결함을 일으킬 수 있음"),
    "H341": ("생식세포 변이원성", "구분 2 - 유전적인 결함을 일으킬 것으로 의심됨"),
    "H350": ("발암성", "구분 1A - 암을 일으킬 수 있음"),
    "H351": ("발암성", "구분 2 - 암을 일으킬 것으로 의심됨"),
    "H360": ("생식독성", "구분 1 - 생식능력 또는 태아에 손상을 일으킬 수 있음"),
    "H361": ("생식독성", "구분 2 - 생식능력 또는 태아에 손상을 일으킬 것으로 의심됨"),
    "H362": ("생식독성", "수유 중인 아이에게 유해할 수 있음"),
    "H370": ("특정 표적장기 독성 (1회 노출)", "구분 1 - 장기에 손상을 일으킴"),
    "H371": ("특정 표적장기 독성 (1회 노출)", "구분 2 - 장기에 손상을 일으킬 수 있음"),
    "H372": ("특정 표적장기 독성 (반복 노출)", "구분 1 - 장기간/반복 노출 시 장기에 손상을 일으킴"),
    "H373": ("특정 표적장기 독성 (반복 노출)", "구분 2 - 장기간/반복 노출 시 장기에 손상을 일으킬 수 있음"),
}

H_ENVIRONMENT_MAP = {
    "H400": ("수생환경 유해성 (급성)", "구분 1 - 수생생물에 매우 유독함"),
    "H410": ("수생환경 유해성 (만성)", "구분 1 - 장기적 영향에 의해 수생생물에 매우 유독함"),
    "H411": ("수생환경 유해성 (만성)", "구분 2 - 장기적 영향에 의해 수생생물에 유독함"),
    "H412": ("수생환경 유해성 (만성)", "구분 3 - 장기적 영향에 의해 수생생물에 유해함"),
    "H413": ("수생환경 유해성 (만성)", "구분 4 - 장기적 영향에 의해 수생생물에 유해의 우려가 있음"),
    "H420": ("오존층 유해성", "구분 1 - 대기 상층의 오존층을 파괴하여 유해함"),
}


def _extract_h_statements(ghs_data: dict) -> List[str]:
    """GHS 분류 데이터에서 H-statement 코드를 추출한다."""
    h_codes = set()
    raw = json.dumps(ghs_data)
    # H코드 패턴 매칭 (H200~H499)
    for match in re.finditer(r'\b(H\d{3}[a-zA-Z]?)\b', raw):
        h_codes.add(match.group(1))
    return sorted(h_codes)


# ============================================================
# 독성 정보 조회 (섹션 11용)
# ============================================================
def get_toxicity_info(cas_no: str, substance_id: str = "") -> Dict[str, Any]:
    """
    PubChem에서 독성 정보 조회 (MSDS 11번 항목용)

    조회 순서:
    1. GHS Classification → H-statement에서 분류 추출
    2. Toxicity 섹션 → LD50, LC50, 자극성 등 상세 데이터
    3. Safety and Hazards → 추가 독성 정보

    Returns:
        {
            'raw_items': [{'name': ..., 'detail': ..., 'source': 'PubChem'}],
            'error': ''
        }
    """
    result = {"raw_items": [], "error": ""}

    try:
        # CID 확보
        cid = int(substance_id) if substance_id else _cas_to_cid(cas_no)
        if not cid:
            result["error"] = f"PubChem에서 CAS {cas_no}을 찾을 수 없습니다."
            return result

        # ── 1단계: GHS 분류에서 H-statement 추출 ──
        time.sleep(DELAY)
        ghs_data = _get_pug_view(cid, "GHS Classification")
        h_codes = _extract_h_statements(ghs_data)

        if h_codes:
            for hc in h_codes:
                if hc in H_TOXICITY_MAP:
                    name, detail = H_TOXICITY_MAP[hc]
                    result["raw_items"].append({
                        "name": name,
                        "detail": f"{detail} ({hc}) [GHS 분류]",
                        "source": "PubChem/GHS"
                    })

        # ── 2단계: Toxicity 섹션에서 상세 데이터 ──
        time.sleep(DELAY)
        tox_data = _get_pug_view(cid, "Toxicity")
        if tox_data:
            sections = tox_data.get("Record", {}).get("Section", [])
            for sec in sections:
                items = _extract_strings(sec)
                for item in items:
                    name = item["name"]
                    detail = item["detail"]

                    # 중복/불필요한 항목 필터
                    if len(detail) < 3:
                        continue
                    if detail.lower() in ("not available", "n/a", "none"):
                        continue

                    # 독성 관련 키워드 매칭
                    toxicity_keywords = [
                        "LD50", "LC50", "oral", "dermal", "inhalation",
                        "skin", "eye", "irritat", "sensitiz", "mutagen",
                        "carcino", "IARC", "NTP", "reproduct", "STOT",
                        "aspiration", "경구", "경피", "흡입", "피부", "눈",
                        "Acute Toxicity", "Acute Oral", "Acute Dermal",
                        "Acute Inhalation", "Skin Corrosion", "Eye",
                        "Respiratory", "Carcinogen", "Reproductive",
                        "Specific Target", "Aspiration"
                    ]

                    if any(kw.lower() in (name + " " + detail).lower() for kw in toxicity_keywords):
                        # 이미 GHS에서 추가된 항목과 중복 방지
                        if not any(detail[:30] in existing["detail"] for existing in result["raw_items"]):
                            result["raw_items"].append({
                                "name": name,
                                "detail": detail[:300],  # 너무 긴 텍스트 제한
                                "source": "PubChem"
                            })

        # ── 3단계: Safety and Hazards 추가 ──
        time.sleep(DELAY)
        safety_data = _get_pug_view(cid, "Safety and Hazards")
        if safety_data:
            sections = safety_data.get("Record", {}).get("Section", [])
            for sec in sections:
                heading = sec.get("TOCHeading", "")
                if any(k in heading for k in ["Toxicity", "Health", "IARC", "NTP"]):
                    items = _extract_strings(sec)
                    for item in items:
                        if len(item["detail"]) > 5:
                            if not any(item["detail"][:30] in ex["detail"] for ex in result["raw_items"]):
                                result["raw_items"].append({
                                    "name": item["name"],
                                    "detail": item["detail"][:300],
                                    "source": "PubChem"
                                })

        if not result["raw_items"]:
            result["error"] = "PubChem에서 독성 데이터를 찾을 수 없습니다."

    except Exception as e:
        result["error"] = f"PubChem 독성 조회 오류: {str(e)}"

    return result


# ============================================================
# 환경 정보 조회 (섹션 12용)
# ============================================================
def get_environmental_info(cas_no: str, substance_id: str = "") -> Dict[str, Any]:
    """
    PubChem에서 환경 영향 정보 조회 (MSDS 12번 항목용)

    조회 순서:
    1. GHS Classification → 환경 H-statement (H400~H420)
    2. Ecological Information → 생태독성, 분해성, 농축성

    Returns:
        {
            'raw_items': [{'name': ..., 'detail': ..., 'source': 'PubChem'}],
            'error': ''
        }
    """
    result = {"raw_items": [], "error": ""}

    try:
        cid = int(substance_id) if substance_id else _cas_to_cid(cas_no)
        if not cid:
            result["error"] = f"PubChem에서 CAS {cas_no}을 찾을 수 없습니다."
            return result

        # ── 1단계: GHS 분류에서 환경 H-statement ──
        time.sleep(DELAY)
        ghs_data = _get_pug_view(cid, "GHS Classification")
        h_codes = _extract_h_statements(ghs_data)

        if h_codes:
            for hc in h_codes:
                if hc in H_ENVIRONMENT_MAP:
                    name, detail = H_ENVIRONMENT_MAP[hc]
                    result["raw_items"].append({
                        "name": name,
                        "detail": f"{detail} ({hc}) [GHS 분류]",
                        "source": "PubChem/GHS"
                    })

        # ── 2단계: Ecological Information ──
        time.sleep(DELAY)
        eco_data = _get_pug_view(cid, "Ecological Information")
        if eco_data:
            sections = eco_data.get("Record", {}).get("Section", [])
            for sec in sections:
                items = _extract_strings(sec)
                for item in items:
                    detail = item["detail"]
                    if len(detail) < 3:
                        continue
                    if detail.lower() in ("not available", "n/a", "none"):
                        continue

                    eco_keywords = [
                        "LC50", "EC50", "IC50", "NOEC", "LOEC",
                        "fish", "daphn", "alga", "crustacea",
                        "biodeg", "BOD", "COD", "BCF", "Koc",
                        "log Kow", "log P", "bioconcentrat",
                        "persistence", "soil", "aquatic",
                        "어류", "갑각류", "조류", "생분해", "농축",
                        "Ecotoxicity", "Bioaccumulation", "Biodegradation",
                        "Environmental Fate", "Octanol", "Soil"
                    ]

                    if any(kw.lower() in (item["name"] + " " + detail).lower() for kw in eco_keywords):
                        if not any(detail[:30] in ex["detail"] for ex in result["raw_items"]):
                            result["raw_items"].append({
                                "name": item["name"],
                                "detail": detail[:300],
                                "source": "PubChem"
                            })

        # ── 3단계: Toxicity 섹션 중 생태독성 부분 ──
        time.sleep(DELAY)
        tox_data = _get_pug_view(cid, "Toxicity")
        if tox_data:
            sections = tox_data.get("Record", {}).get("Section", [])
            for sec in sections:
                heading = sec.get("TOCHeading", "")
                if any(k in heading.lower() for k in ["ecotox", "ecologic", "aquatic", "environment"]):
                    items = _extract_strings(sec)
                    for item in items:
                        if len(item["detail"]) > 5:
                            if not any(item["detail"][:30] in ex["detail"] for ex in result["raw_items"]):
                                result["raw_items"].append({
                                    "name": item["name"],
                                    "detail": item["detail"][:300],
                                    "source": "PubChem"
                                })

        if not result["raw_items"]:
            result["error"] = "PubChem에서 환경 데이터를 찾을 수 없습니다."

    except Exception as e:
        result["error"] = f"PubChem 환경 조회 오류: {str(e)}"

    return result


# ============================================================
# 통합 조회
# ============================================================
def get_substance_full_info(cas_no: str) -> Dict[str, Any]:
    """CAS 번호로 전체 정보 통합 조회"""
    search = search_substance(cas_no)
    sub_id = search.get("substance_id", "") if search.get("success") else ""

    time.sleep(DELAY)
    toxicity = get_toxicity_info(cas_no, sub_id)

    time.sleep(DELAY)
    environmental = get_environmental_info(cas_no, sub_id)

    return {
        "success": search.get("success", False) or bool(toxicity["raw_items"]) or bool(environmental["raw_items"]),
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
    print(f"=== PubChem 조회: {cas} ===\n")

    print("1. 물질 검색...")
    s = search_substance(cas)
    print(json.dumps(s, ensure_ascii=False, indent=2))

    if s.get("success"):
        sid = s["substance_id"]

        print("\n2. 독성 정보...")
        tox = get_toxicity_info(cas, sid)
        for item in tox["raw_items"]:
            print(f"  🔹 {item['name']}: {item['detail'][:80]}")
        if tox["error"]:
            print(f"  ⚠️ {tox['error']}")

        print(f"\n3. 환경 정보...")
        env = get_environmental_info(cas, sid)
        for item in env["raw_items"]:
            print(f"  🔹 {item['name']}: {item['detail'][:80]}")
        if env["error"]:
            print(f"  ⚠️ {env['error']}")
