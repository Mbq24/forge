import { Routes, Route, NavLink } from 'react-router-dom'
import DslList from './pages/DslList'
import DslDetail from './pages/DslDetail'
import DslNew from './pages/DslNew'
import Templates from './pages/Templates'
import Advisor from './pages/Advisor'
import Compare from './pages/Compare'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <div>
      <nav className="navbar">
        <NavLink to="/" className="navbar-brand">◈ Forge</NavLink>
        <NavLink to="/" end className="nav-link">Dashboard</NavLink>
        <NavLink to="/templates" className="nav-link" style={{ color: 'var(--amber)' }}>Templates</NavLink>
        <NavLink to="/dsl" className="nav-link">Indicator DSL</NavLink>
        <NavLink to="/advisor" className="nav-link" style={{ color: 'var(--violet)' }}>🔮 Advisor</NavLink>
        <NavLink to="/compare" className="nav-link" style={{ color: 'var(--cyan)' }}>🧪 Compare</NavLink>
        <NavLink to="/dsl/new" className="nav-link" style={{ color: 'var(--emerald)' }}>+ New</NavLink>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/dsl" element={<DslList />} />
          <Route path="/dsl/new" element={<DslNew />} />
          <Route path="/dsl/:name" element={<DslDetail />} />
          <Route path="/advisor" element={<Advisor />} />
          <Route path="/compare" element={<Compare />} />
        </Routes>
      </div>
    </div>
  )
}
