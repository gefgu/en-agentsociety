import { useEffect, useState, useRef } from "react";

import { Col, Row, message, Table, Button, Space, Popconfirm, Modal, } from 'antd';
import dayjs from "dayjs";
import { parseT } from "../../components/util";
import { useNavigate } from "react-router-dom";
import React from "react";
import { Experiment, experimentStatusMap } from "../../components/type";
import { ProColumns, ProDescriptions, ProTable } from "@ant-design/pro-components";
import { ActionType } from "@ant-design/pro-table";

const Page = () => {
    const navigate = useNavigate(); // 获取导航函数
    const [detail, setDetail] = useState<Experiment | null>(null);
    const actionRef = useRef<ActionType>();

    const columns: ProColumns<Experiment>[] = [
        { title: 'ID', dataIndex: 'id', width: '15%' },
        { title: 'Name', dataIndex: 'name', width: '5%' },
        { title: 'Num Day', dataIndex: 'num_day', width: '5%', search: false },
        {
            title: 'Status',
            dataIndex: 'status',
            width: '5%',
            valueEnum: experimentStatusMap,
        },
        { title: 'Current Day', dataIndex: 'cur_day', width: '5%', search: false },
        { title: 'Current Time', dataIndex: 'cur_t', width: '5%', render: (t: number) => parseT(t), search: false },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            width: '5%',
            valueType: "dateTime",
            search: false
        },
        {
            title: 'Updated At',
            dataIndex: 'updated_at',
            width: '5%',
            valueType: "dateTime",
            search: false,
        },
        {
            title: 'Action',
            width: '10%',
            search: false,
            render: (_, record) => {
                // copy record to avoid reference change
                record = { ...record };
                return <Space>
                    <Button
                        type="primary"
                        onClick={() => navigate(`/exp/${record.id}`)}
                        disabled={record.status === 0}
                    >Goto</Button>
                    <Button
                        type="primary"
                        onClick={() => setDetail(record)}
                    >Detail</Button>
                    <Popconfirm
                        title="Are you sure to delete this experiment?"
                        onConfirm={async () => {
                            try {
                                const res = await fetch(`/api/experiments/${record.id}`, {
                                    method: 'DELETE',
                                })
                                if (res.ok) {
                                    message.success('Delete experiment successfully');
                                    actionRef.current?.reload();
                                } else {
                                    // Read the error message as text
                                    const errMessage = await res.text();
                                    throw new Error(errMessage);
                                }
                            } catch (err) {
                                message.error('Failed to delete experiment: ' + err);
                            }
                        }}
                    >
                        <Button type="primary" danger>Delete</Button>
                    </Popconfirm>
                </Space>
            },
        },
    ];

    return (
        <>
            <Row>
                <Col span={24}>
                    <ProTable<Experiment>
                        actionRef={actionRef}
                        columns={columns}
                        request={async (params) => {
                            try {
                                const res = await fetch('/api/experiments')
                                let data = await res.json()
                                data = data.data;
                                if (params.name !== undefined && params.name !== '') {
                                    console.log('params.name:', params.name)
                                    data = data.filter((d: Experiment) => d.name.includes(params.name))
                                }
                                if (params.id !== undefined && params.id !== '') {
                                    data = data.filter((d: Experiment) => d.id === params.id)
                                }
                                if (params.status !== undefined) {
                                    data = data.filter((d: Experiment) => d.status == params.status)
                                }
                                return { data, success: true };
                            } catch (err) {
                                console.error('Failed to fetch experiments:', err)
                                return { data: [], success: false }
                            }
                        }}
                        rowKey="id"
                        columnEmptyText="-"
                    />
                </Col>
            </Row>
            <Modal
                title="Experiment Detail"
                width="60vw"
                open={detail !== null}
                onCancel={() => setDetail(null)}
                footer={null}
            >
                <ProDescriptions<Experiment>
                    column={2}
                    title={detail?.name}
                    request={async () => {
                        return {
                            success: true,
                            data: detail,
                        };
                    }}
                    columns={[
                        { title: 'ID', dataIndex: 'id' },
                        { title: 'Name', dataIndex: 'name' },
                        { title: 'Created At', dataIndex: 'created_at', valueType: 'dateTime' },
                        { title: 'Updated At', dataIndex: 'updated_at', valueType: 'dateTime' },
                        { title: 'Num Day', dataIndex: 'num_day' },
                        { title: 'Status', dataIndex: 'status', valueEnum: experimentStatusMap },
                        { title: 'Current Day', dataIndex: 'cur_day' },
                        { title: 'Current Time', dataIndex: 'cur_t', render: (t: number) => parseT(t) },
                        { title: 'Config', dataIndex: 'config', span: 2, valueType: 'jsonCode' },
                        { title: 'Error', dataIndex: 'error', span: 2, valueType: 'code' },
                    ]}
                />
            </Modal>
        </>
    );
}

export default Page;
