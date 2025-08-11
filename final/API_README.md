# 토지 분석 AI 서비스 API v2.0

MSA 기반 토지 분석 서비스 - JSON API

## 주요 변경사항

- ✅ JSON 데이터 입력 지원
- ✅ 메인 페이지 입력 폼 제거 (MSA 아키텍처)
- ✅ RESTful API 엔드포인트
- ✅ 로딩 페이지 유지 (프론트엔드 연동용)
- ✅ 상태 모니터링 API
- ✅ 자동 API 문서 생성

## API 엔드포인트

### 1. 분석 시작
```http
POST /api/analyze
Content-Type: application/json

{
  "land_data": {
    "주소": "대구광역시 중구 동인동1가 2-1",
    "지목": "대",
    "용도지역": "중심상업지역",
    "용도지구": "지정되지않음",
    "토지이용상황": "업무용",
    "지형고저": "평지",
    "형상": "세로장방",
    "도로접면": "광대소각",
    "공시지가": 3735000
  }
}
```

**응답:**
```json
{
  "task_id": "uuid-string",
  "status": "processing",
  "message": "분석이 시작되었습니다."
}
```

### 2. 분석 상태 확인
```http
GET /api/status/{task_id}
```

**응답:**
```json
{
  "task_id": "uuid-string",
  "status": "processing|completed|error",
  "progress": 75,
  "message": "분석 진행 중...",
  "created_at": "2025-01-08T10:30:00"
}
```

### 3. 분석 결과 조회 (JSON)
```http
GET /api/result/{task_id}
```

**응답:**
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "land_data": { ... },
  "result": {
    "ai_analysis": "HTML 형식 분석 결과",
    "policies": [...],
    "analysis_date": "2025년 1월 8일",
    "markdown_report": "마크다운 보고서"
  }
}
```

### 4. 분석 결과 조회 (HTML)
```http
GET /result/{task_id}
```
완성된 HTML 보고서 반환

### 5. 로딩 페이지
```http
GET /loading/{task_id}
```
프론트엔드에서 사용할 로딩 페이지

### 6. 기타 API
- `GET /health` - 헬스 체크
- `GET /api/tasks` - 활성 작업 목록
- `GET /` - API 정보
- `GET /docs` - Swagger UI 문서
- `GET /redoc` - ReDoc 문서

## 사용법

### 1. 서버 시작
```bash
python run_server.py
# 또는
python fastapi_server.py
```

### 2. API 테스트
```bash
python test_json_api.py
```

### 3. 프론트엔드 연동 예시

```javascript
// 1. 분석 시작
const response = await fetch('/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    land_data: {
      "주소": "대구광역시 중구 동인동1가 2-1",
      "지목": "대",
      "용도지역": "중심상업지역",
      "용도지구": "지정되지않음",
      "토지이용상황": "업무용",
      "지형고저": "평지",
      "형상": "세로장방",
      "도로접면": "광대소각",
      "공시지가": 3735000
    }
  })
});

const { task_id } = await response.json();

// 2. 로딩 페이지 표시
window.open(`/loading/${task_id}`, '_blank');

// 3. 상태 모니터링
const checkStatus = async () => {
  const statusResponse = await fetch(`/api/status/${task_id}`);
  const status = await statusResponse.json();
  
  if (status.status === 'completed') {
    // 결과 페이지로 이동
    window.location.href = `/result/${task_id}`;
  } else if (status.status === 'error') {
    alert('분석 중 오류가 발생했습니다.');
  } else {
    // 계속 모니터링
    setTimeout(checkStatus, 2000);
  }
};

checkStatus();
```

## 데이터 형식

### 입력 데이터 (LandData)
- `주소` (string, required): 토지 주소
- `지목` (string, required): 토지 지목
- `용도지역` (string, required): 용도지역
- `용도지구` (string, optional): 용도지구 (기본값: "지정되지않음")
- `토지이용상황` (string, required): 토지이용상황
- `지형고저` (string, required): 지형고저
- `형상` (string, required): 토지 형상
- `도로접면` (string, required): 도로접면
- `공시지가` (integer, required): 공시지가

### 출력 데이터
- AI 분석 결과 (HTML 형식)
- 관련 정부 정책 목록
- 마크다운 보고서
- 완성된 HTML 보고서

## 개발 정보

- **Framework**: FastAPI
- **Python**: 3.8+
- **Dependencies**: fastapi, uvicorn, pydantic, jinja2
- **Architecture**: MSA (Microservice Architecture)
- **API Documentation**: Swagger UI, ReDoc

## 마이그레이션 가이드

기존 문자열 입력에서 JSON 입력으로 변경:

**Before (v1.0):**
```
'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', ...
```

**After (v2.0):**
```json
{
  "주소": "대구광역시 중구 동인동1가 2-1",
  "지목": "대",
  ...
}
```