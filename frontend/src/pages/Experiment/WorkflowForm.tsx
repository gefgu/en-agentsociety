import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Select, Card, Tabs, Button, Space, Switch, Tooltip, Row, Col } from 'antd';
import { PlusOutlined, MinusCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { ExpConfig, WorkflowStepConfig, MetricExtractorConfig } from '../../types/config';
import { WorkflowType, MetricType } from '../../utils/enums';
import { fetchCustom } from '../../components/fetch';
import { useTranslation } from 'react-i18next';

const { TabPane } = Tabs;

interface WorkflowFormProps {
    value: { workflow: WorkflowStepConfig[] };
    onChange: (value: { workflow: WorkflowStepConfig[] }) => void;
}

const WorkflowForm: React.FC<WorkflowFormProps> = ({ value, onChange }) => {
    const { t } = useTranslation();
    const [form] = Form.useForm();
    const [stepTypes, setStepTypes] = useState<Record<number, WorkflowType>>({});
    const [functionList, setFunctionList] = useState<string[]>([]);

    // 获取函数列表
    useEffect(() => {
        const fetchFunctionList = async () => {
            try {
                const response = await fetchCustom('/api/community/workflow/functions');
                const data = await response.json();
                setFunctionList(data.data);
            } catch (error) {
                console.error('Failed to fetch function list:', error);
            }
        };
        fetchFunctionList();
    }, []);

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

            <Form.List
                name="workflow"
                initialValue={[{
                    type: WorkflowType.RUN,
                    days: 1,
                    description: t('form.workflow.defaultRunDescription')
                }]}
            >
                {(fields, { add, remove }) => (
                    <>
                        {fields.map(({ key, name, ...restField }) => (
                            <Card
                                key={key}
                                title={t('form.workflow.step', { number: name + 1 })}
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
                                <Row gutter={16}>
                                    <Col span={8}>
                                        <Form.Item
                                            {...restField}
                                            name={[name, 'type']}
                                            label={t('form.workflow.stepType')}
                                            rules={[{ required: true, message: t('form.workflow.pleaseSelectStepType') }]}
                                        >
                                            <Select
                                                placeholder={t('form.workflow.selectStepType')}
                                                options={[
                                                    {
                                                        value: WorkflowType.RUN,
                                                        label: (
                                                            <Space>
                                                                {t('form.workflow.run')}
                                                                <Tooltip title={t('form.workflow.runTooltip')}>
                                                                    <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                </Tooltip>
                                                            </Space>
                                                        )
                                                    },
                                                    {
                                                        value: WorkflowType.STEP,
                                                        label: (
                                                            <Space>
                                                                {t('form.workflow.step')}
                                                                <Tooltip title={t('form.workflow.stepTooltip')}>
                                                                    <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                </Tooltip>
                                                            </Space>
                                                        )
                                                    },
                                                    {
                                                        value: WorkflowType.ENVIRONMENT_INTERVENE,
                                                        label: (
                                                            <Space>
                                                                {t('form.workflow.environmentIntervene')}
                                                                <Tooltip title={t('form.workflow.environmentInterveneTooltip')}>
                                                                    <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                </Tooltip>
                                                            </Space>
                                                        )
                                                    },
                                                    {
                                                        value: WorkflowType.NEXT_ROUND,
                                                        label: (
                                                            <Space>
                                                                {t('form.workflow.nextRound')}
                                                                <Tooltip title={t('form.workflow.nextRoundTooltip')}>
                                                                    <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                </Tooltip>
                                                            </Space>
                                                        )
                                                    },
                                                    {
                                                        value: WorkflowType.FUNCTION,
                                                        label: (
                                                            <Space>
                                                                {t('form.workflow.function')}
                                                                <Tooltip title={t('form.workflow.functionTooltip')}>
                                                                    <QuestionCircleOutlined style={{ color: '#1890ff' }} />
                                                                </Tooltip>
                                                            </Space>
                                                        )
                                                    },
                                                ]}
                                            />
                                        </Form.Item>
                                    </Col>
                                    <Col span={16}>
                                        {/* 所有类型都可以有描述 */}
                                        <Form.Item
                                            {...restField}
                                            name={[name, 'description']}
                                            label={t('form.workflow.description')}
                                            tooltip={t('form.workflow.descriptionTooltip')}
                                        >
                                            <Input placeholder={t('form.workflow.enterStepDescription')} />
                                        </Form.Item>
                                    </Col>
                                </Row>


                                {/* RUN 类型字段 */}
                                {stepTypes[name] === WorkflowType.RUN && (
                                    <Row gutter={16}>
                                        <Col span={12}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'days']}
                                                label={t('form.workflow.days')}
                                                rules={[{ required: true, message: t('form.workflow.pleaseEnterDays') }]}
                                                tooltip={t('form.workflow.daysTooltip')}
                                            >
                                                <InputNumber min={0} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </Col>
                                        <Col span={12}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'ticks_per_step']}
                                                label={t('form.workflow.ticksPerStep')}
                                                initialValue={300}
                                                tooltip={t('form.workflow.ticksPerStepTooltip')}
                                            >
                                                <InputNumber min={1} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </Col>
                                    </Row>
                                )}

                                {/* STEP 类型字段 */}
                                {stepTypes[name] === WorkflowType.STEP && (
                                    <Row gutter={16}>
                                        <Col span={12}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'steps']}
                                                label={t('form.workflow.steps')}
                                                initialValue={1}
                                                rules={[{ required: true, message: t('form.workflow.pleaseEnterSteps') }]}
                                                tooltip={t('form.workflow.stepsTooltip')}
                                            >
                                                <InputNumber min={1} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </Col>
                                        <Col span={12}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'ticks_per_step']}
                                                label={t('form.workflow.ticksPerStep')}
                                                initialValue={300}
                                                tooltip={t('form.workflow.ticksPerStepTooltip')}
                                            >
                                                <InputNumber min={1} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </Col>
                                    </Row>
                                )}

                                {/* ENVIRONMENT_INTERVENE 类型字段 */}
                                {stepTypes[name] === WorkflowType.ENVIRONMENT_INTERVENE && (
                                    <Row gutter={16}>
                                        <Col span={8}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'key']}
                                                label={t('form.workflow.environmentKey')}
                                                rules={[{ required: true, message: t('form.workflow.pleaseEnterEnvironmentKey') }]}
                                                tooltip={t('form.workflow.environmentKeyTooltip')}
                                            >
                                                <Input placeholder={t('form.workflow.enterEnvironmentKey')} />
                                            </Form.Item>
                                        </Col>
                                        <Col span={16}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'value']}
                                                label={t('form.workflow.environmentValue')}
                                                rules={[{ required: true, message: t('form.workflow.pleaseEnterEnvironmentValue') }]}
                                                tooltip={t('form.workflow.environmentValueTooltip')}
                                            >
                                                <Input.TextArea rows={1} placeholder={t('form.workflow.enterEnvironmentValue')} />
                                            </Form.Item>
                                        </Col>
                                    </Row>
                                )}

                                {/* FUNCTION 类型字段 */}
                                {stepTypes[name] === WorkflowType.FUNCTION && (
                                    <Row gutter={16}>
                                        <Col span={24}>
                                            <Form.Item
                                                {...restField}
                                                name={[name, 'function_name']}
                                                label={t('form.workflow.functionName')}
                                                rules={[{ required: true, message: t('form.workflow.pleaseSelectFunction') }]}
                                                tooltip={t('form.workflow.functionNameTooltip')}
                                            >
                                                <Select
                                                    placeholder={t('form.workflow.selectFunction')}
                                                    options={functionList.map(func => ({
                                                        value: func,
                                                        label: func
                                                    }))}
                                                />
                                            </Form.Item>
                                        </Col>
                                    </Row>
                                )}
                            </Card>
                        ))}
                        <Form.Item>
                            <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                                {t('form.workflow.addWorkflowStep')}
                            </Button>
                        </Form.Item>
                    </>
                )}
            </Form.List>

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
        </Form>
    );
};

export default WorkflowForm; 