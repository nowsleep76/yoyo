import './Navbar.css'

function Navbar({ currentPage, onPageChange }) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <i className="fas fa-water"></i>
          <span className="brand-text">광어와복어</span>
        </div>
        <div className="navbar-tabs">
          <button
            className={`nav-tab ${currentPage === 'tide' ? 'active' : ''}`}
            onClick={() => onPageChange('tide')}
          >
            <i className="fas fa-water"></i>
            <span>물때</span>
          </button>
          <button
            className={`nav-tab ${currentPage === 'explore' ? 'active' : ''}`}
            onClick={() => onPageChange('explore')}
          >
            <i className="fas fa-search"></i>
            <span>탐색</span>
          </button>
          <button
            className={`nav-tab ${currentPage === 'records' ? 'active' : ''}`}
            onClick={() => onPageChange('records')}
          >
            <i className="fas fa-book"></i>
            <span>기록</span>
          </button>
          <button
            className={`nav-tab ${currentPage === 'profile' ? 'active' : ''}`}
            onClick={() => onPageChange('profile')}
          >
            <i className="fas fa-cog"></i>
            <span>설정</span>
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
