import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import MapForm from './MapForm';
import { ConfigItem } from '../../services/storageService';
import { MapConfig } from '../../types/config';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';

const MapList: React.FC = () => {
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
                throw new Error('Failed to fetch map configurations');
            }
            const data = (await res.json()).data;
            setMaps(data);
        } catch (error) {
            message.error(`Failed to load maps: ${JSON.stringify(error)}`, 3);
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
                throw new Error('Failed to delete map');
            }
            message.success('Map deleted successfully');
            loadMaps();
        } catch (error) {
            message.error(`Failed to delete map: ${JSON.stringify(error)}`, 3);
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
                throw new Error('Failed to save map config');
            }

            message.success(`Map config ${currentMap ? 'updated' : 'created'} successfully`);
            setIsModalVisible(false);
            loadMaps();
        } catch (error) {
            message.error(`Map config ${currentMap ? 'update' : 'create'} failed: ${JSON.stringify(error)}`, 3);
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
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a: ConfigItem, b: ConfigItem) => a.name.localeCompare(b.name)
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true
        },
        {
            title: 'Last Updated',
            dataIndex: 'updatedAt',
            key: 'updatedAt',
            render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
            sorter: (a: ConfigItem, b: ConfigItem) => dayjs(a.updatedAt).valueOf() - dayjs(b.updatedAt).valueOf()
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: ConfigItem) => (
                <Space size="small">
                    <Tooltip title="Edit">
                        <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
                    </Tooltip>
                    <Tooltip title="View">
                        <Button icon={<EyeOutlined />} size="small" onClick={() => message.info('Map viewer not implemented yet')} />
                    </Tooltip>
                    <Tooltip title="Delete">
                        <Popconfirm
                            title="Are you sure you want to delete this map?"
                            onConfirm={() => handleDelete(record.id)}
                            okText="Yes"
                            cancelText="No"
                        >
                            <Button icon={<DeleteOutlined />} size="small" danger />
                        </Popconfirm>
                    </Tooltip>
                </Space>
            )
        }
    ];

    return (
        <Card
            title="Map Configurations"
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Create New</Button>}
        >
            <Input.Search
                placeholder="Search maps"
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
                title={currentMap ? "Edit Map" : "Create Map"}
                open={isModalVisible}
                onOk={handleModalOk}
                onCancel={handleModalCancel}
                width={800}
                destroyOnClose
            >
                <Card title="Configuration Metadata" style={{ marginBottom: 16 }}>
                    <Form
                        form={metaForm}
                        layout="vertical"
                    >
                        <Form.Item
                            name="name"
                            label="Name"
                            rules={[{ required: true, message: 'Please enter a name for this configuration' }]}
                        >
                            <Input placeholder="Enter configuration name" />
                        </Form.Item>
                        <Form.Item
                            name="description"
                            label="Description"
                        >
                            <Input.TextArea
                                rows={2}
                                placeholder="Enter a description for this configuration"
                            />
                        </Form.Item>
                    </Form>
                </Card>

                <Card title="Map Settings">
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
