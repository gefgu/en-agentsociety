import React, { useState } from 'react';
import { Form, Input, InputNumber, Select, Card, Tabs, Button, Space, Switch } from 'antd';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { ExpConfig, WorkflowStepConfig, MetricExtractorConfig } from '../../types/config';
import { WorkflowType, MetricType } from '../../utils/enums';

const { TabPane } = Tabs;

interface WorkflowFormProps {
    value: { workflow: WorkflowStepConfig[] };
    onChange: (value: { workflow: WorkflowStepConfig[] }) => void;
}

const WorkflowForm: React.FC<WorkflowFormProps> = ({ value, onChange }) => {
    const [form] = Form.useForm();
    const [stepTypes, setStepTypes] = useState<Record<number, WorkflowType>>({});

    // Update parent component state when form values change
    const handleValuesChange = (changedValues: any, allValues: any) => {
        // 如果改变了类型，更新本地状态
        if (changedValues && changedValues.workflow) {
            const newStepTypes: Record<number, WorkflowType> = { ...stepTypes };
            changedValues.workflow.forEach((step: any, index: number) => {
                if (step && step.type !== undefined) {
                    newStepTypes[index] = step.type;
                }
            });
            setStepTypes(newStepTypes);
        }
        onChange(allValues);
    };

    // Set initial values
    React.useEffect(() => {
        form.setFieldsValue(value);
        
        // 初始化 stepTypes
        const initialStepTypes: Record<number, WorkflowType> = {};
        if (value && value.workflow) {  // 添加检查确保 value 和 value.workflow 存在
            value.workflow.forEach((step, index) => {
                if (step && step.type) {  // 添加检查确保 step 存在
                    initialStepTypes[index] = step.type;
                }
            });
        }
        setStepTypes(initialStepTypes);
    }, [form, value]);

    return (
        <Form
            form={form}
            layout="vertical"
            onValuesChange={handleValuesChange}
            initialValues={value}
        >
            <Tabs defaultActiveKey="1">
                {/* <TabPane tab="Basic Settings" key="1">
          <Card bordered={false}>
            <Form.Item
              name="name"
              label="Experiment Name"
              rules={[{ required: true, message: 'Please enter experiment name' }]}
            >
              <Input placeholder="Enter experiment name" />
            </Form.Item>
          </Card>
        </TabPane> */}

                {/* <TabPane tab="Environment Settings" key="2">
          <Card bordered={false}>
            <Form.Item
              name={['environment', 'weather']}
              label="Weather"
              initialValue="The weather is normal"
            >
              <Input placeholder="Enter weather description" />
            </Form.Item>

            <Form.Item
              name={['environment', 'temperature']}
              label="Temperature"
              initialValue="The temperature is normal"
            >
              <Input placeholder="Enter temperature description" />
            </Form.Item>

            <Form.Item
              name={['environment', 'workday']}
              label="Is Workday"
              valuePropName="checked"
              initialValue={true}
            >
              <Switch />
            </Form.Item>

            <Form.Item
              name={['environment', 'other_information']}
              label="Other Information"
              initialValue=""
            >
              <Input.TextArea rows={4} placeholder="Enter other environment information" />
            </Form.Item>
            
            <Form.Item
              name={['environment', 'start_tick']}
              label="Start Tick"
              initialValue={28800}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            
            <Form.Item
              name={['environment', 'total_tick']}
              label="Total Tick"
              initialValue={7200}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Card>
        </TabPane> */}

                <TabPane tab="Workflow Steps" key="3">
                    <Card bordered={false}>
                        <Form.List
                            name="workflow"
                            initialValue={[{
                                type: WorkflowType.RUN,
                                days: 1,
                                description: "Run simulation for 1 day"
                            }]}
                        >
                            {(fields, { add, remove }) => (
                                <>
                                    {fields.map(({ key, name, ...restField }) => (
                                        <Card
                                            key={key}
                                            title={`Step ${name + 1}`}
                                            style={{ marginBottom: 16 }}
                                            extra={
                                                <Button
                                                    type="text"
                                                    danger
                                                    icon={<MinusCircleOutlined />}
                                                    onClick={() => remove(name)}
                                                />
                                            }
                                        >
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'type']}
                                                label="Step Type"
                                                rules={[{ required: true, message: 'Please select step type' }]}
                                            >
                                                <Select
                                                    placeholder="Select step type"
                                                    options={[
                                                        { value: WorkflowType.RUN, label: 'Run' },
                                                        { value: WorkflowType.STEP, label: 'Step' },
                                                        { value: WorkflowType.INTERVIEW, label: 'Interview' },
                                                        { value: WorkflowType.SURVEY, label: 'Survey' },
                                                        { value: WorkflowType.ENVIRONMENT_INTERVENE, label: 'Environment Intervene' },
                                                        { value: WorkflowType.UPDATE_STATE_INTERVENE, label: 'Update State Intervene' },
                                                        { value: WorkflowType.MESSAGE_INTERVENE, label: 'Message Intervene' },
                                                        { value: WorkflowType.NEXT_ROUND, label: 'Next Round' },
                                                        { value: WorkflowType.INTERVENE, label: 'Other' },
                                                        { value: WorkflowType.FUNCTION, label: 'Function' },
                                                    ]}
                                                />
                                            </Form.Item>

                                            {/* 根据选择的类型显示不同的字段 */}
                                            
                                            {/* RUN 类型字段 */}
                                            {stepTypes[name] === WorkflowType.RUN && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'days']}
                                                        label="Days"
                                                        rules={[{ required: true, message: 'Please enter number of days' }]}
                                                        tooltip="Duration (in days) for which this step lasts"
                                                    >
                                                        <InputNumber min={0} style={{ width: '100%' }} />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'ticks_per_step']}
                                                        label="Ticks Per Step"
                                                        initialValue={300}
                                                        tooltip="Number of ticks per step in the environment"
                                                    >
                                                        <InputNumber min={1} style={{ width: '100%' }} />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* STEP 类型字段 */}
                                            {stepTypes[name] === WorkflowType.STEP && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'steps']}
                                                        label="Steps"
                                                        initialValue={1}
                                                        rules={[{ required: true, message: 'Please enter number of steps' }]}
                                                        tooltip="Number of steps for which this step lasts"
                                                    >
                                                        <InputNumber min={1} style={{ width: '100%' }} />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'ticks_per_step']}
                                                        label="Ticks Per Step"
                                                        initialValue={300}
                                                        tooltip="Number of ticks per step in the environment"
                                                    >
                                                        <InputNumber min={1} style={{ width: '100%' }} />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* INTERVIEW 类型字段 */}
                                            {stepTypes[name] === WorkflowType.INTERVIEW && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'target_agent']}
                                                        label="Target Agents"
                                                        tooltip="List of agent IDs to interview"
                                                        rules={[{ required: true, message: 'Please specify target agents' }]}
                                                    >
                                                        <Select
                                                            mode="tags"
                                                            placeholder="Enter agent IDs"
                                                            tokenSeparators={[',']}
                                                        />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'interview_message']}
                                                        label="Interview Message"
                                                        rules={[{ required: true, message: 'Please enter interview message' }]}
                                                        tooltip="Message to send to agents during interview"
                                                    >
                                                        <Input.TextArea rows={3} placeholder="Enter interview message" />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* SURVEY 类型字段 */}
                                            {stepTypes[name] === WorkflowType.SURVEY && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'target_agent']}
                                                        label="Target Agents"
                                                        tooltip="List of agent IDs to survey"
                                                        rules={[{ required: true, message: 'Please specify target agents' }]}
                                                    >
                                                        <Select
                                                            mode="tags"
                                                            placeholder="Enter agent IDs"
                                                            tokenSeparators={[',']}
                                                        />
                                                    </Form.Item>
                                                    
                                                    {/* 这里可以添加更多的调查相关字段 */}
                                                </>
                                            )}

                                            {/* ENVIRONMENT_INTERVENE 类型字段 */}
                                            {stepTypes[name] === WorkflowType.ENVIRONMENT_INTERVENE && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'key']}
                                                        label="Environment Key"
                                                        rules={[{ required: true, message: 'Please enter environment key' }]}
                                                        tooltip="Key identifier for the environment intervention"
                                                    >
                                                        <Input placeholder="Enter environment key" />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'value']}
                                                        label="Environment Value"
                                                        rules={[{ required: true, message: 'Please enter environment value' }]}
                                                        tooltip="Value to set for the environment key"
                                                    >
                                                        <Input.TextArea rows={2} placeholder="Enter environment value" />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* UPDATE_STATE_INTERVENE 类型字段 */}
                                            {stepTypes[name] === WorkflowType.UPDATE_STATE_INTERVENE && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'target_agent']}
                                                        label="Target Agents"
                                                        tooltip="List of agent IDs to update state"
                                                        rules={[{ required: true, message: 'Please specify target agents' }]}
                                                    >
                                                        <Select
                                                            mode="tags"
                                                            placeholder="Enter agent IDs"
                                                            tokenSeparators={[',']}
                                                        />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'key']}
                                                        label="State Key"
                                                        rules={[{ required: true, message: 'Please enter state key' }]}
                                                        tooltip="Key identifier for the state update"
                                                    >
                                                        <Input placeholder="Enter state key" />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'value']}
                                                        label="State Value"
                                                        rules={[{ required: true, message: 'Please enter state value' }]}
                                                        tooltip="Value to set for the state key"
                                                    >
                                                        <Input.TextArea rows={2} placeholder="Enter state value" />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* MESSAGE_INTERVENE 类型字段 */}
                                            {stepTypes[name] === WorkflowType.MESSAGE_INTERVENE && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'target_agent']}
                                                        label="Target Agents"
                                                        tooltip="List of agent IDs to send message"
                                                        rules={[{ required: true, message: 'Please specify target agents' }]}
                                                    >
                                                        <Select
                                                            mode="tags"
                                                            placeholder="Enter agent IDs"
                                                            tokenSeparators={[',']}
                                                        />
                                                    </Form.Item>
                                                    
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'intervene_message']}
                                                        label="Intervention Message"
                                                        rules={[{ required: true, message: 'Please enter intervention message' }]}
                                                        tooltip="Message to send to agents"
                                                    >
                                                        <Input.TextArea rows={3} placeholder="Enter intervention message" />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* FUNCTION 类型字段 */}
                                            {stepTypes[name] === WorkflowType.FUNCTION && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'func']}
                                                        label="Function Name"
                                                        rules={[{ required: true, message: 'Please enter function name' }]}
                                                        tooltip="Name of the function to execute"
                                                    >
                                                        <Input placeholder="Enter function name" />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* INTERVENE 类型字段 */}
                                            {stepTypes[name] === WorkflowType.INTERVENE && (
                                                <>
                                                    <Form.Item
                                                        {...restField}
                                                        name={[name, 'func']}
                                                        label="Function Name"
                                                        rules={[{ required: true, message: 'Please enter function name' }]}
                                                        tooltip="Name of the function to execute for intervention"
                                                    >
                                                        <Input placeholder="Enter function name" />
                                                    </Form.Item>
                                                </>
                                            )}

                                            {/* 所有类型都可以有描述 */}
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'description']}
                                                label="Description"
                                                tooltip="Description of this workflow step"
                                            >
                                                <Input placeholder="Enter step description" />
                                            </Form.Item>
                                        </Card>
                                    ))}
                                    <Form.Item>
                                        <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                                            Add Workflow Step
                                        </Button>
                                    </Form.Item>
                                </>
                            )}
                        </Form.List>
                    </Card>
                </TabPane>

                {/* <TabPane tab="Message Interception" key="4">
          <Card bordered={false}>
            <Form.Item
              name={['message_intercept', 'mode']}
              label="Interception Mode"
              initialValue="point"
            >
              <Select
                placeholder="Select interception mode"
                options={[
                  { value: 'point', label: 'Point' },
                  { value: 'edge', label: 'Edge' }
                ]}
              />
            </Form.Item>

            <Form.Item
              name={['message_intercept', 'max_violation_time']}
              label="Max Violation Time"
              initialValue={3}
              tooltip="Maximum number of allowed violations"
            >
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name={['message_intercept', 'listener']}
              label="Message Listener"
              tooltip="Name of the message listener class"
            >
              <Input placeholder="Enter message listener class name" />
            </Form.Item>
          </Card>
        </TabPane>

        <TabPane tab="Metrics" key="5">
          <Card bordered={false}>
            <Form.List
              name="metric_extractors"
              initialValue={[]}
            >
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card
                      key={key}
                      title={`Metric ${name + 1}`}
                      style={{ marginBottom: 16 }}
                      extra={
                        <Button
                          type="text"
                          danger
                          icon={<MinusCircleOutlined />}
                          onClick={() => remove(name)}
                        />
                      }
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'type']}
                        label="Metric Type"
                        rules={[{ required: true, message: 'Please select metric type' }]}
                      >
                        <Select
                          placeholder="Select metric type"
                          options={[
                            { value: MetricType.FUNCTION, label: 'Function' },
                            { value: MetricType.STATE, label: 'State' },
                          ]}
                        />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'step_interval']}
                        label="Step Interval"
                        tooltip="Interval between metric extractions"
                        initialValue={1}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'key']}
                        label="Metric Key"
                        tooltip="Key to identify this metric"
                      >
                        <Input placeholder="Enter metric key" />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'method']}
                        label="Aggregation Method"
                      >
                        <Select
                          placeholder="Select aggregation method"
                          options={[
                            { value: 'mean', label: 'Mean' },
                            { value: 'sum', label: 'Sum' },
                            { value: 'max', label: 'Maximum' },
                            { value: 'min', label: 'Minimum' },
                          ]}
                        />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'extract_time']}
                        label="Extract Time"
                        tooltip="The simulation time or step at which extraction occurs"
                        initialValue={0}
                      >
                        <InputNumber min={0} style={{ width: '100%' }} />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'description']}
                        label="Description"
                      >
                        <Input placeholder="Enter metric description" />
                      </Form.Item>
                    </Card>
                  ))}
                  <Form.Item>
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      Add Metric Extractor
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </Card>
        </TabPane> */}
            </Tabs>
        </Form>
    );
};

export default WorkflowForm; 