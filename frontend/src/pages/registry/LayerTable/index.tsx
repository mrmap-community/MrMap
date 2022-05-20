import PageContainer from '@/components/PageContainer';
import SchemaTable from '@/components/SchemaTable';
import type { ReactElement } from 'react';

const LayerTable = (): ReactElement => {

  return (
    <PageContainer
      menuPaths={['registry']}
    >
      <SchemaTable 
        resourceTypes={{baseResourceType: 'Layer'}} 
      />
    </PageContainer>
  );
};

export default LayerTable;
