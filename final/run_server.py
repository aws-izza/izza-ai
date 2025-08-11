#!/usr/bin/env python3
"""
FastAPI 서버 실행 스크립트
"""

import os
import sys
from pathlib import Path

def create_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "static/css",
        "static/js", 
        "templates",
        "reports"  # 생성된 보고서 저장용
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 디렉토리 생성: {directory}")

def check_dependencies():
    """의존성 확인"""
    required_modules = [
        "fastapi",
        "uvicorn", 
        "jinja2"
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} 모듈 확인됨")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} 모듈 없음")
    
    if missing_modules:
        print(f"\n⚠️ 누락된 모듈: {', '.join(missing_modules)}")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements_fastapi.txt")
        return False
    
    return True

def main():
    print("🚀 토지 분석 AI 서비스 API 시작 준비")
    print("=" * 50)
    
    # 디렉토리 생성
    create_directories()
    
    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    print("\n✅ 모든 준비가 완료되었습니다!")
    print("🌐 MSA JSON API 서버를 시작합니다...")
    print("📍 API 문서: http://localhost:8000/docs")
    print("📍 API 정보: http://localhost:8000")
    print("🧪 테스트: python test_json_api.py")
    print("=" * 50)
    
    # FastAPI 서버 실행
    import uvicorn
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()