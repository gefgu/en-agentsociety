import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import LLMForm from './LLMForm';
import { ConfigItem } from '../../services/storageService';
import { Config, LLMConfig } from '../../types/config';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const LLMList: React.FC = () => {
    const { t } = useTranslation();
    const [llms, setLLMs] = useState<ConfigItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [currentLLM, setCurrentLLM] = useState<ConfigItem | null>(null);
    const [formValues, setFormValues] = useState<{ llm_configs: LLMConfig[] }>({ llm_configs: [] });
    const [metaForm] = Form.useForm();

    // Load LLM configurations
    const loadLLMs = async () => {
        setLoading(true);
        try {
            const res = await fetchCustom('/api/llm-configs');
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = (await res.json()).data;
            setLLMs(data);
        } catch (error) {
            message.error(`Failed to load LLMs: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Initialize data
    useEffect(() => {
        const init = async () => {
            await loadLLMs();
        };
        init();
    }, []);

    // Handle search
    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    // Filter LLMs based on search text
    const filteredLLMs = llms.filter(llm =>
        llm.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (llm.description && llm.description.toLowerCase().includes(searchText.toLowerCase()))
    );

    // Handle create new LLM
    const handleCreate = () => {
        setCurrentLLM(null);
        metaForm.setFieldsValue({
            name: `LLM ${llms.length + 1}`,
            description: ''
        });
        setIsModalVisible(true);
    };

    // Handle edit LLM
    const handleEdit = (llm: ConfigItem) => {
        setCurrentLLM(llm);
        setFormValues({
            llm_configs: llm.config
        });
        metaForm.setFieldsValue({
            name: llm.name,
            description: llm.description
        });
        setIsModalVisible(true);
    };

    // Handle duplicate LLM
    const handleDuplicate = (llm: ConfigItem) => {
        setCurrentLLM(null);
        setFormValues({
            llm_configs: llm.config
        });
        metaForm.setFieldsValue({
            name: `${llm.name} (Copy)`,
            description: llm.description
        });
        setIsModalVisible(true);
    };

    // Handle delete LLM
    const handleDelete = async (id: string) => {
        try {
            const res = await fetchCustom(`/api/llm-configs/${id}`, {
                method: 'DELETE'
            });
            if (!res.ok) {
                throw new Error(await res.text());
            }
            message.success('LLM config deleted successfully');
            loadLLMs();
        } catch (error) {
            message.error(`Failed to delete LLM config: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        }
    };

    // Handle export LLM
    const handleExport = (llm: ConfigItem) => {
        const dataStr = JSON.stringify(llm, null, 2);
        const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;

        const exportFileDefaultName = `${llm.name.replace(/\s+/g, '_')}_llm.json`;

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
                config: formValues.llm_configs,
            };
            let res: Response;
            if (currentLLM) {
                res = await fetchCustom(`/api/llm-configs/${currentLLM.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(configData),
                });
            } else {
                res = await fetchCustom('/api/llm-configs', {
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

            message.success(`LLM config ${currentLLM ? 'updated' : 'created'} successfully`);
            setIsModalVisible(false);
            loadLLMs();
        } catch (error) {
            message.error(`LLM config ${currentLLM ? 'update' : 'create'} failed: ${JSON.stringify(error.message)}`, 3);
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
            render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss')
        },
        {
            title: t('form.common.actions'),
            key: 'action',
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
            title={t('form.llm.title')}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>{t('form.llm.createNew')}</Button>}
        >
            <Input.Search
                placeholder={t('form.llm.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 16 }}
            />

            <Table
                columns={columns}
                dataSource={filteredLLMs}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
            />

            <Modal
                title={currentLLM ? t('form.llm.editTitle') : t('form.llm.createTitle')}
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

                <Card title={t('form.llm.settingsTitle')}>
                    <LLMForm
                        value={formValues}
                        onChange={setFormValues}
                    />
                </Card>
            </Modal>
        </Card>
    );
};

export default LLMList;
