#!/usr/bin/env python3
"""
FastAPI 서버 실행 스크립트
"""

import os
import sys
from pathlib import Path


def main():
    print("토지 분석 AI 서비스 API 시작")
    print("=" * 50)
    
    # FastAPI 서버 실행
    import uvicorn
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()