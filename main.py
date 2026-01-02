import os
import json
import requests
import time
import hmac
import hashlib
from datetime import datetime, timedelta

# 환경변수
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
COUPANG_ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

def get_header():
    if not NAVER_CLIENT_ID: return None
    return {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

def get_blog_count(keyword):
    """ 네이버 블로그 글 수 조회 """
    if not NAVER_CLIENT_ID: return 0
    url = "https://openapi.naver.com/v1/search/blog.json"
    try:
        time.sleep(0.05)
        # 정확도(sim)순으로 검색하여 관련도 체크
        res = requests.get(url, headers=get_header(), params={"query": keyword, "display": 1}, timeout=5)
        if res.status_code == 200:
            return res.json().get('total', 0)
    except:
        pass
    return 0

def get_naver_shopping():
    """ 네이버 쇼핑 인기 검색어 (3일 전 데이터) """
    print("🔎 네이버 수집 시작...")
    headers = get_header()
    if not headers: return []
    
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/rank"
    # 안전하게 3일 전 데이터 사용
    target_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    
    body = {
        "startDate": target_date, "endDate": target_date, "timeUnit": "date",
        "category": "50000003", "device": "", "gender": "", "ages": []
    }
    
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and data['data']:
                ranks = data['data'][0]['ranks'][:10]
                return [{"keyword": item['keyword'], "rank": item['rank'], "source": "NAVER"} for item in ranks]
    except Exception as e:
        print(f"네이버 에러: {e}")
    return []

def get_coupang_best():
    """ 쿠팡 골드박스 상품 """
    print("🔎 쿠팡 수집 시작...")
    if not COUPANG_ACCESS_KEY: return []

    url_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    # 서명 생성
    dt = datetime.utcnow().strftime('%y%m%d') + 'T' + datetime.utcnow().strftime('%H%M%S') + 'Z'
    msg = dt + "GET" + url_path
    sig = hmac.new(COUPANG_SECRET_KEY.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()
    auth = f"CEA algorithm=HmacSHA256, access-key={COUPANG_ACCESS_KEY}, signed-date={dt}, signature={sig}"

    try:
        res = requests.get(f"https://api-gateway.coupang.com{url_path}", headers={"Authorization": auth}, timeout=10)
        if res.status_code == 200:
            products = res.json().get('data', [])[:5]
            keywords = []
            for idx, p in enumerate(products):
                # 쿠팡 상품명은 너무 기니까 앞 2단어만 자름
                raw = p.get('productName', '')
                short_kw = ' '.join(raw.split()[:2])
                keywords.append({"keyword": short_kw, "rank": idx+1, "source": "COUPANG"})
            return keywords
    except Exception as e:
        print(f"쿠팡 에러: {e}")
    return []

def main():
    all_data = []
    all_data.extend(get_naver_shopping())
    all_data.extend(get_coupang_best())
    
    results = []
    for item in all_data:
        kw = item['keyword']
        src = item['source']
        rank = item['rank']
        
        blog_cnt = get_blog_count(kw)
        
        # 황금지수 로직 개선
        score = "Normal"
        if blog_cnt == 0: 
            # 블로그가 0개면 너무 구체적인 상품명일 확률이 높음 -> 검색해볼 가치 있음
            score = "🔍 확인필요"
        elif blog_cnt < 2000:
            score = "🌟 GOLD"
        elif blog_cnt < 10000:
            score = "✨ Silver"
            
        # 랭킹 텍스트
        rank_text = f"{rank}위"

        results.append({
            "source": src,      # 표에서 색깔 구분을 위해 추가
            "keyword": kw,
            "golden_score": score,
            "rank": rank_text,
            "blog_count": blog_cnt
        })

    # 저장
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
