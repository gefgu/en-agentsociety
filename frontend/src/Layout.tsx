import { Layout } from "antd";
import { Content } from "antd/es/layout/layout";
import RootMenu from "./Menu";
import { Link } from "react-router-dom";
import React, { useEffect, useRef } from "react";

const HexLogoMark = ({ size = 26 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
        <polygon points="13,1 23,6.5 23,19.5 13,25 3,19.5 3,6.5" stroke="#0fb8a4" strokeWidth="1.4" fill="none" opacity="0.6" />
        <polygon points="13,5 19.5,8.75 19.5,17.25 13,21 6.5,17.25 6.5,8.75" stroke="#0fb8a4" strokeWidth="1" fill="none" opacity="0.25" />
        <circle cx="13" cy="13" r="1.8" fill="#0fb8a4" />
        <circle cx="13" cy="3.5" r="1.2" fill="#0fb8a4" />
        <circle cx="21.5" cy="8.5" r="1.2" fill="#0fb8a4" />
        <circle cx="21.5" cy="17.5" r="1.2" fill="#0fb8a4" />
        <circle cx="13" cy="22.5" r="1.2" fill="#0fb8a4" />
        <line x1="13" y1="3.5" x2="13" y2="11.2" stroke="#0fb8a4" strokeWidth="0.7" opacity="0.22" />
        <line x1="21.5" y1="8.5" x2="14.6" y2="12.1" stroke="#0fb8a4" strokeWidth="0.7" opacity="0.22" />
        <line x1="21.5" y1="17.5" x2="14.6" y2="13.9" stroke="#0fb8a4" strokeWidth="0.7" opacity="0.22" />
        <line x1="13" y1="22.5" x2="13" y2="14.8" stroke="#0fb8a4" strokeWidth="0.7" opacity="0.22" />
    </svg>
);

export { HexLogoMark };

export default function RootLayout({
    children,
    selectedKey,
    homePage,
}: {
    children: React.ReactNode
    selectedKey: string
    homePage?: boolean
}) {
    const headerRef = useRef<HTMLElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (contentRef.current === null) {
            return;
        }
        if (headerRef.current) {
            const headerHeight = headerRef.current.clientHeight;
            if (contentRef.current) {
                contentRef.current.style.minHeight = `calc(100vh - ${headerHeight}px)`;
                return;
            }
        }
        contentRef.current.style.minHeight = `90vh`;
    }, [headerRef, contentRef]);

    const contentStyle: React.CSSProperties = homePage ? {
        width: "100vw",
        background: 'transparent',
        top: 0,
        left: 0,
    } : {
        background: 'transparent',
    };

    return (
        <Layout style={{ background: 'transparent' }}>
            <nav className="site-nav" ref={headerRef}>
                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none', marginRight: 16, flexShrink: 0 }}>
                    <HexLogoMark size={26} />
                    <span style={{
                        fontFamily: 'var(--font-heading)',
                        fontWeight: 600,
                        fontSize: 15,
                        color: 'var(--color-text)',
                        letterSpacing: '-0.025em',
                        whiteSpace: 'nowrap',
                    }}>
                        En-AgentSociety
                    </span>
                </Link>
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
                    <RootMenu selectedKey={homePage ? "" : selectedKey} />
                </div>
            </nav>
            <Content ref={contentRef} style={contentStyle}>
                {children}
            </Content>
        </Layout>
    );
}
