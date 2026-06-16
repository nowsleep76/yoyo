import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      isNetworkError: false
    }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error Boundary 에러:', error)
    console.error('Error Info:', errorInfo)

    // 네트워크 에러 판단
    const isNetworkError = error.message.includes('fetch') ||
                          error.message.includes('API') ||
                          error.message.includes('network')

    this.setState({
      error,
      errorInfo,
      isNetworkError
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          border: '2px solid #cc0000',
          borderRadius: '8px',
          backgroundColor: '#fff5f5',
          fontFamily: 'Arial, sans-serif'
        }}>
          <h2 style={{ color: '#cc0000', marginTop: 0 }}>
            ⚠️ {this.state.isNetworkError ? 'API 연결 실패' : '오류 발생'}
          </h2>

          {this.state.isNetworkError ? (
            <div>
              <p><strong>백엔드 서버에 연결할 수 없습니다.</strong></p>
              <ul>
                <li>로컬 개발: 백엔드 서버가 http://localhost:8000에서 실행 중인지 확인하세요</li>
                <li>프로덕션: 백엔드가 배포되고 API_URL이 올바르게 설정되었는지 확인하세요</li>
              </ul>
              <p style={{ color: '#666' }}>
                <small>브라우저 개발자 도구(F12) → Console 탭에서 자세한 오류 메시지를 확인할 수 있습니다.</small>
              </p>
            </div>
          ) : (
            <div>
              <p><strong>예상치 못한 오류가 발생했습니다.</strong></p>
              {process.env.NODE_ENV === 'development' && (
                <details style={{ marginTop: '10px' }}>
                  <summary style={{ cursor: 'pointer', color: '#0066cc' }}>
                    오류 세부정보 (개발자용)
                  </summary>
                  <pre style={{
                    backgroundColor: '#f5f5f5',
                    padding: '10px',
                    borderRadius: '4px',
                    overflow: 'auto',
                    fontSize: '12px'
                  }}>
                    {this.state.error && this.state.error.toString()}
                    {'\n\n'}
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
            </div>
          )}

          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '15px',
              padding: '10px 20px',
              backgroundColor: '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            페이지 새로고침
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
