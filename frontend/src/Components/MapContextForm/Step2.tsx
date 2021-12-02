import { InfoCircleOutlined } from '@ant-design/icons';
import { Divider, Form, Modal, notification } from 'antd';
import React, { FC, useEffect, useState } from 'react';

import DatasetMetadataRepo from '../../Repos/DatasetMetadataRepo';
import FeatureTypeRepo from '../../Repos/FeatureTypeRepo';
import LayerRepo from '../../Repos/LayerRepo';
import { InputFormField } from '../Shared/FormFields/InputFormField/InputFormField';
import { SelectAutocompleteFormField } from '../Shared/FormFields/SelectAutocompleteFormField/SelectAutocompleteFormField';
import { TreeNodeType } from './MapContextForm';

interface MapContextLayerFormProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (values?:any) => void;
  isEditing: boolean;
  node: TreeNodeType | undefined;
  okButtonProps: any;
}

const fetchData = async (
  fetcher: () => void,
  setValues: (values: any) => void,
  setLoading: (bool: boolean) => void
) => {
  setLoading(true);
  try {
    const response:any = await fetcher();
    setValues(response);
  } catch (error: any) {
    notification.error({
      message: 'Search  failed',
      description: error,
      duration: null
    });
    throw new Error(error);
  } finally {
    setLoading(false);
  }
};

const layerRepo = new LayerRepo();
const datasetMetadataRepo = new DatasetMetadataRepo();
const featureTypesRepo = new FeatureTypeRepo();

export const MapContextLayerForm: FC<MapContextLayerFormProps> = ({
  visible,
  onCancel,
  isEditing,
  node,
  onSubmit,
  okButtonProps

}) => {
  const [form] = Form.useForm();

  const [isDatasetMetadataOptionsLoading, setIsDatasetMetadataOptionsLoading] = useState<boolean>(false);
  const [isRenderingLayerOptionsLoading, setIsRenderingLayerOptionsLoading] = useState<boolean>(false);
  const [isFeatureSelectionLayerOptionsLoading, setIsFeatureSelectionLayerOptionsLoading] = useState<boolean>(false);

  const [datasetMetadataOptions, setDatasetMetadataOptions] = useState<any[]>([]);
  const [renderingLayerOptions, setRenderingLayerOptions] = useState<any[]>([]);
  const [featureSelectionLayerOptions, setFeatureSelectionLayerOptions] = useState<any[]>([]);

  const [isShowingRenderingData, setIsShowingRenderingData] = useState<boolean>(false);
  const [isShowingRenderingLayerAttributes, setIsShowingRenderingLayerAttributes] = useState<boolean>(false);
  /**
   * @description: Hook to run on component mount. Fetches initial results for daataset metadata autocomplete
   */
  useEffect(() => {
    fetchData(
      () => datasetMetadataRepo.autocomplete(''),
      (values) => setDatasetMetadataOptions(values),
      (boolean) => setIsDatasetMetadataOptionsLoading(boolean)
    );
  }, []);

  /**
   * @description: Hook to run on component mount. Fetches initial results for rendering layer autocomplete
   */
  useEffect(() => {
    fetchData(
      () => layerRepo.autocomplete(''),
      (values) => setRenderingLayerOptions(values),
      (boolean) => setIsRenderingLayerOptionsLoading(boolean)
    );
  }, []);

  /**
   * @description: Hook to run on component mount. Fetches initial results for rendering feature type selection
   * layers autocomplete
   */
  useEffect(() => {
    fetchData(
      () => featureTypesRepo.autocomplete(''),
      (values) => setFeatureSelectionLayerOptions(values),
      (boolean) => setIsFeatureSelectionLayerOptionsLoading(boolean)
    );
  }, []);

  useEffect(() => {
    if (!isShowingRenderingData) {
      form.resetFields(['renderingLayer']);
    }
  }, [isShowingRenderingData]);

  useEffect(() => {
    if (!isShowingRenderingLayerAttributes) {
      form.resetFields(['scaleMin', 'scaleMax', 'style']);
    }
  }, [isShowingRenderingLayerAttributes]);

  useEffect(() => {
    // since the modal is not being destroyed on close,
    // this is a backup solution. Reseting or setting the values when the modal becomes visible
    if (visible) {
      form.resetFields();
      setIsShowingRenderingData(false);
      setIsShowingRenderingLayerAttributes(false);
      setRenderingLayerOptions([]);
      if (isEditing && node) {
        form.setFieldsValue({
          name: node.properties.name,
          title: node.title
        });
      }
    }
  }, [visible]);

  return (
    <Modal
      title={isEditing ? 'Edit Node' : 'Add Node'}
      visible={visible}
      onOk={() => {
        form.submit();
      }}
      onCancel={onCancel}
      destroyOnClose={true} // not working for some unknown reason
      okButtonProps={okButtonProps}
    >
      <Form
        form={form}
        layout='vertical'
        initialValues={{
          name: '',
          title: ''
        }}
        onFinish={(values) => onSubmit(values)}
      >
      <Divider
        plain
        orientation='left'
      >
        <h3> Metainformation of MapContextLayer </h3>
      </Divider>
        <InputFormField
          label='Name'
          name='name'
          tooltip={{ title: 'an identifying name for this map context layer', icon: <InfoCircleOutlined /> }}
          placeholder='Map Context Layer Name'
          validation={{
            rules: [{ required: true, message: 'Please input a name!' }],
            hasFeedback: true
          }}
        />
        <InputFormField
          label='Title'
          name='title'
          tooltip={{ title: 'a short descriptive title for this map context layer', icon: <InfoCircleOutlined /> }}
          placeholder='Map Context Layer Title'
          validation={{
            rules: [{ required: true, message: 'Please input a title!' }],
            hasFeedback: true
          }}
        />
        <Divider
          plain
          orientation='left'
        >
          <h3> Associated metadata record </h3>
        </Divider>

        <SelectAutocompleteFormField
          loading={isDatasetMetadataOptionsLoading}
          label='Dataset Metadata'
          name='datasetMetadata'
          placeholder='Select Metadata'
          searchData={datasetMetadataOptions}
          tooltip={{
            title: 'You can use this field to pre filter possible Layer selection.',
            icon: <InfoCircleOutlined />
          }}
          // validation={{
          //   rules: [{ required: true, message: 'Please select metadata!' }],
          //   hasFeedback: true
          // }}
          onSelect={(value, option) => {
            setIsShowingRenderingData(true);
            // TODO set rendering layer list
            // TODO reset dependents
          }}
          onClear={() => {
            setIsShowingRenderingData(false);
            // TODO clear rendering layer list
            // TODO reset dependents
          }}
          onSearch={(value: string) => {
            fetchData(
              () => datasetMetadataRepo.autocomplete(value),
              (values) => setDatasetMetadataOptions(values),
              (boolean) => setIsDatasetMetadataOptionsLoading(boolean)
            );
          }}
          pagination
        />

        {isShowingRenderingData && (
          <>
            <Divider
              plain
              orientation='left'
            >
              <h3> Rendering options </h3>
            </Divider>

            <SelectAutocompleteFormField
              loading={isRenderingLayerOptionsLoading}
              label='Rendering Layer'
              name='renderingLayer'
              placeholder='Select a rendering layer'
              searchData={renderingLayerOptions}
              tooltip={{ title: 'Select a layer for rendering.', icon: <InfoCircleOutlined /> }}
              // validation={{
              //   rules: [{ required: true, message: 'Please input a rendering layer!' }],
              //   hasFeedback: true
              // }}
              onSelect={(value, option) => {
                setIsShowingRenderingLayerAttributes(true);
                // fill attribute fields with current layer attributes
                form.setFieldsValue({
                  scaleMin: option.attributes.scaleMin,
                  scaleMax: option.attributes.scaleMax,
                  style: option.attributes.style
                });
              }}
              onSearch={(value: string) => {
                fetchData(
                  () => layerRepo.autocomplete(value),
                  (values) => setRenderingLayerOptions(values),
                  (boolean) => setIsRenderingLayerOptionsLoading(boolean)
                );
              }}
              onClear={() => {
                setIsShowingRenderingLayerAttributes(false);
              }}
            />
            {isShowingRenderingLayerAttributes && (
              <>
                <InputFormField
                  disabled={!form.getFieldValue('scaleMin')}
                  label='Scale minimum value'
                  name='scaleMin'
                  tooltip={{
                    title: 'minimum scale for a possible request to this layer. If the request is out of the given' +
                    'scope, the service will response with empty transparentimages. None value means no restriction.',
                    icon: <InfoCircleOutlined />
                  }}
                  placeholder='Scale minimum value'
                  type='number'
                />

                <InputFormField
                  disabled={!form.getFieldValue('scaleMax')}
                  label='Scale maximum value'
                  name='scaleMax'
                  tooltip={{
                    title: 'maximum scale for a possible request to this layer. If the request is out of the given' +
                    'scope, the service will response with empty transparentimages. None value means no restriction.',
                    icon: <InfoCircleOutlined />
                  }}
                  placeholder='Scale maximum value'
                  type='number'
                />

                <InputFormField
                  disabled={!form.getFieldValue('style')}
                  label='Style'
                  name='style'
                  tooltip={{ title: 'Select a style for rendering.', icon: <InfoCircleOutlined /> }}
                  placeholder='Style'
                />
            </>
            )}
          </>
        )}
        <Divider
          plain
          orientation='left'
        >
          <h3> Feature selection options </h3>
        </Divider>

        <SelectAutocompleteFormField
          loading={isFeatureSelectionLayerOptionsLoading}
          label='Selection Layer'
          name='featureSelectionLayer'
          placeholder='Select a feature type'
          searchData={featureSelectionLayerOptions}
          tooltip={{ title: ' Select a layer for feature selection.', icon: <InfoCircleOutlined /> }}
          onSearch={(value: string) => {
            fetchData(
              () => layerRepo.autocomplete(value),
              (values) => setFeatureSelectionLayerOptions(values),
              (boolean) => setIsFeatureSelectionLayerOptionsLoading(boolean)
            );
          }}
        />
      </Form>
    </Modal>
  );
};
