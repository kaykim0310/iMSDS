"""
화학물질 데이터 크롤링 모듈

데이터 소스:
1. PubChem API (무료, API 키 불필요)
2. KOSHA MSDS API (공공데이터포털 API 키 필요)
"""

import requests
import json
import time
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any, List
from urllib.parse import quote

# Streamlit secrets에서 API 키 로드 시도
def get_kosha_api_key() -> Optional[str]:
    """Streamlit secrets 또는 환경변수에서 KOSHA API 키 가져오기"""
    try:
        import streamlit as st
        return st.secrets.get("KOSHA_API_KEY")
    except Exception:
        pass

    try:
        import os
        return os.environ.get("KOSHA_API_KEY")
    except Exception:
        pass

    return None


class PubChemFetcher:
    """
    PubChem API를 통한 화학물질 정보 조회
    - 물리화학적 특성 (섹션 9)
    - 독성 정보 (섹션 11)
    - 환경 영향 (섹션 12)
    """

    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    VIEW_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MSDS-Manager/1.0 (Educational Purpose)'
        })

    def search_by_cas(self, cas_number: str) -> Optional[int]:
        """CAS 번호로 PubChem CID 검색"""
        try:
            url = f"{self.BASE_URL}/compound/name/{cas_number}/cids/JSON"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                cids = data.get('IdentifierList', {}).get('CID', [])
                return cids[0] if cids else None
        except Exception as e:
            print(f"CAS 검색 오류: {e}")
        return None

    def search_by_name(self, name: str) -> Optional[int]:
        """화학물질명으로 PubChem CID 검색"""
        try:
            url = f"{self.BASE_URL}/compound/name/{name}/cids/JSON"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                cids = data.get('IdentifierList', {}).get('CID', [])
                return cids[0] if cids else None
        except Exception as e:
            print(f"이름 검색 오류: {e}")
        return None

    def get_compound_properties(self, cid: int) -> Dict[str, Any]:
        """화합물의 물리화학적 특성 조회"""
        properties = [
            "MolecularFormula",
            "MolecularWeight",
            "XLogP",  # 옥탄올/물 분배계수
            "ExactMass",
            "MonoisotopicMass",
            "TPSA",  # 극성 표면적
            "Complexity",
            "Charge",
            "HBondDonorCount",
            "HBondAcceptorCount",
            "RotatableBondCount",
            "HeavyAtomCount",
            "IsotopeAtomCount",
            "AtomStereoCount",
            "DefinedAtomStereoCount",
            "UndefinedAtomStereoCount",
            "BondStereoCount",
            "DefinedBondStereoCount",
            "UndefinedBondStereoCount",
            "CovalentUnitCount",
            "Volume3D",
            "XStericQuadrupole3D",
            "YStericQuadrupole3D",
            "ZStericQuadrupole3D",
            "FeatureCount3D",
            "FeatureAcceptorCount3D",
            "FeatureDonorCount3D",
            "FeatureAnionCount3D",
            "FeatureCationCount3D",
            "FeatureRingCount3D",
            "FeatureHydrophobeCount3D",
            "ConformerModelRMSD3D",
            "EffectiveRotorCount3D",
            "ConformerCount3D"
        ]

        try:
            props_str = ",".join(properties)
            url = f"{self.BASE_URL}/compound/cid/{cid}/property/{props_str}/JSON"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                props = data.get('PropertyTable', {}).get('Properties', [{}])[0]
                return props
        except Exception as e:
            print(f"속성 조회 오류: {e}")
        return {}

    def get_full_record(self, cid: int) -> Dict[str, Any]:
        """화합물의 전체 상세 정보 조회 (PUG View API)"""
        try:
            url = f"{self.VIEW_URL}/{cid}/JSON"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"전체 기록 조회 오류: {e}")
        return {}

    def _extract_section_data(self, record: Dict, section_heading: str) -> List[Dict]:
        """레코드에서 특정 섹션 데이터 추출"""
        sections = []

        def search_sections(obj, target_heading):
            if isinstance(obj, dict):
                if obj.get('TOCHeading') == target_heading:
                    sections.append(obj)
                for value in obj.values():
                    search_sections(value, target_heading)
            elif isinstance(obj, list):
                for item in obj:
                    search_sections(item, target_heading)

        search_sections(record, section_heading)
        return sections

    def _extract_string_values(self, section: Dict) -> List[str]:
        """섹션에서 문자열 값들 추출"""
        values = []

        def extract_strings(obj):
            if isinstance(obj, dict):
                if 'String' in obj:
                    values.append(obj['String'])
                elif 'StringWithMarkup' in obj:
                    for item in obj['StringWithMarkup']:
                        if 'String' in item:
                            values.append(item['String'])
                for value in obj.values():
                    extract_strings(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item)

        extract_strings(section)
        return values

    def get_physical_properties(self, cid: int) -> Dict[str, str]:
        """
        섹션 9: 물리화학적 특성 데이터 조회
        """
        result = {
            '외관': '',
            '냄새': '',
            'pH': '',
            '녹는점': '',
            '끓는점': '',
            '인화점': '',
            '증기압': '',
            '용해도': '',
            '비중': '',
            '분자량': '',
            '옥탄올_물분배계수': '',
            '자연발화온도': '',
            '분해온도': '',
            '점도': ''
        }

        # 기본 속성 조회
        props = self.get_compound_properties(cid)
        if props:
            if 'MolecularWeight' in props:
                result['분자량'] = f"{props['MolecularWeight']} g/mol"
            if 'XLogP' in props:
                result['옥탄올_물분배계수'] = str(props['XLogP'])

        # 상세 레코드에서 추가 정보 추출
        record = self.get_full_record(cid)
        if record:
            # Experimental Properties 섹션 검색
            exp_sections = self._extract_section_data(record, 'Experimental Properties')
            for section in exp_sections:
                values = self._extract_string_values(section)
                # 값들을 파싱하여 적절한 필드에 매핑
                for value in values:
                    value_lower = value.lower()
                    if 'boiling' in value_lower or '끓는' in value_lower:
                        if not result['끓는점']:
                            result['끓는점'] = value
                    elif 'melting' in value_lower or '녹는' in value_lower:
                        if not result['녹는점']:
                            result['녹는점'] = value
                    elif 'flash point' in value_lower or '인화점' in value_lower:
                        if not result['인화점']:
                            result['인화점'] = value
                    elif 'density' in value_lower or 'specific gravity' in value_lower:
                        if not result['비중']:
                            result['비중'] = value
                    elif 'solubility' in value_lower or '용해' in value_lower:
                        if not result['용해도']:
                            result['용해도'] = value
                    elif 'vapor pressure' in value_lower or '증기압' in value_lower:
                        if not result['증기압']:
                            result['증기압'] = value
                    elif 'color' in value_lower or 'appearance' in value_lower:
                        if not result['외관']:
                            result['외관'] = value
                    elif 'odor' in value_lower or '냄새' in value_lower:
                        if not result['냄새']:
                            result['냄새'] = value

        return result

    def get_toxicity_data(self, cid: int) -> Dict[str, Any]:
        """
        섹션 11: 독성 정보 데이터 조회
        """
        result = {
            '급성독성': {
                '경구': '',
                '경피': '',
                '흡입': ''
            },
            '피부부식성_자극성': '',
            '심한눈손상_자극성': '',
            '호흡기과민성': '',
            '피부과민성': '',
            '생식세포변이원성': '',
            '발암성': '',
            '생식독성': '',
            '특정표적장기독성_1회': '',
            '특정표적장기독성_반복': '',
            '흡인유해성': '',
            '기타정보': []
        }

        record = self.get_full_record(cid)
        if record:
            # Toxicity 섹션 검색
            tox_sections = self._extract_section_data(record, 'Toxicity')

            for section in tox_sections:
                values = self._extract_string_values(section)

                for value in values:
                    value_lower = value.lower()
                    # LD50, LC50 값 파싱
                    if 'ld50' in value_lower:
                        if 'oral' in value_lower or '경구' in value_lower:
                            result['급성독성']['경구'] = value
                        elif 'dermal' in value_lower or '경피' in value_lower:
                            result['급성독성']['경피'] = value
                    elif 'lc50' in value_lower:
                        result['급성독성']['흡입'] = value
                    elif 'carcinogen' in value_lower or '발암' in value_lower:
                        result['발암성'] = value
                    elif 'mutagen' in value_lower or '변이원' in value_lower:
                        result['생식세포변이원성'] = value
                    elif 'irritat' in value_lower:
                        if 'skin' in value_lower or '피부' in value_lower:
                            result['피부부식성_자극성'] = value
                        elif 'eye' in value_lower or '눈' in value_lower:
                            result['심한눈손상_자극성'] = value
                    elif 'sensitiz' in value_lower or '과민' in value_lower:
                        if 'skin' in value_lower or '피부' in value_lower:
                            result['피부과민성'] = value
                        elif 'respiratory' in value_lower or '호흡' in value_lower:
                            result['호흡기과민성'] = value
                    else:
                        if len(value) > 10 and value not in result['기타정보']:
                            result['기타정보'].append(value)

            # GHS Classification 섹션도 검색
            ghs_sections = self._extract_section_data(record, 'GHS Classification')
            for section in ghs_sections:
                values = self._extract_string_values(section)
                for value in values:
                    if value not in result['기타정보'] and len(value) > 10:
                        result['기타정보'].append(value)

        return result

    def get_ecological_data(self, cid: int) -> Dict[str, Any]:
        """
        섹션 12: 환경에 미치는 영향 데이터 조회
        """
        result = {
            '수생생태독성': {
                '어류': '',
                '갑각류': '',
                '조류': ''
            },
            '잔류성_분해성': '',
            '생물농축성': '',
            '토양이동성': '',
            '기타유해영향': [],
            '오존층유해성': ''
        }

        record = self.get_full_record(cid)
        if record:
            # Ecological Information 섹션 검색
            eco_sections = self._extract_section_data(record, 'Ecological Information')

            for section in eco_sections:
                values = self._extract_string_values(section)

                for value in values:
                    value_lower = value.lower()
                    # 수생독성 데이터 파싱
                    if 'fish' in value_lower or '어류' in value_lower:
                        if 'lc50' in value_lower or 'ec50' in value_lower:
                            result['수생생태독성']['어류'] = value
                    elif 'daphnia' in value_lower or 'crustacea' in value_lower or '갑각' in value_lower:
                        if 'lc50' in value_lower or 'ec50' in value_lower:
                            result['수생생태독성']['갑각류'] = value
                    elif 'algae' in value_lower or '조류' in value_lower:
                        if 'ec50' in value_lower:
                            result['수생생태독성']['조류'] = value
                    elif 'biodegradation' in value_lower or '분해' in value_lower:
                        result['잔류성_분해성'] = value
                    elif 'bioaccumulation' in value_lower or 'bcf' in value_lower or '농축' in value_lower:
                        result['생물농축성'] = value
                    elif 'mobility' in value_lower or 'koc' in value_lower or '이동' in value_lower:
                        result['토양이동성'] = value
                    elif 'ozone' in value_lower or '오존' in value_lower:
                        result['오존층유해성'] = value
                    else:
                        if len(value) > 10 and value not in result['기타유해영향']:
                            result['기타유해영향'].append(value)

        return result

    def fetch_all_data(self, identifier: str, search_type: str = 'cas') -> Dict[str, Any]:
        """
        모든 섹션 데이터 한번에 조회

        Args:
            identifier: CAS 번호 또는 화학물질명
            search_type: 'cas' 또는 'name'

        Returns:
            물리화학적 특성, 독성 정보, 환경 영향 데이터
        """
        # CID 검색
        if search_type == 'cas':
            cid = self.search_by_cas(identifier)
        else:
            cid = self.search_by_name(identifier)

        if not cid:
            return {
                'success': False,
                'error': f'물질을 찾을 수 없습니다: {identifier}',
                'cid': None
            }

        # 각 섹션 데이터 조회
        return {
            'success': True,
            'cid': cid,
            'source': 'PubChem',
            'physical_properties': self.get_physical_properties(cid),
            'toxicity': self.get_toxicity_data(cid),
            'ecological': self.get_ecological_data(cid)
        }


class KoshaMSDSFetcher:
    """
    안전보건공단 MSDS API를 통한 화학물질 정보 조회
    공공데이터포털 API 키 필요: https://www.data.go.kr/data/15001197/openapi.do
    """

    BASE_URL = "http://apis.data.go.kr/B552468/msdsInfoService"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or get_kosha_api_key()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MSDS-Manager/1.0'
        })

    def set_api_key(self, api_key: str):
        """API 키 설정"""
        self.api_key = api_key

    def _parse_xml_response(self, xml_text: str) -> List[Dict]:
        """XML 응답을 파싱하여 딕셔너리 리스트로 변환"""
        results = []
        try:
            root = ET.fromstring(xml_text)

            # 에러 체크
            result_code = root.find('.//resultCode')
            if result_code is not None and result_code.text != '00':
                result_msg = root.find('.//resultMsg')
                print(f"KOSHA API 에러: {result_msg.text if result_msg is not None else 'Unknown error'}")
                return []

            # items 파싱
            items = root.findall('.//item')
            for item in items:
                item_dict = {}
                for child in item:
                    item_dict[child.tag] = child.text
                results.append(item_dict)

        except ET.ParseError as e:
            print(f"XML 파싱 오류: {e}")
        except Exception as e:
            print(f"응답 처리 오류: {e}")

        return results

    def search_by_cas(self, cas_number: str) -> List[Dict]:
        """CAS 번호로 MSDS 검색"""
        if not self.api_key:
            print("KOSHA API 키가 설정되지 않았습니다.")
            return []

        try:
            url = f"{self.BASE_URL}/getMsdsInfo"
            params = {
                'serviceKey': self.api_key,
                'casNo': cas_number,
                'numOfRows': 10,
                'pageNo': 1
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return self._parse_xml_response(response.text)
        except Exception as e:
            print(f"KOSHA API 오류: {e}")
        return []

    def search_by_name(self, name: str) -> List[Dict]:
        """화학물질명으로 MSDS 검색"""
        if not self.api_key:
            print("KOSHA API 키가 설정되지 않았습니다.")
            return []

        try:
            url = f"{self.BASE_URL}/getMsdsInfo"
            params = {
                'serviceKey': self.api_key,
                'chemNm': name,
                'numOfRows': 10,
                'pageNo': 1
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return self._parse_xml_response(response.text)
        except Exception as e:
            print(f"KOSHA API 오류: {e}")
        return []

    def get_msds_detail(self, msds_no: str) -> Dict[str, Any]:
        """MSDS 상세 정보 조회"""
        if not self.api_key:
            return {}

        try:
            url = f"{self.BASE_URL}/getMsdsDetailInfo"
            params = {
                'serviceKey': self.api_key,
                'msdsNo': msds_no
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                items = self._parse_xml_response(response.text)
                return items[0] if items else {}
        except Exception as e:
            print(f"KOSHA 상세 조회 오류: {e}")
        return {}

    def extract_physical_properties(self, detail: Dict) -> Dict[str, str]:
        """KOSHA 데이터에서 물리화학적 특성 추출"""
        result = {
            '외관': detail.get('appearance', ''),
            '냄새': detail.get('odor', ''),
            'pH': detail.get('ph', ''),
            '녹는점': detail.get('meltingPoint', ''),
            '끓는점': detail.get('boilingPoint', ''),
            '인화점': detail.get('flashPoint', ''),
            '증기압': detail.get('vaporPressure', ''),
            '용해도': detail.get('solubility', ''),
            '비중': detail.get('specificGravity', ''),
            '분자량': detail.get('molecularWeight', ''),
            '옥탄올_물분배계수': detail.get('partitionCoefficient', ''),
            '자연발화온도': detail.get('autoIgnitionTemp', ''),
            '분해온도': detail.get('decompositionTemp', ''),
            '점도': detail.get('viscosity', '')
        }
        return result

    def extract_toxicity_data(self, detail: Dict) -> Dict[str, Any]:
        """KOSHA 데이터에서 독성 정보 추출"""
        result = {
            '급성독성': {
                '경구': detail.get('acuteToxicityOral', ''),
                '경피': detail.get('acuteToxicityDermal', ''),
                '흡입': detail.get('acuteToxicityInhalation', '')
            },
            '피부부식성_자극성': detail.get('skinCorrosion', ''),
            '심한눈손상_자극성': detail.get('eyeDamage', ''),
            '호흡기과민성': detail.get('respiratorySensitization', ''),
            '피부과민성': detail.get('skinSensitization', ''),
            '생식세포변이원성': detail.get('germCellMutagenicity', ''),
            '발암성': detail.get('carcinogenicity', ''),
            '생식독성': detail.get('reproductiveToxicity', ''),
            '특정표적장기독성_1회': detail.get('stotSingle', ''),
            '특정표적장기독성_반복': detail.get('stotRepeated', ''),
            '흡인유해성': detail.get('aspirationHazard', ''),
            '기타정보': []
        }
        return result

    def extract_ecological_data(self, detail: Dict) -> Dict[str, Any]:
        """KOSHA 데이터에서 환경 영향 정보 추출"""
        result = {
            '수생생태독성': {
                '어류': detail.get('fishToxicity', ''),
                '갑각류': detail.get('crustaceanToxicity', ''),
                '조류': detail.get('algaeToxicity', '')
            },
            '잔류성_분해성': detail.get('persistence', ''),
            '생물농축성': detail.get('bioaccumulation', ''),
            '토양이동성': detail.get('soilMobility', ''),
            '기타유해영향': [],
            '오존층유해성': detail.get('ozoneDepletion', '')
        }
        return result


class ChemicalDataFetcher:
    """
    통합 화학물질 데이터 조회 클래스
    PubChem과 KOSHA API를 함께 사용
    """

    def __init__(self, kosha_api_key: str = None):
        self.pubchem = PubChemFetcher()
        self.kosha = KoshaMSDSFetcher(kosha_api_key)

    def fetch_data(self, identifier: str, search_type: str = 'cas',
                   prefer_kosha: bool = False) -> Dict[str, Any]:
        """
        화학물질 데이터 조회

        Args:
            identifier: CAS 번호 또는 화학물질명
            search_type: 'cas' 또는 'name'
            prefer_kosha: KOSHA 데이터 우선 사용 여부

        Returns:
            통합 데이터 결과
        """
        result = {
            'success': False,
            'source': None,
            'physical_properties': {},
            'toxicity': {},
            'ecological': {}
        }

        # KOSHA API 시도 (API 키가 있는 경우)
        if self.kosha.api_key:
            if search_type == 'cas':
                kosha_results = self.kosha.search_by_cas(identifier)
            else:
                kosha_results = self.kosha.search_by_name(identifier)

            if kosha_results:
                # 첫 번째 결과의 상세 정보 조회
                msds_no = kosha_results[0].get('msdsNo')
                if msds_no:
                    detail = self.kosha.get_msds_detail(msds_no)
                    if detail:
                        result['success'] = True
                        result['source'] = 'KOSHA'
                        result['physical_properties'] = self.kosha.extract_physical_properties(detail)
                        result['toxicity'] = self.kosha.extract_toxicity_data(detail)
                        result['ecological'] = self.kosha.extract_ecological_data(detail)

                        if prefer_kosha:
                            return result

        # PubChem에서 조회
        pubchem_result = self.pubchem.fetch_all_data(identifier, search_type)

        if pubchem_result.get('success'):
            if not result['success']:
                # KOSHA 데이터가 없으면 PubChem 사용
                result = pubchem_result
            else:
                # KOSHA 데이터가 있으면 빈 필드만 PubChem으로 보완
                for key in ['physical_properties', 'toxicity', 'ecological']:
                    if key in pubchem_result:
                        self._merge_data(result.get(key, {}), pubchem_result[key])
                result['source'] = 'KOSHA + PubChem'

        return result

    def _merge_data(self, target: Dict, source: Dict):
        """빈 필드만 source에서 target으로 병합"""
        for key, value in source.items():
            if key not in target or not target[key]:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                self._merge_data(target[key], value)

    def get_section9_data(self, identifier: str, search_type: str = 'cas') -> Dict[str, str]:
        """섹션 9 물리화학적 특성 데이터만 조회"""
        # 먼저 KOSHA 시도
        if self.kosha.api_key:
            if search_type == 'cas':
                kosha_results = self.kosha.search_by_cas(identifier)
            else:
                kosha_results = self.kosha.search_by_name(identifier)

            if kosha_results:
                msds_no = kosha_results[0].get('msdsNo')
                if msds_no:
                    detail = self.kosha.get_msds_detail(msds_no)
                    if detail:
                        return self.kosha.extract_physical_properties(detail)

        # PubChem fallback
        if search_type == 'cas':
            cid = self.pubchem.search_by_cas(identifier)
        else:
            cid = self.pubchem.search_by_name(identifier)

        if cid:
            return self.pubchem.get_physical_properties(cid)
        return {}

    def get_section11_data(self, identifier: str, search_type: str = 'cas') -> Dict[str, Any]:
        """섹션 11 독성 정보 데이터만 조회"""
        # 먼저 KOSHA 시도
        if self.kosha.api_key:
            if search_type == 'cas':
                kosha_results = self.kosha.search_by_cas(identifier)
            else:
                kosha_results = self.kosha.search_by_name(identifier)

            if kosha_results:
                msds_no = kosha_results[0].get('msdsNo')
                if msds_no:
                    detail = self.kosha.get_msds_detail(msds_no)
                    if detail:
                        return self.kosha.extract_toxicity_data(detail)

        # PubChem fallback
        if search_type == 'cas':
            cid = self.pubchem.search_by_cas(identifier)
        else:
            cid = self.pubchem.search_by_name(identifier)

        if cid:
            return self.pubchem.get_toxicity_data(cid)
        return {}

    def get_section12_data(self, identifier: str, search_type: str = 'cas') -> Dict[str, Any]:
        """섹션 12 환경 영향 데이터만 조회"""
        # 먼저 KOSHA 시도
        if self.kosha.api_key:
            if search_type == 'cas':
                kosha_results = self.kosha.search_by_cas(identifier)
            else:
                kosha_results = self.kosha.search_by_name(identifier)

            if kosha_results:
                msds_no = kosha_results[0].get('msdsNo')
                if msds_no:
                    detail = self.kosha.get_msds_detail(msds_no)
                    if detail:
                        return self.kosha.extract_ecological_data(detail)

        # PubChem fallback
        if search_type == 'cas':
            cid = self.pubchem.search_by_cas(identifier)
        else:
            cid = self.pubchem.search_by_name(identifier)

        if cid:
            return self.pubchem.get_ecological_data(cid)
        return {}


# 테스트용 코드
if __name__ == "__main__":
    fetcher = ChemicalDataFetcher()

    # 벤젠(CAS: 71-43-2) 테스트
    print("=== PubChem 테스트 ===")
    result = fetcher.fetch_data("71-43-2", "cas")
    print(json.dumps(result, indent=2, ensure_ascii=False))
