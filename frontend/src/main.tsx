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
import Callback from './pages/Callback'
import { AuthProvider, sdkConfig } from './components/Auth'
import './i18n'
import { useTranslation } from 'react-i18next'
import Bill from './pages/Bill'
import AgentTemplateForm from './pages/AgentTemplate/AgentTemplateForm'
import { WITH_AUTH } from './components/fetch'

const authProvider = (children: React.ReactNode) => {
    if (WITH_AUTH) {
        return (
            <AuthProvider sdkConfig={sdkConfig}>
                {children}
            </AuthProvider>
        )
    }
    return children;
}

const router = createBrowserRouter([
    {
        path: "/",
        element: <RootLayout selectedKey='/' homePage><Home /></RootLayout>,
    },
    {
        path: "/console",
        element: (
            authProvider(
                <RootLayout selectedKey='/console'><Console /></RootLayout>
            )
        ),
    },
    {
        path: "/exp/:id",
        element: (
            authProvider(
                <RootLayout selectedKey='/console'><Replay /></RootLayout>
            )
        ),
    },
    {
        path: "/survey",
        element: (
            authProvider(
                <RootLayout selectedKey='/survey'><Survey /></RootLayout>
            )
        ),
    },
    {
        path: "/create-experiment",
        element: (
            authProvider(
                <RootLayout selectedKey='/create-experiment'><CreateExperiment /></RootLayout>
            )
        ),
    },
    {
        path: "/llms",
        element: (
            authProvider(
                <RootLayout selectedKey='/llms'><LLM /></RootLayout>
            )
        ),
    },
    {
        path: "/agents",
        element: (
            authProvider(
                <RootLayout selectedKey='/agents'><AgentList /></RootLayout>
            )
        ),
    },
    {
        path: "/profiles",
        element: (
            authProvider(
                <RootLayout selectedKey='/profiles'><ProfileList /></RootLayout>
            )
        ),
    },
    {
        path: "/workflows",
        element: (
            authProvider(
                <RootLayout selectedKey='/workflows'><WorkflowList /></RootLayout>
            )
        ),
    },
    {
        path: "/maps",
        element: (
            authProvider(
                <RootLayout selectedKey='/maps'><Map /></RootLayout>
            )
        ),
    },
    {
        path: "/bill",
        element: (
            authProvider(
                <RootLayout selectedKey='/bill'><Bill /></RootLayout>
            )
        ),
    },
    {
        path: "/callback",
        element: <Callback />,
    },
    {
        path: "/agent-templates",
        element: (
            authProvider(
                <RootLayout selectedKey='/agent-templates'><AgentTemplate /></RootLayout>
            )
        ),
    },
    {
        path: "/agent-templates/create",
        element: (
            authProvider(
                <RootLayout selectedKey='/agent-templates'><AgentTemplateForm /></RootLayout>
            )
        ),
    },
    {
        path: "/agent-templates/edit/:id",
        element: (
            authProvider(
                <RootLayout selectedKey='/agent-templates'><AgentTemplateForm /></RootLayout>
            )
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
