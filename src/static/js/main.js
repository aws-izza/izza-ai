// 토지 분석 AI 서비스 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 폼 제출 시 로딩 상태 표시
    const form = document.querySelector('.analysis-form');
    const submitBtn = document.querySelector('.submit-btn');
    
    if (form && submitBtn) {
        form.addEventListener('submit', function(e) {
            // 버튼 비활성화 및 로딩 표시
            submitBtn.disabled = true;
            submitBtn.innerHTML = '🔄 분석 시작 중...';
            submitBtn.style.opacity = '0.7';
        });
    }
    
    // 텍스트 영역 자동 크기 조정
    const textarea = document.querySelector('#land_data');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // 샘플 데이터 입력 기능
        addSampleDataButton();
    }
});

// 샘플 데이터 입력 버튼 추가
function addSampleDataButton() {
    const formGroup = document.querySelector('.form-group');
    const sampleBtn = document.createElement('button');
    sampleBtn.type = 'button';
    sampleBtn.className = 'sample-btn';
    sampleBtn.innerHTML = '📝 샘플 데이터 입력';
    sampleBtn.style.cssText = `
        margin-top: 10px;
        padding: 8px 16px;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.2s;
    `;
    
    sampleBtn.addEventListener('click', function() {
        const textarea = document.querySelector('#land_data');
        const sampleData = `'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', '용도지역': '중심상업지역', '용도지구': '지정되지않음', '토지이용상황': '업무용', '지형고저': '평지', '형상': '세로장방', '도로접면': '광대소각', '공시지가': 3735000`;
        
        textarea.value = sampleData;
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
        
        // 버튼 스타일 변경
        this.innerHTML = '✅ 샘플 데이터 입력됨';
        this.style.background = '#d4edda';
        this.style.borderColor = '#c3e6cb';
        
        setTimeout(() => {
            this.innerHTML = '📝 샘플 데이터 입력';
            this.style.background = '#f8f9fa';
            this.style.borderColor = '#dee2e6';
        }, 2000);
    });
    
    sampleBtn.addEventListener('mouseenter', function() {
        this.style.background = '#e9ecef';
    });
    
    sampleBtn.addEventListener('mouseleave', function() {
        if (this.innerHTML === '📝 샘플 데이터 입력') {
            this.style.background = '#f8f9fa';
        }
    });
    
    formGroup.appendChild(sampleBtn);
}

// 유틸리티 함수들
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    // 타입별 색상 설정
    const colors = {
        info: '#17a2b8',
        success: '#28a745',
        warning: '#ffc107',
        error: '#dc3545'
    };
    
    notification.style.background = colors[type] || colors.info;
    
    document.body.appendChild(notification);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// CSS 애니메이션 추가
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);