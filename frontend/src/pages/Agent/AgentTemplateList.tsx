import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

interface AgentTemplate {
    id: string;
    name: string;
    description: string;
    // agent_class: string;
    // number: number;
    memory_distributions: {
        [key: string]: {
            dist_type: 'choice' | 'uniform_int' | 'normal';
            choices?: string[];
            weights?: number[];
            min_value?: number;
            max_value?: number;
            mean?: number;
            std?: number;
        };
    };
    agent_params: {
        enable_cognition: boolean;
        UBI: number;
        num_labor_hours: number;
        productivity_per_labor: number;
        time_diff: number;
        max_plan_steps: number;
        environment_reflection_prompt?: string;
        need_initialization_prompt?: string;
        need_evaluation_prompt?: string;
        need_reflection_prompt?: string;
        plan_generation_prompt?: string;
    };
    blocks: {
        [key: string]: Record<string, any>;
    };
    created_at: string;
    updated_at: string;
    tenant_id?: string;
}

const AgentTemplateList: React.FC = () => {
    const [templates, setTemplates] = useState<AgentTemplate[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const navigate = useNavigate();
    const { t } = useTranslation();

    // Load templates
    const loadTemplates = async () => {
        try {
            setLoading(true);
            const res = await fetchCustom('/api/agent-templates');
            console.log('API response for template list:', await res.clone().json());

            if (!res.ok) {
                throw new Error('Failed to load templates');
            }

            const data = await res.json();
            console.log('Processed template data:', data);
            setTemplates(data.data);
        } catch (error) {
            console.error('Error loading templates:', error);
            message.error('Failed to load templates');
        } finally {
            setLoading(false);
        }
    };

    // Initialize data
    useEffect(() => {
        loadTemplates();
    }, []);

    // Handle search
    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    // Filter templates based on search text
    const filteredTemplates = templates.filter(template =>
        template.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (template.description && template.description.toLowerCase().includes(searchText.toLowerCase()))
    );

    // Duplicate template
    const handleDuplicate = async (template: AgentTemplate) => {
        try {
            console.log('Duplicating template:', template);
            const duplicateData = {
                ...template,
                name: `${template.name} (Copy)`,
                id: undefined,
            };

            const res = await fetchCustom('/api/agent-templates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(duplicateData),
            });

            if (!res.ok) {
                const errorData = await res.json();
                console.error('Duplicate API error response:', errorData);
                throw new Error(errorData.detail || 'Failed to duplicate template');
            }

            message.success('Template duplicated successfully');
            loadTemplates();
        } catch (error) {
            console.error('Error duplicating template:', error);
            message.error(error.message || 'Failed to duplicate template');
        }
    };

    // Delete template
    const handleDelete = async (id: string) => {
        try {
            console.log('Attempting to delete template:', id);
            const res = await fetchCustom(`/api/agent-templates/${id}`, {
                method: 'DELETE'
            });

            if (!res.ok) {
                const errorData = await res.json();
                console.error('Delete API error response:', errorData);
                throw new Error(errorData.detail || 'Failed to delete template');
            }

            message.success('Template deleted successfully');
            loadTemplates();
        } catch (error) {
            console.error('Error deleting template:', error);
            message.error(error.message || 'Failed to delete template');
        }
    };

    // Export template
    const handleExport = (template: AgentTemplate) => {
        const dataStr = JSON.stringify(template, null, 2);
        const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
        const exportFileDefaultName = `${template.name.replace(/\s+/g, '_')}_template.json`;

        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
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
            render: (_: any, record: AgentTemplate) => (
                <Space size="small">
                    {
                        <Tooltip title={t('form.common.edit')}>
                            <Button icon={<EditOutlined />} size="small" onClick={() => navigate(`/agent-templates/edit/${record.id}`)} />
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
            title={t('form.template.title')}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/agent-templates/create')}>{t('form.template.createNew')}</Button>}
        >
            <Input.Search
                placeholder={t('form.template.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 16 }}
            />

            <Table
                columns={columns}
                dataSource={filteredTemplates}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
            />
        </Card>
    );
};

export default AgentTemplateList;