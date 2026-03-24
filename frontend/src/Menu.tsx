import { GithubOutlined, ExperimentOutlined, ApiOutlined, TeamOutlined, GlobalOutlined, NodeIndexOutlined, LineChartOutlined, BarChartOutlined, FileSearchOutlined, DashboardOutlined, ProfileOutlined, UserOutlined } from "@ant-design/icons";
import { Menu, MenuProps, Space, Button } from "antd";
import { Link } from "react-router-dom";
import Account from "./components/Account";
import { useTranslation } from 'react-i18next';
import { WITH_AUTH } from "./components/fetch";

const RootMenu = ({ selectedKey, style }: {
  selectedKey: string,
  style?: React.CSSProperties
}) => {
  const { t, i18n } = useTranslation();

  const handleLanguageChange = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  const menuItems: MenuProps['items'] = [
    {
      key: '/console',
      label: <Link to="/console"><Space><DashboardOutlined />{t('menu.dashboard')}</Space></Link>,
    },
    {
      key: '/documentation',
      label: <Link to="https://agentsociety.readthedocs.io/en/latest/" rel="noopener noreferrer" target="_blank"><Space>{t('menu.documentation')}</Space></Link>,
    },
    {
      key: '/github',
      label: <Link to="https://github.com/tsinghua-fib-lab/agentsociety/" rel="noopener noreferrer" target="_blank"><Space>{t('menu.github')}<GithubOutlined /></Space></Link>,
    },
  ];

  const menuStyle: React.CSSProperties = {
    ...style,
    display: 'flex',
    width: '100%',
    alignItems: 'center',
  };

  const menuClass = "root-top-menu";

  return (
    <div style={{ display: 'flex', width: '100%' }}>
      <style>
        {`
                .${menuClass}.ant-menu {
                  width: auto;
                }
                .${menuClass} .anticon {
                  font-size: 1em !important;
                }
                `}
      </style>
      <Menu
        theme="dark"
        mode="horizontal"
        items={menuItems}
        selectedKeys={selectedKey ? [selectedKey] : []}
        style={menuStyle}
        className={menuClass}
      />
      <div style={{
        marginLeft: 'auto',
        display: 'flex',
        alignItems: 'center',
        minWidth: '320px',
        justifyContent: 'flex-end'
      }}>
        <Button
          type="text"
          style={{ color: 'white' }}
          onClick={handleLanguageChange}
        >
          {i18n.language === 'en' ? '中文' : 'English'}
        </Button>
        {WITH_AUTH && <Account />}
      </div>
    </div>
  );
};

export default RootMenu;

export const AppSidebarMenu = ({ selectedKey, style }: {
  selectedKey: string,
  style?: React.CSSProperties
}) => {
  const { t } = useTranslation();

  const sidebarItems: MenuProps['items'] = [
    {
      key: '/llms',
      label: <Link to="/llms">{t('menu.llmConfigs')}</Link>,
      icon: <ApiOutlined />,
    },
    {
      key: '/maps',
      label: <Link to="/maps">{t('menu.maps')}</Link>,
      icon: <GlobalOutlined />,
    },
    {
      key: '/agents',
      label: <Link to="/agents">{t('menu.agents')}</Link>,
      icon: <TeamOutlined />,
    },
    {
      key: '/profiles',
      label: <Link to="/profiles">{t('menu.profiles')}</Link>,
      icon: <UserOutlined />,
    },
    {
      key: '/agent-templates',
      label: <Link to="/agent-templates">{t('menu.agentTemplates')}</Link>,
      icon: <ProfileOutlined />,
    },
    {
      key: '/workflows',
      label: <Link to="/workflows">{t('menu.workflows')}</Link>,
      icon: <NodeIndexOutlined />,
    },
    {
      key: '/console',
      label: <Link to="/console">{t('menu.experiments')}</Link>,
      icon: <ExperimentOutlined />,
    },
    {
      key: '/grafana',
      label: <Link to="/grafana">{t('menu.grafana')}</Link>,
      icon: <LineChartOutlined />,
    },
    {
      key: '/charts',
      label: <Link to="/charts">{t('menu.charts')}</Link>,
      icon: <BarChartOutlined />,
    },
    {
      key: '/loki',
      label: <Link to="/loki">{t('menu.loki')}</Link>,
      icon: <FileSearchOutlined />,
    },
    {
      key: '/survey',
      label: <Link to="/survey">{t('menu.survey')}</Link>,
    },
  ];

  return (
    <Menu
      mode="inline"
      theme="dark"
      items={sidebarItems}
      selectedKeys={selectedKey ? [selectedKey] : []}
      style={{
        height: '100%',
        borderInlineEnd: 0,
        fontSize: '1.1rem',
        ...style,
      }}
      className="app-sidebar-menu"
    />
  );
};

export const SidebarBottomActions = () => {
  const { t, i18n } = useTranslation();

  const handleLanguageChange = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  const footerItems: MenuProps['items'] = [
    {
      key: 'sidebar-docs',
      label: (
        <a href="https://agentsociety.readthedocs.io/en/latest/" rel="noopener noreferrer" target="_blank">
          <Space>{t('menu.documentation')}</Space>
        </a>
      ),
    },
    {
      key: 'sidebar-github',
      label: (
        <a href="https://github.com/tsinghua-fib-lab/agentsociety/" rel="noopener noreferrer" target="_blank">
          <Space>{t('menu.github')}<GithubOutlined /></Space>
        </a>
      ),
    },
  ];

  return (
    <div style={{ borderTop: '2px solid #000000', padding: '8px 0 12px' }}>
      <Menu mode="inline" theme="dark" selectable={false} items={footerItems} style={{ borderInlineEnd: 0, fontSize: '1.1rem' }} />
      <div style={{ padding: '12px 0', justifyContent: 'center', display: 'flex' }}>
        <Button type="text" onClick={handleLanguageChange} style={{ paddingInline: 0, color: 'white' }}>
          {i18n.language === 'en' ? '中文' : 'English'}
        </Button>
        {WITH_AUTH && <Account />}
      </div>
    </div>
  );
};
