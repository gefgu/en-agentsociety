import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import AgentForm from './AgentForm';
import { ConfigItem } from '../../services/storageService';
import { AgentsConfig } from '../../types/config';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const AgentList: React.FC = () => {
    const { t } = useTranslation();
    const [agents, setAgents] = useState<ConfigItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [currentAgent, setCurrentAgent] = useState<ConfigItem | null>(null);
    const [formValues, setFormValues] = useState<Partial<AgentsConfig>>({});
    const [metaForm] = Form.useForm();

    // Load agent configurations
    const loadAgents = async () => {
        setLoading(true);
        try {
            const res = await fetchCustom('/api/agent-configs');
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = (await res.json()).data;
            setAgents(data);
        } catch (error) {
            message.error(`Failed to load agents: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Initialize data
    useEffect(() => {
        const init = async () => {
            await loadAgents();
        };
        init();
    }, []);

    // Handle search
    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    // Filter agents based on search text
    const filteredAgents = agents.filter(agent =>
        agent.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (agent.description && agent.description.toLowerCase().includes(searchText.toLowerCase()))
    );

    // Handle create new agent
    const handleCreate = () => {
        setCurrentAgent(null);
        // Create a basic agent config based on config.json structure
        setFormValues({
            citizens: [
                {
                    agent_class: 'citizen',
                    number: 10,
                    memory_config_func: null,
                    memory_distributions: null
                }
            ],
            firms: [
                {
                    agent_class: 'firm',
                    number: 5,
                    memory_config_func: null,
                    memory_distributions: null
                }
            ],
            governments: [
                {
                    agent_class: 'government',
                    number: 1,
                    memory_config_func: null,
                    memory_distributions: null
                }
            ],
            banks: [
                {
                    agent_class: 'bank',
                    number: 1,
                    memory_config_func: null,
                    memory_distributions: null
                }
            ],
            nbs: [
                {
                    agent_class: 'nbs',
                    number: 1,
                    memory_config_func: null,
                    memory_distributions: null
                }
            ]
        });
        metaForm.setFieldsValue({
            name: `Agent ${agents.length + 1}`,
            description: ''
        });
        setIsModalVisible(true);
    };

    // Handle edit agent
    const handleEdit = (agent: ConfigItem) => {
        setCurrentAgent(agent);
        setFormValues(agent.config);
        metaForm.setFieldsValue({
            name: agent.name,
            description: agent.description
        });
        setIsModalVisible(true);
    };

    // Handle duplicate agent
    const handleDuplicate = (agent: ConfigItem) => {
        setCurrentAgent(null);
        setFormValues(agent.config);
        metaForm.setFieldsValue({
            name: `${agent.name} (Copy)`,
            description: agent.description
        });
        setIsModalVisible(true);
    };

    // Handle delete agent
    const handleDelete = async (id: string) => {
        try {
            const res = await fetchCustom(`/api/agent-configs/${id}`, {
                method: 'DELETE'
            });
            if (!res.ok) {
                throw new Error(await res.text());
            }
            message.success('Agent deleted successfully');
            loadAgents();
        } catch (error) {
            message.error(`Failed to delete agent: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        }
    };

    // Handle export agent
    const handleExport = (agent: ConfigItem) => {
        const dataStr = JSON.stringify(agent, null, 2);
        const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;

        const exportFileDefaultName = `${agent.name.replace(/\s+/g, '_')}_agent.json`;

        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    };

    // Handle modal OK
    const handleModalOk = async () => {
        try {
            // Validate meta form
            const metaValues = await metaForm.validateFields();

            const configData = {
                name: metaValues.name,
                description: metaValues.description || '',
                config: formValues,
            };
            let res: Response;
            if (currentAgent) {
                res = await fetchCustom(`/api/agent-configs/${currentAgent.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(configData),
                });
            } else {
                res = await fetchCustom('/api/agent-configs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(configData),
                });
            }
            if (!res.ok) {
                throw new Error(await res.text());
            }
            message.success(`Agent ${currentAgent ? 'updated' : 'created'} successfully`);
            setIsModalVisible(false);
            loadAgents();
        } catch (error) {
            message.error(`Agent ${currentAgent ? 'update' : 'create'} failed: ${JSON.stringify(error.message)}`, 3);
            console.error('Validation failed:', error);
        }
    };

    // Handle modal cancel
    const handleModalCancel = () => {
        setIsModalVisible(false);
    };

    // Table columns
    const columns = [
        {
            title: t('form.common.name'),
            dataIndex: 'name',
            key: 'name',
            sorter: (a: ConfigItem, b: ConfigItem) => a.name.localeCompare(b.name)
        },
        {
            title: t('form.common.description'),
            dataIndex: 'description',
            key: 'description',
            ellipsis: true
        },
        {
            title: t('form.common.lastUpdated'),
            dataIndex: 'updated_at',
            key: 'updated_at',
            render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
            sorter: (a: ConfigItem, b: ConfigItem) => dayjs(a.updated_at).valueOf() - dayjs(b.updated_at).valueOf()
        },
        {
            title: t('form.common.actions'),
            key: 'actions',
            render: (_: any, record: ConfigItem) => (
                <Space size="small">
                    {
                        <Tooltip title={t('form.common.edit')}>
                            <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
                        </Tooltip>
                    }
                    <Tooltip title={t('form.common.duplicate')}>
                        <Button icon={<CopyOutlined />} size="small" onClick={() => handleDuplicate(record)} />
                    </Tooltip>
                    <Tooltip title={t('form.common.export')}>
                        <Button icon={<ExportOutlined />} size="small" onClick={() => handleExport(record)} />
                    </Tooltip>
                    {
                        <Tooltip title={t('form.common.delete')}>
                            <Popconfirm
                                title={t('form.common.deleteConfirm')}
                                onConfirm={() => handleDelete(record.id)}
                                okText={t('form.common.submit')}
                                cancelText={t('form.common.cancel')}
                            >
                                <Button icon={<DeleteOutlined />} size="small" danger />
                            </Popconfirm>
                        </Tooltip>
                    }
                </Space>
            )
        }
    ];

    return (
        <Card
            title={t('form.agent.title')}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>{t('form.agent.createNew')}</Button>}
        >
            <Input.Search
                placeholder={t('form.agent.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 16 }}
            />

            <Table
                columns={columns}
                dataSource={filteredAgents}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
            />

            <Modal
                title={currentAgent ? t('form.agent.editTitle') : t('form.agent.createTitle')}
                open={isModalVisible}
                onOk={handleModalOk}
                onCancel={handleModalCancel}
                width={800}
                destroyOnHidden
            >
                <Card title={t('form.common.metadataTitle')} style={{ marginBottom: 16 }}>
                    <Form
                        form={metaForm}
                        layout="vertical"
                    >
                        <Form.Item
                            name="name"
                            label={t('form.common.name')}
                            rules={[{ required: true, message: t('form.common.nameRequired') }]}
                        >
                            <Input placeholder={t('form.common.namePlaceholder')} />
                        </Form.Item>
                        <Form.Item
                            name="description"
                            label={t('form.common.description')}
                        >
                            <Input.TextArea
                                rows={2}
                                placeholder={t('form.common.descriptionPlaceholder')}
                            />
                        </Form.Item>
                    </Form>
                </Card>

                <Card title="Agent Settings">
                    <AgentForm
                        value={formValues}
                        onChange={(newValues) => setFormValues(newValues)}
                    />
                </Card>
            </Modal>
        </Card>
    );
};

export default AgentList; 
