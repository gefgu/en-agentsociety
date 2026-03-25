import { Divider, Flex, Layout } from "antd";
import { Content, Header } from "antd/es/layout/layout";
import RootMenu, { AppSidebarMenu, SidebarBottomActions } from "./Menu";
import { Link, useLocation } from "react-router-dom";
import React, { useEffect, useRef } from "react";

export default function RootLayout({
    children,
    selectedKey,
    homePage,
}: {
    children: React.ReactNode
    selectedKey: string
    homePage?: boolean
}) {
    const headerRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);
    const location = useLocation();
    const isReplayPage = location.pathname.startsWith('/exp/');

    const headerStyle = {
        background: '#14213d',
        color: 'white',
    }

    const menuStyle = {
        background: '#14213d',
        color: 'white',
        fontSize: '1.25em',
    }

    // get the height of the header to set the content height
    useEffect(() => {
        if (!homePage) {
            if (contentRef.current) {
                contentRef.current.style.minHeight = '100vh';
            }
            return;
        }

        if (contentRef.current === null) {
            return
        }
        if (headerRef.current) {
            const headerHeight = headerRef.current.clientHeight;
            if (contentRef.current) {
                contentRef.current.style.minHeight = `calc(100vh - ${headerHeight}px)`;
                return
            }
        }
        contentRef.current.style.minHeight = `90vh`;
    }, [headerRef, contentRef, homePage]);

    const contentStyle: React.CSSProperties = homePage ? {
        width: "100vw",
        background: '#14213d',
        top: 0,
        left: 0,
        alignContent: "center",
        justifyContent: "center",
    } : {
    }

    return (
        <Layout>
            {homePage ? (
                <>
                    <Header ref={headerRef} style={headerStyle}>
                        <Flex gap='small' align='center' style={{ width: '100%' }}>
                            <Link to="/" style={{ display: 'flex', alignItems: 'center' }}>
                                <img src="/logo.png" alt="FastSociety" style={{ height: '42px', display: 'block' }} />
                            </Link>
                            <Divider type="vertical" />
                            <div style={{ flex: 1 }}>
                                <RootMenu selectedKey="" style={menuStyle} />
                            </div>
                        </Flex>
                    </Header>
                    <Content ref={contentRef} style={contentStyle}>
                        {children}
                    </Content>
                </>
            ) : (
                <Layout ref={contentRef} style={{ minHeight: '100vh', padding: 0 }}>
                    <Layout.Sider
                        width={220}
                        breakpoint="lg"
                        collapsedWidth={0}
                        theme="dark"
                    >
                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                            <div style={{ height: 68, padding: '0 16px', display: 'flex', alignItems: 'center' }}>
                                <Link to="/" style={{ display: 'flex', alignItems: 'center' }}>
                                    <img src="/logo.png" alt="FastSociety" style={{ height: '42px', display: 'block' }} />
                                </Link>
                            </div>
                            <div style={{ flex: 1, minHeight: 0, overflow: 'auto', color: 'white', overflowX: "hidden" }}>
                                <AppSidebarMenu selectedKey={selectedKey} />
                            </div>
                            <SidebarBottomActions />
                        </div>
                    </Layout.Sider>
                    <Content style={{ padding: isReplayPage ? 0 : '16px 20px' }}>
                        {children}
                    </Content>
                </Layout>
            )}
        </Layout>
    )
}
