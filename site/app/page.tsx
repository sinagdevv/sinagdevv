'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { SolarScene } from '../components/SolarScene';
import { projects } from '../lib/projects';

const disciplines = ['AI agent security', 'MCP governance', 'RAG systems', 'Authorization', 'Full-stack architecture', 'Cloud automation', 'Data systems'];
const experience = [
  ['10 / 2026 — now', 'AI Automation Engineer Intern', 'AgentGenius.ai / KeywordGenius', 'Shopify application development, Next.js, React, TypeScript, APIs, MCP integration, and AI automation security.'],
  ['08 / 2026 — now', 'Data Innovation Track Intern', 'Eskwelabs', 'Synthetic data modeling, Python, dataset validation, and data workflows.'],
  ['06 / 2026 — 10 / 2026', 'Machine Learning Intern', 'FlyRank AI', 'Applied machine learning, preprocessing, model evaluation, and NLP experimentation.']
];

export default function Home() {
  const [activeProject, setActiveProject] = useState(0);
  const [paused, setPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(media.matches);
    update(); media.addEventListener('change', update);
    const onScroll = () => setScrollProgress(Math.min(window.scrollY / (document.body.scrollHeight - window.innerHeight || 1), 1));
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => { media.removeEventListener('change', update); window.removeEventListener('scroll', onScroll); };
  }, []);

  const selected = projects[activeProject];
  return <main className="site-shell">
    <div className="progress-line" style={{ transform: `scaleX(${scrollProgress})` }} aria-hidden="true" />
    <nav className="top-nav" aria-label="Primary navigation"><a className="wordmark" href="#top">SINAG <span>/ 01</span></a><div className="nav-links"><a href="#work">Work</a><a href="#systems">Systems</a><a href="#about">About</a></div><button className="motion-toggle" type="button" onClick={() => setPaused((value) => !value)} aria-pressed={paused}>{paused ? 'Resume motion' : 'Pause motion'}</button></nav>

    <section className="hero" id="top">
      <div className="hero-copy"><p className="eyebrow">01 / SOLAR OBSERVATORY · MANILA, PH</p><h1>Engineering<br /><em>with intent.</em></h1><p className="hero-lede">I’m John Ray Cacananta — a full-stack developer working where AI security, cloud automation, and useful software meet.</p><div className="hero-actions"><a className="button button-primary" href="#work">Explore selected work <span>↓</span></a><a className="text-link" href="https://github.com/sinagdevv" target="_blank" rel="noreferrer">GitHub / @sinagdevv ↗</a></div></div>
      <div className="hero-scene"><SolarScene paused={paused} reducedMotion={reducedMotion} activeProject={activeProject} onProjectSelect={setActiveProject} /><div className="scene-caption"><span>CORE / 001</span><span>{reducedMotion ? 'REDUCED MOTION' : paused ? 'MOTION PAUSED' : 'LIVE ORBITAL MODEL'}</span></div></div>
    </section>

    <section className="signal-strip" aria-label="Profile signal"><span>FULL-STACK DEVELOPER</span><i /> <span>AI SECURITY</span><i /> <span>CLOUD & AUTOMATION</span><i /> <span>PUBLIC SYSTEMS / PRIVATE CARE</span></section>

    <section className="section work-section" id="work"><div className="section-heading"><p className="eyebrow">02 / SELECTED ENGINEERING WORK</p><h2>Projects with a<br /><em>point of view.</em></h2><p>Real systems, real constraints, and a preference for making the important parts legible.</p></div><div className="work-grid"><div className="project-rail" role="tablist" aria-label="Featured projects">{projects.map((project, index) => <button key={project.name} className={index === activeProject ? 'project-tab active' : 'project-tab'} type="button" role="tab" aria-selected={index === activeProject} onClick={() => setActiveProject(index)}><span>{String(index + 1).padStart(2, '0')}</span><strong>{project.name}</strong><small>{project.role}</small></button>)}</div><article className="project-detail" aria-live="polite"><div className="project-mark"><span>{selected.code}</span><small>SELECTED / {String(activeProject + 1).padStart(2, '0')}</small></div><p className="eyebrow">{selected.role}</p><h3>{selected.name}</h3><p className="project-description">{selected.description}</p><p className="project-highlight">↳ {selected.highlight}</p><div className="tag-row">{selected.stack.map((tag) => <span key={tag}>{tag}</span>)}</div><div className="project-links"><a href={selected.live} target="_blank" rel="noreferrer">Live system ↗</a>{selected.repository && <a href={selected.repository} target="_blank" rel="noreferrer">Public repository ↗</a>}</div></article></div></section>

    <section className="section systems-section" id="systems"><div className="section-heading"><p className="eyebrow">03 / TECHNICAL SPECIALIZATIONS</p><h2>The layer<br /><em>beneath the interface.</em></h2></div><div className="discipline-grid">{disciplines.map((item, index) => <div className="discipline" key={item}><span>0{index + 1}</span><strong>{item}</strong><p>{index < 2 ? 'Designing boundaries, policy, and decisions that can be inspected.' : index < 4 ? 'Building grounded paths from data and intent to usable software.' : 'Shipping interfaces, APIs, and workflows that survive contact with people.'}</p></div>)}</div><div className="stack-line"><span>WORKING STACK</span><p>Python · Java · JavaScript · TypeScript · SQL · Bash · PowerShell · React · Next.js · Vite · FastAPI · Node.js · PostgreSQL · Supabase · SQLite · Firebase · pgvector · PyTorch · scikit-learn · Docker · AWS · Azure · Vercel · GitHub Actions</p></div></section>

    <section className="section experience-section"><div className="section-heading"><p className="eyebrow">04 / PROFESSIONAL EXPERIENCE</p><h2>Still learning.<br /><em>Already shipping.</em></h2></div><div className="experience-list">{experience.map(([date, title, company, detail]) => <article key={title}><time>{date}</time><div><h3>{title}</h3><p className="company">{company}</p><p>{detail}</p></div></article>)}</div></section>

    <section className="section telemetry-section"><div className="section-heading"><p className="eyebrow">05 / GITHUB ACTIVITY</p><h2>Signals from<br /><em>the public orbit.</em></h2><p>Generated from public repositories only. Language composition describes repository code, not personal skill.</p></div><Image className="telemetry" src="/activity.svg" width={920} height={470} alt="Generated public GitHub telemetry panel showing recent repository signals and language composition." /><div className="telemetry-fallback">Telemetry asset appears after the first GitHub Actions sync.</div></section>

    <section className="section about-section" id="about"><div><p className="eyebrow">06 / ABOUT THE BUILDER</p><h2>Make the system<br /><em>worth trusting.</em></h2></div><div className="about-copy"><p>John Ray Cacananta is an IT student and developer focused on useful, security-minded systems — from agent authorization and retrieval workflows to full-stack products that help teams move with more clarity.</p><p>B.S. Information Technology, specialization in Mobile and Internet Technologies, National University - Fairview. Consistent First Honor Dean’s Lister · 4.0 GPA · Blue Scholar.</p><div className="contact-links"><a href="mailto:johnray.cacananta@gmail.com">Start a conversation ↗</a><a href="https://linkedin.com/in/jrcacananta" target="_blank" rel="noreferrer">LinkedIn ↗</a></div></div></section>

    <footer><span>SINAG / JOHN RAY CACANANTA</span><span>BUILT WITH CURIOSITY · 2026</span><a href="#top">Back to top ↑</a></footer>
  </main>;
}
