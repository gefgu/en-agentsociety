import { GithubOutlined } from "@ant-design/icons";
import { Link, useLocation } from "react-router-dom";
import Account from "./components/Account";
import { useTranslation } from 'react-i18next';
import { WITH_AUTH } from "./components/fetch";

const RootMenu = ({ selectedKey }: { selectedKey: string }) => {
  const { t, i18n } = useTranslation();
  const location = useLocation();

  const handleLanguageChange = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  const isActive = (path: string) =>
    selectedKey === path || location.pathname.startsWith(path + '/') ? ' active' : '';

  return (
    <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1, overflow: 'hidden' }}>
      {/* Config group */}
      <Link to="/llms" className={`site-nav-link${isActive('/llms')}`}>{t('menu.llmConfigs')}</Link>
      <Link to="/maps" className={`site-nav-link${isActive('/maps')}`}>{t('menu.maps')}</Link>
      <Link to="/agents" className={`site-nav-link${isActive('/agents')}`}>{t('menu.agents')}</Link>
      <Link to="/workflows" className={`site-nav-link${isActive('/workflows')}`}>{t('menu.workflows')}</Link>

      <div className="site-nav-separator" />

      {/* App group */}
      <Link to="/console" className={`site-nav-link${isActive('/console')}`}>{t('menu.experiments')}</Link>
      <Link to="/grafana" className={`site-nav-link${isActive('/grafana')}`}>{t('menu.grafana')}</Link>
      <Link to="/charts" className={`site-nav-link${isActive('/charts')}`}>{t('menu.charts')}</Link>
      <Link to="/loki" className={`site-nav-link${isActive('/loki')}`}>{t('menu.loki')}</Link>
      <Link to="/daily-schedule" className={`site-nav-link${isActive('/daily-schedule')}`}>{t('menu.dailySchedule')}</Link>

      <div className="site-nav-separator" />

      {/* Docs group */}
      <Link to="/survey" className={`site-nav-link${isActive('/survey')}`}>{t('menu.survey')}</Link>
      <a
        href="https://agentsociety.readthedocs.io/en/latest/"
        target="_blank"
        rel="noopener noreferrer"
        className="site-nav-link"
      >
        {t('menu.documentation')}
      </a>

      <div style={{ flex: 1 }} />

      {/* Right side */}
      <a
        href="https://github.com/tsinghua-fib-lab/agentsociety/"
        target="_blank"
        rel="noopener noreferrer"
        className="site-nav-link"
        style={{
          border: '1px solid rgba(255,255,255,0.09)',
          background: 'rgba(255,255,255,0.05)',
          display: 'flex',
          alignItems: 'center',
          gap: 5,
        }}
      >
        <GithubOutlined />
        GitHub
      </a>

      <button
        className="site-nav-link"
        onClick={handleLanguageChange}
        style={{ background: 'none', border: 'none', cursor: 'pointer', flexShrink: 0 }}
      >
        {i18n.language === 'en' ? 'ZH' : 'EN'}
      </button>

      {WITH_AUTH && <Account />}
    </div>
  );
};

export default RootMenu;
