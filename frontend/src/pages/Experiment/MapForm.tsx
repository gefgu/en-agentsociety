import React, { useState } from 'react';
import { Form, Input, Card, Upload, Button, message } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadProps, UploadFile } from 'antd';
import { MapConfig } from '../../types/config';

const { Dragger } = Upload;

interface MapFormProps {
  value: Partial<MapConfig>;
  onChange: (value: Partial<MapConfig>) => void;
}

const MapForm: React.FC<MapFormProps> = ({ value, onChange }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // Update parent component state when form values change
  const handleValuesChange = (changedValues: any, allValues: any) => {
    onChange(allValues);
  };

  // Set initial values
  React.useEffect(() => {
    form.setFieldsValue(value);
  }, [form, value]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    action: '/api/upload-map',
    fileList,
    onChange(info) {
      let newFileList = [...info.fileList];
      
      // Just keep the latest file
      newFileList = newFileList.slice(-1);
      
      setFileList(newFileList);
      
      if (info.file.status === 'done') {
        message.success(`${info.file.name} file uploaded successfully`);
        // Update the form with the file path
        form.setFieldsValue({
          file_path: `maps/${info.file.name}`
        });
        handleValuesChange({ file_path: `maps/${info.file.name}` }, form.getFieldsValue());
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} file upload failed.`);
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
      <Card title="Map Configuration" bordered={false}>
        <Form.Item
          name="file_path"
          label="Map File Path"
          rules={[{ required: true, message: 'Please enter map file path or upload a map file' }]}
        >
          <Input placeholder="Enter map file path (e.g., maps/default_map.pb)" />
        </Form.Item>
        
        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Click or drag map file to this area to upload</p>
          <p className="ant-upload-hint">
            Support for a single .pb file upload. The file will be stored in the maps directory.
          </p>
        </Dragger>
        
        <Form.Item
          name="cache_path"
          label="Cache Path (Optional)"
        >
          <Input placeholder="Enter cache path (optional)" />
        </Form.Item>
      </Card>
    </Form>
  );
};

export default MapForm; 