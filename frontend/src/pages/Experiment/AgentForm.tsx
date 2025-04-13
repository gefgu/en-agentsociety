import React from 'react';
import { Form, Input, InputNumber, Select, Card, Tabs, Button } from 'antd';
import { AgentConfig, AgentsConfig } from '../../types/config';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;
const { Option } = Select;

interface AgentFormProps {
    value: Partial<AgentsConfig>;
    onChange: (value: Partial<AgentsConfig>) => void;
}

const AgentForm: React.FC<AgentFormProps> = ({ value, onChange }) => {
    const [form] = Form.useForm();

    // Define agent type options
    const agentClassOptions = [
        { label: 'Citizen', value: 'citizen' },
        { label: 'Firm', value: 'firm' },
        { label: 'Government', value: 'government' },
        { label: 'Bank', value: 'bank' },
        { label: 'NBS', value: 'nbs' },
    ];

    // Update parent component state when form values change
    const handleValuesChange = (changedValues: any, allValues: any) => {
        // 使用form.getFieldsValue()获取完整的表单值，而不是依赖allValues
        const completeValues = form.getFieldsValue();

        // Transform form values to match the expected AgentsConfig structure
        const transformedValues = transformFormToAgentsConfig(completeValues);
        onChange(transformedValues);
    };

    // Transform form data to AgentsConfig structure
    const transformFormToAgentsConfig = (formValues: any): Partial<AgentsConfig> => {
        let { citizenGroups, firmGroups, governmentGroups, bankGroups, nbsGroups } = formValues;
        // set default number if not provided
        if (citizenGroups === undefined) {
            citizenGroups = [{ number: 10 }];
        }
        if (firmGroups === undefined) {
            firmGroups = [{ number: 5 }];
        }
        if (governmentGroups === undefined) {
            governmentGroups = [{ number: 1 }];
        }
        if (bankGroups === undefined) {
            bankGroups = [{ number: 1 }];
        }
        if (nbsGroups === undefined) {
            nbsGroups = [{ number: 1 }];
        }
        return {
            citizens: citizenGroups.map((group: any) => ({
                agent_class: 'citizen',
                number: group.number || 1,
                memory_config_func: group.memory_config_func || null,
                memory_distributions: group.memory_distributions || null
            })),
            firms: firmGroups.map((group: any) => ({
                agent_class: 'firm',
                number: group.number || 1,
                memory_config_func: group.memory_config_func || null,
                memory_distributions: group.memory_distributions || null
            })),
            governments: governmentGroups.map((group: any) => ({
                agent_class: 'government',
                number: group.number || 1,
                memory_config_func: group.memory_config_func || null,
                memory_distributions: group.memory_distributions || null
            })),
            banks: bankGroups.map((group: any) => ({
                agent_class: 'bank',
                number: group.number || 1,
                memory_config_func: group.memory_config_func || null,
                memory_distributions: group.memory_distributions || null
            })),
            nbs: nbsGroups.map((group: any) => ({
                agent_class: 'nbs',
                number: group.number || 1,
                memory_config_func: group.memory_config_func || null,
                memory_distributions: group.memory_distributions || null
            }))
        };
    };

    // Transform AgentsConfig to form structure
    const transformAgentsConfigToForm = (agentsConfig: Partial<AgentsConfig>) => {
        return {
            citizenGroups: agentsConfig.citizens?.map(agent => ({
                number: agent.number,
                memory_config_func: agent.memory_config_func,
                memory_distributions: agent.memory_distributions
            })) || [{ number: 10 }],
            firmGroups: agentsConfig.firms?.map(agent => ({
                number: agent.number,
                memory_config_func: agent.memory_config_func,
                memory_distributions: agent.memory_distributions
            })) || [{ number: 5 }],
            governmentGroups: agentsConfig.governments?.map(agent => ({
                number: agent.number,
                memory_config_func: agent.memory_config_func,
                memory_distributions: agent.memory_distributions
            })) || [{ number: 1 }],
            bankGroups: agentsConfig.banks?.map(agent => ({
                number: agent.number,
                memory_config_func: agent.memory_config_func,
                memory_distributions: agent.memory_distributions
            })) || [{ number: 1 }],
            nbsGroups: agentsConfig.nbs?.map(agent => ({
                number: agent.number,
                memory_config_func: agent.memory_config_func,
                memory_distributions: agent.memory_distributions
            })) || [{ number: 1 }]
        };
    };

    // Set initial values
    React.useEffect(() => {
        const formValues = transformAgentsConfigToForm(value);
        form.setFieldsValue(formValues);
    }, [form, value]);

    return (
        <Form
            form={form}
            layout="vertical"
            onValuesChange={handleValuesChange}
        >
            <Tabs defaultActiveKey="1">
                <TabPane tab="Citizens" key="1">
                    <Card bordered={false}>
                        <Form.List name="citizenGroups" initialValue={[{ number: 10 }]}>
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }) => (
                                        <Card
                                            key={key}
                                            title={`Citizen Group ${name + 1}`}
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
                                                label="Number of Citizens"
                                                rules={[{ required: true, message: 'Please enter number of citizens' }]}
                                            >
                                                <InputNumber min={1} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </Card>
                                    ))}
                                    <Button
                                        type="dashed"
                                        onClick={() => add({ number: 10 })}
                                        block
                                        icon={<PlusOutlined />}
                                    >
                                        Add Citizen Group
                                    </Button>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </TabPane>

                <TabPane tab="Firms" key="2">
                    <Card bordered={false}>
                        <Form.List name="firmGroups" initialValue={[{ number: 5 }]}>
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }) => (
                                        <Card
                                            key={key}
                                            title={`Firm Group ${name + 1}`}
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
                                                label="Number of Firms"
                                                rules={[{ required: true, message: 'Please enter number of firms' }]}
                                            >
                                                <InputNumber min={1} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </Card>
                                    ))}
                                    <Button
                                        type="dashed"
                                        onClick={() => add({ number: 5 })}
                                        block
                                        icon={<PlusOutlined />}
                                    >
                                        Add Firm Group
                                    </Button>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </TabPane>

                <TabPane tab="Government" key="3">
                    <Card bordered={false}>
                        <Form.List name="governmentGroups" initialValue={[{ number: 1 }]}>
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }) => (
                                        <Card
                                            key={key}
                                            title={`Government Group ${name + 1}`}
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
                                                label="Number of Governments"
                                                rules={[{ required: true, message: 'Please enter number of governments' }]}
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
                                        Add Government Group
                                    </Button>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </TabPane>

                <TabPane tab="Banks" key="4">
                    <Card bordered={false}>
                        <Form.List name="bankGroups" initialValue={[{ number: 1 }]}>
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }) => (
                                        <Card
                                            key={key}
                                            title={`Bank Group ${name + 1}`}
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
                                                label="Number of Banks"
                                                rules={[{ required: true, message: 'Please enter number of banks' }]}
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
                                        Add Bank Group
                                    </Button>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </TabPane>

                <TabPane tab="NBS" key="5">
                    <Card bordered={false}>
                        <Form.List name="nbsGroups" initialValue={[{ number: 1 }]}>
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }) => (
                                        <Card
                                            key={key}
                                            title={`NBS Group ${name + 1}`}
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
                                                label="Number of NBS"
                                                rules={[{ required: true, message: 'Please enter number of NBS' }]}
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
                                        Add NBS Group
                                    </Button>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </TabPane>
            </Tabs>
        </Form>
    );
};

export default AgentForm; 