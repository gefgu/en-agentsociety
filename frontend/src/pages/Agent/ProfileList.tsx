import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Upload } from 'antd';
import { DeleteOutlined, DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import { fetchCustom } from '../../components/fetch';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';

const ProfileList: React.FC = () => {
    const { t } = useTranslation();
    const [profiles, setProfiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [uploadModalVisible, setUploadModalVisible] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [fileList, setFileList] = useState([]);
    const [description, setDescription] = useState('');

    // Load profiles
    const loadProfiles = async () => {
        setLoading(true);
        try {
            const response = await fetchCustom('/api/agent-profiles');
            const data = await response.json();
            setProfiles(data.data || []);
        } catch (error) {
            console.error('Failed to fetch profiles:', error);
            message.error(t('form.profile.messages.loadFailed'));
        } finally {
            setLoading(false);
        }
    };

    // Initialize data
    useEffect(() => {
        loadProfiles();
    }, []);

    // Handle search
    const handleSearch = (e) => {
        setSearchText(e.target.value);
    };

    // Filter profiles based on search text
    const filteredProfiles = profiles.filter(profile =>
        profile.name.toLowerCase().includes(searchText.toLowerCase())
    );

    // Handle profile preview
    // const handlePreview = async (profileId) => {
    //     try {
    //         setPreviewLoading(true);
    //         setCurrentProfileId(profileId);
            
    //         // Call the API to get profile data
    //         const response = await fetchCustom(`/api/agent-profiles/${profileId}`);
            
    //         if (!response.ok) {
    //             throw new Error(`Failed to fetch profile: ${response.statusText}`);
    //         }
            
    //         const data = await response.json();
            
    //         if (data && data.data) {
    //             // Prepare data for table display
    //             const previewData = data.data.slice(0, 100); // Limit to first 100 records
                
    //             // Create columns for the table
    //             const firstRecord = previewData[0] || {};
    //             const columns = Object.keys(firstRecord).map(key => ({
    //                 title: key,
    //                 dataIndex: key,
    //                 key: key,
    //             }));
                
    //             setPreviewData(previewData);
    //             setPreviewColumns(columns);
    //             setPreviewVisible(true);
    //         } else {
    //             message.warning('No data available for preview');
    //         }
    //     } catch (error) {
    //         console.error('Failed to fetch profile preview:', error);
    //         message.error('Failed to fetch profile preview');
    //     } finally {
    //         setPreviewLoading(false);
    //     }
    // };

    // Handle profile download
    const handleDownload = async (profileId, profileName) => {
        try {
            // Call the API to get profile data
            const response = await fetchCustom(`/api/agent-profiles/${profileId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch profile: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data && data.data) {
                // 创建 JSON 格式的 blob
                const jsonContent = JSON.stringify(data.data, null, 2); // 使用 2 空格缩进，使输出更易读
                const blob = new Blob([jsonContent], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `${profileName}`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url); // 清理创建的 URL
            } else {
                message.warning(t('form.profile.messages.noData'));
            }
        } catch (error) {
            console.error('Failed to download profile:', error);
            message.error(t('form.profile.messages.loadFailed'));
        }
    };

    // Handle profile delete
    const handleDelete = async (profileId) => {
        try {
            const response = await fetchCustom(`/api/agent-profiles/${profileId}`, {
                method: 'DELETE',
            });
            
            if (!response.ok) {
                throw new Error(`Failed to delete profile: ${response.statusText}`);
            }
            
            message.success(t('form.profile.messages.deleteSuccess'));
            loadProfiles(); // Refresh the list
        } catch (error) {
            console.error('Failed to delete profile:', error);
            message.error(t('form.profile.messages.deleteFailed'));
        }
    };

    // Handle file upload
    const handleUpload = async () => {
        if (fileList.length === 0) {
            message.warning(t('form.profile.pleaseSelectFile'));
            return;
        }

        const formData = new FormData();
        formData.append('file', fileList[0].originFileObj as File);
        formData.append('name', fileList[0].name);
        if (description) {
            formData.append('description', description);
        }

        setUploading(true);

        try {
            const response = await fetchCustom('/api/agent-profiles/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
            }

            setFileList([]);
            setDescription('');
            setUploadModalVisible(false);
            message.success(t('form.profile.messages.uploadSuccess'));
            loadProfiles(); // Refresh the list
        } catch (error) {
            console.error('Failed to upload profile:', error);
            message.error(error instanceof Error ? error.message : t('form.profile.messages.uploadFailed'));
        } finally {
            setUploading(false);
        }
    };

    // Handle file change
    const handleFileChange = ({ fileList }) => {
        setFileList(fileList);
    };

    // Define table columns
    const columns = [
        {
            title: t('form.profile.table.name'),
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: t('form.profile.table.description'),
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
        },
        {
            title: t('form.profile.table.count'),
            dataIndex: 'count',
            key: 'count',
        },
        {
            title: t('form.profile.table.createdAt'),
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '',
        },
        {
            title: t('form.common.actions'),
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Tooltip title={t('form.profile.table.download')}>
                        <Button 
                            icon={<DownloadOutlined />} 
                            size="small" 
                            onClick={() => handleDownload(record.id, record.name)}
                        />
                    </Tooltip>
                    <Tooltip title={t('form.profile.table.delete')}>
                        <Popconfirm
                            title={t('form.profile.messages.deleteConfirm')}
                            onConfirm={() => handleDelete(record.id)}
                            okText={t('form.common.submit')}
                            cancelText={t('form.common.cancel')}
                        >
                            <Button icon={<DeleteOutlined />} size="small" danger />
                        </Popconfirm>
                    </Tooltip>
                </Space>
            ),
        },
    ];

    return (
        <Card
            title={t('form.profile.title')}
            extra={
                <Space>
                    <Button 
                        type="primary"
                        icon={<UploadOutlined />}
                        onClick={() => setUploadModalVisible(true)}
                    >
                        {t('form.profile.uploadProfile')}
                    </Button>
                </Space>
            }
        >
            <Input.Search
                placeholder={t('form.profile.searchPlaceholder')}
                onChange={handleSearch}
                style={{ marginBottom: 16 }}
            />

            <Table
                columns={columns}
                dataSource={filteredProfiles}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
            />

            {/* 注释掉预览模态框
            <Modal
                title="Profile Preview"
                open={previewVisible}
                onCancel={() => setPreviewVisible(false)}
                width={1000}
                footer={[
                    <Button key="close" onClick={() => setPreviewVisible(false)}>
                        Close
                    </Button>
                ]}
            >
                {previewLoading ? (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <Spin size="large" />
                        <div style={{ marginTop: '10px' }}>Loading preview data...</div>
                    </div>
                ) : previewData.length > 0 ? (
                    <Table 
                        dataSource={previewData.map((item, index) => ({ ...item, key: index }))} 
                        columns={previewColumns} 
                        scroll={{ x: 'max-content', y: 400 }}
                        pagination={{ pageSize: 10 }}
                    />
                ) : (
                    <div>No preview data available</div>
                )}
            </Modal>
            */}

            {/* Upload Modal */}
            <Modal
                title={t('form.profile.uploadTitle')}
                open={uploadModalVisible}
                onCancel={() => {
                    setUploadModalVisible(false);
                    setFileList([]);
                    setDescription('');
                }}
                footer={[
                    <Button key="cancel" onClick={() => {
                        setUploadModalVisible(false);
                        setFileList([]);
                        setDescription('');
                    }}>
                        {t('form.profile.cancel')}
                    </Button>,
                    <Button 
                        key="upload" 
                        type="primary" 
                        onClick={handleUpload}
                        loading={uploading}
                        disabled={fileList.length === 0}
                    >
                        {t('form.profile.upload')}
                    </Button>
                ]}
            >
                <Space direction="vertical" style={{ width: '100%' }}>
                    <Upload.Dragger
                        fileList={fileList}
                        onChange={handleFileChange}
                        beforeUpload={() => false}
                        multiple={false}
                        // accept=".csv,.json"
                        accept=".json"
                    >
                        <p className="ant-upload-drag-icon">
                            <UploadOutlined />
                        </p>
                        <p className="ant-upload-text">{t('form.profile.uploadHint')}</p>
                        <p className="ant-upload-hint">
                            {t('form.profile.uploadDescription')}
                        </p>
                    </Upload.Dragger>
                    <Input.TextArea
                        placeholder={t('form.profile.enterDescription')}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={4}
                    />
                </Space>
            </Modal>
        </Card>
    );
};

export default ProfileList; 