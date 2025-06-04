import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form, Col, Row, InputNumber, Select, Divider } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined, MinusCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { ConfigWrapper, WorkflowStepConfig, ExpConfig } from '../../types/config';
import { WorkflowType } from '../../utils/enums';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

interface FormValues {
    name: string;
    description?: string;
    config: WorkflowStepConfig[];
}

const WorkflowList: React.FC = () => {
    const { t } = useTranslation();
    const [workflows, setWorkflows] = useState<ConfigWrapper<WorkflowStepConfig[]>[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [currentWorkflow, setCurrentWorkflow] = useState<ConfigWrapper<WorkflowStepConfig[]> | null>(null);
    const [functionList, setFunctionList] = useState<string[]>([]);
    const [form] = Form.useForm<FormValues>();

    // 获取函数列表
    useEffect(() => {
        const fetchFunctionList = async () => {
            try {
                const response = await fetchCustom('/api/community/workflow/functions');
                const data = await response.json();
                setFunctionList(data.data);
            } catch (error) {
                console.error('Failed to fetch function list:', error);
            }
        };
        fetchFunctionList();
    }, []);

    // Load workflow configurations
    const loadWorkflows = async () => {
        setLoading(true);
        try {
            const res = await fetchCustom('/api/workflow-configs');
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = (await res.json()).data as ConfigWrapper<WorkflowStepConfig[]>[];
            setWorkflows(data);
        } catch (error) {
            message.error(t('workflow.messages.loadFailed') + `: ${JSON.stringify(error.message)}`, 3);
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
        form.setFieldsValue({
            name: `Workflow ${workflows.length + 1}`,
            description: '',
            config: [{
                type: WorkflowType.RUN,
                days: 1,
            }]
        });
        setIsModalVisible(true);
    };

    // Handle edit workflow
    const handleEdit = (workflow: ConfigWrapper<WorkflowStepConfig[]>) => {
        setCurrentWorkflow(workflow);

        form.setFieldsValue({
            name: workflow.name,
            description: workflow.description || '',
            config: workflow.config || []
        });
        setIsModalVisible(true);
    };

    // Handle duplicate workflow
    const handleDuplicate = (workflow: ConfigWrapper<WorkflowStepConfig[]>) => {
        setCurrentWorkflow(null);

        form.setFieldsValue({
            name: `${workflow.name} (Copy)`,
            description: workflow.description || '',
            config: workflow.config,
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
            message.success(t('workflow.messages.deleteSuccess'));
            loadWorkflows();
        } catch (error) {
            message.error(t('workflow.messages.deleteFailed') + `: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        }
    };

    // Handle export workflow
    const handleExport = (workflow: ConfigWrapper<WorkflowStepConfig[]>) => {
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
            // Validate form
            const formValues = await form.validateFields();

            let res: Response;
            if (currentWorkflow) {
                res = await fetchCustom(`/api/workflow-configs/${currentWorkflow.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formValues),
                });
            } else {
                res = await fetchCustom('/api/workflow-configs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formValues),
                });
            }
            if (!res.ok) {
                throw new Error(await res.text());
            }
            message.success(currentWorkflow ? t('workflow.messages.updateSuccess') : t('workflow.messages.createSuccess'));
            setIsModalVisible(false);
            loadWorkflows();
        } catch (error) {
            message.error((currentWorkflow ? t('workflow.messages.updateFailed') : t('workflow.messages.createFailed')) + `: ${JSON.stringify(error.message)}`, 3);
            console.error('Validation failed:', error);
        }
    };

    // Handle modal cancel
    const handleModalCancel = () => {
        setIsModalVisible(false);
        form.resetFields();
    };

    // Table columns
    const columns = [
        {
            title: t('common.name'),
            dataIndex: 'name',
            key: 'name',
            sorter: (a: ConfigWrapper<WorkflowStepConfig[]>, b: ConfigWrapper<WorkflowStepConfig[]>) => a.name.localeCompare(b.name)
        },
        {
            title: t('common.description'),
            dataIndex: 'description',
            key: 'description',
            ellipsis: true
        },
        {
            title: t('common.lastUpdated'),
            dataIndex: 'updated_at',
            key: 'updated_at',
            render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
            sorter: (a: ConfigWrapper<WorkflowStepConfig[]>, b: ConfigWrapper<WorkflowStepConfig[]>) => dayjs(a.updated_at).valueOf() - dayjs(b.updated_at).valueOf()
        },
        {
            title: t('common.actions'),
            key: 'actions',
            render: (_: any, record: ConfigWrapper<WorkflowStepConfig[]>) => (
                <Space size="small">
                    {
                        (record.tenant_id ?? '') !== '' && (
                            <Tooltip title={t('common.edit')}>
                                <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
                            </Tooltip>
                        )
                    }
                    <Tooltip title={t('common.duplicate')}>
                        <Button icon={<CopyOutlined />} size="small" onClick={() => handleDuplicate(record)} />
                    </Tooltip>
                    <Tooltip title={t('common.export')}>
                        <Button icon={<ExportOutlined />} size="small" onClick={() => handleExport(record)} />
                    </Tooltip>
                    {
                        (record.tenant_id ?? '') !== '' && (
                            <Tooltip title={t('common.delete')}>
                                <Popconfirm
                                    title={t('workflow.deleteConfirm')}
                                    onConfirm={() => handleDelete(record.id)}
                                    okText={t('common.submit')}
                                    cancelText={t('common.cancel')}
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
            title={t('workflow.title')}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>{t('workflow.createNew')}</Button>}
        >
            <Input.Search
                placeholder={t('workflow.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 8 }}
            />

            <Table
                columns={columns}
                dataSource={filteredWorkflows}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10, size: 'small', showSizeChanger: false }}
            />

            <Modal
                title={currentWorkflow ? t('workflow.editTitle') : t('workflow.createTitle')}
                open={isModalVisible}
                onOk={handleModalOk}
                onCancel={handleModalCancel}
                width="75vw"
                destroyOnHidden
            >
                <Form
                    form={form}
                    layout="vertical"
                >
                    {/* 元数据部分 */}
                    <Card
                        title={t('common.metadataTitle')}
                        style={{ marginBottom: 8 }}
                        bodyStyle={{ padding: '12px' }}
                        headStyle={{ padding: '8px 12px' }}
                    >
                        <Row gutter={8}>
                            <Col span={8}>
                                <Form.Item
                                    name="name"
                                    label={t('common.name')}
                                    rules={[{ required: true, message: t('common.nameRequired') }]}
                                    style={{ marginBottom: 8 }}
                                >
                                    <Input placeholder={t('common.namePlaceholder')} />
                                </Form.Item>
                            </Col>
                            <Col span={16}>
                                <Form.Item
                                    name="description"
                                    label={t('common.description')}
                                    style={{ marginBottom: 8 }}
                                >
                                    <Input.TextArea
                                        rows={1}
                                        placeholder={t('common.descriptionPlaceholder')}
                                    />
                                </Form.Item>
                            </Col>
                        </Row>
                    </Card>

                    {/* 工作流配置部分 */}
                    <Card
                        title={t('workflow.settingsTitle')}
                    >
                        <Form.List
                            name="config"
                        >
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }, index) => (
                                        <>
                                            {/* 基本配置行 */}
                                            <Row gutter={8} align="middle" style={{ marginBottom: 8 }}>
                                                <Col span={4}>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'type']}
                                                        label={t('workflow.stepType', { number: name + 1 })}
                                                        rules={[{ required: true, message: t('workflow.pleaseSelectStepType') }]}
                                                        style={{ marginBottom: 8 }}
                                                    >
                                                        <Select
                                                            placeholder={t('workflow.selectStepType')}
                                                            options={[
                                                                {
                                                                    value: WorkflowType.RUN,
                                                                    label: (
                                                                        <Space size={4}>
                                                                            {t('workflow.run')}
                                                                            <Tooltip title={t('workflow.runTooltip')}>
                                                                                <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                            </Tooltip>
                                                                        </Space>
                                                                    )
                                                                },
                                                                {
                                                                    value: WorkflowType.STEP,
                                                                    label: (
                                                                        <Space size={4}>
                                                                            {t('workflow.step')}
                                                                            <Tooltip title={t('workflow.stepTooltip')}>
                                                                                <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                            </Tooltip>
                                                                        </Space>
                                                                    )
                                                                },
                                                                {
                                                                    value: WorkflowType.ENVIRONMENT_INTERVENE,
                                                                    label: (
                                                                        <Space size={4}>
                                                                            {t('workflow.environmentIntervene')}
                                                                            <Tooltip title={t('workflow.environmentInterveneTooltip')}>
                                                                                <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                            </Tooltip>
                                                                        </Space>
                                                                    )
                                                                },
                                                                {
                                                                    value: WorkflowType.NEXT_ROUND,
                                                                    label: (
                                                                        <Space size={4}>
                                                                            {t('workflow.nextRound')}
                                                                            <Tooltip title={t('workflow.nextRoundTooltip')}>
                                                                                <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                            </Tooltip>
                                                                        </Space>
                                                                    )
                                                                },
                                                                {
                                                                    value: WorkflowType.FUNCTION,
                                                                    label: (
                                                                        <Space size={4}>
                                                                            {t('workflow.function')}
                                                                            <Tooltip title={t('workflow.functionTooltip')}>
                                                                                <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                            </Tooltip>
                                                                        </Space>
                                                                    )
                                                                },
                                                            ]}
                                                        />
                                                    </Form.Item>
                                                </Col>
                                                <Col span={7}>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'description']}
                                                        label={t('workflow.description')}
                                                        tooltip={t('workflow.descriptionTooltip')}
                                                        style={{ marginBottom: 8 }}
                                                    >
                                                        <Input placeholder={t('workflow.enterStepDescription')} />
                                                    </Form.Item>
                                                </Col>
                                                {/* 动态字段渲染 */}
                                                <Form.Item shouldUpdate noStyle>
                                                    {() => {
                                                        const workflowSteps = form.getFieldValue('config') || [];
                                                        const currentStep = workflowSteps[name];
                                                        const stepType = currentStep?.type;

                                                        if (stepType === WorkflowType.RUN) {
                                                            return (
                                                                <>
                                                                    <Col span={6}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'days']}
                                                                            label={t('workflow.days')}
                                                                            rules={[{ required: true, message: t('workflow.pleaseEnterDays') }]}
                                                                            tooltip={t('workflow.daysTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <InputNumber min={0} style={{ width: '100%' }} />
                                                                        </Form.Item>
                                                                    </Col>
                                                                    <Col span={6}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'ticks_per_step']}
                                                                            label={t('workflow.ticksPerStep')}
                                                                            initialValue={300}
                                                                            tooltip={t('workflow.ticksPerStepTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <InputNumber min={1} style={{ width: '100%' }} />
                                                                        </Form.Item>
                                                                    </Col>
                                                                </>
                                                            );
                                                        }

                                                        if (stepType === WorkflowType.STEP) {
                                                            return (
                                                                <>
                                                                    <Col span={6}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'steps']}
                                                                            label={t('workflow.steps')}
                                                                            initialValue={1}
                                                                            rules={[{ required: true, message: t('workflow.pleaseEnterSteps') }]}
                                                                            tooltip={t('workflow.stepsTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <InputNumber min={1} style={{ width: '100%' }} />
                                                                        </Form.Item>
                                                                    </Col>
                                                                    <Col span={6}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'ticks_per_step']}
                                                                            label={t('workflow.ticksPerStep')}
                                                                            initialValue={300}
                                                                            tooltip={t('workflow.ticksPerStepTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <InputNumber min={1} style={{ width: '100%' }} />
                                                                        </Form.Item>
                                                                    </Col>
                                                                </>
                                                            );
                                                        }

                                                        if (stepType === WorkflowType.ENVIRONMENT_INTERVENE) {
                                                            return (
                                                                <>
                                                                    <Col span={6}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'key']}
                                                                            label={t('workflow.environmentKey')}
                                                                            rules={[{ required: true, message: t('workflow.pleaseEnterEnvironmentKey') }]}
                                                                            tooltip={t('workflow.environmentKeyTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <Input placeholder={t('workflow.enterEnvironmentKey')} />
                                                                        </Form.Item>
                                                                    </Col>
                                                                    <Col span={6}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'value']}
                                                                            label={t('workflow.environmentValue')}
                                                                            rules={[{ required: true, message: t('workflow.pleaseEnterEnvironmentValue') }]}
                                                                            tooltip={t('workflow.environmentValueTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <Input.TextArea rows={1} placeholder={t('workflow.enterEnvironmentValue')} />
                                                                        </Form.Item>
                                                                    </Col>
                                                                </>
                                                            );
                                                        }

                                                        if (stepType === WorkflowType.FUNCTION) {
                                                            return (
                                                                <>
                                                                    <Col span={12}>
                                                                        <Form.Item
                                                                            {...restField}
                                                                            name={[name, 'func']}
                                                                            label={t('workflow.functionName')}
                                                                            rules={[{ required: true, message: t('workflow.pleaseSelectFunction') }]}
                                                                            tooltip={t('workflow.functionNameTooltip')}
                                                                            style={{ marginBottom: 8 }}
                                                                        >
                                                                            <Select
                                                                                placeholder={t('workflow.selectFunction')}
                                                                                options={functionList.map(func => ({
                                                                                    value: func,
                                                                                    label: func
                                                                                }))}
                                                                            />
                                                                        </Form.Item>
                                                                    </Col>
                                                                </>
                                                            );
                                                        }
                                                        return null;
                                                    }}
                                                </Form.Item>
                                                <Col span={1}>
                                                    <Button
                                                        type="text"
                                                        danger
                                                        icon={<MinusCircleOutlined />}
                                                        onClick={() => remove(name)}
                                                        size="small"
                                                    />
                                                </Col>
                                            </Row>
                                            <Divider />
                                        </>
                                    ))}
                                    <Form.Item style={{ marginBottom: 0 }}>
                                        <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />} size="small">
                                            {t('workflow.addWorkflowStep')}
                                        </Button>
                                    </Form.Item>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </Form>
            </Modal>
        </Card>
    );
};

export default WorkflowList; 
