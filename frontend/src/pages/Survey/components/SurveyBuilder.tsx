import React, { useState, useEffect } from 'react';
import { Card, Button, Form, Input, Select, Space, List, Modal, InputNumber, Typography, Row, Col, Tag, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

interface Choice {
    value: string;
    text: string;
}

interface Question {
    name: string;
    title: string;
    type: 'text' | 'radiogroup' | 'checkbox' | 'rating';
    choices?: Choice[];
    rateMin?: number;
    rateMax?: number;
    rateStep?: number;
}

interface SurveyBuilderProps {
    value?: string;
    onChange?: (value: string) => void;
}

const SurveyBuilder: React.FC<SurveyBuilderProps> = ({ value, onChange }) => {
    const [questions, setQuestions] = useState<Question[]>([]);
    const [surveyTitle, setSurveyTitle] = useState('');
    const [surveyDescription, setSurveyDescription] = useState('');
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
    const [editingIndex, setEditingIndex] = useState<number>(-1);
    const [form] = Form.useForm();

    // 初始化：从JSON字符串解析问卷数据
    useEffect(() => {
        if (value) {
            try {
                const surveyData = JSON.parse(value);
                setSurveyTitle(surveyData.title || '');
                setSurveyDescription(surveyData.description || '');
                if (surveyData.pages && surveyData.pages[0] && surveyData.pages[0].elements) {
                    setQuestions(surveyData.pages[0].elements);
                }
            } catch (e) {
                console.warn('Failed to parse survey JSON:', e);
            }
        }
    }, [value]);

    // 当问卷数据改变时，生成JSON并回调
    useEffect(() => {
        const surveyJson = {
            title: surveyTitle,
            description: surveyDescription,
            pages: [
                {
                    name: 'page1',
                    elements: questions
                }
            ]
        };
        onChange?.(JSON.stringify(surveyJson, null, 2));
    }, [questions, surveyTitle, surveyDescription, onChange]);

    const showQuestionModal = (question?: Question, index?: number) => {
        if (question && index !== undefined) {
            setEditingQuestion(question);
            setEditingIndex(index);
            form.setFieldsValue({
                ...question,
                choices: question.choices?.map(c => c.text) || []
            });
        } else {
            setEditingQuestion(null);
            setEditingIndex(-1);
            form.resetFields();
        }
        setIsModalVisible(true);
    };

    const handleQuestionSubmit = (values: any) => {
        const newQuestion: Question = {
            name: values.name || `question_${Date.now()}`,
            title: values.title,
            type: values.type,
        };

        // 根据问题类型添加特定字段
        if (values.type === 'radiogroup' || values.type === 'checkbox') {
            newQuestion.choices = values.choices?.map((text: string, index: number) => ({
                value: `choice_${index + 1}`,
                text: text.trim()
            })).filter((choice: Choice) => choice.text) || [];
        } else if (values.type === 'rating') {
            newQuestion.rateMin = values.rateMin || 1;
            newQuestion.rateMax = values.rateMax || 5;
            newQuestion.rateStep = values.rateStep || 1;
        }

        const newQuestions = [...questions];
        if (editingIndex >= 0) {
            newQuestions[editingIndex] = newQuestion;
        } else {
            newQuestions.push(newQuestion);
        }
        
        setQuestions(newQuestions);
        setIsModalVisible(false);
        form.resetFields();
    };

    const deleteQuestion = (index: number) => {
        const newQuestions = questions.filter((_, i) => i !== index);
        setQuestions(newQuestions);
    };

    const moveQuestion = (index: number, direction: 'up' | 'down') => {
        const newQuestions = [...questions];
        const targetIndex = direction === 'up' ? index - 1 : index + 1;
        
        if (targetIndex >= 0 && targetIndex < questions.length) {
            [newQuestions[index], newQuestions[targetIndex]] = [newQuestions[targetIndex], newQuestions[index]];
            setQuestions(newQuestions);
        }
    };

    const getQuestionTypeText = (type: string) => {
        const typeMap = {
            text: '文本输入',
            radiogroup: '单选题',
            checkbox: '多选题',
            rating: '评分题'
        };
        return typeMap[type] || type;
    };

    return (
        <div>
            <Card title="问卷基本信息" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                    <Col span={12}>
                        <Form.Item label="问卷标题">
                            <Input
                                value={surveyTitle}
                                onChange={(e) => setSurveyTitle(e.target.value)}
                                placeholder="请输入问卷标题"
                            />
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item label="问卷描述">
                            <Input
                                value={surveyDescription}
                                onChange={(e) => setSurveyDescription(e.target.value)}
                                placeholder="请输入问卷描述"
                            />
                        </Form.Item>
                    </Col>
                </Row>
            </Card>

            <Card 
                title="问题列表"
                extra={
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => showQuestionModal()}>
                        添加问题
                    </Button>
                }
            >
                <List
                    dataSource={questions}
                    renderItem={(item, index) => (
                        <List.Item
                            actions={[
                                <Button
                                    key="up"
                                    size="small"
                                    icon={<ArrowUpOutlined />}
                                    disabled={index === 0}
                                    onClick={() => moveQuestion(index, 'up')}
                                />,
                                <Button
                                    key="down"
                                    size="small"
                                    icon={<ArrowDownOutlined />}
                                    disabled={index === questions.length - 1}
                                    onClick={() => moveQuestion(index, 'down')}
                                />,
                                <Button
                                    key="edit"
                                    size="small"
                                    icon={<EditOutlined />}
                                    onClick={() => showQuestionModal(item, index)}
                                />,
                                <Popconfirm
                                    key="delete"
                                    title="确定要删除这个问题吗？"
                                    onConfirm={() => deleteQuestion(index)}
                                >
                                    <Button size="small" danger icon={<DeleteOutlined />} />
                                </Popconfirm>
                            ]}
                        >
                            <List.Item.Meta
                                title={
                                    <Space>
                                        <Text strong>{item.title}</Text>
                                        <Tag color="blue">{getQuestionTypeText(item.type)}</Tag>
                                    </Space>
                                }
                                description={
                                    <div>
                                        {item.type === 'radiogroup' || item.type === 'checkbox' ? (
                                            <Text type="secondary">
                                                选项: {item.choices?.map(c => c.text).join(', ')}
                                            </Text>
                                        ) : item.type === 'rating' ? (
                                            <Text type="secondary">
                                                评分范围: {item.rateMin} - {item.rateMax}
                                            </Text>
                                        ) : null}
                                    </div>
                                }
                            />
                        </List.Item>
                    )}
                />
                {questions.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                        还没有添加任何问题。点击"添加问题"开始构建您的问卷。
                    </div>
                )}
            </Card>

            <Modal
                title={editingQuestion ? '编辑问题' : '添加问题'}
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                footer={null}
                width={600}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleQuestionSubmit}
                >
                    <Form.Item
                        name="title"
                        label="问题标题"
                        rules={[{ required: true, message: '请输入问题标题' }]}
                    >
                        <Input placeholder="请输入问题标题" />
                    </Form.Item>

                    <Form.Item
                        name="type"
                        label="问题类型"
                        rules={[{ required: true, message: '请选择问题类型' }]}
                    >
                        <Select placeholder="选择问题类型">
                            <Option value="text">文本输入</Option>
                            <Option value="radiogroup">单选题</Option>
                            <Option value="checkbox">多选题</Option>
                            <Option value="rating">评分题</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.type !== currentValues.type}>
                        {({ getFieldValue }) => {
                            const questionType = getFieldValue('type');
                            
                            if (questionType === 'radiogroup' || questionType === 'checkbox') {
                                return (
                                    <Form.List name="choices">
                                        {(fields, { add, remove }) => (
                                            <>
                                                <Form.Item label="选项">
                                                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                                                        添加选项
                                                    </Button>
                                                </Form.Item>
                                                {fields.map(({ key, name, ...restField }) => (
                                                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                                                        <Form.Item
                                                            {...restField}
                                                            name={name}
                                                            rules={[{ required: true, message: '请输入选项内容' }]}
                                                        >
                                                            <Input placeholder="请输入选项内容" />
                                                        </Form.Item>
                                                        <DeleteOutlined onClick={() => remove(name)} />
                                                    </Space>
                                                ))}
                                            </>
                                        )}
                                    </Form.List>
                                );
                            }
                            
                            if (questionType === 'rating') {
                                return (
                                    <Row gutter={16}>
                                        <Col span={8}>
                                            <Form.Item
                                                name="rateMin"
                                                label="最小值"
                                                initialValue={1}
                                            >
                                                <InputNumber min={0} />
                                            </Form.Item>
                                        </Col>
                                        <Col span={8}>
                                            <Form.Item
                                                name="rateMax"
                                                label="最大值"
                                                initialValue={5}
                                            >
                                                <InputNumber min={1} />
                                            </Form.Item>
                                        </Col>
                                        <Col span={8}>
                                            <Form.Item
                                                name="rateStep"
                                                label="步长"
                                                initialValue={1}
                                            >
                                                <InputNumber min={0.1} step={0.1} />
                                            </Form.Item>
                                        </Col>
                                    </Row>
                                );
                            }
                            
                            return null;
                        }}
                    </Form.Item>

                    <Form.Item>
                        <Space>
                            <Button type="primary" htmlType="submit">
                                {editingQuestion ? '更新问题' : '添加问题'}
                            </Button>
                            <Button onClick={() => setIsModalVisible(false)}>
                                取消
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default SurveyBuilder; 