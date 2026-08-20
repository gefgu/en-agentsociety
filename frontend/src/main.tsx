import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { Navigate, Outlet, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { ConfigProvider, ThemeConfig, theme as antTheme } from 'antd'
import { ThemeProvider, useTheme } from './context/ThemeContext'
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
import enUS from 'antd/locale/en_US'
import Callback from './pages/Callback'
import { AuthProvider, sdkConfig } from './components/Auth'
import './i18n'
import Bill from './pages/Bill'
import AgentTemplateForm from './pages/AgentTemplate/AgentTemplateForm'
import { WITH_AUTH } from './components/fetch'
import GrafanaPage from './pages/Grafana'
import ChartsPage from './pages/Charts';
import ErrorPage from './pages/ErrorPage'
import LokiPage from './pages/Loki'
import DailySchedule from './pages/DailySchedule'

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

const router = createBrowserRouter([{
  element: <Outlet />,

  errorElement: <ErrorPage />,

  children: [
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
      path: "/grafana/:exp_id?",
      element: (
        authProvider(
          <RootLayout selectedKey='/grafana'><GrafanaPage /></RootLayout>
        )
      ),
    },
    {
      path: "/charts/:exp_id?/:name?",
      element: (
        authProvider(
          <RootLayout selectedKey='/charts'><ChartsPage /></RootLayout>
        )
      ),
    },
    {
      path: "/loki/:exp_id?",
      element: (
        authProvider(
          <RootLayout selectedKey='/loki'><LokiPage /></RootLayout>
        )
      ),
    },
    {
      path: "/daily-schedule/:exp_id?/:agent_id?",
      element: (
        authProvider(
          <RootLayout selectedKey='/daily-schedule'><DailySchedule /></RootLayout>
        )
      ),
    },
    {
      path: "*",
      element: <Navigate to="/" />,
    }]
}])

const darkTheme: ThemeConfig = {
  algorithm: antTheme.darkAlgorithm,
  token: {
    colorPrimary:       '#0fb8a4',
    colorInfo:          '#0fb8a4',
    colorBgBase:        '#0c1728',
    colorBgContainer:   '#0c1728',
    colorBgLayout:      '#070d1a',
    colorBgElevated:    '#122238',
    colorBorder:        'rgba(255,255,255,0.10)',
    colorText:          '#e2eaf5',
    colorTextSecondary: 'rgba(226,234,245,0.65)',
    borderRadius:       8,
    fontFamily:         "'DM Sans', system-ui, sans-serif",
  },
  components: {
    Layout: { headerBg: '#070d1a', bodyBg: '#070d1a', siderBg: '#0c1728' },
    Table:  { headerBg: '#0e1e36', rowHoverBg: 'rgba(15,184,164,0.06)' },
    Card:   { colorBgContainer: '#0c1728' },
    Modal:  { contentBg: '#0c1728', headerBg: '#0c1728' },
    Select: { colorBgContainer: '#0c1728' },
    Input:  { colorBgContainer: '#0c1728' },
  },
};

const lightTheme: ThemeConfig = {
  algorithm: antTheme.defaultAlgorithm,
  token: {
    colorPrimary:       '#0a9e8c',
    colorInfo:          '#0a9e8c',
    colorBgContainer:   '#ffffff',
    colorBgLayout:      '#f5f7fa',
    colorBgElevated:    '#ffffff',
    colorBorder:        'rgba(0,0,0,0.12)',
    colorText:          '#111827',
    colorTextSecondary: 'rgba(17,24,39,0.65)',
    borderRadius:       8,
    fontFamily:         "'DM Sans', system-ui, sans-serif",
  },
  components: {
    Layout: { headerBg: '#f5f7fa', bodyBg: '#f5f7fa' },
    Table:  { headerBg: '#eef2f7', rowHoverBg: 'rgba(10,158,140,0.06)' },
    Card:   { colorBgContainer: '#ffffff' },
    Modal:  { contentBg: '#ffffff', headerBg: '#ffffff' },
    Select: { colorBgContainer: '#ffffff' },
    Input:  { colorBgContainer: '#ffffff' },
  },
};

const AppShell = () => {
  const { theme } = useTheme();
  return (
    <ConfigProvider
      theme={theme === 'dark' ? darkTheme : lightTheme}
      // This distribution is English-only, including Ant Design's built-in
      // empty-state and pagination labels.
      locale={enUS}
    >
      <RouterProvider router={router} />
    </ConfigProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ThemeProvider>
    <AppShell />
  </ThemeProvider>
)
