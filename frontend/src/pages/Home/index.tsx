import React, { useState, useEffect } from 'react';
import { Button } from 'antd';
import { GithubOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { HexLogoMark } from '../../Layout';

const PILL_COLORS = [
    { color: '#0fb8a4', bg: 'rgba(15,184,164,0.1)', border: 'rgba(15,184,164,0.22)' },
    { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)', border: 'rgba(96,165,250,0.22)' },
    { color: '#34d399', bg: 'rgba(52,211,153,0.1)', border: 'rgba(52,211,153,0.22)' },
    { color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', border: 'rgba(167,139,250,0.22)' },
];

const CARD_ACCENTS = ['#0fb8a4', '#60a5fa', '#34d399', '#a78bfa'];
const CARD_ICON_BG = [
    'rgba(15,184,164,0.1)', 'rgba(96,165,250,0.1)', 'rgba(52,211,153,0.1)', 'rgba(167,139,250,0.1)'
];

const cardIcons = [
    // Observability — eye icon
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
    // Validation — check-circle icon
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
    // Regional Scale — map icon
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>,
    // Open Source — github icon
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
            <style>{`
                @keyframes fadeUp {
                    from { opacity: 0; transform: translateY(16px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
                .hero-animate { animation: fadeUp 0.55s 0.08s ease both; opacity: 0; }
                .hero-badge-animate { animation: fadeUp 0.45s ease both; }
                .feature-card:hover {
                    background: #0f1d30 !important;
                    border-color: rgba(255,255,255,0.12) !important;
                }
            `}</style>

            {/* Hero section */}
            <section style={{
                position: 'relative',
                minHeight: 'calc(100vh - var(--nav-height))',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '80px 32px 140px',
                overflow: 'hidden',
            }}>
                {/* Radial glow */}
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'radial-gradient(ellipse 1000px 700px at 50% 48%, rgba(15,184,164,0.07) 0%, transparent 62%)',
                    pointerEvents: 'none',
                }} />
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'radial-gradient(ellipse 500px 400px at 50% 40%, rgba(15,184,164,0.04) 0%, transparent 62%)',
                    pointerEvents: 'none',
                }} />

                {/* Badge */}
                <div className="hero-badge-animate" style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '4px 14px',
                    borderRadius: 20,
                    background: 'rgba(15,184,164,0.1)',
                    border: '1px solid rgba(15,184,164,0.22)',
                    color: '#0fb8a4',
                    fontFamily: 'var(--font-body)',
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: '0.07em',
                    textTransform: 'uppercase',
                    marginBottom: 28,
                }}>
                    {t('home.badge')}
                </div>

                <div className="hero-animate" style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 0,
                }}>
                    {/* SVG Logomark */}
                    <div style={{ marginBottom: 24 }}>
                        <HexLogoMark size={76} />
                    </div>

                    {/* H1 */}
                    <h1 style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: 58,
                        fontWeight: 700,
                        letterSpacing: '-0.038em',
                        lineHeight: 1.04,
                        color: 'var(--color-text)',
                        margin: '0 0 20px',
                        textAlign: 'center',
                    }}>
                        {t('home.heroTitle')}
                    </h1>

                    {/* Subtitle */}
                    <p style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: 17.5,
                        fontWeight: 300,
                        color: 'var(--color-text-muted)',
                        margin: '0 0 32px',
                        maxWidth: 560,
                        textAlign: 'center',
                        lineHeight: 1.6,
                    }}>
                        {t('home.heroSubtitle')}
                    </p>

                    {/* Capability pills */}
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 40 }}>
                        {pills.map((pill, i) => (
                            <span key={pill} style={{
                                padding: '4px 14px',
                                borderRadius: 20,
                                background: PILL_COLORS[i % PILL_COLORS.length].bg,
                                border: `1px solid ${PILL_COLORS[i % PILL_COLORS.length].border}`,
                                color: PILL_COLORS[i % PILL_COLORS.length].color,
                                fontFamily: 'var(--font-body)',
                                fontSize: 11.5,
                                fontWeight: 500,
                                letterSpacing: '0.05em',
                                textTransform: 'uppercase',
                            }}>
                                {pill}
                            </span>
                        ))}
                    </div>

                    {/* CTA buttons */}
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                        <Button
                            type="primary"
                            size="large"
                            onClick={() => navigate('/console')}
                            style={{ padding: '0 34px', height: 48, fontSize: 15, fontFamily: 'var(--font-body)', fontWeight: 600 }}
                        >
                            {t('home.getStarted')}
                        </Button>
                        <a
                            href="https://github.com/tsinghua-fib-lab/agentsociety"
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 8,
                                padding: '0 24px',
                                height: 48,
                                borderRadius: 8,
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                color: 'var(--color-text)',
                                fontFamily: 'var(--font-body)',
                                fontSize: 15,
                                fontWeight: 400,
                                textDecoration: 'none',
                                transition: 'background 0.15s',
                            }}
                        >
                            <GithubOutlined />
                            {stars > 0 ? `${stars.toLocaleString()} ${t('home.stars')}` : 'GitHub'}
                        </a>
                    </div>

                    {/* Scroll indicator */}
                    <div style={{
                        marginTop: 56,
                        color: 'var(--color-text-muted)',
                        fontSize: 20,
                        opacity: 0.5,
                    }}>↓</div>
                </div>
            </section>

            {/* Features section */}
            <section style={{
                maxWidth: 1120,
                margin: '0 auto',
                padding: '64px 48px 100px',
            }}>
                {/* Overline */}
                <p style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    color: 'var(--color-accent)',
                    margin: '0 0 12px',
                }}>
                    {t('home.featuresOverline')}
                </p>

                {/* H2 */}
                <h2 style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 35,
                    fontWeight: 600,
                    letterSpacing: '-0.025em',
                    lineHeight: 1.18,
                    color: 'var(--color-text)',
                    margin: '0 0 40px',
                }}>
                    {t('home.featuresTitle')}
                </h2>

                {/* 2×2 card grid */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 18,
                }}>
                    {cardTitles.map((title, i) => (
                        <div
                            key={title}
                            className="feature-card"
                            style={{
                                background: 'var(--color-surface)',
                                border: '1px solid var(--color-border)',
                                borderTop: `2px solid ${CARD_ACCENTS[i]}`,
                                borderRadius: 12,
                                padding: 30,
                                transition: 'background 0.2s, border-color 0.2s',
                            }}
                        >
                            {/* Icon box */}
                            <div style={{
                                width: 40,
                                height: 40,
                                borderRadius: 8,
                                background: CARD_ICON_BG[i],
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: 18,
                                color: CARD_ACCENTS[i],
                            }}>
                                {cardIcons[i]}
                            </div>

                            <h3 style={{
                                fontFamily: 'var(--font-heading)',
                                fontSize: 16.5,
                                fontWeight: 600,
                                color: 'var(--color-text)',
                                margin: '0 0 10px',
                            }}>
                                {title}
                            </h3>

                            <p style={{
                                fontFamily: 'var(--font-body)',
                                fontSize: 13.5,
                                fontWeight: 400,
                                color: 'rgba(226,234,245,0.48)',
                                margin: 0,
                                lineHeight: 1.72,
                            }}>
                                {cardBodies[i]}
                            </p>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
};

export default HomePage;
