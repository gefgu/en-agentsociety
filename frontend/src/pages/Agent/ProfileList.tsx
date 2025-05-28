import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Upload } from 'antd';
import { PlusOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import { Spin } from 'antd';
import { fetchCustom } from '../../components/fetch';

const ProfileList: React.FC = () => {
    const [profiles, setProfiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [previewVisible, setPreviewVisible] = useState(false);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [previewData, setPreviewData] = useState([]);
    const [previewColumns, setPreviewColumns] = useState([]);
    const [currentProfileId, setCurrentProfileId] = useState(null);
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
            message.error('Failed to fetch agent profiles');
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
                message.warning('No data available for download');
            }
        } catch (error) {
            console.error('Failed to download profile:', error);
            message.error('Failed to download profile');
        }
    };

    // Convert JSON to CSV
    // const convertToCSV = (data) => {
    //     if (!data || data.length === 0) return '';
        
    //     const headers = Object.keys(data[0]);
    //     const csvRows = [];
        
    //     // Add header row
    //     csvRows.push(headers.join(','));
        
    //     // Add data rows
    //     for (const row of data) {
    //         const values = headers.map(header => {
    //             const value = row[header];
    //             // Handle values that contain commas, quotes, etc.
    //             return typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value;
    //         });
    //         csvRows.push(values.join(','));
    //     }
        
    //     return csvRows.join('\n');
    // };

    // Handle profile delete
    const handleDelete = async (profileId) => {
        try {
            const response = await fetchCustom(`/api/agent-profiles/${profileId}`, {
                method: 'DELETE',
            });
            
            if (!response.ok) {
                throw new Error(`Failed to delete profile: ${response.statusText}`);
            }
            
            message.success('Profile deleted successfully');
            loadProfiles(); // Refresh the list
        } catch (error) {
            console.error('Failed to delete profile:', error);
            message.error('Failed to delete profile');
        }
    };

    // Handle file upload
    const handleUpload = async () => {
        if (fileList.length === 0) {
            message.warning('Please select a file to upload');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileList[0].originFileObj as File);
        formData.append('name', fileList[0].name);
        formData.append('description', description);

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
            message.success('Profile uploaded successfully');
            loadProfiles(); // Refresh the list
        } catch (error) {
            console.error('Failed to upload profile:', error);
            message.error(error instanceof Error ? error.message : 'Failed to upload profile');
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
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
        },
        {
            title: 'Count',
            dataIndex: 'count',
            key: 'count',
        },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    {/* 注释掉预览按钮
                    <Tooltip title="Preview">
                        <Button 
                            icon={<EyeOutlined />} 
                            size="small" 
                            onClick={() => handlePreview(record.id)}
                        />
                    </Tooltip>
                    */}
                    <Tooltip title="Download">
                        <Button 
                            icon={<DownloadOutlined />} 
                            size="small" 
                            onClick={() => handleDownload(record.id, record.name)}
                        />
                    </Tooltip>
                    <Tooltip title="Delete">
                        <Popconfirm
                            title="Are you sure you want to delete this profile?"
                            onConfirm={() => handleDelete(record.id)}
                            okText="Yes"
                            cancelText="No"
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
            title="Agent Profiles"
            extra={
                <Space>
                    <Button 
                        type="primary"
                        icon={<UploadOutlined />}
                        onClick={() => setUploadModalVisible(true)}
                    >
                        Upload Profile
                    </Button>
                </Space>
            }
        >
            <Input.Search
                placeholder="Search profiles"
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
                title="Upload Profile"
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
                        Cancel
                    </Button>,
                    <Button 
                        key="upload" 
                        type="primary" 
                        onClick={handleUpload}
                        loading={uploading}
                        disabled={fileList.length === 0}
                    >
                        Upload
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
                        <p className="ant-upload-text">Click or drag file to this area to upload</p>
                        <p className="ant-upload-hint">
                            Support for JSON files. The file should contain agent profile data.
                        </p>
                    </Upload.Dragger>
                    <Input.TextArea
                        placeholder="Enter description for this profile"
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