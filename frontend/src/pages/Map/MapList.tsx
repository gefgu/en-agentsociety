import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    CopyOutlined,
    ExportOutlined,
    EyeOutlined,
    DownloadOutlined
} from '@ant-design/icons';
import MapForm from './MapForm';
import { ConfigItem } from '../../services/storageService';
import { MapConfig } from '../../types/config';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const MapList: React.FC = () => {
    const { t } = useTranslation();
    const [maps, setMaps] = useState<ConfigItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [currentMap, setCurrentMap] = useState<ConfigItem | null>(null);
    const [formValues, setFormValues] = useState<Partial<MapConfig>>({});
    const [metaForm] = Form.useForm();

    // Load map configurations
    const loadMaps = async () => {
        setLoading(true);
        try {
            const res = await fetchCustom('/api/map-configs');
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const data = (await res.json()).data;
            setMaps(data);
        } catch (error) {
            message.error(`Failed to load maps: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Initialize data
    useEffect(() => {
        const init = async () => {
            await loadMaps();
        };
        init();
    }, []);

    // Handle search
    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    // Filter maps based on search text
    const filteredMaps = maps.filter(map =>
        map.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (map.description && map.description.toLowerCase().includes(searchText.toLowerCase()))
    );

    // Handle create new map
    const handleCreate = () => {
        setCurrentMap(null);
        // Create a basic map config based on config.json structure
        setFormValues({
            file_path: "maps/default_map.pb",
            cache_path: "maps/default_map.cache"
        });
        metaForm.setFieldsValue({
            name: `Map ${maps.length + 1}`,
            description: ''
        });
        setIsModalVisible(true);
    };

    // Handle edit map
    const handleEdit = (map: ConfigItem) => {
        setCurrentMap(map);
        setFormValues(map.config);
        metaForm.setFieldsValue({
            name: map.name,
            description: map.description
        });
        setIsModalVisible(true);
    };

    // Handle delete map
    const handleDelete = async (id: string) => {
        try {
            const res = await fetchCustom(`/api/map-configs/${id}`, {
                method: 'DELETE'
            });
            if (!res.ok) {
                throw new Error(await res.text());
            }
            message.success('Map deleted successfully');
            loadMaps();
        } catch (error) {
            message.error(`Failed to delete map: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        }
    };

    // Handle duplicate map
    const handleDuplicate = async (map: ConfigItem) => {
        try {
            const duplicateData = {
                ...map,
                name: `${map.name} (Copy)`,
                id: undefined,
            };

            const res = await fetchCustom('/api/map-configs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(duplicateData),
            });

            if (!res.ok) {
                throw new Error(await res.text());
            }

            message.success('Map duplicated successfully');
            loadMaps();
        } catch (error) {
            message.error(`Failed to duplicate map: ${JSON.stringify(error.message)}`, 3);
            console.error(error);
        }
    };

    // Handle modal OK
    const handleModalOk = async () => {
        try {
            // Validate meta form
            const metaValues = await metaForm.validateFields();

            const configData: ConfigItem = {
                name: metaValues.name,
                description: metaValues.description || '',
                config: formValues,
            };
            let res: Response;
            if (currentMap) {
                res = await fetchCustom(`/api/map-configs/${currentMap.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(configData),
                });
            } else {
                res = await fetchCustom('/api/map-configs', {
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

            message.success(`Map config ${currentMap ? 'updated' : 'created'} successfully`);
            setIsModalVisible(false);
            loadMaps();
        } catch (error) {
            message.error(`Map config ${currentMap ? 'update' : 'create'} failed: ${JSON.stringify(error.message)}`, 3);
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
                    <Tooltip title={t('form.common.view')}>
                        <Button icon={<EyeOutlined />} size="small" onClick={async () => {
                            // get token
                            const url = `/api/map-configs/${record.id}/temp-link`
                            try {
                                const res = await fetchCustom(url, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({ expire_seconds: 600 }),
                                })
                                if (!res.ok) {
                                    throw new Error(await res.text());
                                }
                                const data = await res.json();
                                const token = data.data.token;
                                // create temp-link url
                                // format: ${window.location.origin}/api/map-configs/{config_id}/temp-link?token=${token}
                                const tempLinkUrl = `${window.location.origin}/api/map-configs/${record.id}/temp-link?token=${token}`;
                                // open in new tab
                                // format: https://moss.fiblab.net/tools/map-editor?dataSource=${tempLinkUrl}
                                window.open(`https://moss.fiblab.net/tools/map-editor?dataSource=${tempLinkUrl}`, '_blank');
                            } catch (error) {
                                message.error(`Failed to get temp link: ${JSON.stringify(error.message)}`, 3);
                                console.error(error);
                            }
                        }} />
                    </Tooltip>
                    <Tooltip title={t('form.common.export')}>
                        <Button icon={<DownloadOutlined />} size="small" onClick={() => {
                            const url = `/api/map-configs/${record.id}/export`
                            // use form post to download the file
                            const form = document.createElement('form');
                            form.action = url;
                            form.method = 'POST';
                            form.target = '_blank';
                            document.body.appendChild(form);
                            form.submit();
                            document.body.removeChild(form);
                        }} />
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
            title={t('form.map.title')}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>{t('form.map.createNew')}</Button>}
        >
            <Input.Search
                placeholder={t('form.map.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 16 }}
            />

            <Table
                columns={columns}
                dataSource={filteredMaps}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
            />

            <Modal
                title={currentMap ? t('form.map.editTitle') : t('form.map.createTitle')}
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

                <Card title={t('form.map.settingsTitle')}>
                    <MapForm
                        value={formValues}
                        onChange={setFormValues}
                    />
                </Card>
            </Modal>
        </Card>
    );
};

export default MapList; 
