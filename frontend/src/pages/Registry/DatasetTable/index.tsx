import SchemaTable from '@/components/SchemaTable';
import { PageContainer } from '@ant-design/pro-layout';
import type { ReactElement } from 'react';
import React from 'react';

const DatasetTable = (): ReactElement => {
  return (
    <PageContainer>
      <SchemaTable resourceTypes={['DatasetMetadata']} />
    </PageContainer>
  );
};

export default DatasetTable;
