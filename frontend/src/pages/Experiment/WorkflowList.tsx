import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import WorkflowForm from './WorkflowForm';
import storageService, { STORAGE_KEYS, ConfigItem } from '../../services/storageService';
import configService from '../../services/configService';
import { ExpConfig } from '../../types/config';

const WorkflowList: React.FC = () => {
  const [workflows, setWorkflows] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<ConfigItem | null>(null);
  const [formValues, setFormValues] = useState<Partial<ExpConfig>>({});
  const [metaForm] = Form.useForm();

  // Load workflow configurations
  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const data = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.WORKFLOWS);
      setWorkflows(data);
    } catch (error) {
      message.error('Failed to load workflows');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    const init = async () => {
      await storageService.initializeExampleData();
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
    setFormValues(workflow.config);
    metaForm.setFieldsValue({
      name: workflow.name,
      description: workflow.description
    });
    setIsModalVisible(true);
  };

  // Handle duplicate workflow
  const handleDuplicate = (workflow: ConfigItem) => {
    setCurrentWorkflow(null);
    setFormValues(workflow.config);
    metaForm.setFieldsValue({
      name: `${workflow.name} (Copy)`,
      description: workflow.description
    });
    setIsModalVisible(true);
  };

  // Handle delete workflow
  const handleDelete = async (id: string) => {
    try {
      await storageService.deleteConfig(STORAGE_KEYS.WORKFLOWS, id);
      message.success('Workflow deleted successfully');
      loadWorkflows();
    } catch (error) {
      message.error('Failed to delete workflow');
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
      
      const configData: ConfigItem = {
        id: currentWorkflow?.id || `workflow_${Date.now()}`,
        name: metaValues.name,
        description: metaValues.description || '',
        config: formValues,
        createdAt: currentWorkflow?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      await storageService.saveConfig(STORAGE_KEYS.WORKFLOWS, configData);
      
      message.success(`Workflow ${currentWorkflow ? 'updated' : 'created'} successfully`);
      setIsModalVisible(false);
      loadWorkflows();
    } catch (error) {
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
      render: (text: string) => new Date(text).toLocaleString(),
      sorter: (a: ConfigItem, b: ConfigItem) => new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: ConfigItem) => (
        <Space size="small">
          <Tooltip title="Edit">
            <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button icon={<CopyOutlined />} size="small" onClick={() => handleDuplicate(record)} />
          </Tooltip>
          <Tooltip title="Export">
            <Button icon={<ExportOutlined />} size="small" onClick={() => handleExport(record)} />
          </Tooltip>
          <Tooltip title="Delete">
            <Popconfirm
              title="Are you sure you want to delete this workflow?"
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
      title="Workflow Configurations" 
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Create New</Button>}
    >
      <Input.Search
        placeholder="Search workflows"
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
        title={currentWorkflow ? "Edit Workflow" : "Create Workflow"}
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
        
        <Card title="Workflow Settings">
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
