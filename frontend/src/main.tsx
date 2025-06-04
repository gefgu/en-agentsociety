import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { ConfigProvider, ThemeConfig } from 'antd'
import RootLayout from './Layout'
import Console from './pages/Console/index'
import Replay from './pages/Replay/index'
import Survey from './pages/Survey/index'
import LLM from './pages/LLM'
import AgentList from './pages/Agent/'
import WorkflowList from './pages/Workflow'
import Map from './pages/Map'
import CreateExperiment from './pages/Experiment/CreateExperiment'
import ProfileList from './pages/AgentProfile'
import AgentTemplate from './pages/AgentTemplate/AgentTemplateList'
import Home from './pages/Home'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import './i18n'
import { useTranslation } from 'react-i18next'
import AgentTemplateForm from './pages/AgentTemplate/AgentTemplateForm'

const router = createBrowserRouter([
    {
        path: "/",
        element: <RootLayout selectedKey='/' homePage><Home /></RootLayout>,
    },
    {
        path: "/console",
        element: (
            <RootLayout selectedKey='/console'><Console /></RootLayout>
        ),
    },
    {
        path: "/exp/:id",
        element: (
            <RootLayout selectedKey='/console'><Replay /></RootLayout>
        ),
    },
    {
        path: "/survey",
        element: (
            <RootLayout selectedKey='/survey'><Survey /></RootLayout>
        ),
    },
    {
        path: "/create-experiment",
        element: (
            <RootLayout selectedKey='/create-experiment'><CreateExperiment /></RootLayout>
        ),
    },
    {
        path: "/llms",
        element: (
            <RootLayout selectedKey='/llms'><LLM /></RootLayout>
        ),
    },
    {
        path: "/agents",
        element: (
            <RootLayout selectedKey='/agents'><AgentList /></RootLayout>
        ),
    },
    {
        path: "/profiles",
        element: (
            <RootLayout selectedKey='/profiles'><ProfileList /></RootLayout>
        ),
    },
    {
        path: "/workflows",
        element: (
            <RootLayout selectedKey='/workflows'><WorkflowList /></RootLayout>
        ),
    },
    {
        path: "/maps",
        element: (
            <RootLayout selectedKey='/maps'><Map /></RootLayout>
        ),
    },
    {
        path: "/agent-templates",
        element: (
            <RootLayout selectedKey='/agent-templates'><AgentTemplate /></RootLayout>
        ),
    },
    {
        path: "/agent-templates/create",
        element: (
            <RootLayout selectedKey='/agent-templates'><AgentTemplateForm /></RootLayout>
        ),
    },
    {
        path: "/agent-templates/edit/:id",
        element: (
            <RootLayout selectedKey='/agent-templates'><AgentTemplateForm /></RootLayout>
        ),
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

const App = () => {
    const { i18n } = useTranslation()
    
    return (
        <ConfigProvider 
            theme={theme} 
            locale={i18n.language === 'en' ? enUS : zhCN}
        >
            <RouterProvider router={router} />
        </ConfigProvider>
    )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <App />
)
