import React, { useState, useEffect } from 'react';
import { Typography, Button } from 'antd';
import { GithubOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import './style.css';

const { Link } = Typography;

const HomePage = () => {
    const [stars, setStars] = useState(0);
    const { t } = useTranslation();

    useEffect(() => {
        fetch('https://api.github.com/repos/tsinghua-fib-lab/agentsociety')
            .then(res => res.json())
            .then(data => setStars(data.stargazers_count))
            .catch(() => setStars(0));
    }, []);

    return (
        <section className="home-page">
            <div className="hero-glow hero-glow-left" />
            <div className="hero-glow hero-glow-right" />

            <div className="home-container">
                <div className="hero-grid">
                    <div className="hero-copy">
                        <Link
                            href="https://agentsociety.readthedocs.io/en/latest/"
                            className="hero-announcement anim-up"
                            // style={{color: "white"}}
                        >
                            {t('home.whatsNew')}: {t('home.releaseNotes')}
                        </Link>

                        <img src="/logo.png" alt="UrbGen" className="hero-logo anim-up anim-delay-1" />

                        <h1 className="hero-title anim-up anim-delay-2">
                            {t('home.heroTitle')}
                        </h1>

                        <p className="hero-subtitle anim-up anim-delay-3">
                            {t('home.heroSubtitle')}
                        </p>

                        <div className="hero-ctas anim-up anim-delay-4">
                            <Link href="/console">
                                <Button className="hero-btn hero-btn-primary" size="large">
                                    {t('home.getStarted')}
                                </Button>
                            </Link>
                            <Link href="https://github.com/tsinghua-fib-lab/agentsociety" target="_blank">
                                <Button icon={<GithubOutlined />} className="hero-btn hero-btn-secondary" size="large">
                                    {stars > 0 ? `${stars.toLocaleString()} ${t('home.stars')}` : 'GitHub'}
                                </Button>
                            </Link>
                        </div>

                        <div className="hero-kpis anim-up anim-delay-5" role="list" aria-label={t('home.kpiAriaLabel')}>
                            <div className="kpi-card" role="listitem">
                                <strong>10k+</strong>
                                <span>{t('home.kpiAgents')}</span>
                            </div>
                            <div className="kpi-card" role="listitem">
                                <strong>3</strong>
                                <span>{t('home.kpiCities')}</span>
                            </div>
                            <div className="kpi-card" role="listitem">
                                <strong>Open</strong>
                                <span>{t('home.kpiOpen')}</span>
                            </div>
                        </div>
                    </div>

                    <div className="hero-panel anim-panel" aria-label={t('home.previewAriaLabel')}>
                        <div className="panel-header">
                            <span className="dot" />
                            <span className="dot" />
                            <span className="dot" />
                            <p>{t('home.previewTitle')}</p>
                        </div>
                        <div className="panel-body">
                            <div className="panel-stat-row">
                                <div>
                                    <p className="stat-label">{t('home.previewStat1Label')}</p>
                                    <p className="stat-value">0.91</p>
                                </div>
                                <div>
                                    <p className="stat-label">{t('home.previewStat2Label')}</p>
                                    <p className="stat-value">-12.4%</p>
                                </div>
                            </div>
                            <div className="panel-timeline">
                                <span>06:00</span>
                                <span>09:00</span>
                                <span>12:00</span>
                                <span>18:00</span>
                                <span>22:00</span>
                            </div>
                            <div className="panel-bar-track">
                                <div className="panel-bar-fill" />
                            </div>
                            <ul className="panel-list">
                                <li>{t('home.previewList1')}</li>
                                <li>{t('home.previewList2')}</li>
                                <li>{t('home.previewList3')}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div className="feature-strip">
                    <article className="feature-item anim-up anim-delay-6">
                        <h3>{t('home.feature1Title')}</h3>
                        <p>{t('home.feature1Body')}</p>
                    </article>
                    <article className="feature-item anim-up anim-delay-7">
                        <h3>{t('home.feature2Title')}</h3>
                        <p>{t('home.feature2Body')}</p>
                    </article>
                    <article className="feature-item anim-up anim-delay-8">
                        <h3>{t('home.feature3Title')}</h3>
                        <p>{t('home.feature3Body')}</p>
                    </article>
                </div>
            </div>
        </section>
    );
};

export default HomePage;