import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { ConfigProvider, ThemeConfig } from 'antd'
import RootLayout from './Layout'
import Console from './pages/Console/index'
import Replay from './pages/Replay/index'
import Survey from './pages/Survey/index'
import LLMList from './pages/Experiment/LLMList'
import AgentList from './pages/Experiment/AgentList'
import WorkflowList from './pages/Experiment/WorkflowList'
import MapList from './pages/Experiment/MapList'
import CreateExperiment from './pages/Experiment/CreateExperiment'
import Home from './pages/Home'
import storageService from './services/storageService'
import enUS from 'antd/locale/en_US'

const router = createBrowserRouter([
    {
        path: "/",
        element: <RootLayout selectedKey='/' homePage><Home /></RootLayout>,
    },
    {
        path: "/console",
        element: <RootLayout selectedKey='/console'><Console /></RootLayout>,
    },
    {
        path: "/exp/:id",
        element: <RootLayout selectedKey='/console'><Replay /></RootLayout>,
    },
    {
        path: "/survey",
        element: <RootLayout selectedKey='/survey'><Survey /></RootLayout>,
    },
    {
        path: "/create-experiment",
        element: <RootLayout selectedKey='/create-experiment'><CreateExperiment /></RootLayout>,
    },
    {
        path: "/llms",
        element: <RootLayout selectedKey='/llms'><LLMList /></RootLayout>,
    },
    {
        path: "/agents",
        element: <RootLayout selectedKey='/agents'><AgentList /></RootLayout>,
    },
    {
        path: "/workflows",
        element: <RootLayout selectedKey='/workflows'><WorkflowList /></RootLayout>,
    },
    {
        path: "/maps",
        element: <RootLayout selectedKey='/maps'><MapList /></RootLayout>,
    },
    {
        path: "*",
        element: <Navigate to="/" />,
    }
])

const theme: ThemeConfig = {
    token: {
        colorPrimary: "#0000CC",
        colorInfo: "#0000CC",
        borderRadius: 16,
        colorBgContainer: "#FFFFFF",
        colorBgLayout: "#FFFFFF",
    },
    components: {
        Layout: {
            lightSiderBg: "#F8F8F8",
            headerBg: "#FFFFFF",
        },
        Button: {
            algorithm: true,
            colorBgContainer: "#FFFFFF",
        },
        Select: {
            colorBgContainer: "#FFFFFF",
        }
    }
};

// 初始化示例数据
storageService.initializeExampleData().catch(error => {
    console.error('Failed to initialize example data:', error);
});

ReactDOM.createRoot(document.getElementById('root')!).render(
    <ConfigProvider theme={theme} locale={enUS}>
        <RouterProvider router={router} />
    </ConfigProvider>,
)
