import React, { useEffect, useState } from 'react';
import { Form, Input, InputNumber, Select, Card, Tabs, Button, Space, Radio, message, Row, Col } from 'antd';
import { AgentConfig, AgentsConfig } from '../../types/config';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { fetchCustom } from '../../components/fetch';
import { useTranslation } from 'react-i18next';

const { TabPane } = Tabs;
const { Option } = Select;

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  // ... 其他字段
}

interface AgentProfile {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  count: number;
  created_at: string;
  file_path: string;
}

interface AgentFormProps {
  value: Partial<AgentsConfig>;
  onChange: (value: Partial<AgentsConfig>) => void;
}

const AgentForm: React.FC<AgentFormProps> = ({ value, onChange }) => {
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = React.useState('1');
  const [citizenConfigMode, setCitizenConfigMode] = React.useState('manual');
  const [selectedCitizenProfile, setSelectedCitizenProfile] = React.useState({});
  const [selectedCustomProfiles, setSelectedCustomProfiles] = React.useState<{[key: number]: string}>({});
  const [distributionsState, setDistributionsState] = React.useState({});
  const addDistributionRef = React.useRef(null);
  const [manualDistributions, setManualDistributions] = React.useState({});
  const [templates, setTemplates] = useState<AgentTemplate[]>([]);
  const [profiles, setProfiles] = useState<AgentProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [customConfigMode, setCustomConfigMode] = React.useState('manual');
  const { t } = useTranslation();


  // Define distribution type options
  const distributionTypeOptions = [
    { label: 'Choice', value: 'choice' },
    { label: 'Uniform Integer', value: 'uniform_int' },
    { label: 'Uniform Float', value: 'uniform_float' },
    { label: 'Normal', value: 'normal' },
    { label: 'Constant', value: 'constant' },
  ];

  // Initialize distributionsState when component mounts
  React.useEffect(() => {
    const formValues = form.getFieldsValue();
    
    if (formValues.citizens) {
      const newDistributionsState = {};
      
      formValues.citizens.forEach((group, index) => {
        if (group.memory_distributions) {
          // 不再转换为数组，保持对象格式
          newDistributionsState[index] = group.memory_distributions;
        } else {
          // 初始化为空对象而不是空数组
          newDistributionsState[index] = {};
        }
      });
      
      setDistributionsState(newDistributionsState);
    }
  }, []);

  // Load templates
  useEffect(() => {
    const loadTemplates = async () => {
      setLoading(true);
      try {
        const response = await fetchCustom('/api/agent-templates');
        if (response.ok) {
          const data = await response.json();
          setTemplates(data.data);
        } else {
          message.error('Failed to load templates');
        }
      } catch (error) {
        message.error('Error loading templates');
      } finally {
        setLoading(false);
      }
    };

    loadTemplates();
  }, []);

  // Load profiles
  useEffect(() => {
    const loadProfiles = async () => {
      try {
        const response = await fetchCustom('/api/agent-profiles');
        if (response.ok) {
          const data = await response.json();
          setProfiles(data.data || []);
        } else {
          message.error('Failed to load profiles');
        }
      } catch (error) {
        message.error('Error loading profiles');
      }
    };

    loadProfiles();
  }, []);

  // Handle citizen profile selection
  const handleCitizenProfileSelect = (filePath: string, citizenIndex: number) => {
    setSelectedCitizenProfile(prev => ({
      ...prev,
      [citizenIndex]: filePath
    }));
    
    // Update form values based on selected profile
    const formValues = form.getFieldsValue();
    formValues.citizens[citizenIndex] = {
      ...formValues.citizens[citizenIndex],
      agent_class: 'citizen',
      memory_from_file: filePath
    };
    
    form.setFieldsValue(formValues);
    onChange(formValues);
  };

  // Handle custom profile selection
  const handleCustomProfileSelect = (filePath: string, customIndex: number) => {
    setSelectedCustomProfiles(prev => ({
      ...prev,
      [customIndex]: filePath
    }));
    
    // Update form values based on selected profile
    const formValues = form.getFieldsValue();
    formValues.customs[customIndex] = {
      ...formValues.customs[customIndex],
      memory_from_file: filePath
    };
    
    form.setFieldsValue(formValues);
    onChange(formValues);
  };

  // Render distribution form based on type
  const renderDistributionForm = (type, basePath) => {
    switch (type) {
      case 'choice':
      return (
          <Form.Item
            name={[...basePath, 'params', 'choices']}
            label="Choices (comma separated)"
            rules={[{ required: true, message: 'Please enter choices' }]}
          >
            <Input placeholder="e.g. option1, option2, option3" />
          </Form.Item>
      );
      case 'uniform_int':
      case 'uniform_float':
      return (
          <>
          <Form.Item
              name={[...basePath, 'params', 'low']}
                  label="Minimum Value"
              rules={[{ required: true, message: 'Please enter minimum value' }]}
              initialValue={0}
                >
              <InputNumber style={{ width: '100%' }} step={0.1} />
                </Form.Item>
                <Form.Item
              name={[...basePath, 'params', 'high']}
                  label="Maximum Value"
              rules={[{ required: true, message: 'Please enter maximum value' }]}
              initialValue={1}
                >
              <InputNumber style={{ width: '100%' }} step={0.1} />
                </Form.Item>
          </>
        );
      case 'normal':
        return (
          <>
                <Form.Item
              name={[...basePath, 'params', 'loc']}
                  label="Mean"
              rules={[{ required: true, message: 'Please enter mean value' }]}
              initialValue={0}
                >
              <InputNumber style={{ width: '100%' }} step={0.1} />
                </Form.Item>
                <Form.Item
              name={[...basePath, 'params', 'scale']}
                  label="Standard Deviation"
              rules={[{ required: true, message: 'Please enter standard deviation' }]}
              initialValue={1}
                >
              <InputNumber style={{ width: '100%' }} step={0.1} min={0} />
                </Form.Item>
          </>
      );
      case 'constant':
        return (
          <Form.Item
            name={[...basePath, 'params', 'val']}
            label="Value"
            rules={[{ required: true, message: 'Please enter constant value' }]}
            initialValue=""
          >
            <Input />
          </Form.Item>
        );
      default:
        return null;
    }
  };

  return (
    <>
      <Card bordered={false}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            citizens: [{ number: 10, agent_class: 'citizen', memory_distributions: {} }],
            firms: [{ number: 1, agent_class: 'firm' }],
            governments: [{ number: 1, agent_class: 'government' }],
            banks: [{ number: 1, agent_class: 'bank' }],
            nbs: [{ number: 1, agent_class: 'nbs' }],
            customs: []
          }}
          onValuesChange={async (_, allValues) => {
            // 处理自定义模板
            const customAgents = allValues.customs || [];
            const citizenAgents = allValues.citizens || [];
            
            console.log('原始表单数据:', JSON.stringify(allValues, null, 2));
            console.log('自定义模板数据:', JSON.stringify(customAgents, null, 2));
            console.log('公民数据:', JSON.stringify(citizenAgents, null, 2));
            
            // 获取所有自定义模板的数据
            const customCitizens = await Promise.all(
              customAgents.map(async (custom) => {
                if (custom.templateId) {
                  try {
                    const response = await fetchCustom(`/api/agent-templates/${custom.templateId}`);
                    if (response.ok) {
                      const template = (await response.json()).data;
                      console.log('获取到的模板数据:', JSON.stringify(template, null, 2));

                      // 转换blocks格式
                      const convertedBlocks = {};
                      Object.entries(template.blocks).forEach(([key, value]) => {
                        // 确保block key是小写的
                        const blockKey = key.toLowerCase();
                        convertedBlocks[blockKey] = value;
                      });

                      // 如果使用 profile，不包含 memory_distributions
                      if (custom.memory_from_file) {
                        return {
                          agent_class: 'citizen',
                          memory_from_file: custom.memory_from_file,
                          agent_params: template.agent_params,
                          blocks: convertedBlocks
                        };
                      }

                      // 转换memory_distributions格式
                      const convertedDistributions = {};
                      Object.entries(template.memory_distributions).forEach(([key, value]: [string, any]) => {
                        if (value.type === 'choice') {
                          convertedDistributions[key] = {
                            dist_type: 'choice',
                            choices: value.choices || value.params?.choices,
                            weights: value.weights || value.params?.weights
                          };
                        } else if (value.type === 'uniform_int') {
                          convertedDistributions[key] = {
                            dist_type: 'uniform_int',
                            min_value: value.min_value || value.params?.min_value,
                            max_value: value.max_value || value.params?.max_value
                          };
                        } else if (value.type === 'normal') {
                          convertedDistributions[key] = {
                            dist_type: 'normal',
                            mean: value.mean || value.params?.mean,
                            std: value.std || value.params?.std
                          };
                        }
                      });

                      return {
                        number: custom.number,
                        agent_class: 'citizen',
                        memory_distributions: convertedDistributions,
                        agent_params: template.agent_params,
                        blocks: convertedBlocks
                      };
                    }
                  } catch (error) {
                    console.error('Error fetching template:', error);
                  }
                }
                return null;
              })
            );

            // 过滤掉空值并合并到citizens中
            const validCustomCitizens = customCitizens.filter(Boolean);
            console.log('处理后的自定义公民数据:', JSON.stringify(validCustomCitizens, null, 2));
            
            // 转换现有citizens的memory_distributions格式
            const convertedCitizens = citizenAgents.map(citizen => {
              if (!citizen.memory_distributions) return citizen;

              const convertedDistributions = {};
              Object.entries(citizen.memory_distributions).forEach(([key, value]: [string, any]) => {
                if (value.type === 'choice') {
                  convertedDistributions[key] = {
                    dist_type: 'choice',
                    choices: value.choices,
                    weights: value.weights
                  };
                } else if (value.type === 'uniform_int') {
                  convertedDistributions[key] = {
                    dist_type: 'uniform_int',
                    min_value: value.min_value,
                    max_value: value.max_value
                  };
                } else if (value.type === 'normal') {
                  convertedDistributions[key] = {
                    dist_type: 'normal',
                    mean: value.mean,
                    std: value.std
                  };
                }
              });

              // 转换blocks格式
              const convertedBlocks = {};
              if (citizen.blocks) {
                Object.entries(citizen.blocks).forEach(([key, value]) => {
                  const blockKey = key.toLowerCase();
                  convertedBlocks[blockKey] = value;
                });
              }

              return {
                ...citizen,
                memory_distributions: convertedDistributions,
                blocks: convertedBlocks
              };
            });
            
            // 构造最终的数据
            const transformedValues = {
              citizens: [
                ...convertedCitizens,
                ...validCustomCitizens
              ],
              firms: allValues.firms?.length ? allValues.firms : [{ number: 1, agent_class: 'firm' }],
              governments: allValues.governments?.length ? allValues.governments : [{ number: 1, agent_class: 'government' }],
              banks: allValues.banks?.length ? allValues.banks : [{ number: 1, agent_class: 'bank' }],
              nbs: allValues.nbs?.length ? allValues.nbs : [{ number: 1, agent_class: 'nbs' }],
            };
            
            console.log('最终提交的数据:', JSON.stringify(transformedValues, null, 2));
            onChange(transformedValues);
          }}
        >
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane tab="Citizens" key="1">
              <Card bordered={false}>
                <Form.Item label="Configuration Mode">
                  <Radio.Group
                    value={citizenConfigMode}
                    onChange={(e) => setCitizenConfigMode(e.target.value)}
                  >
                    <Radio.Button value="manual">Manual</Radio.Button>
                    <Radio.Button value="profile">Use Profile</Radio.Button>
                  </Radio.Group>
                </Form.Item>
                
                {citizenConfigMode === 'profile' ? (
                  <Form.List name="citizens" initialValue={[{ agent_class: 'citizen' }]}>
                    {(fields, { add, remove }) => (
                      <>
                        {fields.map(({ key, name, ...restField }) => (
                          <Card
                            key={key}
                            title={`${t('form.agent.citizenGroup')} ${name + 1}`}
                            style={{ marginBottom: 16 }}
                            extra={
                              fields.length > 1 ? (
                                <MinusCircleOutlined onClick={() => remove(name)} />
                              ) : null
                            }
                          >
                            <Form.Item
                              {...restField}
                              name={[name, 'memory_from_file']}
                              label="Select Profile"
                              rules={[{ required: true, message: 'Please select a profile' }]}
                            >
                              <Select
                                placeholder="Select a profile"
                                loading={loading}
                                value={selectedCitizenProfile[name]}
                                onChange={(value) => handleCitizenProfileSelect(value, name)}
                              >
                                {profiles.map(profile => (
                                  <Option key={profile.id} value={profile.file_path}>
                                    {profile.name}
                                    <span style={{ color: '#999', marginLeft: 8 }}>
                                      ({profile.count} records)
                                    </span>
                                  </Option>
                                ))}
                              </Select>
                            </Form.Item>
                          </Card>
                        ))}
                        <Button
                          type="dashed"
                          onClick={() => add({ agent_class: 'citizen' })}
                          block
                          icon={<PlusOutlined />}
                        >
                          {t('form.agent.addGroup')}
                        </Button>
                      </>
                    )}
                  </Form.List>
                ) : (
                  <Form.List name="citizens" initialValue={[{ number: 10, agent_class: 'citizen', memory_distributions: {} }]}>
                    {(fields, { add, remove }) => (
                      <>
                        {fields.map(({ key, name, ...restField }) => (
                          <Card
                            key={key}
                            title={`${t('form.agent.citizenGroup')} ${name + 1}`}
                            style={{ marginBottom: 16 }}
                            extra={
                              fields.length > 1 ? (
                                <MinusCircleOutlined onClick={() => remove(name)} />
                              ) : null
                            }
                          >
                            <Form.Item
                              {...restField}
                              name={[name, 'number']}
                              label={t('form.agent.numberLabel')}
                              rules={[{ required: true, message: t('form.agent.numberPlaceholder') }]}
                            >
                              <InputNumber min={1} style={{ width: '100%' }} />
                            </Form.Item>
                            
                            <div>
                              {Object.entries(form.getFieldValue(['citizens', name, 'memory_distributions']) || {}).map(([distName, dist]) => (
                                <Card
                                  key={distName}
                                  title={`${t('form.agent.distributionTitle')} ${parseInt(distName.split('_')[1]) + 1}`}
                                  style={{ marginBottom: 8 }}
                                  size="small"
                                  extra={
                                    <Button
                                      icon={<MinusCircleOutlined />}
                                      onClick={() => {
                                        const currentValues = form.getFieldsValue();
                                        const { [distName]: _, ...rest } = currentValues.citizens[name].memory_distributions;
                                        currentValues.citizens[name].memory_distributions = rest;
                                        form.setFieldsValue(currentValues);
                                      }}
                                      size="small"
                                      danger
                                    />
                                  }
                                >
                                  <Form.Item
                                    name={['citizens', name, 'memory_distributions', distName, 'name']}
                                    label={t('form.agent.attributeName')}
                                    rules={[{ required: true, message: 'Please enter attribute name' }]}
                                  >
                                    <Input placeholder={t('form.agent.attributePlaceholder')} />
                                  </Form.Item>
                                  
                                  <Form.Item
                                    name={['citizens', name, 'memory_distributions', distName, 'type']}
                                    label={t('form.agent.distributionType')}
                                    rules={[{ required: true, message: 'Please select distribution type' }]}
                                  >
                                    <Select
                                      options={distributionTypeOptions}
                                      onChange={(value) => {
                                        // Reset params when distribution type changes
                                        const currentValues = form.getFieldsValue();
                                        let defaultParams = {};
                                        
                                        switch (value) {
                                          case 'choice':
                                            defaultParams = { choices: '' };
                                            break;
                                          case 'uniform_int':
                                          case 'uniform_float':
                                            defaultParams = { low: 0, high: 10 };
                                            break;
                                          case 'normal':
                                            defaultParams = { loc: 0, scale: 1 };
                                            break;
                                          case 'constant':
                                            defaultParams = { val: '' };
                                            break;
                                        }
                                        
                                        currentValues.citizens[name].memory_distributions[distName].params = defaultParams;
                                        form.setFieldsValue(currentValues);
                                      }}
                                    />
                                  </Form.Item>
                                  
                                  {renderDistributionForm(
                                    form.getFieldValue(['citizens', name, 'memory_distributions', distName, 'type']),
                                    ['citizens', name, 'memory_distributions', distName]
                                  )}
                                </Card>
                              ))}
                              <Button
                                type="dashed"
                                onClick={() => {
                                  const currentValues = form.getFieldsValue();
                                  const currentDistributions = currentValues.citizens[name].memory_distributions || {};
                                  const newDistName = `dist_${Object.keys(currentDistributions).length}`;
                                  
                                  currentValues.citizens[name].memory_distributions = {
                                    ...currentDistributions,
                                    [newDistName]: {
                                      name: '',
                                      type: 'constant',
                                      params: { val: '' }
                                    }
                                  };
                                  
                                  form.setFieldsValue(currentValues);
                                }}
                                block
                                icon={<PlusOutlined />}
                                size="small"
                                style={{ marginBottom: 16 }}
                              >
                                {t('form.agent.addDistribution')}
                              </Button>
                            </div>
                          </Card>
                        ))}
                        <Button
                          type="dashed"
                          onClick={() => add({ number: 10, agent_class: 'citizen', memory_distributions: {} })}
                          block
                          icon={<PlusOutlined />}
                        >
                          {t('form.agent.addGroup')}
                        </Button>
                      </>
                    )}
                  </Form.List>
                )}
              </Card>
            </TabPane>

            <TabPane tab="Firms" key="2">
              <Card bordered={false}>
                <Form.List name="firms" initialValue={[{ number: 1, agent_class: 'firm' }]}>
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card
                          key={key}
                          title={`${t('form.agent.firmGroup')} ${name + 1}`}
                          style={{ marginBottom: 16 }}
                          extra={
                            fields.length > 1 ? (
                              <MinusCircleOutlined onClick={() => remove(name)} />
                            ) : null
                          }
                        >
                          <Form.Item
                            {...restField}
                            name={[name, 'number']}
                            label={t('form.agent.numberLabel')}
                            rules={[{ required: true, message: t('form.agent.numberPlaceholder') }]}
                          >
                            <InputNumber min={1} style={{ width: '100%' }} />
                          </Form.Item>
                        </Card>
                      ))}
                      <Button
                        type="dashed"
                        onClick={() => add({ number: 1 })}
                        block
                        icon={<PlusOutlined />}
                      >
                        {t('form.agent.addGroup')}
                      </Button>
                    </>
                  )}
                </Form.List>
              </Card>
            </TabPane>

            <TabPane tab="Government" key="3">
              <Card bordered={false}>
                <Form.List name="governments" initialValue={[{ number: 1, agent_class: 'government' }]}>
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card
                          key={key}
                          title={`${t('form.agent.governmentGroup')} ${name + 1}`}
                          style={{ marginBottom: 16 }}
                          extra={
                            fields.length > 1 ? (
                              <MinusCircleOutlined onClick={() => remove(name)} />
                            ) : null
                          }
                        >
                          <Form.Item
                            {...restField}
                            name={[name, 'number']}
                            label={t('form.agent.numberLabel')}
                            rules={[{ required: true, message: t('form.agent.numberPlaceholder') }]}
                          >
                            <InputNumber min={1} style={{ width: '100%' }} />
                          </Form.Item>
                        </Card>
                      ))}
                      <Button
                        type="dashed"
                        onClick={() => add({ number: 1 })}
                        block
                        icon={<PlusOutlined />}
                      >
                        {t('form.agent.addGroup')}
                      </Button>
                    </>
                  )}
                </Form.List>
              </Card>
            </TabPane>

            <TabPane tab="Banks" key="4">
              <Card bordered={false}>
                <Form.List name="banks" initialValue={[{ number: 1, agent_class: 'bank' }]}>
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card
                          key={key}
                          title={`${t('form.agent.bankGroup')} ${name + 1}`}
                          style={{ marginBottom: 16 }}
                          extra={
                            fields.length > 1 ? (
                              <MinusCircleOutlined onClick={() => remove(name)} />
                            ) : null
                          }
                        >
                          <Form.Item
                            {...restField}
                            name={[name, 'number']}
                            label={t('form.agent.numberLabel')}
                            rules={[{ required: true, message: t('form.agent.numberPlaceholder') }]}
                          >
                            <InputNumber min={1} style={{ width: '100%' }} />
                          </Form.Item>
                        </Card>
                      ))}
                      <Button
                        type="dashed"
                        onClick={() => add({ number: 1 })}
                        block
                        icon={<PlusOutlined />}
                      >
                        {t('form.agent.addGroup')}
                      </Button>
                    </>
                  )}
                </Form.List>
              </Card>
            </TabPane>

            <TabPane tab="NBS" key="5">
              <Card bordered={false}>
                <Form.List name="nbs" initialValue={[{ number: 1, agent_class: 'nbs' }]}>
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card
                          key={key}
                          title={`${t('form.agent.nbsGroup')} ${name + 1}`}
                          style={{ marginBottom: 16 }}
                          extra={
                            fields.length > 1 ? (
                              <MinusCircleOutlined onClick={() => remove(name)} />
                            ) : null
                          }
                        >
                          <Form.Item
                            {...restField}
                            name={[name, 'number']}
                            label={t('form.agent.numberLabel')}
                            rules={[{ required: true, message: t('form.agent.numberPlaceholder') }]}
                          >
                            <InputNumber min={1} style={{ width: '100%' }} />
                          </Form.Item>
                        </Card>
                      ))}
                      <Button
                        type="dashed"
                        onClick={() => add({ number: 1 })}
                        block
                        icon={<PlusOutlined />}
                      >
                        {t('form.agent.addGroup')}
                      </Button>
                    </>
                  )}
                </Form.List>
              </Card>
            </TabPane>

            <TabPane tab="Custom" key="6">
              <Card bordered={false}>
                <Form.List name="customs" initialValue={[{}]}>
                  {(fields, { add, remove }) => (
                    <>
                      {fields.map(({ key, name, ...restField }) => (
                        <Card
                          key={key}
                          title={`${t('form.agent.customGroup')} ${name + 1}`}
                          style={{ marginBottom: 16 }}
                          extra={
                            fields.length > 1 ? (
                              <MinusCircleOutlined onClick={() => remove(name)} />
                            ) : null
                          }
                        >
                          <Form.Item
                            {...restField}
                            name={[name, 'templateId']}
                            label="Agent Template"
                            rules={[{ required: true, message: 'Please select a template' }]}
                          >
                            <Select
                              loading={loading}
                              placeholder="Select a template"
                              style={{ width: '100%' }}
                            >
                              {templates.map(template => (
                                <Option key={template.id} value={template.id}>
                                  {template.name}
                                  <span style={{ color: '#999', marginLeft: 8 }}>
                                    {template.description}
                                  </span>
                                </Option>
                              ))}
                            </Select>
                          </Form.Item>

                          <Form.Item label="Configuration Mode">
                            <Radio.Group
                              value={customConfigMode}
                              onChange={(e) => setCustomConfigMode(e.target.value)}
                            >
                              <Radio.Button value="manual">Set Number</Radio.Button>
                              <Radio.Button value="profile">Use Profile</Radio.Button>
                            </Radio.Group>
                          </Form.Item>

                          {customConfigMode === 'manual' ? (
                            <Form.Item
                              {...restField}
                              name={[name, 'number']}
                              label={t('form.agent.numberLabel')}
                              rules={[{ required: true, message: t('form.agent.numberPlaceholder') }]}
                            >
                              <InputNumber min={1} style={{ width: '100%' }} />
                            </Form.Item>
                          ) : (
                            <Form.Item
                              {...restField}
                              name={[name, 'memory_from_file']}
                              label="Select Profile"
                              rules={[{ required: true, message: 'Please select a profile' }]}
                            >
                              <Select
                                placeholder="Select a profile"
                                loading={loading}
                                value={selectedCustomProfiles[name]}
                                onChange={(value) => handleCustomProfileSelect(value, name)}
                              >
                                {profiles.map(profile => (
                                  <Option key={profile.id} value={profile.file_path}>
                                    {profile.name}
                                    <span style={{ color: '#999', marginLeft: 8 }}>
                                      ({profile.count} records)
                                    </span>
                                  </Option>
                                ))}
                              </Select>
                            </Form.Item>
                          )}
                        </Card>
                      ))}
                      <Button
                        type="dashed"
                        onClick={() => add({})}
                        block
                        icon={<PlusOutlined />}
                      >
                        {t('form.agent.addGroup')}
                      </Button>
                    </>
                  )}
                </Form.List>
              </Card>
            </TabPane>
          </Tabs>
        </Form>
      </Card>
    </>
  );
};

export default AgentForm; 