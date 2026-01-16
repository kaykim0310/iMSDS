import time
import json
import re
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import streamlit as st

class EChemPortalScraper:
    """eChemPortal에서 화학물질 정보를 크롤링하는 클래스"""
    
    def __init__(self):
        self.base_url = "https://www.echemportal.org/echemportal/"
        self.sources = []
        
    def _get_driver(self):
        """Selenium 웹드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Streamlit Cloud에서는 다른 설정이 필요할 수 있음
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except:
            st.error("Chrome 드라이버를 찾을 수 없습니다. 로컬 환경에서 실행해주세요.")
            return None
    
    def search_chemical(self, cas_number: str) -> List[Dict]:
        """CAS 번호로 화학물질 검색하고 가능한 소스 목록 반환"""
        driver = self._get_driver()
        if not driver:
            return []
        
        try:
            # eChemPortal 접속
            driver.get(self.base_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            # CAS 번호 입력 (실제 선택자는 사이트 확인 필요)
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "searchQuery"))
            )
            search_input.clear()
            search_input.send_keys(cas_number)
            
            # 검색 버튼 클릭
            search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            search_button.click()
            
            time.sleep(5)  # 검색 결과 로딩 대기
            
            # 검색 결과에서 가능한 소스 추출
            sources = []
            
            # 실제 선택자는 사이트 구조에 맞게 수정 필요
            source_elements = driver.find_elements(By.CSS_SELECTOR, ".result-item")
            
            for element in source_elements:
                try:
                    source_name = element.find_element(By.CSS_SELECTOR, ".source-name").text
                    source_link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    sources.append({
                        'name': source_name,
                        'url': source_link,
                        'cas_number': cas_number
                    })
                except:
                    continue
            
            self.sources = sources
            return sources
            
        except Exception as e:
            st.error(f"검색 중 오류 발생: {e}")
            return []
            
        finally:
            driver.quit()
    
    def extract_msds_data(self, source: Dict) -> Dict:
        """선택한 소스에서 MSDS 섹션 9, 11, 12 데이터 추출"""
        driver = self._get_driver()
        if not driver:
            return {}
        
        try:
            # 소스 페이지 접속
            driver.get(source['url'])
            time.sleep(3)
            
            # ECHA의 경우 동의 버튼 처리
            if 'echa' in source['url'].lower():
                try:
                    agree_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'I agree')]"))
                    )
                    agree_button.click()
                    time.sleep(3)
                except:
                    pass  # 동의 버튼이 없을 수도 있음
            
            # 페이지 소스를 BeautifulSoup으로 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 섹션별 데이터 추출
            data = {
                'section9': self._extract_section9(soup),
                'section11': self._extract_section11(soup),
                'section12': self._extract_section12(soup)
            }
            
            return data
            
        except Exception as e:
            st.error(f"데이터 추출 중 오류 발생: {e}")
            return {}
            
        finally:
            driver.quit()
    
    def _extract_section9(self, soup) -> Dict:
        """섹션 9: 물리화학적 특성 추출"""
        section9_data = {
            'appearance': {'value': '', 'unit': '', 'selectable': True},
            'odor': {'value': '', 'unit': '', 'selectable': True},
            'odor_threshold': {'value': '', 'unit': 'ppm', 'selectable': True},
            'ph': {'value': '', 'unit': '', 'selectable': True},
            'melting_point': {'value': '', 'unit': '°C', 'selectable': True},
            'boiling_point': {'value': '', 'unit': '°C', 'selectable': True},
            'flash_point': {'value': '', 'unit': '°C', 'selectable': True},
            'evaporation_rate': {'value': '', 'unit': '', 'selectable': True},
            'flammability': {'value': '', 'unit': '', 'selectable': True},
            'vapor_pressure': {'value': '', 'unit': 'mmHg', 'selectable': True},
            'vapor_density': {'value': '', 'unit': '', 'selectable': True},
            'specific_gravity': {'value': '', 'unit': '', 'selectable': True},
            'solubility': {'value': '', 'unit': 'g/L', 'selectable': True},
            'partition_coefficient': {'value': '', 'unit': '', 'selectable': True},
            'autoignition_temp': {'value': '', 'unit': '°C', 'selectable': True},
            'decomposition_temp': {'value': '', 'unit': '°C', 'selectable': True},
            'viscosity': {'value': '', 'unit': 'cP', 'selectable': True}
        }
        
        # 실제 크롤링 로직 (사이트 구조에 맞게 수정 필요)
        # 예시 패턴 - 실제 사이트 구조에 맞게 수정
        try:
            # 녹는점 찾기
            melting_elem = soup.find(text=re.compile(r'melting point', re.I))
            if melting_elem:
                value_text = melting_elem.find_next().text
                match = re.search(r'([-\d.]+)\s*°?C', value_text)
                if match:
                    section9_data['melting_point']['value'] = match.group(1)
            
            # 끓는점 찾기
            boiling_elem = soup.find(text=re.compile(r'boiling point', re.I))
            if boiling_elem:
                value_text = boiling_elem.find_next().text
                match = re.search(r'([-\d.]+)\s*°?C', value_text)
                if match:
                    section9_data['boiling_point']['value'] = match.group(1)
                    
        except Exception as e:
            st.warning(f"섹션 9 일부 데이터 추출 실패: {e}")
        
        return section9_data
    
    def _extract_section11(self, soup) -> Dict:
        """섹션 11: 독성에 관한 정보 추출"""
        section11_data = {
            'acute_toxicity_oral': {'value': '', 'unit': 'mg/kg', 'selectable': True},
            'acute_toxicity_dermal': {'value': '', 'unit': 'mg/kg', 'selectable': True},
            'acute_toxicity_inhalation': {'value': '', 'unit': 'mg/L', 'selectable': True},
            'skin_corrosion': {'value': '', 'unit': '', 'selectable': True},
            'eye_damage': {'value': '', 'unit': '', 'selectable': True},
            'respiratory_sensitization': {'value': '', 'unit': '', 'selectable': True},
            'skin_sensitization': {'value': '', 'unit': '', 'selectable': True},
            'germ_cell_mutagenicity': {'value': '', 'unit': '', 'selectable': True},
            'carcinogenicity': {'value': '', 'unit': '', 'selectable': True},
            'reproductive_toxicity': {'value': '', 'unit': '', 'selectable': True},
            'stot_single': {'value': '', 'unit': '', 'selectable': True},
            'stot_repeated': {'value': '', 'unit': '', 'selectable': True},
            'aspiration_hazard': {'value': '', 'unit': '', 'selectable': True}
        }
        
        # 실제 크롤링 로직
        try:
            # LD50/LC50 값 찾기
            ld50_oral = soup.find(text=re.compile(r'LD50.*oral', re.I))
            if ld50_oral:
                value_text = ld50_oral.find_next().text
                match = re.search(r'([\d.]+)\s*mg/kg', value_text)
                if match:
                    section11_data['acute_toxicity_oral']['value'] = match.group(1)
                    
        except Exception as e:
            st.warning(f"섹션 11 일부 데이터 추출 실패: {e}")
        
        return section11_data
    
    def _extract_section12(self, soup) -> Dict:
        """섹션 12: 환경에 미치는 영향 추출"""
        section12_data = {
            'aquatic_toxicity_fish': {'value': '', 'unit': 'mg/L', 'selectable': True},
            'aquatic_toxicity_daphnia': {'value': '', 'unit': 'mg/L', 'selectable': True},
            'aquatic_toxicity_algae': {'value': '', 'unit': 'mg/L', 'selectable': True},
            'persistence': {'value': '', 'unit': '', 'selectable': True},
            'bioaccumulation': {'value': '', 'unit': '', 'selectable': True},
            'mobility_in_soil': {'value': '', 'unit': '', 'selectable': True},
            'pbt_vpvb': {'value': '', 'unit': '', 'selectable': True},
            'other_adverse_effects': {'value': '', 'unit': '', 'selectable': True}
        }
        
        # 실제 크롤링 로직
        try:
            # LC50/EC50 값 찾기
            lc50_fish = soup.find(text=re.compile(r'LC50.*fish', re.I))
            if lc50_fish:
                value_text = lc50_fish.find_next().text
                match = re.search(r'([\d.]+)\s*mg/L', value_text)
                if match:
                    section12_data['aquatic_toxicity_fish']['value'] = match.group(1)
                    
        except Exception as e:
            st.warning(f"섹션 12 일부 데이터 추출 실패: {e}")
        
        return section12_data
    
    def _clean_value(self, value: str) -> str:
        """추출한 값 정제"""
        if not value:
            return ''
        # 불필요한 공백, 특수문자 제거
        value = value.strip()
        value = re.sub(r'\s+', ' ', value)
        return value


# Streamlit Cloud에서는 대안 방법 사용
def search_chemical_simple(cas_number: str) -> List[Dict]:
    """간단한 대체 검색 (API나 정적 데이터 사용)"""
    # 임시 데모 데이터
    demo_sources = [
        {
            'name': 'ECHA (European Chemicals Agency)',
            'url': f'https://echa.europa.eu/substance-information/-/substanceinfo/{cas_number}',
            'cas_number': cas_number
        },
        {
            'name': 'OECD eChemPortal',
            'url': f'https://www.echemportal.org/echemportal/search?query={cas_number}',
            'cas_number': cas_number
        }
    ]
    
    return demo_sources

def extract_msds_data_simple(source: Dict) -> Dict:
    """간단한 데모 데이터 반환"""
    # 실제로는 API나 데이터베이스에서 가져와야 함
    demo_data = {
        'section9': {
            'melting_point': {'value': '5.5', 'unit': '°C', 'selectable': True},
            'boiling_point': {'value': '80.1', 'unit': '°C', 'selectable': True},
            'flash_point': {'value': '-11', 'unit': '°C', 'selectable': True},
        },
        'section11': {
            'acute_toxicity_oral': {'value': '930', 'unit': 'mg/kg', 'selectable': True},
            'carcinogenicity': {'value': 'IARC Group 1', 'unit': '', 'selectable': True},
        },
        'section12': {
            'aquatic_toxicity_fish': {'value': '5.3', 'unit': 'mg/L', 'selectable': True},
            'bioaccumulation': {'value': 'BCF = 13.1', 'unit': '', 'selectable': True},
        }
    }
    
    return demo_data

# 실제 사용 함수 (환경에 따라 선택)
def search_chemical_sync(cas_number: str) -> List[Dict]:
    """동기 방식으로 화학물질 검색"""
    try:
        scraper = EChemPortalScraper()
        return scraper.search_chemical(cas_number)
    except:
        # Selenium이 실패하면 간단한 방법 사용
        st.info("로컬 크롤링이 불가능하여 대체 방법을 사용합니다.")
        return search_chemical_simple(cas_number)

def extract_msds_data_sync(source: Dict) -> Dict:
    """동기 방식으로 MSDS 데이터 추출"""
    try:
        scraper = EChemPortalScraper()
        return scraper.extract_msds_data(source)
    except:
        # Selenium이 실패하면 데모 데이터 사용
        st.info("실제 데이터 추출이 불가능하여 데모 데이터를 표시합니다.")
        return extract_msds_data_simple(source)