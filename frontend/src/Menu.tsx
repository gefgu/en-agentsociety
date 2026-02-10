import { GithubOutlined, ExperimentOutlined, ApiOutlined, TeamOutlined, GlobalOutlined, NodeIndexOutlined, SettingOutlined, LineChartOutlined, BarChartOutlined, FileSearchOutlined, CalendarOutlined } from "@ant-design/icons";
import { Menu, MenuProps, Space, Dropdown, Button } from "antd";
import { Link } from "react-router-dom";
import Account from "./components/Account";
import { useTranslation } from 'react-i18next';
import { WITH_AUTH } from "./components/fetch";
// import Account from "./components/Account";

const RootMenu = ({ selectedKey, style }: {
  selectedKey: string,
  style?: React.CSSProperties
}) => {
  const { t, i18n } = useTranslation();

  const handleLanguageChange = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  const agentItems: MenuProps['items'] = [
    {
      key: '/agent-templates',
      label: <Link to="/agent-templates">{t('menu.agentTemplates')}</Link>,
      icon: <SettingOutlined />,
    },
    {
      key: '/profiles',
      label: <Link to="/profiles">{t('menu.profiles')}</Link>,
      icon: <TeamOutlined />,
    },
  ];

  const menuItems: MenuProps['items'] = [
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
      label: (
        <Dropdown menu={{ items: agentItems }} placement="bottomLeft" arrow>
          <div>
            <Link to="/agents"><Space><TeamOutlined />{t('menu.agents')}</Space></Link>
          </div>
        </Dropdown>
      ),

    },
    {
      key: '/workflows',
      label: <Link to="/workflows">{t('menu.workflows')}</Link>,
      icon: <NodeIndexOutlined />,
    },
    {
      key: "/console",
      label: <Link to="/console">{t('menu.experiments')}</Link>,
      icon: <ExperimentOutlined />,
    },
    {
      key: "/grafana",
      label: <Link to="/grafana">{t('menu.grafana')}</Link>,
      icon: <LineChartOutlined />,
    },
    {
      key: "/charts",
      label: <Link to="/charts">{t('menu.charts')}</Link>,
      icon: <BarChartOutlined />,
    },
    {
      key: "/loki",
      label: <Link to="/loki">{t('menu.loki')}</Link>,
      icon: <FileSearchOutlined />,
    },
    {
      key: "/daily-schedule",
      label: <Link to="/daily-schedule">{t('menu.dailySchedule')}</Link>,
      icon: <CalendarOutlined />,
    },
    { key: "/survey", label: <Link to="/survey">{t('menu.survey')}</Link> },
    ...(WITH_AUTH ? [{ key: "/bill", label: <Link to="/bill">{t('menu.bill')}</Link> }] : []),
  ];

  menuItems.push({ key: "/Documentation", label: <Link to="https://agentsociety.readthedocs.io/en/latest/" rel="noopener noreferrer" target="_blank"><Space>{t('menu.documentation')}</Space></Link> });
  menuItems.push({ key: "/Github", label: <Link to="https://github.com/tsinghua-fib-lab/agentsociety/" rel="noopener noreferrer" target="_blank"><Space>{t('menu.github')}<GithubOutlined /></Space></Link> });

  const menuStyle: React.CSSProperties = {
    ...style,
    display: 'flex',
    width: '100%',
    alignItems: 'center',
  };

  const menuClass = "large-icons-menu";

  return (
    <div style={{ display: 'flex', width: '100%' }}>
      <style>
        {`
                .${menuClass} .anticon {
                    font-size: 1em !important; /* Adjust pixel value as needed */
                }
                `}
      </style>
      <Menu
        theme="dark"
        mode="horizontal"
        items={menuItems}
        selectedKeys={[selectedKey]}
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
