import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form, Col, Row } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import WorkflowForm from './WorkflowForm';
import { ConfigItem } from '../../services/storageService';
import { WorkflowStepConfig } from '../../types/config';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const WorkflowList: React.FC = () => {
    const { t } = useTranslation();
    const [workflows, setWorkflows] = useState<ConfigItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [currentWorkflow, setCurrentWorkflow] = useState<ConfigItem | null>(null);
    const [formValues, setFormValues] = useState<{ workflow: WorkflowStepConfig[] }>({ workflow: [] });
    const [metaForm] = Form.useForm();

    // Load workflow configurations
    const loadWorkflows = async () => {
        setLoading(true);
        try {
            const res = await fetchCustom('/api/workflow-configs');
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = (await res.json()).data;
            setWorkflows(data);
        } catch (error) {
            message.error(t('form.workflow.messages.loadFailed') + `: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Initialize data
    useEffect(() => {
        const init = async () => {
            await loadWorkflows();
        };
        init();
    }, []);

    // Handle search
    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    // Filter workflows based on search text
    const filteredWorkflows = workflows.filter(workflow =>
        workflow.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (workflow.description && workflow.description.toLowerCase().includes(searchText.toLowerCase()))
    );

    // Handle create new workflow
    const handleCreate = () => {
        setCurrentWorkflow(null);
        // setFormValues(configService.getDefaultConfigs().workflow);
        metaForm.setFieldsValue({
            name: `Workflow ${workflows.length + 1}`,
            description: ''
        });
        setIsModalVisible(true);
    };

    // Handle edit workflow
    const handleEdit = (workflow: ConfigItem) => {
        setCurrentWorkflow(workflow);
        setFormValues({
            workflow: workflow.config
        });
        metaForm.setFieldsValue({
            name: workflow.name,
            description: workflow.description
        });
        setIsModalVisible(true);
    };

    // Handle duplicate workflow
    const handleDuplicate = (workflow: ConfigItem) => {
        setCurrentWorkflow(null);
        setFormValues({
            workflow: workflow.config
        });
        metaForm.setFieldsValue({
            name: `${workflow.name} (Copy)`,
            description: workflow.description
        });
        setIsModalVisible(true);
    };

    // Handle delete workflow
    const handleDelete = async (id: string) => {
        try {
            const res = await fetchCustom(`/api/workflow-configs/${id}`, {
                method: 'DELETE'
            });
            if (!res.ok) {
                throw new Error(await res.text());
            }
            message.success(t('form.workflow.messages.deleteSuccess'));
            loadWorkflows();
        } catch (error) {
            message.error(t('form.workflow.messages.deleteFailed') + `: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        }
    };

    // Handle export workflow
    const handleExport = (workflow: ConfigItem) => {
        const dataStr = JSON.stringify(workflow, null, 2);
        const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;

        const exportFileDefaultName = `${workflow.name.replace(/\s+/g, '_')}_workflow.json`;

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
                config: formValues.workflow,
            };
            let res: Response;
            if (currentWorkflow) {
                res = await fetchCustom(`/api/workflow-configs/${currentWorkflow.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(configData),
                });
            } else {
                res = await fetchCustom('/api/workflow-configs', {
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
            message.success(currentWorkflow ? t('form.workflow.messages.updateSuccess') : t('form.workflow.messages.createSuccess'));
            setIsModalVisible(false);
            loadWorkflows();
        } catch (error) {
            message.error((currentWorkflow ? t('form.workflow.messages.updateFailed') : t('form.workflow.messages.createFailed')) + `: ${JSON.stringify(error.message)}`, 3);
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
                        (record.tenant_id ?? '') !== '' && (
                            <Tooltip title={t('form.common.edit')}>
                                <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
                            </Tooltip>
                        )
                    }
                    <Tooltip title={t('form.common.duplicate')}>
                        <Button icon={<CopyOutlined />} size="small" onClick={() => handleDuplicate(record)} />
                    </Tooltip>
                    <Tooltip title={t('form.common.export')}>
                        <Button icon={<ExportOutlined />} size="small" onClick={() => handleExport(record)} />
                    </Tooltip>
                    {
                        (record.tenant_id ?? '') !== '' && (
                            <Tooltip title={t('form.common.delete')}>
                                <Popconfirm
                                    title={t('form.workflow.deleteConfirm')}
                                    onConfirm={() => handleDelete(record.id)}
                                    okText={t('form.common.submit')}
                                    cancelText={t('form.common.cancel')}
                                >
                                    <Button icon={<DeleteOutlined />} size="small" danger />
                                </Popconfirm>
                            </Tooltip>
                        )
                    }
                </Space>
            )
        }
    ];

    return (
        <Card
            title={t('form.workflow.title')}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>{t('form.workflow.createNew')}</Button>}
        >
            <Input.Search
                placeholder={t('form.workflow.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 16 }}
            />

            <Table
                columns={columns}
                dataSource={filteredWorkflows}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
            />

            <Modal
                title={currentWorkflow ? t('form.workflow.editTitle') : t('form.workflow.createTitle')}
                open={isModalVisible}
                onOk={handleModalOk}
                onCancel={handleModalCancel}
                width="80vw"
                destroyOnHidden
            >
                <Card title={t('form.common.metadataTitle')} style={{ marginBottom: 8 }}>
                    <Form
                        form={metaForm}
                        layout="vertical"
                    >
                        <Row gutter={16}>
                            <Col span={8}>
                                <Form.Item
                                    name="name"
                                    label={t('form.common.name')}
                                    rules={[{ required: true, message: t('form.common.nameRequired') }]}
                                >
                                    <Input placeholder={t('form.common.namePlaceholder')} />
                                </Form.Item>
                            </Col>
                            <Col span={16}>
                                <Form.Item
                                    name="description"
                                    label={t('form.common.description')}
                                >
                                    <Input.TextArea
                                        rows={1}
                                        placeholder={t('form.common.descriptionPlaceholder')}
                                    />
                                </Form.Item>
                            </Col>
                        </Row>
                    </Form>
                </Card>

                <Card title={t('form.workflow.settingsTitle')}>
                    <WorkflowForm
                        value={formValues}
                        onChange={setFormValues}
                    />
                </Card>
            </Modal>
        </Card>
    );
};

export default WorkflowList; 
