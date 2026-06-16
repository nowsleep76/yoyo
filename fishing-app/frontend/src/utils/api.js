/**
 * API 호출 유틸리티
 * 환경에 따라 API 엔드포인트를 동적으로 설정
 */

// API 기본 URL 가져오기
const getApiBaseUrl = () => {
  // 1. 환경 변수에서 가져오기
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL !== 'https://api.example.com') {
    return import.meta.env.VITE_API_URL
  }

  // 2. 브라우저 환경에서 현재 호스트 기반으로 설정
  const hostname = window.location.hostname
  const protocol = window.location.protocol

  // 로컬 개발 환경
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }

  // 프로덕션 환경 (현재는 백엔드 없음 - 목데이터 사용)
  // 나중에 백엔드 배포 후 여기에 URL 설정
  return '/api-mock'
}

/**
 * API 호출 래퍼 함수
 * @param {string} endpoint - API 엔드포인트 (예: '/tide/hourly')
 * @param {object} options - fetch 옵션
 * @returns {Promise<Response>}
 */
export const apiFetch = async (endpoint, options = {}) => {
  const baseUrl = getApiBaseUrl()
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })

    // 네트워크 에러 또는 404/500 에러 확인
    if (!response.ok) {
      console.warn(`API 요청 실패: ${response.status} ${response.statusText}`)
      console.warn(`URL: ${url}`)
      
      // 개발 환경에서는 에러 로그, 프로덕션에서는 조용히 처리
      if (import.meta.env.DEV) {
        const text = await response.text()
        console.error('응답 내용:', text)
      }
    }

    return response
  } catch (error) {
    console.error('API 호출 에러:', error.message)
    console.error('엔드포인트:', endpoint)
    console.error('기본 URL:', getApiBaseUrl())
    throw error
  }
}

/**
 * JSON 응답 파싱 래퍼
 */
export const apiJson = async (endpoint, options = {}) => {
  const response = await apiFetch(endpoint, options)

  if (!response.ok) {
    const contentType = response.headers.get('content-type')
    const isHtml = contentType && contentType.includes('text/html')

    if (isHtml) {
      throw new Error(
        `백엔드 서버에 연결할 수 없습니다. ` +
        `${getApiBaseUrl()}이(가) 실행 중인지 확인해주세요.`
      )
    }

    throw new Error(`API 에러: ${response.status}`)
  }

  try {
    const text = await response.text()

    if (!text) {
      throw new Error('빈 응답')
    }

    return JSON.parse(text)
  } catch (e) {
    console.error('❌ JSON 파싱 에러:', e.message)
    console.error('엔드포인트:', endpoint)

    if (e.message.includes('Unexpected token')) {
      throw new Error(
        `백엔드 서버에 연결할 수 없거나 잘못된 응답입니다. ` +
        `${getApiBaseUrl()}이(가) 올바르게 응답하는지 확인해주세요.`
      )
    }

    throw e
  }
}

/**
 * API 기본 URL 반환 (디버깅용)
 */
export const getApiUrl = () => {
  return getApiBaseUrl()
}
