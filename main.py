import os
import json
import requests
import time
import hmac
import hashlib
from datetime import datetime, timedelta

# ---------------------------------------------------------
# [설정] 환경변수 로드
# ---------------------------------------------------------
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
COUPANG_ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

# ---------------------------------------------------------
# [기능 1] 네이버 로직
# ---------------------------------------------------------
def get_naver_headers():
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET: return None
    return {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

def get_blog_count(keyword):
    """ 네이버 블로그 문서 수 조회 (타임아웃 5초 적용) """
    if not NAVER_CLIENT_ID: return 0
    url = "https://openapi.naver.com/v1/search/blog.json"
    try:
        time.sleep(0.1) 
        # timeout=5 추가 (5초 안에 응답 안 오면 포기)
        res = requests.get(url, headers=get_naver_headers(), params={"query": keyword, "display": 1}, timeout=5)
        if res.status_code == 200:
            return res.json().get('total', 0)
    except Exception as e:
        print(f"블로그 조회 실패({keyword}): {e}")
        pass
    return 0

def get_naver_shopping_keywords():
    """ 네이버 쇼핑 인기검색어 """
    print("🔎 네이버 데이터 요청 중...")
    headers = get_naver_headers()
    if not headers: 
        print("⚠️ 네이버 키 없음")
        return []
    
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/rank"
    target_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    
    body = {
        "startDate": target_date, "endDate": target_date, "timeUnit": "date",
        "category": "50000003", "device": "", "gender": "", "ages": []
    }
    
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and data['data']:
                # 상위 10개만 가져오기 (시간 절약)
                ranks = data['data'][0]['ranks'][:10]
                return [{"keyword": item['keyword'], "source": "Naver", "rank": item['rank']} for item in ranks]
        else:
            print(f"네이버 API 에러 코드: {res.status_code}")
    except Exception as e:
        print(f"네이버 API 에러: {e}")
    return []

# ---------------------------------------------------------
# [기능 2] 쿠팡 로직
# ---------------------------------------------------------
def generate_coupang_signature(method, url):
    date_gmt = datetime.utcnow().strftime('%y%m%d') + 'T' + datetime.utcnow().strftime('%H%M%S') + 'Z'
    message = date_gmt + method + url
    signature = hmac.new(COUPANG_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={COUPANG_ACCESS_KEY}, signed-date={date_gmt}, signature={signature}"

def get_coupang_best_products():
    """ 쿠팡 골드박스 상품명 수집 """
    print("🔎 쿠팡 데이터 요청 중...")
    if not COUPANG_ACCESS_KEY or not COUPANG_SECRET_KEY:
        print("⚠️ 쿠팡 키 없음")
        return []

    url_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    full_url = f"https://api-gateway.coupang.com{url_path}"
    
    try:
        auth_header = generate_coupang_signature("GET", url_path)
        headers = { "Authorization": auth_header, "Content-Type": "application/json" }
        
        res = requests.get(full_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            products = data.get('data', [])
            keywords = []
            # 상위 5개만 추출
            for idx, p in enumerate(products[:5]): 
                raw_name = p.get('productName', '')
                short_keyword = ' '.join(raw_name.split()[:2]) 
                keywords.append({"keyword": short_keyword, "source": "Coupang", "rank": idx+1})
            return keywords
        else:
            print(f"쿠팡 API 에러 코드: {res.status_code}")
            return []
    except Exception as e:
        print(f"쿠팡 로직 에러: {e}")
        return []

# ---------------------------------------------------------
# [메인] 통합 실행
# ---------------------------------------------------------
def main():
    print("🚀 데이터 수집 시작...")
    start_time = time.time()
    
    all_keywords = []
    all_keywords.extend(get_naver_shopping_keywords())
    all_keywords.extend(get_coupang_best_products())
    
    final_result = []
    
    print(f"📊 총 {len(all_keywords)}개 키워드 분석 시작...")
    
    if not all_keywords:
         final_result.append({
            "keyword": "데이터 수집 실패",
            "golden_score": "-",
            "search_volume": "-",
            "blog_count": "-"
        })
    else:
        for item in all_keywords:
            kw = item['keyword']
            src = item['source']
            rank = item['rank']
            
            # 블로그 수 조회
            blog_cnt = get_blog_count(kw)
            
            # 황금지수 평가
            score = "Normal"
            if blog_cnt < 1000: score = "🌟 GOLD"
            elif blog_cnt < 5000: score = "✨ Silver"

            # 표시용 텍스트
            vol_text = f"Top {rank}"
            if src == "Coupang": vol_text = f"Best {rank} (CP)"
            else: vol_text = f"Rank {rank} (NV)"

            final_result.append({
                "keyword": kw,
                "golden_score": score,
                "search_volume": vol_text,
                "blog_count": blog_cnt
            })

    # 저장
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    print(f"✅ 완료. 총 소요시간: {elapsed:.2f}초")

if __name__ == "__main__":
    main()
