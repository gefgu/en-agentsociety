import React from 'react';
import { Form, Input, InputNumber, Select, Card, Tabs, Button, Space, Switch } from 'antd';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { ExpConfig, WorkflowStepConfig, MetricExtractorConfig } from '../../types/config';
import { WorkflowType, MetricType } from '../../utils/enums';

const { TabPane } = Tabs;

interface WorkflowFormProps {
  value: Partial<ExpConfig>;
  onChange: (value: Partial<ExpConfig>) => void;
}

const WorkflowForm: React.FC<WorkflowFormProps> = ({ value, onChange }) => {
  const [form] = Form.useForm();

  // Update parent component state when form values change
  const handleValuesChange = (changedValues: any, allValues: any) => {
    onChange(allValues);
  };

  // Set initial values
  React.useEffect(() => {
    form.setFieldsValue(value);
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
              // initialValue={[{
              //   type: WorkflowType.RUN,
              //   days: 1,
              //   description: "Run simulation for 1 day"
              // }]}
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
                            { value: WorkflowType.STEP, label: 'Step' },
                            { value: WorkflowType.RUN, label: 'Run' }
                          ]}
                        />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'times']}
                        label="Times"
                        rules={[{ required: true, message: 'Please enter number of times' }]}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>

                      {/* <Form.Item
                        {...restField}
                        name={[name, 'func']}
                        label="Function Name"
                        tooltip="Name of the function to call (for Function type)"
                      >
                        <Input placeholder="Enter function name" />
                      </Form.Item> */}

                      {/* <Form.Item
                        {...restField}
                        name={[name, 'interview_message']}
                        label="Interview Message"
                        tooltip="Message to send to agents (for Interview type)"
                      >
                        <Input.TextArea rows={3} placeholder="Enter interview message" />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'key']}
                        label="State Key"
                        tooltip="Key to update in agent state (for Update State type)"
                      >
                        <Input placeholder="Enter state key" />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'value']}
                        label="State Value"
                        tooltip="Value to set for the key (for Update State type)"
                      >
                        <Input placeholder="Enter state value" />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'intervene_message']}
                        label="Intervention Message"
                        tooltip="Message to send to agents (for Message Intervention type)"
                      >
                        <Input.TextArea rows={3} placeholder="Enter intervention message" />
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'description']}
                        label="Description"
                      >
                        <Input placeholder="Enter step description" />
                      </Form.Item> */}
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