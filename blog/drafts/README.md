# 📋 초안 검수 폴더

이 폴더는 AI가 자동 생성한 초안이 저장되는 곳입니다.
**직접 배포되지 않습니다.** 검수 후 `blog/posts/`로 이동해야 배포됩니다.

---

## 검수 순서 (5단계, 약 10분)

### 1. 사실 확인
- 인텔 보고서의 원문 링크를 클릭해서 실제 내용과 일치하는지 확인
- 날짜, 버전 번호, 이름 오류 체크

### 2. 제목·메타 확인
- 제목이 65자 이하인지
- 메타 디스크립션이 155자 이하인지
- 타겟 키워드가 제목에 포함됐는지

### 3. 내용 보완
- AI가 채운 배경 설명이 너무 generic하면 구체적 디테일 추가
- 코드 스니펫이 있다면 실제 실행 가능한지 확인

### 4. 발행 준비
- 파일을 `blog/posts/`로 이동
- `blog/index.html`에 포스트 카드 추가 (아래 템플릿 복붙)

```html
<article class="post-card" data-category="CATEGORY">
  <div class="post-card-meta">
    <span class="post-tag CATEGORY">CATEGORY_LABEL</span>
    <span class="post-date">YYYY-MM-DD</span>
  </div>
  <h2><a href="posts/SLUG.html">TITLE</a></h2>
  <p>META_DESCRIPTION</p>
</article>
```

### 5. 배포
- GitHub Desktop에서 커밋 + 푸시
- Cloudflare Pages가 30초 내 자동 배포

---

## 배포 후 (트래픽 확보)

포스트 발행 직후 아래 두 곳에 공유하세요.

**Reddit (영어):**
```
Title: [포스트 제목 그대로]
Body: 2-3줄 요약 + 링크
Subreddit: r/MachineLearning 또는 r/LocalLLaMA (Karpathy 관련) / r/ClaudeAI (Anthropic 관련)
```

**X 스레드:**
```
트윗 1: 핵심 인사이트 한 줄
트윗 2: 왜 중요한지 한 줄
트윗 3: 링크 + 관련 해시태그 (#AI #LLM #Karpathy 등)
```
