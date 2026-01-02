import os
import json
import requests
import time
from datetime import datetime, timedelta

def get_header():
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }

def get_blog_count(keyword):
    """
    해당 키워드의 네이버 블로그 총 문서 수를 조회합니다.
    """
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = get_header()
    params = {"query": keyword, "display": 1, "sort": "sim"}
    
    try:
        # API 호출 너무 빠르지 않게 살짝 대기
        time.sleep(0.1)
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            return res.json().get('total', 0)
        return 0
    except:
        return 0

def get_naver_shopping_keywords():
    """
    네이버 쇼핑인사이트 API (디지털/가전 - 50000003)
    """
    headers = get_header()
    if not headers["X-Naver-Client-Id"]:
        print("❌ API 키 없음")
        return []

    url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/rank"
    
    # 안전하게 2일 전 데이터 요청
    target_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    body = {
        "startDate": target_date,
        "endDate": target_date,
        "timeUnit": "date",
        "category": "50000003", 
        "device": "",
        "gender": "",
        "ages": []
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            data = response.json()
            # 데이터 구조가 복잡하므로 안전하게 파싱
            if 'data' in data and len(data['data']) > 0:
                ranks = data['data'][0]['ranks']
                return [{"keyword": item['keyword'], "rank": item['rank']} for item in ranks]
        
        print(f"⚠️ 쇼핑 API 응답 코드: {response.status_code} (데이터가 아직 없거나 파라미터 오류)")
        return []
            
    except Exception as e:
        print(f"❌ 쇼핑 API 에러: {e}")
        return []

def main():
    print("🚀 네이버 쇼핑 & 블로그 데이터 수집 시작...")
    
    # 1. 쇼핑 인기 키워드 가져오기
    keywords = get_naver_shopping_keywords()
    
    final_result = []

    if keywords:
        for item in keywords:
            kw = item['keyword']
            rank = item['rank']
            
            # 2. 블로그 문서 수 조회 (경쟁 강도)
            blog_cnt = get_blog_count(kw)
            
            # 3. 황금지수 계산 (임시 로직: 낮을수록 좋음 - 경쟁도)
            # 100위 안에 들면서 블로그 글이 적은 게 황금 키워드
            score = "Normal"
            if blog_cnt < 1000: score = "🌟 GOLD"
            elif blog_cnt < 5000: score = "✨ Silver"

            final_result.append({
                "keyword": kw,
                "golden_score": score,
                "search_volume": f"Top {rank}",
                "blog_count": blog_cnt
            })
    else:
        # 데이터가 없을 때
        final_result.append({
            "keyword": "집계 중 또는 에러",
            "golden_score": "-",
            "search_volume": "-",
            "blog_count": "-"
        })

    # 저장
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 완료. {len(final_result)}개 저장됨.")

if __name__ == "__main__":
    main()
