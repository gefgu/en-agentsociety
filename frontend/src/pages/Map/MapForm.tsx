import React from 'react';
import { Form, Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { MapConfig } from '../../types/config';
import { useTranslation } from 'react-i18next';

const { Dragger } = Upload;

interface MapFormProps {
    value: Partial<MapConfig>;
    onChange: (value: Partial<MapConfig>) => void;
}

const MapForm: React.FC<MapFormProps> = ({ value, onChange }) => {
    const [form] = Form.useForm();
    const { t } = useTranslation();

    // Update parent component state when form values change
    const handleValuesChange = (changedValues: any, allValues: any) => {
        console.log('changedValues', changedValues);
        console.log('allValues', allValues);
        const file = allValues.file_path.file;
        if (file && file.status === 'done') {
            onChange({
                file_path: file.response.data.file_path,
            });
        } else {
            onChange({
                file_path: null,
            });
        }
    };

    // Set initial values
    React.useEffect(() => {
        form.setFieldsValue(value);
    }, [form, value]);

    const uploadProps = {
        name: 'file',
        multiple: false,
        action: '/api/map-configs/-/upload',
        beforeUpload: (file) => {
            // check suffix
            if (!file.name.endsWith('.pb')) {
                message.error('the file must be a .pb file');
                return false;
            }
            return true;
        },
        onChange(info) {
            const { status } = info.file;
            if (status === 'done') {
                message.success(`${info.file.name} uploaded successfully`);
            } else if (status === 'error') {
                message.error(`${info.file.name} uploaded failed`);
            }
        },
    };

    return (
        <Form
            form={form}
            layout="vertical"
            onValuesChange={handleValuesChange}
            initialValues={value}
        >
            <Form.Item
                name="file_path"
                label={t('form.map.uploadTitle')}
                required
            >
                <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                    <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">{t('form.map.uploadHint')}</p>
                    <p className="ant-upload-hint">
                        {t('form.map.uploadDescription')}
                    </p>
                </Dragger>
            </Form.Item>
        </Form>
    );
};

export default MapForm; 