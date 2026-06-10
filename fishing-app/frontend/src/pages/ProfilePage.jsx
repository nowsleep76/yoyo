import { useState, useEffect } from 'react'
import { StorageUtils } from '../utils/storage'
import './ProfilePage.css'

export default function ProfilePage({ userId, setUserId }) {
  const [formData, setFormData] = useState({
    user_id: '',
    nickname: '',
    preferred_rod: '',
    preferred_reel: '',
    preferred_line_weight: '',
    preferred_leader: '',
    preferred_species: []
  })

  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [allSpecies, setAllSpecies] = useState([])

  const SPECIES_OPTIONS = [
    '우럭', '광어', '놀래기', '볼락', '독까치', '우무로',
    '수우치', '열기', '망둥어', '멸치', '전갱이', '고등어',
    '삼치', '감성돔', '검은도미', '돌돔', '황조기', '강태공'
  ]

  useEffect(() => {
    if (userId) {
      fetchUserProfile()
    }
  }, [userId])

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`/api/user/profile?user_id=${userId}`)
      if (response.ok) {
        const user = await response.json()
        setFormData({
          user_id: user.user_id || '',
          nickname: user.nickname || '',
          preferred_rod: user.preferred_rod || '',
          preferred_reel: user.preferred_reel || '',
          preferred_line_weight: user.preferred_line_weight || '',
          preferred_leader: user.preferred_leader || '',
          preferred_species: user.preferred_species ? user.preferred_species.split(',') : []
        })
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error)
      setMessage('프로필 조회에 실패했습니다.')
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSpeciesToggle = (species) => {
    setFormData(prev => ({
      ...prev,
      preferred_species: prev.preferred_species.includes(species)
        ? prev.preferred_species.filter(s => s !== species)
        : [...prev.preferred_species, species]
    }))
  }

  const handleSave = async () => {
    if (!formData.user_id.trim() || !formData.nickname.trim()) {
      setMessage('사용자 ID와 닉네임은 필수입니다.')
      return
    }

    setIsLoading(true)
    setMessage('')

    try {
      const payload = {
        ...formData,
        preferred_species: formData.preferred_species.join(',')
      }

      let response
      if (userId) {
        response = await fetch(`/api/user/profile?user_id=${userId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      } else {
        response = await fetch('/api/user/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      }

      if (response.ok || response.status === 201) {
        setMessage('프로필이 저장되었습니다.')
        if (!userId) {
          setUserId(formData.user_id)
          const saved = StorageUtils.setItem('userId', formData.user_id)
          if (!saved) {
            console.warn('사용자 ID 저장 실패')
          }
        }
        setTimeout(() => setMessage(''), 3000)
      } else {
        const error = await response.json()
        setMessage(error.error || '저장에 실패했습니다.')
      }
    } catch (error) {
      console.error('Save error:', error)
      setMessage('저장에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    if (userId) {
      fetchUserProfile()
    } else {
      setFormData({
        user_id: '',
        nickname: '',
        preferred_rod: '',
        preferred_reel: '',
        preferred_line_weight: '',
        preferred_leader: '',
        preferred_species: []
      })
    }
    setMessage('')
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2>나의 정보</h2>

        {/* 기본 정보 */}
        <div className="section">
          <h3>기본 정보</h3>
          <div className="form-group">
            <label>사용자 ID</label>
            <input
              type="text"
              name="user_id"
              value={formData.user_id}
              onChange={handleInputChange}
              placeholder="영문, 숫자 조합 (변경 불가)"
              disabled={!!userId}
            />
          </div>
          <div className="form-group">
            <label>닉네임</label>
            <input
              type="text"
              name="nickname"
              value={formData.nickname}
              onChange={handleInputChange}
              placeholder="사용할 닉네임"
            />
          </div>
        </div>

        {/* 장비 설정 */}
        <div className="section">
          <h3>선호 장비</h3>
          <div className="form-group">
            <label>선호 로드</label>
            <input
              type="text"
              name="preferred_rod"
              value={formData.preferred_rod}
              onChange={handleInputChange}
              placeholder="예: 심해에깅 7.0H"
            />
          </div>
          <div className="form-group">
            <label>선호 릴</label>
            <input
              type="text"
              name="preferred_reel"
              value={formData.preferred_reel}
              onChange={handleInputChange}
              placeholder="예: 스테라 SW 8000"
            />
          </div>
          <div className="form-group">
            <label>선호 원줄</label>
            <input
              type="text"
              name="preferred_line_weight"
              value={formData.preferred_line_weight}
              onChange={handleInputChange}
              placeholder="예: PE 3호"
            />
          </div>
          <div className="form-group">
            <label>선호 목줄</label>
            <input
              type="text"
              name="preferred_leader"
              value={formData.preferred_leader}
              onChange={handleInputChange}
              placeholder="예: 나일론 40lb"
            />
          </div>
        </div>

        {/* 자주 사용하는 어종 */}
        <div className="section">
          <h3>자주 사용하는 어종</h3>
          <div className="species-grid">
            {SPECIES_OPTIONS.map(species => (
              <button
                key={species}
                className={`species-btn ${formData.preferred_species.includes(species) ? 'selected' : ''}`}
                onClick={() => handleSpeciesToggle(species)}
              >
                {species}
              </button>
            ))}
          </div>
        </div>

        {/* 메시지 */}
        {message && (
          <div className={`message ${message.includes('실패') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}

        {/* 버튼 */}
        <div className="button-group">
          <button
            className="btn-save"
            onClick={handleSave}
            disabled={isLoading}
          >
            {isLoading ? '저장 중...' : '저장'}
          </button>
          <button
            className="btn-reset"
            onClick={handleReset}
            disabled={isLoading}
          >
            초기화
          </button>
        </div>
      </div>
    </div>
  )
}
