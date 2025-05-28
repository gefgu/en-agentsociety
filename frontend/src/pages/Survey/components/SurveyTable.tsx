import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, message, Space, Flex, Col, Row, Alert, Popconfirm, Dropdown } from 'antd';
import dayjs from 'dayjs';
import { Model, Survey as SurveyUI } from 'survey-react-ui';
import 'survey-core/defaultV2.min.css';
import { useForm } from 'antd/lib/form/Form';
import { ExportOutlined, EllipsisOutlined } from '@ant-design/icons';
import { Editor } from '../../../components/Editor';
import { Survey } from '../../../components/type';
import { fetchCustom } from '../../../components/fetch';
import { useTranslation } from 'react-i18next';

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
    const { t } = useTranslation();
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
                const errMessage = await res.text();
                throw new Error(errMessage);
            }
            const data = await res.json();
            setSurveys(data.data);
        } catch (err) {
            message.error(`${t('survey.fetchFailed')} ${err}`);
        }
    };

    const handleDelete = async (id) => {
        try {
            const res = await fetchCustom(`/api/surveys/${id}`, { method: 'DELETE' });
            if (!res.ok) {
                const errMessage = await res.text();
                throw new Error(errMessage);
            }
            message.success(t('survey.deleteSuccess'));
            await fetchSurveys();
        } catch (err) {
            message.error(`${t('survey.deleteFailed')} ${err}`);
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
                    const errMessage = await res.text();
                    throw new Error(errMessage);
                }
                message.success(t('survey.updateSuccess'));
                setOpen(false);
                await fetchSurveys();
            } catch (err) {
                message.error(`${t('survey.updateFailed')} ${err}`);
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
                    const errMessage = await res.text();
                    throw new Error(errMessage);
                }
                message.success(t('survey.createSuccess'));
                setOpen(false);
                await fetchSurveys();
            } catch (err) {
                message.error(`${t('survey.createFailed')} ${err}`);
            }
        }
    };

    const handleModalCancel = () => {
        setOpen(false);
    };

    const tableColumns = [
        { title: t('survey.table.id'), dataIndex: 'id', width: '13%' },
        { title: t('survey.table.name'), dataIndex: 'name', width: '7%' },
        {
            title: t('survey.table.data'),
            dataIndex: 'data',
            width: '55%',
            ellipsis: true,
            render: (text) => JSON.stringify(text, null, 2),
        },
        {
            title: t('survey.table.createdAt'),
            dataIndex: 'created_at',
            width: '10%',
            render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: t('survey.table.updatedAt'),
            dataIndex: 'updated_at',
            width: '10%',
            render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: t('survey.table.action'),
            key: 'action',
            width: '15%',
            render: (record) => (
                <Space size="middle">
                    <Button type="primary" onClick={() => handleEdit(record)}
                    >{t('survey.table.edit')}</Button>
                    <Dropdown
                        menu={{
                            items: [
                                {
                                    key: 'delete',
                                    label: (
                                        <Popconfirm
                                            title="Are you sure to delete this survey?"
                                            onConfirm={() => handleDelete(record.id)}
                                        >
                                            <span style={{ color: '#ff4d4f' }}>{t('survey.table.delete')}</span>
                                        </Popconfirm>
                                    )
                                }
                            ]
                        }}
                    >
                        <Button icon={<EllipsisOutlined />} />
                    </Dropdown>
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
                        {t('survey.createSurvey')}
                    </Button>
                </Flex>
                <Table dataSource={surveys} columns={tableColumns} rowKey="id" />
                <Modal
                    open={open}
                    width='80vw'
                    title={editingSurvey.id ? t('survey.editSurvey') : t('survey.createSurvey')}
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
                            <Form.Item label={t('survey.surveyName')} name="name" rules={[
                                { required: true, message: t('survey.pleaseInputName') },
                            ]}>
                                <Input />
                            </Form.Item>
                            <Form.Item
                                label={<span>{t('survey.surveyJsonData')} ({t('survey.onlineVisualEditor')}&nbsp;<ExportOutlined onClick={handleJsonButton} />&nbsp;)</span>}
                                name="data"
                                rules={[
                                    { required: true, message: t('survey.pleaseInputData') },
                                    {
                                        validator: (_, value, callback) => {
                                            try {
                                                JSON.parse(value);
                                                callback();
                                            } catch (e) {
                                                callback(t('survey.invalidJson'));
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
                                {t('survey.submit')}
                            </Button>
                        </Form>
                        <div style={{ overflow: 'auto', maxHeight: '60vh', width: '50%' }}>
                            <SurveyUI model={model} />
                        </div>
                    </Flex>
                </Modal>
            </Flex>
        </>
    );
};

export default SurveyTable;