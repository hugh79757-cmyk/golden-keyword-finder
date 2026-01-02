const CONFIG = {
    site: {
        title: '황금 키워드 발굴기',
        description: '검색량은 높고 경쟁은 낮은 블루오션 키워드를 실시간으로 발굴하세요!',
        url: window.location.href,
        image: 'https://golden-keyword-finder.pages.dev/assets/og-image.png'
    },
    api: {
        data: 'output/data.json',
        archiveList: 'output/archive_list.json',
        archivePath: 'output/archives/'
    },
    kakao: {
        appKey: 'YOUR_KAKAO_JAVASCRIPT_KEY',
        enabled: false
    },
    toastDuration: 3000,
    archiveLimit: 12
};

Object.freeze(CONFIG);
