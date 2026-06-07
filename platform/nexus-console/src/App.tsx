import './App.css';

function App() {
  const launchItems = [
    {
      title: 'Wazuh Dashboard',
      desc: 'Centralized SIEM and Security Event Management',
      icon: '🛡️',
      link: 'https://localhost:5601'
    },
    {
      title: 'MinIO Console',
      desc: 'Artifact, Evidence, and Dataset S3 Storage',
      icon: '🗄️',
      link: 'http://localhost:9001'
    },
    {
      title: 'Jupyter Workbench',
      desc: 'Agentic Workspace & Purple-Team Analytics',
      icon: '💻',
      link: 'http://localhost:8888'
    },
    {
      title: 'Portainer',
      desc: 'Baseline Host Container Management',
      icon: '🐳',
      link: 'https://localhost:9443'
    },
    {
      title: 'Pi-Hole',
      desc: 'Network DNS Filter & Sinkhole Control',
      icon: '🎯',
      link: 'http://localhost:8081/admin'
    }
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <h1>Nexus Console</h1>
        </div>
        <nav className="nav-links">
          <div className="nav-item active">
            <span>⊞</span> Overview
          </div>
          <div className="nav-item">
            <span>🛡️</span> Security
          </div>
          <div className="nav-item">
            <span>💻</span> Workbenches
          </div>
          <div className="nav-item">
            <span>⚙️</span> Platform
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header">
          <h2>Overview</h2>
          <div className="status-badge">
            <span className="status-dot"></span>
            SYSTEM ONLINE
          </div>
        </header>

        <section className="dashboard-grid">
          {launchItems.map((item, index) => (
            <a key={index} href={item.link} className="launch-card" target="_blank" rel="noreferrer">
              <div className="card-icon">{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </a>
          ))}
        </section>
      </main>
    </div>
  );
}

export default App;
