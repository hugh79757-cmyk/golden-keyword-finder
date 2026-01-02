import os
import json
import requests
import time
from datetime import datetime, timedelta

def get_naver_shopping_keywords():
    """
    네이버 쇼핑인사이트 API를 통해 '디지털/가전' 분야의 오늘 인기 검색어를 가져옵니다.
    """
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ 오류: 네이버 API 키가 설정되지 않았습니다.")
        return []

    url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/rank"
    
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }

    # 어제 날짜 구하기 (API는 오늘 날짜 데이터가 아직 없을 수 있음)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 요청 데이터 (디지털/가전 카테고리 예시: 50000003)
    # 다른 카테고리 코드: 패션의류(50000000), 화장품/미용(50000002) 등
    body = {
        "startDate": yesterday,
        "endDate": yesterday,
        "timeUnit": "date",
        "category": "50000003", 
        "device": "",
        "gender": "",
        "ages": []
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        
        # 응답 확인
        if response.status_code == 200:
            data = response.json()
            # 데이터 파싱 (순위, 키워드 추출)
            ranks = data['data'][0]['ranks']
            
            keyword_list = []
            for item in ranks:
                keyword_list.append({
                    "keyword": item['keyword'],
                    "rank": item['rank']
                })
            return keyword_list
        else:
            print(f"❌ 네이버 API 호출 실패: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return []

def main():
    print("🚀 네이버 쇼핑 데이터 수집 시작...")
    
    # 1. 네이버 진짜 데이터 가져오기
    real_keywords = get_naver_shopping_keywords()
    
    final_result = []

    # 2. 가져온 키워드로 리포트 작성
    for item in real_keywords:
        # 현재는 '검색량/블로그수' API는 없으므로 이 부분은 
        # API가 추가되기 전까지는 '예상치'나 '순위'로 대체합니다.
        
        final_result.append({
            "keyword": item['keyword'],
            "golden_score": f"Rank {item['rank']}",  # 황금지수 대신 현재 순위 표시
            "search_volume": "Top 20",       # 쇼핑 베스트 20 안에 듦
            "blog_count": "-"                # 아직 블로그 검색 API 연결 전
        })

    # 데이터가 없을 경우 (API 에러 등)
    if not final_result:
        final_result.append({
            "keyword": "데이터 수집 실패",
            "golden_score": 0,
            "search_volume": 0,
            "blog_count": 0
        })

    # 3. 결과 저장
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 수집 완료: {len(final_result)}개 키워드 저장됨.")

if __name__ == "__main__":
    main()
