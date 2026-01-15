"""
KOSHA (한국산업안전보건공단) API 연동 모듈

이 모듈은 공공데이터포털(data.go.kr)에서 제공하는
한국산업안전보건공단 화학물질 정보 API를 연동합니다.

API 서비스:
- 화학물질정보 조회 서비스
- MSDS 물질정보 조회 서비스
"""

import requests
import os
import streamlit as st
from typing import Optional, Dict, List, Any
from urllib.parse import quote
import time


class KoshaApiClient:
    """KOSHA API 클라이언트"""

    # 공공데이터포털 KOSHA API 기본 URL
    BASE_URL = "http://apis.data.go.kr/B552468"

    # 서비스 엔드포인트
    ENDPOINTS = {
        # 화학물질 정보 조회
        'chemical_info': '/chemSearch/getChemSearchList',
        # 물질안전보건자료(MSDS) 정보 조회
        'msds_info': '/msdsSearch/getMsdsSearchList',
        # 규제물질 정보 조회
        'regulation_info': '/regulatedChem/getRegulatedChemList',
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        KOSHA API 클라이언트 초기화

        Args:
            api_key: 공공데이터포털에서 발급받은 API 키
                    환경변수 KOSHA_API_KEY로도 설정 가능
        """
        self.api_key = api_key or os.environ.get('KOSHA_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def set_api_key(self, api_key: str):
        """API 키 설정"""
        self.api_key = api_key

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        timeout: int = 10,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        API 요청 실행

        Args:
            endpoint: API 엔드포인트 경로
            params: 쿼리 파라미터
            timeout: 요청 타임아웃 (초)
            retries: 재시도 횟수

        Returns:
            API 응답 데이터
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'API 키가 설정되지 않았습니다. 공공데이터포털에서 API 키를 발급받아주세요.',
                'data': None
            }

        url = f"{self.BASE_URL}{endpoint}"
        params['serviceKey'] = self.api_key
        params['type'] = 'json'

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()

                data = response.json()
                return {
                    'success': True,
                    'error': None,
                    'data': data
                }

            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                return {
                    'success': False,
                    'error': 'API 요청 시간이 초과되었습니다. 나중에 다시 시도해주세요.',
                    'data': None
                }

            except requests.exceptions.ConnectionError:
                if attempt < retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                return {
                    'success': False,
                    'error': '네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.',
                    'data': None
                }

            except requests.exceptions.HTTPError as e:
                return {
                    'success': False,
                    'error': f'HTTP 오류가 발생했습니다: {e.response.status_code}',
                    'data': None
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': f'알 수 없는 오류가 발생했습니다: {str(e)}',
                    'data': None
                }

        return {
            'success': False,
            'error': '최대 재시도 횟수를 초과했습니다.',
            'data': None
        }

    def search_chemical_by_cas(self, cas_number: str) -> Dict[str, Any]:
        """
        CAS 번호로 화학물질 정보 조회

        Args:
            cas_number: CAS 등록번호 (예: "7732-18-5")

        Returns:
            화학물질 정보 딕셔너리
        """
        params = {
            'casNo': cas_number,
            'numOfRows': '10',
            'pageNo': '1'
        }

        return self._make_request(self.ENDPOINTS['chemical_info'], params)

    def search_chemical_by_name(self, name: str) -> Dict[str, Any]:
        """
        물질명으로 화학물질 정보 조회

        Args:
            name: 화학물질명 (한글 또는 영문)

        Returns:
            화학물질 정보 딕셔너리
        """
        params = {
            'chemNm': name,
            'numOfRows': '20',
            'pageNo': '1'
        }

        return self._make_request(self.ENDPOINTS['chemical_info'], params)

    def get_regulation_info(self, cas_number: str) -> Dict[str, Any]:
        """
        CAS 번호로 규제물질 정보 조회

        산업안전보건법, 화학물질관리법 등의 규제 해당 여부 조회

        Args:
            cas_number: CAS 등록번호

        Returns:
            규제물질 정보 딕셔너리
        """
        params = {
            'casNo': cas_number,
            'numOfRows': '10',
            'pageNo': '1'
        }

        return self._make_request(self.ENDPOINTS['regulation_info'], params)

    def get_msds_info(self, cas_number: str) -> Dict[str, Any]:
        """
        CAS 번호로 MSDS 정보 조회

        Args:
            cas_number: CAS 등록번호

        Returns:
            MSDS 정보 딕셔너리
        """
        params = {
            'casNo': cas_number,
            'numOfRows': '10',
            'pageNo': '1'
        }

        return self._make_request(self.ENDPOINTS['msds_info'], params)


def parse_regulation_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    규제물질 조회 결과를 파싱하여 사용하기 쉬운 형태로 변환

    Args:
        result: API 응답 결과

    Returns:
        파싱된 규제 정보 딕셔너리
    """
    parsed = {
        '산업안전보건법': {
            '작업환경측정대상물질': False,
            '관리대상유해물질': False,
            '특수건강진단대상물질': False,
            '노출기준설정물질': False,
            '허용기준설정물질': False,
            '허가대상물질': False,
            '제조금지물질': False,
        },
        '화학물질관리법': {
            '유독물질': False,
            '허가물질': False,
            '제한물질': False,
            '금지물질': False,
            '사고대비물질': False,
        },
        '물질정보': {},
        'raw_data': result
    }

    if not result.get('success') or not result.get('data'):
        return parsed

    try:
        data = result['data']

        # 응답 구조에 따라 데이터 추출
        items = []
        if 'response' in data:
            body = data.get('response', {}).get('body', {})
            items_data = body.get('items', {})
            if isinstance(items_data, dict):
                items = items_data.get('item', [])
            elif isinstance(items_data, list):
                items = items_data

        if isinstance(items, dict):
            items = [items]

        for item in items:
            # 산업안전보건법 관련 필드 매핑
            if item.get('wrkEnvMsrYn') == 'Y':
                parsed['산업안전보건법']['작업환경측정대상물질'] = True
            if item.get('mngTgtYn') == 'Y':
                parsed['산업안전보건법']['관리대상유해물질'] = True
            if item.get('spcHlthChkYn') == 'Y':
                parsed['산업안전보건법']['특수건강진단대상물질'] = True
            if item.get('expStdYn') == 'Y':
                parsed['산업안전보건법']['노출기준설정물질'] = True
            if item.get('prmStdYn') == 'Y':
                parsed['산업안전보건법']['허용기준설정물질'] = True
            if item.get('prmTgtYn') == 'Y':
                parsed['산업안전보건법']['허가대상물질'] = True
            if item.get('mfgPrhbtYn') == 'Y':
                parsed['산업안전보건법']['제조금지물질'] = True

            # 화학물질관리법 관련 필드 매핑
            if item.get('txcYn') == 'Y':
                parsed['화학물질관리법']['유독물질'] = True
            if item.get('prmYn') == 'Y':
                parsed['화학물질관리법']['허가물질'] = True
            if item.get('rstYn') == 'Y':
                parsed['화학물질관리법']['제한물질'] = True
            if item.get('prhbtYn') == 'Y':
                parsed['화학물질관리법']['금지물질'] = True
            if item.get('accdPrprdYn') == 'Y':
                parsed['화학물질관리법']['사고대비물질'] = True

            # 물질 기본 정보
            parsed['물질정보'] = {
                'CAS번호': item.get('casNo', ''),
                '물질명(한글)': item.get('chemNmKr', ''),
                '물질명(영문)': item.get('chemNmEn', ''),
                '분자식': item.get('molFormula', ''),
                '분자량': item.get('molWeight', ''),
            }

    except Exception as e:
        parsed['parse_error'] = str(e)

    return parsed


def get_demo_regulation_data(cas_number: str) -> Dict[str, Any]:
    """
    데모용 규제 정보 데이터 반환 (API 키가 없을 때 사용)

    일부 잘 알려진 화학물질에 대한 규제 정보를 반환합니다.
    """
    # 샘플 데이터 (실제 규제 정보와 다를 수 있음)
    demo_data = {
        # 메탄올
        '67-56-1': {
            '물질명': '메탄올 (Methanol)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당',
                '노출기준설정물질': '해당 (TWA 200ppm, STEL 250ppm)',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당 (함유량 25% 이상)',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당 (수량 5톤 이상)',
            }
        },
        # 아세톤
        '67-64-1': {
            '물질명': '아세톤 (Acetone)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당없음',
                '노출기준설정물질': '해당 (TWA 500ppm, STEL 750ppm)',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당없음',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
        # 톨루엔
        '108-88-3': {
            '물질명': '톨루엔 (Toluene)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당',
                '노출기준설정물질': '해당 (TWA 50ppm, STEL 150ppm)',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당 (함유량 1% 이상)',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
        # 벤젠
        '71-43-2': {
            '물질명': '벤젠 (Benzene)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당',
                '노출기준설정물질': '해당 (TWA 0.5ppm, STEL 2.5ppm)',
                '허용기준설정물질': '해당 (TWA 1ppm, STEL 5ppm)',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당 (함유량 0.5% 이상)',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
        # 물 (규제 대상 아님)
        '7732-18-5': {
            '물질명': '물 (Water)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당없음',
                '관리대상유해물질': '해당없음',
                '특수건강진단대상물질': '해당없음',
                '노출기준설정물질': '해당없음',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당없음',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
        # 에탄올
        '64-17-5': {
            '물질명': '에탄올 (Ethanol)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당없음',
                '노출기준설정물질': '해당 (TWA 1000ppm)',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당없음',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
        # 이소프로필알코올
        '67-63-0': {
            '물질명': '이소프로필알코올 (Isopropyl alcohol)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당없음',
                '노출기준설정물질': '해당 (TWA 200ppm, STEL 400ppm)',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당없음',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
        # 자일렌
        '1330-20-7': {
            '물질명': '자일렌 (Xylene)',
            '산업안전보건법': {
                '작업환경측정대상물질': '해당',
                '관리대상유해물질': '해당',
                '특수건강진단대상물질': '해당',
                '노출기준설정물질': '해당 (TWA 100ppm, STEL 150ppm)',
                '허용기준설정물질': '해당없음',
                '허가대상물질': '해당없음',
                '제조금지물질': '해당없음',
            },
            '화학물질관리법': {
                '유독물질': '해당 (함유량 1% 이상)',
                '허가물질': '해당없음',
                '제한물질': '해당없음',
                '금지물질': '해당없음',
                '사고대비물질': '해당없음',
            }
        },
    }

    if cas_number in demo_data:
        return {
            'success': True,
            'data': demo_data[cas_number],
            'source': 'demo'
        }

    return {
        'success': False,
        'error': f'CAS 번호 {cas_number}에 대한 데모 데이터가 없습니다.',
        'data': None
    }


# Streamlit 캐시를 활용한 API 호출
@st.cache_data(ttl=3600, show_spinner=False)
def cached_regulation_lookup(cas_number: str, api_key: str = "") -> Dict[str, Any]:
    """
    규제물질 정보를 캐싱하여 조회

    Args:
        cas_number: CAS 등록번호
        api_key: API 키 (옵션)

    Returns:
        규제물질 정보
    """
    # API 키가 있으면 실제 API 호출
    if api_key:
        client = KoshaApiClient(api_key)
        result = client.get_regulation_info(cas_number)
        if result['success']:
            return parse_regulation_result(result)

    # API 키가 없거나 호출 실패 시 데모 데이터 사용
    demo_result = get_demo_regulation_data(cas_number)
    if demo_result['success']:
        return demo_result['data']

    return {
        'error': '규제 정보를 찾을 수 없습니다.',
        'success': False
    }


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
    import re

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
