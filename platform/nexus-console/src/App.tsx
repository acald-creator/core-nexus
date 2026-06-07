import React from 'react';
import './App.css';

function App() {
  const launchItems = [
    {
      title: 'Wazuh Dashboard',
      desc: 'Centralized SIEM and Security Event Management',
      icon: '🛡️',
      link: 'https://wazuh.dashboard.local'
    },
    {
      title: 'MinIO Console',
      desc: 'Artifact, Evidence, and Dataset S3 Storage',
      icon: '🗄️',
      link: 'http://minio.soc.local'
    },
    {
      title: 'Jupyter Workbench',
      desc: 'Agentic Workspace & Purple-Team Analytics',
      icon: '💻',
      link: 'http://workbench.soc.local'
    },
    {
      title: 'Portainer',
      desc: 'Baseline Host Container Management',
      icon: '🐳',
      link: 'https://portainer.local'
    },
    {
      title: 'Pi-Hole',
      desc: 'Network DNS Filter & Sinkhole Control',
      icon: '🎯',
      link: 'http://pi.hole.home.lan/admin'
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
