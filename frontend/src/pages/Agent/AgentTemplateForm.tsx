import React, { useState, useEffect, useContext, useMemo } from 'react';
import { Form, Input, Card, Row, Col, Button, Switch, InputNumber, Select, Space, message, Tooltip, Table, Modal, Typography, Spin, Tabs, Empty } from 'antd';
import type { FormInstance } from 'antd/es/form';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchCustom } from '../../components/fetch';
import { QuestionCircleOutlined } from '@ant-design/icons';
import MonacoPromptEditor from '../../components/MonacoPromptEditor';
import { useTranslation } from 'react-i18next';

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
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
  agent_params: Record<string, any>;
  blocks: {
    [key: string]: {
      params?: Record<string, any>;
    };
  };
  created_at: string;
  updated_at: string;
  tenant_id?: string;
  agent_type?: string;
  agent_class?: string;
}

// Add default configurations
const defaultProfileFields = {
  name: {
    type: 'choice',
    choices: ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Helen", "Ivy", "Jack"],
    weights: [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
  },
  gender: {
    type: 'choice',
    choices: ["male", "female"],
    weights: [0.5, 0.5]
  },
  age: {
    type: 'uniform_int',
    min_value: 18,
    max_value: 65
  },
  education: {
    type: 'choice',
    choices: ["Doctor", "Master", "Bachelor", "College", "High School"],
    weights: [0.1, 0.2, 0.4, 0.2, 0.1]
  },
  skill: {
    type: 'choice',
    choices: ["Good at problem-solving", "Good at communication", "Good at creativity"],
    weights: [0.33, 0.34, 0.33]
  },
  occupation: {
    type: 'choice',
    choices: ["Student", "Teacher", "Doctor", "Engineer", "Manager"],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2]
  },
  family_consumption: {
    type: 'choice',
    choices: ["low", "medium", "high"],
    weights: [0.3, 0.4, 0.3]
  },
  consumption: {
    type: 'choice',
    choices: ["low", "slightly low", "medium", "slightly high", "high"],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2]
  },
  personality: {
    type: 'choice',
    choices: ["outgoing", "introvert", "ambivert", "extrovert"],
    weights: [0.25, 0.25, 0.25, 0.25]
  },
  income: {
    type: 'uniform_int',
    min_value: 1000,
    max_value: 20000
  },
  currency: {
    type: 'uniform_int',
    min_value: 1000,
    max_value: 100000
  },
  residence: {
    type: 'choice',
    choices: ["city", "suburb", "rural"],
    weights: [0.4, 0.4, 0.2]
  },
  city: {
    type: 'choice',
    choices: ["New York", "Los Angeles", "London", "Paris", "Tokyo"],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2]
  },
  race: {
    type: 'choice',
    choices: ["Chinese", "American", "British", "French", "German"],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2]
  },
  religion: {
    type: 'choice',
    choices: ["none", "Christian", "Muslim", "Buddhist", "Hindu"],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2]
  },
  marriage_status: {
    type: 'choice',
    choices: ["not married", "married", "divorced", "widowed"],
    weights: [0.4, 0.4, 0.1, 0.1]
  }
};

const defaultBaseFields = {
  home: {
    aoi_position: {
      aoi_id: 0
    }
  },
  work: {
    aoi_position: {
      aoi_id: 0
    }
  }
};

// 首先定义字段类型
interface ProfileField {
  label: string;
  type: 'discrete' | 'continuous';
  options?: string[];  // 用于离散型
  defaultParams?: {
    min_value?: number;  // 用于连续型
    max_value?: number;  // 用于连续型
    mean?: number;      // 用于正态分布
    std?: number;       // 用于正态分布
  };
}

// 修改 profileOptions 定义
const profileOptions: Record<string, ProfileField> = {
  name: {
    label: "Name",
    type: 'discrete',
    options: ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Helen", "Ivy", "Jack"],
  },
  gender: {
    label: "Gender",
    type: 'discrete',
    options: ["male", "female"]
  },
  age: {
    label: "Age",
    type: 'continuous',
    defaultParams: { min_value: 18, max_value: 65 }
  },
  education: {
    label: "Education",
    type: 'discrete',
    options: ["Doctor", "Master", "Bachelor", "College", "High School"],
  },
  skill: {
    label: "Skill",
    type: 'discrete',
    options: ["Good at problem-solving", "Good at communication", "Good at creativity"],
  },
  occupation: {
    label: "Occupation",
    type: 'discrete',
    options: ["Student", "Teacher", "Doctor", "Engineer", "Manager"],
  },
  family_consumption: {
    label: "Family Consumption",
    type: 'discrete',
    options: ["low", "medium", "high"],
  },
  consumption: {
    label: "Consumption",
    type: 'discrete',
    options: ["low", "slightly low", "medium", "slightly high", "high"],
  },
  personality: {
    label: "Personality",
    type: 'discrete',
    options: ["outgoing", "introvert", "ambivert", "extrovert"],
  },
  income: {
    label: "Income",
    type: 'continuous',
    defaultParams: {
      min_value: 1000,
      max_value: 20000,
      mean: 5000,
      std: 1000
    }
  },
  currency: {
    label: "Currency",
    type: 'continuous',
    defaultParams: {
      min_value: 1000,
      max_value: 100000,
      mean: 50000,
      std: 10000
    }
  },
  residence: {
    label: "Residence",
    type: 'discrete',
    options: ["city", "suburb", "rural"],
  },
  race: {
    label: "Race",
    type: 'discrete',
    options: ["Chinese", "American", "British", "French", "German"],
  },
  religion: {
    label: "Religion",
    type: 'discrete',
    options: ["none", "Christian", "Muslim", "Buddhist", "Hindu"],
  },
  marriage_status: {
    label: "Marriage Status",
    type: 'discrete',
    options: ["not married", "married", "divorced", "widowed"],
  },
  city: {
    label: "City",
    type: 'discrete',
    options: ["New York", "Los Angeles", "London", "Paris", "Tokyo"],
  }
};



// // 首先添加新的类型定义
// interface Distribution {
//   type: 'choice' | 'uniform_int' | 'normal';
//   params: {
//     choices?: string[];
//     weights?: number[];
//     min_value?: number;
//     max_value?: number;
//     mean?: number;
//     std?: number;
//   };
// }

// interface DistributionConfig {
//   type: 'choice' | 'uniform_int' | 'normal';
//   choices?: string[];
//   min_value?: number;
//   max_value?: number;
//   mean?: number;
//   std?: number;
// }

// Modify the distribution form rendering function
const renderDistributionFields = (fieldName: string, fieldConfig: ProfileField, form: FormInstance) => {
  const { t } = useTranslation();
  const distributionType = Form.useWatch(['profile', fieldName, 'type'], form);

  // 当分布类型改变时，初始化对应的参数
  const handleDistributionTypeChange = (value: string) => {
    if (value === 'uniform_int') {
      form.setFieldsValue({
        profile: {
          [fieldName]: {
            type: value,
            min_value: fieldConfig.defaultParams?.min_value,
            max_value: fieldConfig.defaultParams?.max_value
          }
        }
      });
    } else if (value === 'normal') {
      form.setFieldsValue({
        profile: {
          [fieldName]: {
            type: value,
            mean: fieldConfig.defaultParams?.mean,
            std: fieldConfig.defaultParams?.std
          }
        }
      });
    }
  };

  if (fieldConfig.type === 'discrete') {
    return (
      <div style={{ marginTop: 8 }}>
        <Form.Item
          label={t('form.template.choiceWeights')}
          required
          tooltip={t('form.template.choiceWeightsTooltip')}
        >
          <Table
            size="small"
            pagination={false}
            dataSource={fieldConfig.options?.map((option, index) => ({
              key: index,
              option: option,
              weight: (
                <Form.Item
                  name={['profile', fieldName, 'weights', index]}
                  rules={[{ required: true, message: t('form.template.required') }]}
                  style={{ margin: 0 }}
                >
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    style={{ width: '100%' }}
                    placeholder="0-1"
                  />
                </Form.Item>
              )
            }))}
            columns={[
              {
                title: t('form.template.option'),
                dataIndex: 'option',
                width: '60%'
              },
              {
                title: t('form.template.weight'),
                dataIndex: 'weight',
                width: '40%'
              }
            ]}
          />
        </Form.Item>
      </div>
    );
  } else {
    return (
      <div style={{ marginTop: 8 }}>
        <Form.Item
          name={['profile', fieldName, 'type']}
          label={t('form.template.distributionType')}
          initialValue="uniform_int"
        >
          <Select
            options={[
              { label: t('form.template.uniformDistribution'), value: 'uniform_int' },
              { label: t('form.template.normalDistribution'), value: 'normal' }
            ]}
            onChange={handleDistributionTypeChange}
          />
        </Form.Item>

        {distributionType === 'uniform_int' && (
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={t('form.template.minValue')}
                name={['profile', fieldName, 'min_value']}
                rules={[{ required: true, message: t('form.template.required') }]}
                initialValue={fieldConfig.defaultParams?.min_value}
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label={t('form.template.maxValue')}
                name={['profile', fieldName, 'max_value']}
                rules={[{ required: true, message: t('form.template.required') }]}
                initialValue={fieldConfig.defaultParams?.max_value}
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )}

        {distributionType === 'normal' && (
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={t('form.template.mean')}
                name={['profile', fieldName, 'mean']}
                rules={[{ required: true, message: t('form.template.required') }]}
                initialValue={fieldConfig.defaultParams?.mean}
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label={t('form.template.standardDeviation')}
                name={['profile', fieldName, 'std']}
                rules={[{ required: true, message: t('form.template.required') }]}
                initialValue={fieldConfig.defaultParams?.std}
              >
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
          </Row>
        )}
      </div>
    );
  }
};

// Modify Profile card section rendering
const renderProfileSection = (form: FormInstance) => {
  const { t } = useTranslation();
  return (
    <Card title={t('form.template.profileSection')} bordered={false} style={{ marginBottom: '12px' }}>
      <Row gutter={[12, 12]}>
        {Object.entries(profileOptions).map(([key, config]) => (
          <Col span={24} key={key}>
            <Card size="small" title={config.label} style={{ marginBottom: '8px' }}>
              {config.type === 'discrete' ? (
                <>
                  <Form.Item
                    name={['profile', key, 'type']}
                    label={t('form.template.distributionType')}
                    initialValue="choice"
                    style={{ marginBottom: '8px' }}
                  >
                    <Select
                      options={[{ label: t('form.template.discreteChoice'), value: 'choice' }]}
                      disabled
                    />
                  </Form.Item>
                  <Form.Item
                    name={['profile', key, 'choices']}
                    hidden
                    initialValue={config.options}
                  >
                    <Input />
                  </Form.Item>
                  {renderDistributionFields(key, config, form)}
                </>
              ) : (
                renderDistributionFields(key, config, form)
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
};

// Modify Base Location card
const renderBaseLocation = () => {
  const { t } = useTranslation();
  return (
    <Card title={t('form.template.baseLocation')} bordered={false}>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name={['base', 'home', 'aoi_position', 'aoi_id']}
            label={t('form.template.homeAreaId')}
            rules={[{ required: true }]}
            initialValue={0}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['base', 'work', 'aoi_position', 'aoi_id']}
            label={t('form.template.workAreaId')}
            rules={[{ required: true }]}
            initialValue={0}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>
    </Card>
  );
};


// Add type definitions for context and status
interface ContextItem {
  type: string;
  description: string | null;
  default: any;
}

interface StatusAttribute {
  name: string;
  type: string;
  description: string;
  default: any;
  // whether_embedding: boolean;
}

interface AgentInfo {
  context: Record<string, ContextItem>;
  status_attributes: StatusAttribute[];
  params_type: Record<string, {
    type: string;
    description: string | null;
    default: any;
  }>;
  block_output_type: Record<string, {
    type: string;
    description: string | null;
    default: any;
  }>;
}

// Create AgentContext
const AgentContext = React.createContext<{
  agentInfo: AgentInfo | null;
  setAgentInfo: React.Dispatch<React.SetStateAction<AgentInfo | null>>;
  suggestions: any[];
  setAgentType: React.Dispatch<React.SetStateAction<string>>;
  setAgentClass: React.Dispatch<React.SetStateAction<string>>;
}>({
  agentInfo: null,
  setAgentInfo: () => {},
  suggestions: [],
  setAgentType: () => {},
  setAgentClass: () => {}
});

// Create AgentContextProvider
const AgentContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [agentType, setAgentType] = useState<string>('');
  const [agentClass, setAgentClass] = useState<string>('');

  useEffect(() => {
    const fetchAgentInfo = async () => {
      if (!agentType || !agentClass) {
        setAgentInfo(null);
        setSuggestions([]);
        return;
      }

      try {
        const response = await fetchCustom(`/api/agent-param?agent_type=${agentType}&agent_class=${agentClass}`);
        const data = await response.json();
        
        if (data.data) {
          const newAgentInfo = data.data;
          setAgentInfo(newAgentInfo);
          
          const profileSuggestions = Object.entries(profileOptions).map(([key, config]) => ({
            label: `${key}`,
            detail: `Agent's ${config.label.toLowerCase()}`
          }));

          const contextSuggestions = Object.entries(newAgentInfo.context || {}).map(([key, value]: [string, any]) => ({
            label: key,
            detail: value.description || `Type: ${value.type}`
          }));

          const statusSuggestions = (newAgentInfo.status_attributes || []).map((attr: any) => ({
            label: attr.name,
            detail: attr.description || `Type: ${attr.type}`
          }));

          const newSuggestions = [
            { label: 'profile', children: profileSuggestions },
            { label: 'context', children: contextSuggestions },
            { label: 'status', children: statusSuggestions }
          ];

          setSuggestions(newSuggestions);
        } else {
          setAgentInfo(null);
          setSuggestions([]);
        }
      } catch (err) {
        console.error('Failed to fetch agent parameters:', err);
        setAgentInfo(null);
        setSuggestions([]);
      }
    };

    fetchAgentInfo();
  }, [agentType, agentClass]);

  const contextValue = useMemo(() => ({
    agentInfo,
    setAgentInfo,
    suggestions,
    setAgentType,
    setAgentClass,
  }), [agentInfo, suggestions, agentType, agentClass]);

  return (
    <AgentContext.Provider value={contextValue}>
      {children}
    </AgentContext.Provider>
  );
};

// 在文件开头添加新的类型定义
interface ParamInfo {
  type: string;
  description: string | null;
  default: any;
}

// 创建一个公共的渲染函数
const renderDynamicFormItem = (
  paramName: string, 
  paramInfo: ParamInfo,
  formItemProps: {
    name: (string | number)[],
    suggestions?: any[],
  }
) => {
  const baseProps = {
    name: formItemProps.name,
    label: (
      <Space>
        {paramName}
        <Tooltip title={paramInfo.description || ''}>
          <QuestionCircleOutlined />
        </Tooltip>
      </Space>
    ),
    initialValue: paramInfo.default,
    rules: [{ required: true, message: `请输入${paramName}` }]
  };

  switch (paramInfo.type.toLowerCase()) {
    case 'bool':
      return (
        <Form.Item
          {...baseProps}
          valuePropName="checked"
        >
          <Switch defaultChecked={paramInfo.default} />
        </Form.Item>
      );
    case 'int':
    case 'float':
      return (
        <Form.Item {...baseProps}>
          <InputNumber 
            style={{ width: '100%' }} 
            step={paramInfo.type === 'int' ? 1 : 0.1}
          />
        </Form.Item>
      );
    case 'str':
      return (
        <Form.Item {...baseProps}>
          <MonacoPromptEditor 
            height="200px" 
            suggestions={formItemProps.suggestions} 
            editorId={paramName}
            key={`${paramName}-${formItemProps.suggestions?.length}`}
          />
        </Form.Item>
      );
    default:
      return (
        <Form.Item {...baseProps}>
          <Input />
        </Form.Item>
      );
  }
};

const AgentConfiguration: React.FC = () => {
  const context = useContext(AgentContext);
  const { t } = useTranslation();

  if (!context?.agentInfo) {
    return (
      <Card title={t('form.template.agentConfig')} bordered={false} style={{ marginBottom: '12px' }}>
        <Empty 
          description={t('form.template.selectAgentTypeAndClass')} 
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const { agentInfo, suggestions } = context;

  return (
    <Card title={t('form.template.agentConfig')} bordered={false} style={{ marginBottom: '12px' }}>
      <Row gutter={[12, 12]}>
        {Object.entries(agentInfo.params_type).map(([paramName, paramInfo]) => (
          <Col 
            key={paramName} 
            span={paramName.toLowerCase().includes('prompt') ? 24 : 12}
          >
            {renderDynamicFormItem(
              paramName,
              paramInfo,
              {
                name: ['agent_params', paramName],
                suggestions
              }
            )}
          </Col>
        ))}
      </Row>
    </Card>
  );
};

// 添加参数相关的接口定义
interface BlockParam {
  description: string | null;
  default: any;
  type: string;
}

// interface BlockFunction {
//   function_name: string;
//   description: string;
// }

interface BlockInfo {
  block_name: string;
  description: string;  // 保留字段，但暂时不使用
  // functions: BlockFunction[];
  params: Record<string, BlockParam>;
}

// 新增一个类型定义
interface BlockContextInfo {
  blockName: string;
  context: Record<string, any>;
}

// 修改BlockConfiguration组件
const BlockConfiguration: React.FC<{
  onBlockContextChange?: (contexts: BlockContextInfo[]) => void;
}> = ({ onBlockContextChange }) => {
  const [blocks, setBlocks] = useState<BlockInfo[]>([]);
  const [selectedBlocks, setSelectedBlocks] = useState<string[]>([]);
  const [blockParams, setBlockParams] = useState<Record<string, any>>({});
  const [blockContexts, setBlockContexts] = useState<Record<string, any>>({});
  const [blockSuggestions, setBlockSuggestions] = useState<Record<string, any[]>>({});
  const context = useContext(AgentContext);
  const suggestions = context?.suggestions || [];
  const { t } = useTranslation();

  // 修改 generateBlockSuggestions 函数
  const generateBlockSuggestions = (blockName: string, blockContext: Record<string, any>) => {
    const blockContextSuggestions = Object.entries(blockContext || {}).map(([key, value]: [string, any]) => ({
      label: key,
      detail: value.description || `Type: ${value.type}`
    }));

    // 复制原有的suggestions
    const newSuggestions = suggestions.map(group => {
      // 如果是context组，添加block的context作为children
      if (group.label === 'context') {
        return {
          ...group,
          children: [
            ...(group.children || []),
            // 添加block的context，并标注来源
            ...blockContextSuggestions.map(item => ({
              ...item,
              label: `${item.label}`,
              detail: `[${blockName}] ${item.detail}`
            }))
          ]
        };
      }
      return group;
    });

    return newSuggestions;
  };

  // 当选择block时获取对应的参数配置
  const fetchBlockParams = async (blockType: string) => {
    try {
      const response = await fetchCustom(`/api/block-param/${blockType}`);
      const data = await response.json();
      if (data.data) {
        setBlockParams(prev => ({
          ...prev,
          [blockType]: data.data.params_type
        }));
        
        // 保存context信息
        const blockContext = data.data.context || {};
        setBlockContexts(prev => ({
          ...prev,
          [blockType]: blockContext
        }));

        // 生成并保存block专属的suggestions
        setBlockSuggestions(prev => ({
          ...prev,
          [blockType]: generateBlockSuggestions(blockType, blockContext)
        }));
        
        // 通知父组件context变化
        const newContexts = selectedBlocks.map(block => ({
          blockName: block,
          context: blockContexts[block] || {}
        }));
        onBlockContextChange?.(newContexts);
      }
    } catch (err) {
      console.error(`Failed to fetch params for block ${blockType}:`, err);
    }
  };

  const handleBlockSelect = (values: string[]) => {
    setSelectedBlocks(values);
    
    // 获取新选中的blocks的参数
    const newBlocks = values.filter(block => !blockParams[block]);
    newBlocks.forEach(block => {
      fetchBlockParams(block);
    });

    // 更新context信息
    const selectedContexts = values.map(block => ({
      blockName: block,
      context: blockContexts[block] || {}
    }));
    onBlockContextChange?.(selectedContexts);
  };

  useEffect(() => {
    // 获取所有可用的 blocks
    fetchCustom('/api/agent-blocks')
      .then(res => res.json())
      .then(response => {
        if (response.data && Array.isArray(response.data)) {
          // setBlocks(response.data);
          // 将返回的block名称列表转换为BlockInfo格式
          const blockInfos = response.data.map(blockName => ({
            block_name: blockName,
            description: '',  // 暂时为空
            params: {}
          }));
          setBlocks(blockInfos);
        }
      })
      .catch(err => {
        console.error('Failed to fetch blocks:', err);
        setBlocks([]);
      });
  }, []);

  return (
    <Card title={t('form.template.blockConfig')} bordered={false}>
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* Block 选择框 */}
        <Form.Item
          label={t('form.template.selectBlocks')}
          style={{ marginBottom: '8px' }}
        >
          <Select
            mode="multiple"
            placeholder={t('form.template.selectBlocksPlaceholder')}
            style={{ width: '100%' }}
            onChange={handleBlockSelect}
            options={blocks.map(block => ({
              label: (
                <Space>
                  {block.block_name}
                  {/* 暂时注释掉description的显示
                  <Tooltip title={block.description}>
                    <QuestionCircleOutlined />
                  </Tooltip>
                  */}
                </Space>
              ),
              value: block.block_name
            }))}
          />
        </Form.Item>

        {/* 已选中 Block 的配置 */}
        {selectedBlocks.map(blockName => {
          const blockInfo = blocks.find(b => b.block_name === blockName);
          const params = blockParams[blockName];
          
          if (!blockInfo || !params) return null;

          return (
            <Card
              key={blockName}
              title={blockInfo.block_name}
              size="small"
              style={{ marginBottom: '8px' }}
            >
              {Object.entries(params).map(([paramName, paramInfo]) => (
                renderDynamicFormItem(
                  paramName,
                  paramInfo as ParamInfo,
                  {
                    name: ['blocks', blockName, 'params', paramName],
                    suggestions: blockSuggestions[blockName]
                  }
                )
              ))}
            </Card>
          );
        })}
      </Space>
    </Card>
  );
};

interface AgentInfoSidebarProps {
  blockContexts?: BlockContextInfo[];
}

const AgentInfoSidebar: React.FC<AgentInfoSidebarProps> = ({ blockContexts = [] }) => {
  const context = useContext(AgentContext);
  const { t } = useTranslation();

  if (!context?.agentInfo) {
    return (
      <Tabs defaultActiveKey="context" size="small">
        <Tabs.TabPane tab="Context" key="context">
          <Empty 
            description={t('form.template.selectAgentTypeAndClass')} 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Tabs.TabPane>
        <Tabs.TabPane tab="Status" key="status">
          <Empty 
            description={t('form.template.selectAgentTypeAndClass')} 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Tabs.TabPane>
      </Tabs>
    );
  }

  const { agentInfo } = context;

  // 通用的表格列配置
  const commonColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      width: '25%',
    },
    {
      title: '类型',
      dataIndex: 'type',
      width: '25%',
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: '50%',
      render: (text: string) => text || '-'
    }
  ];

  return (
    <Tabs defaultActiveKey="context" size="small">
      <Tabs.TabPane tab="Context" key="context">
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          {/* Agent Context */}
          <Card size="small" title="Agent Context" style={{ marginBottom: '8px' }}>
            <Table
              size="small"
              pagination={false}
              dataSource={Object.entries(agentInfo.context).map(([key, value]) => ({
                key,
                name: key,
                type: value.type,
                description: value.description,
                default: JSON.stringify(value.default)
              }))}
              columns={commonColumns}
            />
          </Card>

          {/* Block Contexts */}
          {blockContexts.map(({ blockName, context }) => (
            <Card size="small" title={`${blockName} Context`} key={blockName} style={{ marginBottom: '8px' }}>
              <Table
                size="small"
                pagination={false}
                dataSource={Object.entries(context).map(([key, value]: [string, any]) => ({
                  key,
                  name: key,
                  type: value.type,
                  description: value.description,
                  default: JSON.stringify(value.default)
                }))}
                columns={commonColumns}
              />
            </Card>
          ))}
        </Space>
      </Tabs.TabPane>
      <Tabs.TabPane tab="Status" key="status">
        <Table
          size="small"
          pagination={false}
          dataSource={agentInfo.status_attributes.map(attr => ({
            key: attr.name,
            ...attr,
            default: JSON.stringify(attr.default)
          }))}
          columns={[
            {
              title: '名称',
              dataIndex: 'name',
              width: '20%',
            },
            {
              title: '类型',
              dataIndex: 'type',
              width: '20%',
            },
            {
              title: '描述',
              dataIndex: 'description',
              width: '40%',
              render: (text) => text || '-'
            },
          ]}
        />
      </Tabs.TabPane>
    </Tabs>
  );
};

const validateFormData = (values: any, agentInfo: AgentInfo) => {
  // 验证 agent_params
  for (const [key, paramInfo] of Object.entries(agentInfo.params_type)) {
    if (paramInfo.type === 'bool' && typeof values.agent_params?.[key] !== 'boolean') {
      throw new Error(`参数 ${key} 必须是布尔值`);
    }
    if ((paramInfo.type === 'int' || paramInfo.type === 'float') && 
        typeof values.agent_params?.[key] !== 'number') {
      throw new Error(`参数 ${key} 必须是数字`);
    }
    // 可以添加更多类型验证
  }

  // // 验证 blocks
  // if (values.blocks) {
  //   Object.entries(values.blocks).forEach(([blockName, block]: [string, any]) => {
  //     if (block.params) {
  //       Object.entries(block.params).forEach(([paramKey, paramValue]) => {
  //         const paramType = agentInfo.block_output_type[paramKey]?.type;
  //         if (!paramType) {
  //           throw new Error(`未知的块参数: ${blockName}.${paramKey}`);
  //         }
  //         // 可以添加更多参数验证
  //       });
  //     }
  //   });
  // }
};

const AgentTemplateForm: React.FC = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams();
  const [currentTemplate, setCurrentTemplate] = useState<AgentTemplate | null>(null);
  const [selectedBlocks, setSelectedBlocks] = useState<string[]>([]);
  const [agentType, setAgentType] = useState<string>('');
  const [agentClasses, setAgentClasses] = useState<{ value: string; label: string }[]>([]);
  const [agentClass, setAgentClass] = useState<string>('');
  const [loadingAgentClasses, setLoadingAgentClasses] = useState<boolean>(false);
  const [blockContexts, setBlockContexts] = useState<BlockContextInfo[]>([]);
  
  // 将 context 移到组件顶层
  const context = useContext(AgentContext);
  const agentInfo = context?.agentInfo;

  // Agent type 选项
  const agentTypeOptions = [
    { value: 'citizen', label: t('form.template.agentTypes.citizen') },
    { value: 'supervisor', label: t('form.template.agentTypes.supervisor') },
  ];

  // 处理agent type变化
  const handleAgentTypeChange = (value: string) => {
    setAgentType(value);
    setAgentClass(''); // 重置agent class
    setAgentClasses([]); // 清空agent classes
    
    // 通知context更新agent type，重置agent class
    context?.setAgentType(value);
    context?.setAgentClass('');
    
    // 更新表单字段值
    form.setFieldsValue({
      agent_class: undefined,
      agent_type: value
    });
    
    // 根据agent type设置profile数据
    if (value === 'citizen') {
      form.setFieldsValue({
        profile: defaultProfileFields,
        agent_type: value,
        agent_class: undefined
      });
    } else if (value === 'supervisor') {
      form.setFieldsValue({
        profile: {},
        agent_type: value,
        agent_class: undefined
      });
    }
    
    // 获取agent classes
    if (value) {
      fetchAgentClasses(value);
    }
  };

  // 获取agent classes
  const fetchAgentClasses = async (agentType: string) => {
    setLoadingAgentClasses(true);
    try {
      const response = await fetchCustom(`/api/agent-classes?agent_type=${agentType}`);
      if (response.ok) {
        const data = await response.json();
        if (data.data) {
          setAgentClasses(data.data);
        }
      }
    } catch (error) {
      console.error('获取agent classes失败:', error);
      setAgentClasses([]);
    } finally {
      setLoadingAgentClasses(false);
    }
  };

  // 处理agent class变化
  const handleAgentClassChange = (value: string) => {
    setAgentClass(value);
    
    // 通知context更新agent class
    context?.setAgentClass(value);
    
    // 更新表单字段值
    form.setFieldsValue({
      agent_class: value
    });
  };

  // Load template data
  useEffect(() => {
    if (id) {
      fetchCustom(`/api/agent-templates/${id}`).then(async (res) => {
        if (res.ok) {
          const template = (await res.json()).data;
          setCurrentTemplate(template);

          // Set agent type and agent class if available
          if (template.agent_type) {
            setAgentType(template.agent_type);
            // 通知context更新agent type
            context?.setAgentType(template.agent_type);
            // Load agent classes for the agent type
            if (template.agent_type) {
              fetchAgentClasses(template.agent_type);
            }
          }
          if (template.agent_class) {
            setAgentClass(template.agent_class);
            // 通知context更新agent class
            context?.setAgentClass(template.agent_class);
          }

          // Extract block types from template
          const blockTypes = Object.keys(template.blocks);
          setSelectedBlocks(blockTypes);

          form.setFieldsValue({
            name: template.name,
            description: template.description,
            agent_type: template.agent_type,
            agent_class: template.agent_class,
            profile: template.agent_type === 'citizen' ? template.memory_distributions : {},
            agent_params: template.agent_params,
            blocks: template.blocks
          });
        }
      });
    } else {
      // Default values for new template
      form.setFieldsValue({
        description: '',
        profile: {}, // 初始为空，等用户选择agent type后再设置
        // agent_params: {
        //   enable_cognition: true,
        //   UBI: 1000,
        //   num_labor_hours: 168,
        //   productivity_per_labor: 1,
        //   time_diff: 2592000,
        //   max_plan_steps: 6
        // },
        // blocks: {}
      });
    }
  }, [id]);

  const handleBlockTypeChange = (values: string[]) => {
    setSelectedBlocks(values);

    // Update form blocks based on selected types
    const existingBlocks = form.getFieldValue('blocks') || {};

    // Keep blocks that are still selected
    const remainingBlocks = Object.fromEntries(Object.entries(existingBlocks).filter(([key]) => values.includes(key)));

    // Add new blocks for newly selected types
    const newBlockTypes = values.filter(type => !Object.keys(existingBlocks).includes(type));

    const newBlocks = newBlockTypes.map(type => ({
      [type]: {}
    }));

    form.setFieldsValue({
      blocks: { ...remainingBlocks, ...newBlocks }
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (!agentInfo) {
        message.error('缺少必要的配置信息');
        return;
      }

      // 验证表单数据
      try {
        validateFormData(values, agentInfo);
      } catch (validationError) {
        message.error(validationError.message || '表单数据验证失败');
        return;
      }
      
      // 构造 memory_distributions
      const memory_distributions: Record<string, any> = {};
      // 只有citizen类型才处理profile数据
      if (values.agent_type === 'citizen') {
        Object.entries(values.profile || {}).forEach(([key, value]: [string, any]) => {
          if (value.type === 'choice') {
            memory_distributions[key] = {
              dist_type: 'choice',
              choices: value.choices,
              weights: value.weights
            };
          } else if (value.type === 'uniform_int') {
            memory_distributions[key] = {
              dist_type: 'uniform_int',
              min_value: value.min_value,
              max_value: value.max_value
            };
          } else if (value.type === 'normal') {
            memory_distributions[key] = {
              dist_type: 'normal',
              mean: value.mean,
              std: value.std
            };
          }
        });
      }

      // 构造 agent_params
      const agent_params: Record<string, any> = {};
      Object.entries(agentInfo.params_type).forEach(([key, paramInfo]) => {
        const value = values.agent_params?.[key];
        agent_params[key] = value ?? paramInfo.default;
      });

      // 构造 blocks
      const blocksData: Record<string, any> = {};
      if (values.blocks) {
        Object.entries(values.blocks).forEach(([blockName, block]: [string, any]) => {
          if (block.params) {
            // 确保每个参数都有值，如果没有则使用默认值
            const blockParams = {};
            Object.entries(block.params).forEach(([paramKey, paramValue]) => {
              blockParams[paramKey] = paramValue;
            });
            blocksData[blockName] = blockParams;
          } else {
            blocksData[blockName] = {};
          }
        });
      }
      console.log('Converted blocks data:', JSON.stringify(blocksData, null, 2));

      // 构造最终提交的数据
      const templateData = {
        name: values.name || 'Default Template Name',
        description: values.description || '',
        agent_type: values.agent_type,
        agent_class: values.agent_class,
        memory_distributions,
        agent_params,
        blocks: blocksData
      };

      console.log('Final submission data:', JSON.stringify(templateData, null, 2));

      const res = await fetchCustom('/api/agent-templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(templateData),
      });

      if (!res.ok) {
        const errorData = await res.json();
        console.log('API error response:', JSON.stringify(errorData, null, 2));
        // 检查错误数据的结构
        if (errorData.detail) {
          if (typeof errorData.detail === 'object') {
            throw new Error(JSON.stringify(errorData.detail));
          } else {
            throw new Error(errorData.detail);
          }
        } else {
          throw new Error('创建模板失败: ' + JSON.stringify(errorData));
        }
      }

      const data = await res.json();
      console.log('API success response:', JSON.stringify(data, null, 2));
      message.success(t('form.template.messages.createSuccess'));
      navigate('/agent-templates');
    } catch (error) {
      console.log('Error occurred during form submission:', error);
      // 确保错误消息是字符串
      const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
      message.error(errorMessage || t('form.template.messages.createFailed'));
    }
  };

  return (
    <div style={{ padding: '16px' }}>
      <Card
        title={id ? t('form.template.editTitle') : t('form.template.createTitle')}
        extra={
          <Space>
            <Button onClick={() => navigate('/agent-templates')}>{t('form.common.cancel')}</Button>
            <Button type="primary" onClick={() => form.submit()}>
              {t('form.common.submit')}
            </Button>
          </Space>
        }
        bodyStyle={{ padding: '16px 0' }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={0}>
            <Col span={24} style={{ padding: '0 16px', marginBottom: '16px' }}>
              <Card
                title={t('form.template.basicInfo')}
                bordered={false}
                bodyStyle={{ padding: '8px 16px' }}
                headStyle={{ padding: '0 16px 4px' }}
              >
                <Row gutter={12} align="middle">
                  <Col span={6}>
                    <Form.Item
                      name="name"
                      label={t('form.common.name')}
                      rules={[{ required: true }]}
                      style={{ marginBottom: 0 }}
                    >
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={6}>
                    <Form.Item
                      name="agent_type"
                      label={t('form.template.agentType')}
                      rules={[{ required: true, message: t('form.template.pleaseSelectAgentType') }]}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        value={agentType}
                        placeholder={t('form.template.selectAgentType')}
                        style={{ width: '100%' }}
                        onChange={handleAgentTypeChange}
                        options={agentTypeOptions}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={6}>
                    <Form.Item
                      name="agent_class"
                      label={t('form.template.agentClass')}
                      rules={[{ required: true, message: t('form.template.pleaseSelectAgentClass') }]}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        value={agentClass}
                        placeholder={agentType ? t('form.template.selectAgentClass') : t('form.template.selectAgentTypeFirst')}
                        style={{ width: '100%' }}
                        disabled={!agentType || loadingAgentClasses}
                        loading={loadingAgentClasses}
                        onChange={handleAgentClassChange}
                        options={agentClasses}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={6}>
                    <Form.Item
                      name="description"
                      label={t('form.common.description')}
                      style={{ marginBottom: 0 }}
                    >
                      <Input placeholder={t('form.template.descriptionPlaceholder')} />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </Col>

            {/* Profile列 - 始终渲染，但supervisor模式下span为0实现隐藏 */}
            <Col span={agentType === 'citizen' ? 6 : 0} style={{ borderRight: agentType === 'citizen' ? '1px solid #f0f0f0' : 'none' }}>
              <div style={{
                height: 'calc(100vh - 200px)',
                overflowY: 'auto',
                padding: agentType === 'citizen' ? '0 16px' : '0',
                position: 'sticky',
                top: 0,
                display: agentType === 'citizen' ? 'block' : 'none'
              }}>
                {renderProfileSection(form)}
                {renderBaseLocation()}
              </div>
            </Col>

            <Col span={agentType === 'citizen' ? 12 : 18} style={{ borderRight: '1px solid #f0f0f0' }}>
              <div style={{
                height: 'calc(100vh - 200px)',
                overflowY: 'auto',
                padding: '0 16px',
                position: 'sticky',
                top: 0
              }}>
                <AgentConfiguration />
                <BlockConfiguration 
                  onBlockContextChange={setBlockContexts}
                />
              </div>
            </Col>

            <Col span={6}>
              <div style={{
                height: 'calc(100vh - 200px)',
                overflowY: 'auto',
                padding: '0 16px',
                position: 'sticky',
                top: 0
              }}>
                <AgentInfoSidebar blockContexts={blockContexts} />
              </div>
            </Col>
          </Row>
        </Form>
      </Card>
    </div>
  );
};

export default () => (
  <AgentContextProvider>
    <AgentTemplateForm />
  </AgentContextProvider>
); 