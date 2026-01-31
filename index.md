---
layout: default
title: DevSecOps-22 - Complete Course
---

<style>
/* Modern Theme Variables */
:root {
  --primary: #6366f1;
  --primary-dark: #4f46e5;
  --secondary: #ec4899;
  --accent: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --dark: #0f172a;
  --dark-lighter: #1e293b;
  --dark-card: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --border: #475569;
  --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --gradient-4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

/* Reset and Base */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--dark);
  color: var(--text-primary);
  line-height: 1.6;
  overflow-x: hidden;
}

/* Hero Section */
.hero {
  background: linear-gradient(135deg, var(--dark) 0%, var(--dark-lighter) 100%);
  padding: 80px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
}

.hero h1 {
  font-size: 4rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  animation: fadeInUp 0.8s ease;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: var(--text-secondary);
  margin-bottom: 40px;
  animation: fadeInUp 0.8s ease 0.2s both;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-top: 60px;
  animation: fadeInUp 0.8s ease 0.4s both;
}

.stat {
  text-align: center;
}

.stat-number {
  font-size: 3rem;
  font-weight: 700;
  color: var(--primary);
  display: block;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Navigation Tabs */
.nav-tabs {
  background: var(--dark-lighter);
  padding: 20px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.nav-tab {
  padding: 12px 24px;
  background: var(--dark-card);
  border: 2px solid transparent;
  border-radius: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  position: relative;
  overflow: hidden;
}

.nav-tab::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gradient-1);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.nav-tab:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
}

.nav-tab.active {
  border-color: var(--primary);
  color: var(--text-primary);
}

.nav-tab.active::before {
  opacity: 0.1;
}

.nav-icon {
  display: inline-block;
  margin-right: 8px;
}

/* Content Sections */
.content-section {
  display: none;
  animation: fadeIn 0.5s ease;
}

.content-section.active {
  display: block;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
}

/* Section Headers */
.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 15px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-description {
  font-size: 1.2rem;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto;
}

/* Grid Layout */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
  margin-top: 40px;
}

/* Cards */
.card {
  background: var(--dark-lighter);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 30px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-1);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  border-color: var(--primary);
}

.card:hover::before {
  transform: scaleX(1);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.card-icon {
  width: 48px;
  height: 48px;
  background: var(--gradient-1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 1.5rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.card-description {
  color: var(--text-secondary);
  margin-bottom: 25px;
  line-height: 1.6;
}

/* Content Lists */
.content-list {
  list-style: none;
}

.content-item {
  background: var(--dark);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 15px;
  transition: all 0.3s ease;
}

.content-item:hover {
  background: var(--dark-card);
  border-color: var(--primary);
  transform: translateX(5px);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.item-title {
  font-weight: 600;
  color: var(--text-primary);
}

.item-badge {
  background: var(--primary);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.item-description {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 15px;
}

.item-links {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.item-link {
  background: var(--dark-card);
  color: var(--text-primary);
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  border: 1px solid var(--border);
}

.item-link:hover {
  background: var(--primary);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

/* Special Cards for Different Sections */
.linux .card-icon { background: var(--gradient-1); }
.python .card-icon { background: var(--gradient-4); }
.coming-soon .card-icon { background: var(--gradient-2); }

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero h1 {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.2rem;
  }
  
  .hero-stats {
    gap: 30px;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .nav-container {
    gap: 10px;
  }
  
  .nav-tab {
    padding: 10px 16px;
    font-size: 0.9rem;
  }
  
  .grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .container {
    padding: 40px 15px;
  }
}

/* Loading Animation */
.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

/* Search Bar */
.search-container {
  max-width: 600px;
  margin: 0 auto 40px;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 15px 20px 15px 50px;
  background: var(--dark-lighter);
  border: 2px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 1rem;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-icon {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

/* Tags */
.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 15px;
}

.tag {
  background: var(--dark-card);
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 0.8rem;
  border: 1px solid var(--border);
}

/* Coming Soon Badge */
.coming-soon-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  color: white;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  display: inline-block;
  margin-left: 10px;
}

</style>

<!-- Hero Section -->
<div class="hero">
  <div class="hero-content">
    <h1>DevSecOps-22</h1>
    <p class="hero-subtitle">Master DevSecOps with Hands-On Learning Experience</p>
    
    <div class="hero-stats">
      <div class="stat">
        <span class="stat-number" id="lessonsCount">3</span>
        <span class="stat-label">Lessons</span>
      </div>
      <div class="stat">
        <span class="stat-number" id="labsCount">1</span>
        <span class="stat-label">Labs</span>
      </div>
      <div class="stat">
        <span class="stat-number" id="cheatsheetsCount">1</span>
        <span class="stat-label">Cheatsheets</span>
      </div>
    </div>
  </div>
</div>

<!-- Navigation Tabs -->
<div class="nav-tabs">
  <div class="nav-container">
    <button class="nav-tab active" onclick="showSection('linux')">
      <span class="nav-icon">🐧</span>Linux
    </button>
    <button class="nav-tab" onclick="showSection('python')">
      <span class="nav-icon">🐍</span>Python
    </button>
    <button class="nav-tab" onclick="showSection('coming-soon')">
      <span class="nav-icon">🚀</span>Coming Soon
    </button>
  </div>
</div>

<!-- Linux Section -->
<div id="linux" class="content-section active">
  <div class="container">
    <div class="section-header">
      <h2 class="section-title">🐧 Linux Fundamentals</h2>
      <p class="section-description">Master Linux command-line, system administration, and shell scripting</p>
    </div>
    
    <div class="grid linux">
      <!-- Lessons Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📚</div>
          <h3 class="card-title">Lessons</h3>
        </div>
        <p class="card-description">Comprehensive lessons covering Linux fundamentals from basics to advanced topics</p>
        
        <ul class="content-list">
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Computer Basics: Hardware and Operating Systems</span>
              <span class="item-badge">Beginner</span>
            </div>
            <p class="item-description">Understand CPU, registers, cache, RAM, storage, kernel, and how operating systems work</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/lessons/01-computer-basics/" class="item-link">📖 Start Lesson</a>
            </div>
          </li>
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Linux Basic Commands</span>
              <span class="item-badge">Beginner</span>
            </div>
            <p class="item-description">Introduction to Linux, shell basics, filesystem structure, navigation, file operations, piping, and redirection</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/lessons/02-linux-basic-commands/" class="item-link">📖 Start Lesson</a>
            </div>
          </li>
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Linux for DevOps - Lesson 3</span>
              <span class="item-badge">Beginner</span>
            </div>
            <p class="item-description">Wildcards, aliases, environment variables, PATH, prompt customization, bashrc, number systems, and file permissions</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/lessons/03-linux/" class="item-link">📖 Start Lesson</a>
            </div>
          </li>
        </ul>
        
        <div class="tags">
          <span class="tag">fundamentals</span>
          <span class="tag">cli</span>
          <span class="tag">bash</span>
        </div>
      </div>
      
      <!-- Labs Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon">🔬</div>
          <h3 class="card-title">Labs</h3>
        </div>
        <p class="card-description">Hands-on exercises to practice and reinforce your Linux skills</p>
        
        <ul class="content-list">
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Linux Fundamentals Lab</span>
              <span class="item-badge">Hands-on</span>
            </div>
            <p class="item-description">Practice essential Linux commands including navigation, file manipulation, permissions, and I/O redirection</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/labs/1-lab/" class="item-link">🧪 Start Lab</a>
            </div>
          </li>
        </ul>
        
        <div class="tags">
          <span class="tag">practice</span>
          <span class="tag">exercises</span>
          <span class="tag">hands-on</span>
        </div>
      </div>
      
      <!-- Cheatsheets Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📋</div>
          <h3 class="card-title">Cheatsheets</h3>
        </div>
        <p class="card-description">Quick reference guides for common Linux commands and operations</p>
        
        <ul class="content-list">
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Basic Linux Commands</span>
              <span class="item-badge">Reference</span>
            </div>
            <p class="item-description">Comprehensive cheatsheet covering system info, navigation, file operations, text processing, networking, and more</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/cheatsheets/basic-linux-commands/" class="item-link">📑 View Cheatsheet</a>
            </div>
          </li>
        </ul>
        
        <div class="tags">
          <span class="tag">reference</span>
          <span class="tag">quick-guide</span>
          <span class="tag">commands</span>
        </div>
      </div>
      
      <!-- PDFs Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📄</div>
          <h3 class="card-title">PDF Resources</h3>
        </div>
        <p class="card-description">Downloadable PDF materials for offline learning</p>
        
        <ul class="content-list">
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Linux Introduction</span>
              <span class="item-badge">PDF</span>
            </div>
            <p class="item-description">Introduction to Linux concepts and fundamentals</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/pdf/linux-intro.pdf" class="item-link">⬇️ Download PDF</a>
            </div>
          </li>
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Linux Basic Commands PDF</span>
              <span class="item-badge">PDF</span>
            </div>
            <p class="item-description">Printable reference for basic Linux commands</p>
            <div class="item-links">
              <a href="{{ site.baseurl }}/linux/pdf/linux%20basic-commands.pdf" class="item-link">⬇️ Download PDF</a>
            </div>
          </li>
        </ul>
        
        <div class="tags">
          <span class="tag">pdf</span>
          <span class="tag">offline</span>
          <span class="tag">printable</span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Python Section -->
<div id="python" class="content-section">
  <div class="container">
    <div class="section-header">
      <h2 class="section-title">🐍 Python Programming</h2>
      <p class="section-description">Learn Python for DevOps automation and scripting</p>
    </div>
    
    <div class="grid python">
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📚</div>
          <h3 class="card-title">Python Content</h3>
          <span class="coming-soon-badge">Coming Soon</span>
        </div>
        <p class="card-description">Python lessons, labs, and resources will be added here as the course progresses</p>
        
        <ul class="content-list">
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Python Basics</span>
              <span class="item-badge">Planned</span>
            </div>
            <p class="item-description">Variables, data types, control flow, and functions</p>
          </li>
          <li class="content-item">
            <div class="item-header">
              <span class="item-title">Python for DevOps</span>
              <span class="item-badge">Planned</span>
            </div>
            <p class="item-description">Automation scripts, API integration, and system administration</p>
          </li>
        </ul>
        
        <div class="tags">
          <span class="tag">automation</span>
          <span class="tag">scripting</span>
          <span class="tag">devops</span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Coming Soon Section -->
<div id="coming-soon" class="content-section">
  <div class="container">
    <div class="section-header">
      <h2 class="section-title">🚀 Coming Soon</h2>
      <p class="section-description">More exciting topics will be added to the course</p>
    </div>
    
    <div class="grid coming-soon">
      <div class="card">
        <div class="card-header">
          <div class="card-icon">🐳</div>
          <h3 class="card-title">Docker</h3>
        </div>
        <p class="card-description">Containerization and Docker fundamentals for building and deploying applications</p>
        <div class="tags">
          <span class="tag">containers</span>
          <span class="tag">virtualization</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div class="card-icon">☸️</div>
          <h3 class="card-title">Kubernetes</h3>
        </div>
        <p class="card-description">Container orchestration and cluster management with Kubernetes</p>
        <div class="tags">
          <span class="tag">orchestration</span>
          <span class="tag">clusters</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div class="card-icon">🔄</div>
          <h3 class="card-title">Git & GitHub</h3>
        </div>
        <p class="card-description">Version control, branching strategies, and collaborative development</p>
        <div class="tags">
          <span class="tag">version-control</span>
          <span class="tag">collaboration</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div class="card-icon">🔧</div>
          <h3 class="card-title">CI/CD</h3>
        </div>
        <p class="card-description">Continuous Integration and Continuous Deployment pipelines with Jenkins, GitHub Actions</p>
        <div class="tags">
          <span class="tag">automation</span>
          <span class="tag">pipelines</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div class="card-icon">🏗️</div>
          <h3 class="card-title">Terraform</h3>
        </div>
        <p class="card-description">Infrastructure as Code for cloud resource provisioning and management</p>
        <div class="tags">
          <span class="tag">iac</span>
          <span class="tag">cloud</span>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📊</div>
          <h3 class="card-title">Monitoring</h3>
        </div>
        <p class="card-description">Prometheus, Grafana, and observability for DevSecOps</p>
        <div class="tags">
          <span class="tag">observability</span>
          <span class="tag">metrics</span>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
// Show section
function showSection(section) {
  // Hide all sections
  document.querySelectorAll('.content-section').forEach(s => {
    s.classList.remove('active');
  });
  
  // Remove active class from all tabs
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.remove('active');
  });
  
  // Show selected section
  document.getElementById(section).classList.add('active');
  
  // Add active class to clicked tab
  event.target.closest('.nav-tab').classList.add('active');
}

// Animate counters on load
document.addEventListener('DOMContentLoaded', function() {
  animateCounter('lessonsCount', 3);
  animateCounter('labsCount', 1);
  animateCounter('cheatsheetsCount', 1);
});

function animateCounter(id, target) {
  const element = document.getElementById(id);
  const duration = 1500;
  const step = target / (duration / 16);
  let current = 0;
  
  const timer = setInterval(() => {
    current += step;
    if (current >= target) {
      element.textContent = target;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 16);
}
</script>
