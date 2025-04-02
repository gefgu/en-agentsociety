import { Button, Col, Divider, Flex, GetProp, message, Modal, Row, Select, Tabs } from 'antd';
import { AndroidOutlined, ArrowUpOutlined, CommentOutlined, ProfileOutlined, SmileOutlined, UpOutlined, UserOutlined } from '@ant-design/icons';
import { AgentDialog, AgentProfile, AgentSurvey } from './components/type';
import { Bubble, Sender } from '@ant-design/x';
import { parseT } from '../../components/util';
import React, { useContext, useState } from 'react';
import { observer } from 'mobx-react-lite';
import { StoreContext } from './store';
import { Model, Survey as SurveyUI } from 'survey-react-ui';

const roles: GetProp<typeof Bubble.List, 'roles'> = {
    self: {
        placement: 'start',
        avatar: { icon: <UserOutlined />, style: { background: '#fde3cf' } },
        style: {
            maxWidth: 600,
        },
    },
    otherAgent: {
        placement: 'end',
        avatar: { icon: <UserOutlined />, style: { background: '#cce3cf' } },
        style: {
            maxWidth: 600,
        },
    },
    user: {
        placement: 'end',
        avatar: { icon: <UserOutlined />, style: { background: '#87d068' } },
    },
};

export const ChatBox = observer(() => {
    const store = useContext(StoreContext);

    const agent = store.clickedAgent;
    const agentDialogs = store.clickedAgentDialogs;
    const agentSurveys = store.clickedAgentSurveys;

    const [content, setContent] = useState<string>('');
    const [openPreview, setOpenPreview] = useState(false);
    const [previewSurvey, setPreviousSurvey] = useState<string>();

    // 生成Select选项
    const selectOptions = Array.from(store.id2surveys.values()).map(item => ({
        value: item.id,
        label: item.name,
    }));

    // 状态管理
    const [selectedSurveyID, setSelectedSurveyID] = useState<string | undefined>(undefined);

    // 处理选择变化
    const handleSelectChange = (value: string) => {
        setSelectedSurveyID(value);
    };

    // 提交操作
    const handleSelectSubmit = async () => {
        console.log('Selected UUID:', selectedSurveyID);
        // 进行其他操作
        const res = await fetch(`/api/experiments/${store.expID}/agents/${agent?.id}/survey`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ survey_id: selectedSurveyID }),
        });
        if (res.status !== 200) {
            console.error('Failed to send survey:', res);
        } else {
            message.success('Survey sent, you should wait for the agent to save the survey into database and respond');
        }
        setSelectedSurveyID(undefined);
    };

    const getRoleByChatMessage = (m: AgentDialog) => {
        if (m.type === 0) {
            return { role: "self", name: agent?.name };
        }
        if (m.type === 1) {
            if (m.speaker === "" || m.speaker === agent?.id) {
                return { role: "self", name: agent?.name };
            } else {
                const otherId = m.speaker;
                const otherAgent = store.agents.get(otherId);
                // console.log('get role for', JSON.stringify(m), 'get agent', JSON.stringify(otherAgent));
                return { role: "otherAgent", name: otherAgent?.name };
            }
        }
        if (m.type === 2) {
            if (m.speaker === "") {
                return { role: "self", name: agent?.name };
            } else {
                return { role: "user", name: "User" };
            }
        }
    };

    const renderDialogs = (type: number) => (<>
        <Bubble.List
            roles={roles}
            className={type === 2 ? 'bubble-input' : 'bubble-no-input'}
            items={agentDialogs.filter(m => m.type === type).map((m, i) => {
                // try to parse content as JSON
                let content = m.content;
                try {
                    const contentJson = JSON.parse(m.content);
                    if (contentJson.content !== undefined) {
                        content = contentJson.content;
                    }
                } catch (e) {
                }
                const { role, name } = getRoleByChatMessage(m);

                return {
                    key: `${m.id}-${i}`,
                    loading: false,
                    role: role,
                    content: content,
                    header: <div>{name} (Day {m.day} {parseT(m.t)})</div>
                }
            })}
        />
        {type === 2 && <>
            <Sender
                value={content}
                onChange={setContent}
                disabled={store.experiment?.status !== 1 || agent === undefined}
                onSubmit={async (content: string) => {
                    if (agent === undefined) {
                        return;
                    }
                    const res = await fetch(`/api/experiments/${store.expID}/agents/${agent.id}/dialog`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content: content }),
                    });
                    if (res.status !== 200) {
                        console.error('Failed to send message:', res);
                    } else {
                        message.success('Message sent, you should wait for the agent to save the message into database and respond');
                    }
                    setContent('');
                }}
            /></>
        }
    </>);

    // 将一个Survey中的提问转换为User，回答转换为Agent
    const renderSurveys = () => (<>
        <Bubble.List
            roles={roles}
            className='bubble-input'
            items={agentSurveys.map((s, i) => {
                console.log(store.id2surveys, s.survey_id);
                const survey = store.id2surveys.get(s.survey_id);
                if (survey === undefined) {
                    return [{
                        key: `${s.id}-${i}`,
                        loading: false,
                        role: "user",
                        content: `Survey ID: ${s.survey_id} (deleted)`,
                        header: <div>Survey Day {s.day} {parseT(s.t)}</div>
                    }, {
                        key: `${s.id}-${i}-1`,
                        loading: false,
                        role: "agent",
                        content: JSON.stringify(s.result),
                        header: <div>{agent?.name} Day {s.day} {parseT(s.t)}</div>
                    }];
                } else {
                    return [{
                        key: `${s.id}-${i}`,
                        loading: false,
                        role: "user",
                        content: <div>Survey Name: {survey.name} <Button
                            type='link'
                            onClick={() => {
                                setPreviousSurvey(JSON.stringify(survey.data));
                                setOpenPreview(true);
                            }}
                        >
                            Preview
                        </Button></div>,
                        header: <div>Survey Day {s.day} {parseT(s.t)}</div>
                    }, {
                        key: `${s.id}-${i}-1`,
                        loading: false,
                        role: "agent",
                        content: <div>{Object.entries(s.result).map(([k, v]) => (
                            <><span>{k}: {v}</span><br /></>
                        ))}</div>,
                        header: <div>{agent?.name} Day {s.day} {parseT(s.t)}</div>
                    }];
                }
            }).flat()}
        />
        <Row align='middle' justify='center'>
            <Select
                style={{ width: 'calc(100% - 64px)' }}
                size="large"
                showSearch
                placement='topLeft'
                suffixIcon={<UpOutlined />}
                value={selectedSurveyID}
                onChange={handleSelectChange}
                filterOption={(input, option) =>
                (option?.label?.toLowerCase()?.includes(input.toLowerCase()) ||
                    option?.value?.toLowerCase()?.includes(input.toLowerCase()))
                }
                options={selectOptions}
                optionRender={(o) => <span>{o.label} ({o.value})</span>}
            />
            <Button
                size='large'
                shape='circle'
                type="primary"
                onClick={handleSelectSubmit}
                icon={<ArrowUpOutlined />}
                disabled={selectedSurveyID === undefined || store.experiment?.status !== 1 || agent === undefined}
            />
        </Row>
    </>);

    let model = new Model({});
    if (previewSurvey !== undefined) {
        try {
            model = new Model(JSON.parse(previewSurvey));
        } catch (e) {
            console.error('Failed to parse JSON data:', e);
        }
    }
    model.showCompleteButton = false;

    const rootClass = agent ? "right-inner" : "right-inner collapsed";

    return (<>
        <Flex vertical className={rootClass}>
            <Tabs centered defaultActiveKey="0" animated={{ inkBar: true, tabPane: true }} className='tabs w-full'>
                <Tabs.TabPane tab="Reflection" icon={<SmileOutlined />} key="0">
                    {renderDialogs(0)}
                </Tabs.TabPane>
                <Tabs.TabPane tab="Agent" icon={<AndroidOutlined />} key="1">
                    {renderDialogs(1)}
                </Tabs.TabPane>
                <Tabs.TabPane tab="User" icon={<CommentOutlined />} key="2">
                    {renderDialogs(2)}
                </Tabs.TabPane>
                <Tabs.TabPane tab="Survey" icon={<ProfileOutlined />} key="3">
                    {renderSurveys()}
                </Tabs.TabPane>
            </Tabs>
        </Flex>
        <Modal
            width='50vw'
            title="Survey Preview"
            open={openPreview}
            onCancel={() => setOpenPreview(false)}
            footer={null}
        >
            <div style={{ overflow: 'auto', height: '70vh', width: '100%' }}>
                <SurveyUI model={model} />
            </div>
        </Modal>
    </>);
});