import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import AgentForm from './AgentForm';
import storageService, { STORAGE_KEYS, ConfigItem } from '../../services/storageService';
import configService from '../../services/configService';
import { AgentsConfig } from '../../types/config';

const AgentList: React.FC = () => {
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
      const data = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.AGENTS);
      setAgents(data);
    } catch (error) {
      message.error('Failed to load agents');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    const init = async () => {
      await storageService.initializeExampleData();
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
      await storageService.deleteConfig(STORAGE_KEYS.AGENTS, id);
      message.success('Agent deleted successfully');
      loadAgents();
    } catch (error) {
      message.error('Failed to delete agent');
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

      const configData: ConfigItem = {
        id: currentAgent?.id || `agent_${Date.now()}`,
        name: metaValues.name,
        description: metaValues.description || '',
        config: formValues,
        createdAt: currentAgent?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      await storageService.saveConfig(STORAGE_KEYS.AGENTS, configData);

      message.success(`Agent ${currentAgent ? 'updated' : 'created'} successfully`);
      setIsModalVisible(false);
      loadAgents();
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
              title="Are you sure you want to delete this agent?"
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
      title="Agent Configurations"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Create New</Button>}
    >
      <Input.Search
        placeholder="Search agents"
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
        title={currentAgent ? "Edit Agent" : "Create Agent"}
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
