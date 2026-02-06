#!/usr/bin/env python3
"""KOSHA API 진단 스크립트 - 독성정보가 왜 안 들어오는지 확인"""

import requests
import xml.etree.ElementTree as ET

API_KEY = "5002b52ede58ae3359d098a19d4e11ce7f88ffddc737233c2ebce75c033ff44a"
BASE_URL = "https://msds.kosha.or.kr/openapi/service/msdschem"
CAS_NO = "50-00-0"  # 포름알데히드

print(f"=== 1단계: CAS {CAS_NO} 검색 (chemlist) ===")
resp1 = requests.get(f"{BASE_URL}/chemlist", params={
    "serviceKey": API_KEY,
    "searchWrd": CAS_NO,
    "searchCnd": 1,
    "numOfRows": 10,
    "pageNo": 1
}, timeout=30)
print(f"Status: {resp1.status_code}")
print(f"Response:\n{resp1.text[:2000]}\n")

root1 = ET.fromstring(resp1.content)
items = root1.findall(".//item")
print(f"items 개수: {len(items)}")

if not items:
    print("ERROR: 검색 결과 없음")
    exit(1)

# chemId 추출
item = items[0]
chem_id = item.find("chemId")
chem_id_text = chem_id.text if chem_id is not None else "(없음)"
print(f"chemId: {chem_id_text}")

# 전체 item 태그 출력
print("\n--- item 태그 전체 ---")
for child in item:
    print(f"  <{child.tag}>{child.text}</{child.tag}>")

print(f"\n=== 2단계: chemdetail11 (chemId={chem_id_text}) ===")
resp2 = requests.get(f"{BASE_URL}/chemdetail11", params={
    "serviceKey": API_KEY,
    "chemId": chem_id_text,
    "numOfRows": 100,
    "pageNo": 1
}, timeout=30)
print(f"Status: {resp2.status_code}")
print(f"Response:\n{resp2.text[:3000]}\n")

root2 = ET.fromstring(resp2.content)
items2 = root2.findall(".//item")
print(f"items 개수: {len(items2)}")

if items2:
    print("\n--- 독성 항목들 ---")
    for i, it in enumerate(items2):
        print(f"\n[항목 {i+1}]")
        for child in it:
            print(f"  <{child.tag}>{child.text}</{child.tag}>")
else:
    print("\n⚠️ chemdetail11에서 item이 0개 반환됨!")
    print("전체 XML 태그 구조:")
    for elem in root2.iter():
        print(f"  <{elem.tag}> = {elem.text}")
