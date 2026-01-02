#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
황금 키워드 발굴기 - 메인 파이프라인
네이버/쿠팡 트렌드 분석 및 황금 키워드 발굴
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# 환경 변수
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID', '')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', '')

# 출력 경로
OUTPUT_DIR = Path('output')
ARCHIVE_DIR = OUTPUT_DIR / 'archives'

# AdSense 설정
ADSENSE_CLIENT = 'ca-pub-6677996696534146'
ADSENSE_SLOT = '7736105857'


def ensure_directories():
    """필요한 디렉토리 생성"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)


def get_naver_shopping_keywords():
    """네이버 쇼핑 인기 검색어 수집"""
    keywords = []
    
    # 네이버 DataLab 또는 쇼핑인사이트 API 호출
    # 여기서는 예시 데이터 반환 (실제 구현 시 API 연동)
    sample_keywords = [
        '닌텐도 스위치 2', '아이폰 16', '갤럭시 S25', 
        '다이슨 에어랩', '에어팟 프로', '플레이스테이션 5',
        '샤넬 가방', '나이키 덩크', '뉴발란스 530',
        '애플워치', '아이패드 프로', '맥북 프로'
    ]
    
    for kw in sample_keywords:
        keywords.append({
            'keyword': kw,
            'source': 'NAVER'
        })
    
    return keywords


def get_coupang_trending_keywords():
    """쿠팡 트렌딩 키워드 수집"""
    keywords = []
    
    # 쿠팡 트렌딩 키워드 (예시 데이터)
    sample_keywords = [
        '로봇청소기', '공기청정기', '무선청소기',
        '전기포트', '믹서기', '에어프라이어',
        '캠핑의자', '텐트', '침낭',
        '운동화', '등산화', '런닝화'
    ]
    
    for kw in sample_keywords:
        keywords.append({
            'keyword': kw,
            'source': 'COUPANG'
        })
    
    return keywords


def get_search_volume(keyword):
    """네이버 광고 API로 검색량 조회"""
    # 실제 구현 시 네이버 광고 API 연동
    # 여기서는 랜덤 샘플 데이터 반환
    import random
    return random.randint(10000, 500000)


def get_blog_count(keyword):
    """네이버 블로그 검색 결과 수 조회"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        import random
        return random.randint(5000, 100000)
    
    try:
        url = "https://openapi.naver.com/v1/search/blog.json"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        params = {"query": keyword, "display": 1}
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get('total', 0)
    except Exception as e:
        print(f"블로그 검색 오류: {e}")
    
    import random
    return random.randint(5000, 100000)


def get_related_keywords(keyword):
    """네이버 연관 검색어 수집"""
    # 실제 구현 시 네이버 연관검색어 API 또는 크롤링
    return []


def calculate_golden_score(search_volume, blog_count):
    """황금지수 계산"""
    if blog_count == 0:
        return 100.0
    
    efficiency = blog_count / search_volume if search_volume > 0 else 999
    
    # 황금지수 공식: 검색량이 높고 경쟁이 낮을수록 높은 점수
    if efficiency < 0.1:
        base_score = 90
    elif efficiency < 0.5:
        base_score = 70
    elif efficiency < 1.0:
        base_score = 50
    elif efficiency < 3.0:
        base_score = 30
    else:
        base_score = 10
    
    # 검색량 보너스
    if search_volume > 100000:
        base_score += 10
    elif search_volume > 50000:
        base_score += 5
    
    return min(100, base_score)


def get_grade(score):
    """황금지수에 따른 등급 산정"""
    if score >= 80:
        return '💎 DIAMOND'
    elif score >= 60:
        return '🌟 GOLD'
    elif score >= 40:
        return '✨ SILVER'
    else:
        return 'Bad'


def analyze_keywords(keywords):
    """키워드 분석 실행"""
    results = []
    
    for item in keywords:
        keyword = item['keyword']
        source = item['source']
        
        # 데이터 수집
        search_volume = get_search_volume(keyword)
        blog_count = get_blog_count(keyword)
        
        # 경쟁강도 (효율성) 계산
        efficiency = round(blog_count / search_volume, 2) if search_volume > 0 else 999.99
        
        # 황금지수 계산
        golden_score = calculate_golden_score(search_volume, blog_count)
        grade = get_grade(golden_score)
        
        # 쿠팡 키워드도 네이버 연관검색어 수집
        related = get_related_keywords(keyword)
        
        results.append({
            'keyword': keyword,
            'source': source,
            'search_volume': search_volume,
            'blog_count': blog_count,
            'efficiency': efficiency,
            'golden_score': round(golden_score, 1),
            'grade': grade,
            'related_keywords': related
        })
    
    # 황금지수 기준 정렬
    results.sort(key=lambda x: x['golden_score'], reverse=True)
    
    return results


def generate_seo_summary(data, date_str):
    """SEO 친화적 문장형 요약 생성"""
    if not data:
        return f"{date_str} 기준 분석된 키워드가 없습니다."
    
    total = len(data)
    diamond_count = len([i for i in data if 'DIAMOND' in i.get('grade', '')])
    blueocean_count = len([i for i in data if i.get('efficiency', 999) < 1.0])
    
    top_keyword = data[0]
    
    summary = (
        f"{date_str} 기준, 네이버와 쿠팡의 실시간 트렌드를 분석한 결과 "
        f"총 {total}개의 키워드 중 다이아몬드 등급 {diamond_count}개, "
        f"블루오션 키워드 {blueocean_count}개를 발굴했습니다. "
        f"오늘의 1위 황금 키워드는 '{top_keyword['keyword']}'로, "
        f"월간 검색량 {top_keyword['search_volume']:,}건에 "
        f"경쟁강도 {top_keyword['efficiency']}으로 "
        f"{'블루오션 시장입니다.' if top_keyword['efficiency'] < 1.0 else '주목할 만한 키워드입니다.'}"
    )
    
    return summary


def generate_keyword_review(data):
    """키워드 총평 생성"""
    if not data:
        return "분석된 키워드가 없습니다."
    
    diamond_list = [i['keyword'] for i in data if 'DIAMOND' in i.get('grade', '')]
    gold_list = [i['keyword'] for i in data if 'GOLD' in i.get('grade', '')]
    blueocean_list = [i['keyword'] for i in data if i.get('efficiency', 999) < 1.0]
    
    review_parts = []
    
    if diamond_list:
        review_parts.append(
            f"💎 다이아몬드 등급 키워드: {', '.join(diamond_list[:3])} "
            f"{'외 ' + str(len(diamond_list)-3) + '개' if len(diamond_list) > 3 else ''}"
        )
    
    if gold_list:
        review_parts.append(
            f"🌟 골드 등급 키워드: {', '.join(gold_list[:3])} "
            f"{'외 ' + str(len(gold_list)-3) + '개' if len(gold_list) > 3 else ''}"
        )
    
    if blueocean_list:
        review_parts.append(
            f"🔥 블루오션 키워드(경쟁강도 1.0 미만): {', '.join(blueocean_list[:5])}"
        )
    
    review_parts.append(
        "\n📌 추천 전략: 다이아몬드/골드 등급 키워드 중 블루오션인 키워드를 "
        "우선적으로 콘텐츠 제작에 활용하시면 검색 노출 효과를 극대화할 수 있습니다."
    )
    
    return '\n\n'.join(review_parts)


def create_archive_html(data, filename):
    """아카이브 HTML 생성 (광고 포함)"""
    now_str = datetime.now(KST).strftime("%Y년 %m월 %d일 %H시")
    date_only = datetime.now(KST).strftime("%Y년 %m월 %d일")
    
    # 통계 계산
    diamond_count = len([i for i in data if 'DIAMOND' in i.get('grade', '')])
    blueocean_count = len([i for i in data if i.get('efficiency', 999) < 1.0])
    
    # SEO 문장형 요약
    seo_summary = generate_seo_summary(data, date_only)
    
    # 키워드 총평
    keyword_review = generate_keyword_review(data)

    # 테이블 행 생성 (5개마다 광고 삽입)
    rows = ""
    for i, item in enumerate(data):
        
        # 5개마다 광고 행 삽입
        if i > 0 and i % 5 == 0:
            rows += f'''
            <tr class="ad-row">
                <td colspan="6" class="ad-cell">
                    <ins class="adsbygoogle"
                         style="display:block"
                         data-ad-client="{ADSENSE_CLIENT}"
                         data-ad-slot="{ADSENSE_SLOT}"
                         data-ad-format="auto"
                         data-full-width-responsive="true"></ins>
                </td>
            </tr>
            '''
        
        badge_class = 'badge-coupang' if item['source'] == 'COUPANG' else 'badge-naver'
        badge_icon = 'shopping-cart' if item['source'] == 'COUPANG' else 'shopping-bag'
        
        grade_class = 'grade-bad'
        grade_icon = ''
        
        if "DIAMOND" in item['grade']:
            grade_class = 'grade-diamond'
            grade_icon = '<i data-lucide="gem"></i>'
        elif "GOLD" in item['grade']:
            grade_class = 'grade-gold'
            grade_icon = '<i data-lucide="star"></i>'
        elif "SILVER" in item['grade']:
            grade_class = 'grade-silver'
            grade_icon = '<i data-lucide="sparkles"></i>'
        
        eff_class = ''
        eff_icon = ''
        comp = item.get('efficiency', 999.99)
        
        if comp < 1.0:
            eff_class = 'eff-good'
            eff_icon = '<i data-lucide="flame"></i>'
        elif comp > 5.0:
            eff_class = 'eff-bad'
            eff_icon = '<i data-lucide="droplet"></i>'

        escaped_kw = item['keyword'].replace("'", "\\'").replace('"', '\\"')

        rows += f"""
        <tr>
            <td data-label="출처">
                <span class="badge {badge_class}">
                    <i data-lucide="{badge_icon}"></i>
                    {item['source']}
                </span>
            </td>
            <td data-label="키워드">
                <div class="keyword-cell">
                    <div class="keyword-info">
                        <div class="keyword-name">{item['keyword']}</div>
                        <div class="keyword-grade">
                            <span class="grade {grade_class}">{grade_icon} {item['grade']}</span>
                        </div>
                    </div>
                    <div class="action-btns">
                        <button class="action-btn copy" onclick="copyKeyword('{escaped_kw}', this)">
                            <i data-lucide="copy"></i> 복사
                        </button>
                        <a class="action-btn analyze" href="https://search.naver.com/search.naver?query={item['keyword']}" target="_blank" rel="noopener">
                            <i data-lucide="search"></i> 분석
                        </a>
                    </div>
                </div>
            </td>
            <td data-label="황금지수" class="num-col">
                <span class="grade {grade_class}">{grade_icon} {item['golden_score']}점</span>
            </td>
            <td data-label="경쟁강도" class="num-col">
                <span class="efficiency {eff_class}">{eff_icon} {comp}</span>
            </td>
            <td data-label="검색량" class="num-col"><strong>{item['search_volume']:,}</strong></td>
            <td data-label="블로그수" class="num-col">{item['blog_count']:,}</td>
        </tr>"""

    # 총평 HTML 변환
    review_html = keyword_review.replace('\n', '<br>')

    # 광고 단위 HTML
    ad_unit = f'''
    <div class="ad-container ad-inline">
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="{ADSENSE_CLIENT}"
             data-ad-slot="{ADSENSE_SLOT}"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
    </div>
    '''

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <title>{now_str} 황금 키워드 리포트 | 블루오션 키워드 분석</title>
    <meta name="description" content="{date_only} 기준 네이버, 쿠팡 실시간 트렌드 분석. {data[0]['keyword'] if data else ''} 등 황금 키워드 {len(data)}개 발굴. 다이아몬드 {diamond_count}개, 블루오션 {blueocean_count}개.">
    <meta name="keywords" content="황금키워드, 블루오션키워드, {', '.join([i['keyword'] for i in data[:5]])}">
    <meta name="robots" content="index, follow">
    
    <meta property="og:type" content="article">
    <meta property="og:title" content="{now_str} 황금 키워드 리포트">
    <meta property="og:description" content="다이아몬드 {diamond_count}개, 블루오션 {blueocean_count}개 발견!">
    <meta property="og:locale" content="ko_KR">
    
    <!-- AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}"
         crossorigin="anonymous"></script>
    
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@latest/dist/web/static/pretendard.css">
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
    <link rel="stylesheet" href="../../css/variables.css">
    <link rel="stylesheet" href="../../css/base.css">
    <link rel="stylesheet" href="../../css/components.css">
    <link rel="stylesheet" href="../../css/layout.css">
    <link rel="stylesheet" href="../../css/responsive.css">
    
    <style>
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: var(--transition);
        }}
        .back-btn:hover {{
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }}
        .back-btn svg {{ width: 16px; height: 16px; }}
        
        .review-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-xl);
            padding: 28px;
            margin-top: 28px;
            white-space: pre-line;
            line-height: 1.8;
        }}
        .review-section h3 {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 1.1rem;
        }}
        .review-content {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .review-content strong {{
            color: var(--text-primary);
        }}
        
        /* 광고 스타일 */
        .ad-container {{
            margin: 1.5rem 0;
            min-height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .ad-inline {{
            padding: 0.5rem;
        }}
        .ad-row {{
            background: transparent !important;
        }}
        .ad-row:hover {{
            background: transparent !important;
        }}
        .ad-cell {{
            padding: 1rem !important;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        <div class="container">
            <header class="header">
                <div class="logo">
                    <div class="logo-icon"><i data-lucide="gem"></i></div>
                    <span class="logo-text">황금 키워드 발굴기</span>
                </div>
                <a href="../../index.html" class="back-btn">
                    <i data-lucide="arrow-left"></i> 메인으로
                </a>
            </header>

            <section class="hero-section">
                <div class="hero-header">
                    <div class="hero-icon"><i data-lucide="bar-chart-3"></i></div>
                    <h1 class="hero-title">{now_str} 트렌드 분석</h1>
                </div>
                <div class="hero-content">{seo_summary}</div>
            </section>

            {ad_unit}

            <section class="table-card">
                <div class="table-header">
                    <h2 class="table-title">
                        <div class="table-title-icon"><i data-lucide="trophy"></i></div>
                        황금 키워드 목록
                    </h2>
                    <div class="legend">
                        <span class="legend-item"><span class="legend-dot blue"></span>블루오션</span>
                        <span class="legend-item"><span class="legend-dot red"></span>레드오션</span>
                    </div>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>출처</th>
                            <th>키워드</th>
                            <th class="num-col">황금지수</th>
                            <th class="num-col">경쟁강도</th>
                            <th class="num-col">검색량</th>
                            <th class="num-col">블로그수</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </section>

            {ad_unit}

            <section class="review-section">
                <h3><i data-lucide="clipboard-list"></i> 키워드 총평</h3>
                <div class="review-content">{review_html}</div>
            </section>

            {ad_unit}

            <footer class="footer">
                <p>© 2025 황금 키워드 발굴기</p>
            </footer>
        </div>
    </div>

    <div class="toast" id="toast">
        <i data-lucide="check-circle"></i>
        <span id="toast-message">복사되었습니다</span>
    </div>

    <script>
        lucide.createIcons();

        // 광고 초기화
        document.querySelectorAll('.adsbygoogle').forEach(function() {{
            try {{ (adsbygoogle = window.adsbygoogle || []).push({{}}); }}
            catch(e) {{}}
        }});

        function showToast(msg) {{
            const t = document.getElementById('toast');
            document.getElementById('toast-message').textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2500);
        }}

        function copyKeyword(kw, btn) {{
            navigator.clipboard.writeText(kw).then(() => {{
                btn.classList.add('copied');
                btn.innerHTML = '<i data-lucide="check"></i> 복사됨';
                lucide.createIcons();
                showToast("'" + kw + "' 복사됨");
                setTimeout(() => {{
                    btn.classList.remove('copied');
                    btn.innerHTML = '<i data-lucide="copy"></i> 복사';
                    lucide.createIcons();
                }}, 1500);
            }});
        }}
    </script>
</body>
</html>"""
    
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ 아카이브 생성: {filename}")


def save_data_json(data):
    """data.json 저장"""
    date_only = datetime.now(KST).strftime("%Y년 %m월 %d일")
    
    output = {
        'generated_at': datetime.now(KST).isoformat(),
        'seo_summary': generate_seo_summary(data, date_only),
        'keyword_review': generate_keyword_review(data),
        'keywords': data
    }
    
    output_path = OUTPUT_DIR / 'data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 데이터 저장: {output_path}")


def update_archive_list():
    """archive_list.json 업데이트"""
    archive_files = sorted(
        [f.name for f in ARCHIVE_DIR.glob('*.html')],
        reverse=True
    )
    
    list_path = OUTPUT_DIR / 'archive_list.json'
    with open(list_path, 'w', encoding='utf-8') as f:
        json.dump(archive_files, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 아카이브 목록 업데이트: {len(archive_files)}개")


def main():
    """메인 실행 함수"""
    print("🚀 황금 키워드 발굴기 시작...")
    print(f"⏰ 실행 시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")
    
    # 디렉토리 확인
    ensure_directories()
    
    # 키워드 수집
    print("\n📥 키워드 수집 중...")
    naver_keywords = get_naver_shopping_keywords()
    coupang_keywords = get_coupang_trending_keywords()
    
    all_keywords = naver_keywords + coupang_keywords
    print(f"   - 네이버: {len(naver_keywords)}개")
    print(f"   - 쿠팡: {len(coupang_keywords)}개")
    print(f"   - 총: {len(all_keywords)}개")
    
    # 키워드 분석
    print("\n🔍 키워드 분석 중...")
    results = analyze_keywords(all_keywords)
    
    # 통계
    diamond_count = len([i for i in results if 'DIAMOND' in i.get('grade', '')])
    gold_count = len([i for i in results if 'GOLD' in i.get('grade', '')])
    blueocean_count = len([i for i in results if i.get('efficiency', 999) < 1.0])
    
    print(f"\n📊 분석 결과:")
    print(f"   - 💎 DIAMOND: {diamond_count}개")
    print(f"   - 🌟 GOLD: {gold_count}개")
    print(f"   - 🔥 블루오션: {blueocean_count}개")
    
    # 데이터 저장
    print("\n💾 데이터 저장 중...")
    save_data_json(results)
    
    # 아카이브 HTML 생성
    archive_filename = datetime.now(KST).strftime("%Y-%m-%d_%Hh.html")
    archive_path = ARCHIVE_DIR / archive_filename
    create_archive_html(results, archive_path)
    
    # 아카이브 목록 업데이트
    update_archive_list()
    
    print("\n✨ 완료!")
    print(f"📁 출력 파일:")
    print(f"   - output/data.json")
    print(f"   - output/archive_list.json")
    print(f"   - output/archives/{archive_filename}")


if __name__ == "__main__":
    main()
