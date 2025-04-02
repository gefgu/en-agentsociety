import { ExportOutlined, GithubOutlined, PlusOutlined, ExperimentOutlined, ApiOutlined, TeamOutlined, GlobalOutlined, NodeIndexOutlined } from "@ant-design/icons";
import { Menu, MenuProps, Space, Dropdown } from "antd";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
// import Account from "./components/Account";

const RootMenu = ({ selectedKey, style }: {
    selectedKey: string,
    style?: React.CSSProperties
}) => {

    const [mlflowUrl, setMlflowUrl] = useState<string>("");

    useEffect(() => {
        fetch("/api/mlflow/url")
            .then(res => res.json())
            .then(res => {
                setMlflowUrl(res.data);
            });
    }, []);

    // Experiment submenu items - horizontal layout
    const experimentItems: MenuProps['items'] = [
        {
            key: '/llms',
            label: <Link to="/llms">LLM Configs</Link>,
            icon: <ApiOutlined />,
        },
        {
            key: '/maps',
            label: <Link to="/maps">Maps</Link>,
            icon: <GlobalOutlined />,
        },
        {
            key: '/agents',
            label: <Link to="/agents">Agents</Link>,
            icon: <TeamOutlined />,
        },
        {
            key: '/workflows',
            label: <Link to="/workflows">Workflows</Link>,
            icon: <NodeIndexOutlined />,
        },
        {
            key: '/create-experiment',
            label: <Link to="/create-experiment">Create</Link>,
            icon: <PlusOutlined />,
        },
    ];

    // Dropdown menu for experiment submenu
    const experimentDropdown = (
        <Menu items={experimentItems} mode="horizontal" style={{ borderBottom: 'none' }} />
    );

    const menuItems: MenuProps['items'] = [
        { 
            key: "/console", 
            label: (
                <Dropdown overlay={experimentDropdown} placement="bottomLeft" arrow>
                    <div>
                        <Link to="/console"><Space><ExperimentOutlined />Experiments</Space></Link>
                    </div>
                </Dropdown>
            ),
        },
        { key: "/survey", label: <Link to="/survey">Survey</Link> },
        // { key: "/exp", label: <Link to="/exp">Replay & Live</Link> },
        // { key: "/sim", label: <Link to="/sim">平台</Link> },
        // { key: "/console", label: <Link to="/console">控制台</Link> },
        // { key: "文档", label: <Link to="https://docs-opencity.fiblab.net/docs/get-started" rel="noopener noreferrer" target="_blank"><Space>文档<ExportOutlined /></Space></Link> },
        // { key: "登录", label: <div style={{ marginLeft: "auto" }}><Account /></div> }
    ];
    if (mlflowUrl !== "") {
        menuItems.push({ key: "/mlflow", label: <Link to={mlflowUrl} rel="noopener noreferrer" target="_blank"><Space>MLFlow<ExportOutlined /></Space></Link> });
    }
    menuItems.push({ key: "/Documentation", label: <Link to="https://agentsociety.readthedocs.io/en/latest/" rel="noopener noreferrer" target="_blank"><Space>Documentation</Space></Link> });
    menuItems.push({ key: "/Github", label: <Link to="https://github.com/tsinghua-fib-lab/agentsociety/" rel="noopener noreferrer" target="_blank"><Space>GitHub<GithubOutlined /></Space></Link> });

    return <Menu
        theme="dark"
        mode="horizontal"
        items={menuItems}
        selectedKeys={[selectedKey]}
        style={style}
    />;
};

export default RootMenu;
