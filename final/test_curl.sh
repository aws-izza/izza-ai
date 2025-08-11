#!/bin/bash

# 토지 분석 API 테스트 스크립트 (curl)

BASE_URL="http://localhost:8000"

echo "🧪 토지 분석 JSON API 테스트 (curl)"
echo "=================================="

# 1. 헬스 체크
echo "1️⃣ 헬스 체크..."
curl -s "$BASE_URL/health" | jq '.'
echo ""

# 2. API 정보
echo "2️⃣ API 정보..."
curl -s "$BASE_URL/" | jq '.endpoints'
echo ""

# 3. 분석 시작
echo "3️⃣ 분석 시작..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
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
  }')

echo "$RESPONSE" | jq '.'

# Task ID 추출
TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')

if [ "$TASK_ID" != "null" ] && [ "$TASK_ID" != "" ]; then
    echo ""
    echo "4️⃣ 분석 상태 모니터링..."
    echo "Task ID: $TASK_ID"
    
    # 상태 확인 루프
    while true; do
        STATUS_RESPONSE=$(curl -s "$BASE_URL/api/status/$TASK_ID")
        STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
        PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress')
        MESSAGE=$(echo "$STATUS_RESPONSE" | jq -r '.message')
        
        echo "진행률: $PROGRESS% - $MESSAGE"
        
        if [ "$STATUS" = "completed" ]; then
            echo "✅ 분석 완료!"
            break
        elif [ "$STATUS" = "error" ]; then
            echo "❌ 분석 오류!"
            echo "$STATUS_RESPONSE" | jq '.error'
            exit 1
        fi
        
        sleep 2
    done
    
    echo ""
    echo "5️⃣ 결과 조회..."
    curl -s "$BASE_URL/api/result/$TASK_ID" | jq '.result | keys'
    
    echo ""
    echo "📄 HTML 결과: $BASE_URL/result/$TASK_ID"
    echo "⏳ 로딩 페이지: $BASE_URL/loading/$TASK_ID"
    
else
    echo "❌ 분석 시작 실패"
fi

echo ""
echo "✅ 테스트 완료!"