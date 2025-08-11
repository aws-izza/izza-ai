#!/usr/bin/env python3
"""
JSON API 테스트 스크립트
"""

import requests
import json
import time
from typing import Dict, Any

# API 기본 URL
BASE_URL = "http://localhost:8000"

def test_json_api():
    """JSON API 테스트"""
    
    # 테스트 데이터
    test_data = {
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
    
    print("🧪 JSON API 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. 헬스 체크
        print("1️⃣ 헬스 체크...")
        health_response = requests.get(f"{BASE_URL}/health")
        print(f"   상태: {health_response.status_code}")
        print(f"   응답: {health_response.json()}")
        
        # 2. 분석 시작
        print("\n2️⃣ 분석 시작...")
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if analyze_response.status_code == 200:
            result = analyze_response.json()
            task_id = result["task_id"]
            print(f"   ✅ 분석 시작됨 - Task ID: {task_id}")
            
            # 3. 상태 모니터링
            print("\n3️⃣ 분석 상태 모니터링...")
            while True:
                status_response = requests.get(f"{BASE_URL}/api/status/{task_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   진행률: {status['progress']}% - {status['message']}")
                    
                    if status["status"] == "completed":
                        print("   ✅ 분석 완료!")
                        break
                    elif status["status"] == "error":
                        print(f"   ❌ 분석 오류: {status.get('error', 'Unknown error')}")
                        return
                    
                    time.sleep(2)
                else:
                    print(f"   ❌ 상태 확인 실패: {status_response.status_code}")
                    return
            
            # 4. 결과 조회
            print("\n4️⃣ 결과 조회...")
            result_response = requests.get(f"{BASE_URL}/api/result/{task_id}")
            if result_response.status_code == 200:
                result_data = result_response.json()
                print("   ✅ 결과 조회 성공!")
                print(f"   토지 주소: {result_data['land_data']['주소']}")
                print(f"   정책 개수: {len(result_data['result'].get('policies', []))}")
                print(f"   HTML 결과 URL: {BASE_URL}/result/{task_id}")
                print(f"   로딩 페이지 URL: {BASE_URL}/loading/{task_id}")
            else:
                print(f"   ❌ 결과 조회 실패: {result_response.status_code}")
                
        else:
            print(f"   ❌ 분석 시작 실패: {analyze_response.status_code}")
            print(f"   오류: {analyze_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print("   서버 시작: python fastapi_server.py")
    except Exception as e:
        print(f"❌ 테스트 오류: {str(e)}")

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    
    print("\n🔍 API 엔드포인트 테스트")
    print("=" * 50)
    
    endpoints = [
        ("GET", "/", "API 정보"),
        ("GET", "/health", "헬스 체크"),
        ("GET", "/api/tasks", "활성 작업 목록"),
        ("GET", "/docs", "API 문서")
    ]
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
                print(f"   {endpoint} ({description}): {response.status_code}")
        except Exception as e:
            print(f"   {endpoint} ({description}): 오류 - {str(e)}")

if __name__ == "__main__":
    print("🚀 토지 분석 JSON API 테스트")
    print("📍 서버 URL:", BASE_URL)
    print()
    
    # 기본 엔드포인트 테스트
    test_api_endpoints()
    
    # 전체 워크플로우 테스트
    test_json_api()
    
    print("\n✅ 테스트 완료!")