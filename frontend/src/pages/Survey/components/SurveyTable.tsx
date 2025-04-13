import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, message, Space, Flex, Col, Row, Alert, Popconfirm } from 'antd';
import dayjs from 'dayjs';
import { Model, Survey as SurveyUI } from 'survey-react-ui';
import 'survey-core/defaultV2.min.css';
import { useForm } from 'antd/lib/form/Form';
import { ExportOutlined } from '@ant-design/icons';
import { Editor } from '../../../components/Editor';
import { Survey } from '../../../components/type';
import { fetchCustom } from '../../../components/fetch';

interface EditingSurvey {
    id: string;
    name: string;
    data: string;
}

const EmptySurvey: EditingSurvey = {
    id: '',
    name: '',
    data: '',
};

const SurveyTable = () => {
    const [surveys, setSurveys] = useState<Survey[]>([]);
    const [open, setOpen] = useState(false);
    const [editingSurvey, setEditingSurvey] = useState<EditingSurvey>(EmptySurvey);
    const [form] = useForm();

    useEffect(() => {
        if (editingSurvey) {
            form.setFieldsValue({
                name: editingSurvey.name,
                data: editingSurvey.data,
            });
        }
    }, [editingSurvey, form]);

    useEffect(() => {
        fetchSurveys();
    }, []);


    const handleJsonButton = () => {
        window.open('https://surveyjs.io/create-free-survey', '_blank');
    };


    const fetchSurveys = async () => {
        try {
            const res = await fetchCustom('/api/surveys');
            if (!res.ok) {
                // Read the error message as text
                const errMessage = await res.text();
                throw new Error(errMessage);
            }
            const data = await res.json();
            setSurveys(data.data);
        } catch (err) {
            message.error(`Fetch surveys failed: ${err}`);
        }
    };

    const handleDelete = async (id) => {
        try {
            const res = await fetchCustom(`/api/surveys/${id}`, { method: 'DELETE' });
            if (!res.ok) {
                // Read the error message as text
                const errMessage = await res.text();
                throw new Error(errMessage);
            }
            message.success('Delete success!');
            await fetchSurveys();
        } catch (err) {
            message.error(`Delete failed: ${err}`);
        }
    };

    const handleEdit = (survey) => {
        setEditingSurvey({
            id: survey.id,
            name: survey.name,
            data: JSON.stringify(survey.data, null, 2),
        });
        setOpen(true);
    };

    const handleCreate = () => {
        setEditingSurvey(EmptySurvey);
        setOpen(true);
    };

    const handleSubmit = async (values) => {
        console.log(values);
        console.log(editingSurvey);
        if (editingSurvey.id !== '') {
            try {
                const res = await fetchCustom(`/api/surveys/${editingSurvey.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: values.name,
                        data: JSON.parse(values.data),
                    }),
                });
                if (!res.ok) {
                    // Read the error message as text
                    const errMessage = await res.text();
                    throw new Error(errMessage);
                }
                message.success('Update success!');
                setOpen(false);
                await fetchSurveys();
            } catch (err) {
                message.error(`Update failed: ${err}`);
            }
        } else {
            try {
                const res = await fetchCustom('/api/surveys', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: values.name,
                        data: JSON.parse(values.data),
                    }),
                });
                if (!res.ok) {
                    // Read the error message as text
                    const errMessage = await res.text();
                    throw new Error(errMessage);
                }
                message.success('Create success!');
                setOpen(false);
                await fetchSurveys();
            } catch (err) {
                message.error(`Create failed: ${err}`);
            }
        }
    };

    const handleModalCancel = () => {
        setOpen(false);
    };

    const tableColumns = [
        { title: 'ID', dataIndex: 'id', width: '13%' },
        { title: 'Name', dataIndex: 'name', width: '7%' },
        {
            title: 'Data',
            dataIndex: 'data',
            width: '55%',
            ellipsis: true,
            render: (text) => JSON.stringify(text, null, 2),
        },
        {
            title: 'Created At',
            dataIndex: 'createdAt',
            width: '10%',
            render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: 'Updated At',
            dataIndex: 'updatedAt',
            width: '10%',
            render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: 'Action',
            key: 'action',
            width: '15%',
            render: (record) => (
                <Space size="middle">
                    <Button type="primary" onClick={() => handleEdit(record)}>Edit & Preview</Button>
                    <Popconfirm title="Are you sure to delete this survey?" onConfirm={() => handleDelete(record.id)}>
                        <Button type="primary" danger>Delete</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    let model = new Model({});
    try {
        model = new Model(JSON.parse(editingSurvey.data));
    } catch (e) {
        console.error('Failed to parse JSON data:', e);
    }
    model.showCompleteButton = false;

    return (
        <>
            <Flex vertical style={{ margin: "16px" }}>
                <Flex justify='end'>
                    <Button type="primary" onClick={handleCreate} style={{ marginBottom: 16 }}>
                        Create Survey
                    </Button>
                </Flex>
                <Table dataSource={surveys} columns={tableColumns} rowKey="id" />
                <Modal
                    open={open}
                    width='80vw'
                    title={editingSurvey ? 'Edit Survey' : 'Create Survey'}
                    onCancel={handleModalCancel}
                    footer={null}
                >
                    <Flex>
                        <Form
                            form={form}
                            style={{ width: '50%', marginRight: 16 }}
                            layout="vertical"
                            onValuesChange={(changedValues, allValues) => {
                                setEditingSurvey({
                                    ...editingSurvey,
                                    ...changedValues,
                                });
                            }}
                            onFinish={handleSubmit}
                        >
                            <Form.Item label="Name" name="name" rules={[
                                { required: true, message: 'Please input name' },
                            ]}>
                                <Input />
                            </Form.Item>
                            <Form.Item
                                label={<span>Survey JSON Data (Online Visual Editor&nbsp;<ExportOutlined onClick={handleJsonButton} />&nbsp;)</span>}
                                name="data"
                                rules={[
                                    { required: true, message: 'Please input data JSON' },
                                    {
                                        validator: (_, value, callback) => {
                                            try {
                                                JSON.parse(value);
                                                callback();
                                            } catch (e) {
                                                callback('Invalid JSON format');
                                            }
                                        }
                                    },
                                ]}
                            >
                                <Editor
                                    width="100%"
                                    height="50vh"
                                    language="json"
                                    defaultValue=''
                                    value={form.getFieldValue('data') || ''}
                                    onChange={(value) => form.setFieldValue('data', value)}
                                />
                            </Form.Item>
                            <Button type="primary" htmlType='submit' style={{ marginTop: 8 }}>
                                Submit
                            </Button>
                        </Form>
                        <div style={{ overflow: 'auto', maxHeight: '60vh', width: '50%' }}>
                            <SurveyUI model={model} />
                        </div>
                    </Flex>
                </Modal>
            </Flex >
        </>
    );
};

export default SurveyTable;