import React, { useState, useEffect } from 'react';
import { Button } from 'antd';
import { GithubOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { HexLogoMark } from '../../Layout';
import './Home.css';

// Per-index accent colors — data-driven so they stay inline
const PILL_COLORS = [
  { color: '#0fb8a4', bg: 'rgba(15,184,164,0.1)',   border: 'rgba(15,184,164,0.22)' },
  { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)',   border: 'rgba(96,165,250,0.22)' },
  { color: '#34d399', bg: 'rgba(52,211,153,0.1)',   border: 'rgba(52,211,153,0.22)' },
  { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)',  border: 'rgba(167,139,250,0.22)' },
];

const CARD_ACCENTS = ['#0fb8a4', '#60a5fa', '#34d399', '#a78bfa'];
const CARD_ICON_BG = [
  'rgba(15,184,164,0.1)', 'rgba(96,165,250,0.1)',
  'rgba(52,211,153,0.1)', 'rgba(167,139,250,0.1)',
];

const cardIcons = [
  <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
  <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
  <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>,
  <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>,
];

const HomePage = () => {
  const [stars, setStars] = useState(0);
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    fetch('https://api.github.com/repos/tsinghua-fib-lab/agentsociety')
      .then(res => res.json())
      .then(data => setStars(data.stargazers_count))
      .catch(() => setStars(0));
  }, []);

  const pills: string[] = t('home.pills', { returnObjects: true }) as string[];
  const cardTitles = [t('home.card1Title'), t('home.card2Title'), t('home.card3Title'), t('home.card4Title')];
  const cardBodies = [t('home.card1Body'), t('home.card2Body'), t('home.card3Body'), t('home.card4Body')];

  return (
    <div>
      {/* Hero */}
      <section className="home-hero">
        <div className="home-glow home-glow-outer" />
        <div className="home-glow home-glow-inner" />

        <div className="home-badge hero-badge-animate">{t('home.badge')}</div>

        <div className="home-hero-content hero-animate">
          <div className="home-logo-mark"><HexLogoMark size={76} /></div>

          <h1 className="home-hero-title">{t('home.heroTitle')}</h1>
          <p className="home-hero-subtitle">{t('home.heroSubtitle')}</p>

          <div className="home-pills">
            {pills.map((pill, i) => {
              const c = PILL_COLORS[i % PILL_COLORS.length];
              return (
                <span key={pill} className="home-pill" style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.color }}>
                  {pill}
                </span>
              );
            })}
          </div>

          <div className="home-cta-group">
            <Button type="primary" size="large" className="home-cta-btn" onClick={() => navigate('/console')}>
              {t('home.getStarted')}
            </Button>
            <a
              href="https://github.com/tsinghua-fib-lab/agentsociety"
              target="_blank"
              rel="noopener noreferrer"
              className="home-github-link"
            >
              <GithubOutlined />
              {stars > 0 ? `${stars.toLocaleString()} ${t('home.stars')}` : 'GitHub'}
            </a>
          </div>

          <div className="home-scroll-indicator">↓</div>
        </div>
      </section>

      {/* Features */}
      <section className="home-features">
        <p className="home-features-overline">{t('home.featuresOverline')}</p>
        <h2 className="home-features-title">{t('home.featuresTitle')}</h2>

        <div className="home-features-grid">
          {cardTitles.map((title, i) => (
            <div
              key={title}
              className="home-feature-card"
              style={{ borderTop: `2px solid ${CARD_ACCENTS[i]}` }}
            >
              <div className="home-card-icon" style={{ background: CARD_ICON_BG[i], color: CARD_ACCENTS[i] }}>
                {cardIcons[i]}
              </div>
              <h3 className="home-card-title">{title}</h3>
              <p className="home-card-body">{cardBodies[i]}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default HomePage;
