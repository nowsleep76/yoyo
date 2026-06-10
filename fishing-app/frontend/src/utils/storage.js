/**
 * localStorage 안전 접근 유틸리티
 * - Private browsing 모드
 * - 저장소 접근 불가
 * - 용량 초과 등의 예외 처리
 */

export const StorageUtils = {
  // localStorage 사용 가능 여부 확인
  isAvailable: () => {
    try {
      const test = '__storage_test__'
      localStorage.setItem(test, test)
      localStorage.removeItem(test)
      return true
    } catch (e) {
      console.warn('localStorage 사용 불가:', e.message)
      return false
    }
  },

  // 안전한 getItem
  getItem: (key, defaultValue = null) => {
    try {
      if (!StorageUtils.isAvailable()) {
        console.warn(`localStorage 사용 불가 - 기본값 반환: ${key}`)
        return defaultValue
      }
      const item = localStorage.getItem(key)
      return item || defaultValue
    } catch (e) {
      console.error(`localStorage getItem 실패 (${key}):`, e.message)
      return defaultValue
    }
  },

  // 안전한 setItem
  setItem: (key, value) => {
    try {
      if (!StorageUtils.isAvailable()) {
        console.warn(`localStorage 사용 불가 - 저장 실패: ${key}`)
        return false
      }
      localStorage.setItem(key, value)
      return true
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        console.error('localStorage 용량 초과:', e.message)
      } else {
        console.error(`localStorage setItem 실패 (${key}):`, e.message)
      }
      return false
    }
  },

  // 안전한 removeItem
  removeItem: (key) => {
    try {
      if (!StorageUtils.isAvailable()) {
        return false
      }
      localStorage.removeItem(key)
      return true
    } catch (e) {
      console.error(`localStorage removeItem 실패 (${key}):`, e.message)
      return false
    }
  },

  // 안전한 clear
  clear: () => {
    try {
      if (!StorageUtils.isAvailable()) {
        return false
      }
      localStorage.clear()
      return true
    } catch (e) {
      console.error('localStorage clear 실패:', e.message)
      return false
    }
  }
}

/**
 * fetch API 안전 래퍼
 * - 네트워크 오류 처리
 * - 타임아웃 처리
 * - CORS 오류 처리
 */

export const SafeFetch = {
  // 기본 fetch with timeout
  fetch: async (url, options = {}, timeout = 10000) => {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout)

      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return {
        ok: true,
        status: response.status,
        data: await response.json()
      }
    } catch (error) {
      let errorMessage = '요청 실패'
      let errorCode = 'UNKNOWN'

      if (error.name === 'AbortError') {
        errorMessage = `요청 타임아웃 (${timeout}ms)`
        errorCode = 'TIMEOUT'
      } else if (error instanceof TypeError) {
        errorMessage = '네트워크 오류 (CORS, 연결 실패 등)'
        errorCode = 'NETWORK'
      } else if (error.message.includes('HTTP')) {
        errorMessage = error.message
        errorCode = 'HTTP'
      } else {
        errorMessage = error.message || '알 수 없는 오류'
        errorCode = 'UNKNOWN'
      }

      console.error(`[${errorCode}] ${url}:`, errorMessage)

      return {
        ok: false,
        status: null,
        error: errorMessage,
        code: errorCode,
        data: null
      }
    }
  },

  // GET 요청
  get: async (url, timeout = 10000) => {
    return SafeFetch.fetch(url, { method: 'GET' }, timeout)
  },

  // POST 요청
  post: async (url, data, timeout = 10000) => {
    return SafeFetch.fetch(
      url,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      },
      timeout
    )
  },

  // PUT 요청
  put: async (url, data, timeout = 10000) => {
    return SafeFetch.fetch(
      url,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      },
      timeout
    )
  },

  // DELETE 요청
  delete: async (url, timeout = 10000) => {
    return SafeFetch.fetch(url, { method: 'DELETE' }, timeout)
  }
}

export default {
  StorageUtils,
  SafeFetch
}
