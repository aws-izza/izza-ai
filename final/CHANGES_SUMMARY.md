# 토지 분석 서비스 리팩토링 완료

## 주요 변경사항

### ✅ JSON 데이터 입력 지원
- **Before**: 문자열 형식 `"'주소': '대구광역시...', '지목': '대'..."`
- **After**: JSON 객체 형식
```json
{
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
```

### ✅ MSA 아키텍처 전환
- 메인 페이지 입력 폼 제거
- RESTful API 엔드포인트 제공
- 프론트엔드와 백엔드 분리

### ✅ 새로운 API 엔드포인트

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/api/analyze` | POST | 토지 분석 시작 (JSON 입력) |
| `/api/status/{task_id}` | GET | 분석 상태 확인 |
| `/api/result/{task_id}` | GET | 분석 결과 JSON |
| `/result/{task_id}` | GET | 분석 결과 HTML |
| `/loading/{task_id}` | GET | 로딩 페이지 (프론트엔드용) |
| `/api/tasks` | GET | 활성 작업 목록 |
| `/health` | GET | 헬스 체크 |
| `/` | GET | API 정보 |

### ✅ 개선된 기능
- **Pydantic 모델**: 입력 데이터 검증
- **자동 API 문서**: Swagger UI (`/docs`), ReDoc (`/redoc`)
- **상태 모니터링**: 실시간 진행률 확인
- **오류 처리**: HTTP 상태 코드 기반 오류 처리
- **로딩 페이지 유지**: 기존 로딩 페이지 그대로 사용 가능

## 수정된 파일

### 1. `fastapi_server.py`
- Pydantic 모델 추가 (`LandData`, `AnalysisRequest`, `AnalysisResponse`)
- JSON API 엔드포인트 구현
- 메인 페이지 제거, API 정보 페이지로 대체
- HTTP 상태 코드 기반 오류 처리

### 2. `main_orchestrator.py`
- `run_land_analysis_inference()` 함수 개선
- JSON 딕셔너리와 문자열 모두 지원
- 하위 호환성 유지

### 3. `run_server.py`
- 시작 메시지 업데이트
- API 문서 URL 안내

## 새로 추가된 파일

### 1. `test_json_api.py`
- Python을 사용한 API 테스트 스크립트
- 전체 워크플로우 테스트 (분석 시작 → 상태 모니터링 → 결과 조회)

### 2. `test_curl.sh`
- curl을 사용한 API 테스트 스크립트
- 명령줄에서 간단한 테스트 가능

### 3. `API_README.md`
- 새로운 API 사용법 문서
- 엔드포인트 설명 및 예시
- 프론트엔드 연동 가이드

## 사용법

### 서버 시작
```bash
python run_server.py
# 또는
python fastapi_server.py
```

### API 테스트
```bash
# Python 테스트
python test_json_api.py

# curl 테스트
./test_curl.sh
```

### API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API 정보: http://localhost:8000

## 하위 호환성

- 기존 문자열 형식 입력도 내부적으로 지원
- 기존 템플릿 및 HTML 보고서 그대로 사용
- 로딩 페이지 URL 형식 동일 (`/loading/{task_id}`)

## 프론트엔드 연동

이제 프론트엔드에서 다음과 같이 사용할 수 있습니다:

1. **분석 시작**: `POST /api/analyze` (JSON 데이터)
2. **로딩 페이지 표시**: `/loading/{task_id}` 
3. **상태 모니터링**: `GET /api/status/{task_id}`
4. **결과 표시**: `/result/{task_id}` (HTML) 또는 `/api/result/{task_id}` (JSON)

## 다음 단계

- [ ] Redis를 사용한 작업 상태 저장소 구현
- [ ] 인증/권한 시스템 추가
- [ ] 로그 시스템 개선
- [ ] Docker 컨테이너화
- [ ] 부하 테스트 및 성능 최적화