import { ExportOutlined, GithubOutlined, PlusOutlined, ExperimentOutlined, ApiOutlined, TeamOutlined, GlobalOutlined, NodeIndexOutlined, SettingOutlined } from "@ant-design/icons";
import { Menu, MenuProps, Space, Dropdown, Button } from "antd";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from 'react-i18next';

const RootMenu = ({ selectedKey, style }: {
    selectedKey: string,
    style?: React.CSSProperties
}) => {
    const { t, i18n } = useTranslation();
    const [mlflowUrl, setMlflowUrl] = useState<string>("");

    useEffect(() => {
        fetch("/api/mlflow/url")
            .then(res => res.json())
            .then(res => {
                setMlflowUrl(res.data);
            });
    }, []);

    const handleLanguageChange = () => {
        const newLang = i18n.language === 'en' ? 'zh' : 'en';
        i18n.changeLanguage(newLang);
    };

    // Experiment submenu items
    const experimentItems: MenuProps['items'] = [
    ];

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
        { key: "/survey", label: <Link to="/survey">{t('menu.survey')}</Link> },
    ];

    if (mlflowUrl !== "") {
        menuItems.push({ key: "/mlflow", label: <Link to={mlflowUrl} rel="noopener noreferrer" target="_blank"><Space>{t('menu.mlflow')}<ExportOutlined /></Space></Link> });
    }
    menuItems.push({ key: "/Documentation", label: <Link to="https://agentsociety.readthedocs.io/en/latest/" rel="noopener noreferrer" target="_blank"><Space>{t('menu.documentation')}</Space></Link> });
    menuItems.push({ key: "/Github", label: <Link to="https://github.com/tsinghua-fib-lab/agentsociety/" rel="noopener noreferrer" target="_blank"><Space>{t('menu.github')}<GithubOutlined /></Space></Link> });

    const menuStyle: React.CSSProperties = {
        ...style,
        display: 'flex',
        width: '100%',
        alignItems: 'center',
    };

    return (
        <div style={{ display: 'flex', width: '100%' }}>
            <Menu
                theme="dark"
                mode="horizontal"
                items={menuItems}
                selectedKeys={[selectedKey]}
                style={menuStyle}
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
            </div>
        </div>
    );
};

export default RootMenu;
