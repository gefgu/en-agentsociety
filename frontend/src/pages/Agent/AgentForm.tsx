import React, { useEffect, useState } from 'react';
import { Form, InputNumber, Select, Button, message, Row, Col, Typography } from 'antd';
import { AgentConfig, AgentsConfig } from '../../types/config';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { fetchCustom } from '../../components/fetch';
import { useTranslation } from 'react-i18next';

const { Option } = Select;
const { Text } = Typography;

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
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
  const [selectedCitizenProfile, setSelectedCitizenProfile] = React.useState({});
  const [selectedCustomProfiles, setSelectedCustomProfiles] = React.useState<{ [key: number]: string }>({});
  const [templates, setTemplates] = useState<AgentTemplate[]>([]);
  const [profiles, setProfiles] = useState<AgentProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

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

    const formValues = form.getFieldsValue();
    formValues.customs[customIndex] = {
      ...formValues.customs[customIndex],
      memory_from_file: filePath
    };

    form.setFieldsValue(formValues);
    onChange(formValues);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        citizens: [],
        supervisor: [],
        firms: [{ number: 1, agent_class: 'firm' }],
        governments: [{ number: 1, agent_class: 'government' }],
        banks: [{ number: 1, agent_class: 'bank' }],
        nbs: [{ number: 1, agent_class: 'nbs' }],
      }}
      onValuesChange={async (_, allValues) => {
        const citizenAgents = allValues.citizens || [];

        const processAgents = async (agents) => {
          const citizens = [];
          let supervisor = null;

          await Promise.all(
            agents.map(async (agent) => {
              if (agent.templateId) {
                try {
                  const response = await fetchCustom(`/api/agent-templates/${agent.templateId}`);
                  if (response.ok) {
                    const template = (await response.json()).data;
                    const convertedBlocks = {};
                    Object.entries(template.blocks).forEach(([key, value]) => {
                      const blockKey = key.toLowerCase();
                      convertedBlocks[blockKey] = value;
                    });

                    const processedAgent = agent.memory_from_file ? {
                      agent_class: template.agent_class || 'citizen',
                      memory_from_file: agent.memory_from_file,
                      agent_params: template.agent_params,
                      blocks: convertedBlocks
                    } : {
                      number: agent.number,
                      agent_class: template.agent_class || 'citizen',
                      agent_params: template.agent_params,
                      blocks: convertedBlocks
                    };

                    if (template.agent_type === 'supervisor') {
                      supervisor = processedAgent;
                    } else {
                      citizens.push(processedAgent);
                    }
                  }
                } catch (error) {
                  console.error('Error fetching template:', error);
                }
              }
            })
          );

          return { citizens, supervisor };
        };

        const { citizens, supervisor } = await processAgents(citizenAgents);

        // 确保 citizens 至少有一个元素
        const transformedValues = {
          citizens: citizens.length > 0 ? citizens : [{ agent_class: 'citizen', number: 1 }],
          supervisor: supervisor,
          firms: [{ number: allValues.firmNumber >= 0 ? allValues.firmNumber : 1, agent_class: 'firm' }],
          governments: [{ number: allValues.governmentNumber >= 0 ? allValues.governmentNumber : 1, agent_class: 'government' }],
          banks: [{ number: allValues.bankNumber >= 0 ? allValues.bankNumber : 1, agent_class: 'bank' }],
          nbs: [{ number: allValues.nbsNumber >= 0 ? allValues.nbsNumber : 1, agent_class: 'nbs' }],
        };

        onChange(transformedValues);
      }}
    >
      <div style={{ marginBottom: 8 }}>
        <Text strong>{t('form.agent.citizenGroup')}</Text>
      </div>
      <Form.List name="citizens" initialValue={[{}]}>
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <Row key={key} gutter={8} align="middle" style={{ marginBottom: 8 }}>
                <Col span={8}>
                  <Form.Item
                    {...restField}
                    name={[name, 'templateId']}
                    label={t('form.agent.selectTemplate')}
                    rules={[{ required: true, message: t('form.agent.pleaseSelectTemplate') }]}
                    style={{ marginBottom: 8 }}
                  >
                    <Select
                      loading={loading}
                      placeholder={t('form.agent.selectTemplatePlaceholder')}
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
                </Col>
                <Col span={4}>
                  <Form.Item
                    {...restField}
                    name={[name, 'number']}
                    label={t('form.agent.numberLabel')}
                    rules={[
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          const profile = getFieldValue(['citizens', name, 'memory_from_file']);
                          if (!value && !profile) {
                            return Promise.reject(new Error(t('form.agent.numberOrProfileRequired')));
                          }
                          if (value && profile) {
                            return Promise.reject(new Error(t('form.agent.numberOrProfileExclusive')));
                          }
                          return Promise.resolve();
                        },
                      }),
                    ]}
                    dependencies={[['citizens', name, 'memory_from_file']]}
                    style={{ marginBottom: 8 }}
                  >
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    {...restField}
                    name={[name, 'memory_from_file']}
                    label={t('form.agent.selectProfile')}
                    rules={[
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          const number = getFieldValue(['citizens', name, 'number']);
                          if (!value && !number) {
                            return Promise.reject(new Error(t('form.agent.numberOrProfileRequired')));
                          }
                          if (value && number) {
                            return Promise.reject(new Error(t('form.agent.numberOrProfileExclusive')));
                          }
                          return Promise.resolve();
                        },
                      }),
                    ]}
                    dependencies={[['citizens', name, 'number']]}
                    style={{ marginBottom: 8 }}
                  >
                    <Select
                      placeholder={t('form.agent.selectProfilePlaceholder')}
                      loading={loading}
                      value={selectedCustomProfiles[name]}
                      onChange={(value) => handleCustomProfileSelect(value, name)}
                      allowClear
                    >
                      {profiles.map(profile => (
                        <Option key={profile.id} value={profile.file_path}>
                          {profile.name}
                          <span style={{ color: '#999', marginLeft: 8 }}>
                            ({profile.count} {t('form.agent.records')})
                          </span>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Button
                    type="text"
                    danger
                    icon={<MinusCircleOutlined />}
                    onClick={() => remove(name)}
                    style={{ marginTop: 24 }}
                  />
                </Col>
              </Row>
            ))}
            <Button
              type="dashed"
              onClick={() => add({})}
              block
              icon={<PlusOutlined />}
              style={{ marginBottom: 16 }}
            >
              {t('form.agent.addGroup')}
            </Button>
          </>
        )}
      </Form.List>
      <div style={{ marginBottom: 8 }}>
        <Text strong>{t('form.agent.institutions')}</Text>
      </div>
      <Row gutter={16}>
        <Col span={6}>
          <Form.Item
            name="firmNumber"
            label={t('form.agent.firmGroup')}
            initialValue={1}
            rules={[{ required: true, message: t('form.agent.pleaseInputFirmNumber') }]}
            style={{ marginBottom: 8 }}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item
            name="governmentNumber"
            label={t('form.agent.governmentGroup')}
            initialValue={1}
            rules={[{ required: true, message: t('form.agent.pleaseInputGovernmentNumber') }]}
            style={{ marginBottom: 8 }}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item
            name="bankNumber"
            label={t('form.agent.bankGroup')}
            initialValue={1}
            rules={[{ required: true, message: t('form.agent.pleaseInputBankNumber') }]}
            style={{ marginBottom: 8 }}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item
            name="nbsNumber"
            label={t('form.agent.nbsGroup')}
            initialValue={1}
            rules={[{ required: true, message: t('form.agent.pleaseInputNbsNumber') }]}
            style={{ marginBottom: 8 }}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>
    </Form>
  );
};

export default AgentForm; 