import '@ant-design/pro-table/dist/table.css';

import { PlusOutlined } from '@ant-design/icons';
import ProTable, { ActionType, ProColumnType } from '@ant-design/pro-table';
import { Button, Modal, notification, Space } from 'antd';
import { SortOrder } from 'antd/lib/table/interface';
import React, { MutableRefObject, ReactElement, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';

import JsonApiRepo from '../../../Repos/JsonApiRepo';
import { augmentColumnWithJsonSchema } from './TableHelper';

export interface RepoTableProps {
    /** Repository that defines the schema and offers CRUD operations */
    repo: JsonApiRepo
    /** Optional column hints, will be augmented by the repository schema */
    columns?: ProColumnType[]
    /** Reference to table actions for custom triggering */
    actionRef?: MutableRefObject<RepoActionType> | ((actions: RepoActionType) => void)
    /** Path to navigate to for adding records (if omitted, no 'New' button will be available) */
    onAddRecord?: string
    /** Function to invoke for editing records (if omitted, no 'Edit' button will be available) */
    onEditRecord?: (recordId: number | string) => void
}

// extends ActionType from Pro Table
// https://procomponents.ant.design/en-US/components/table/?current=1&pageSize=5#protable
export type RepoActionType = ActionType & {
  deleteRecord: (row:any) => void
}

function augmentColumns (resourceSchema: any, columnHints: ProColumnType[] | undefined): ProColumnType[] {
  const props = resourceSchema.properties.data.items.properties.attributes.properties;
  const columns:any = {};
  if (columnHints) {
    columnHints.forEach((columnHint) => {
      const columnName = columnHint.dataIndex as string;
      const schema = props[columnName];
      columns[columnName] = augmentColumnWithJsonSchema(columnHint, schema);
    });
  }
  for (const propName in props) {
    if (propName in columns) {
      continue;
    }
    const prop = props[propName];
    const columnHint = {
      dataIndex: propName
    };
    columns[propName] = augmentColumnWithJsonSchema(columnHint, prop);
  }
  return Object.values(columns);
}

export const RepoTable = ({
  repo,
  columns = undefined,
  actionRef = undefined,
  onAddRecord = undefined,
  onEditRecord = undefined
}: RepoTableProps): ReactElement => {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [augmentedColumns, setAugmentedColumns] = useState<any>([]);

  const actions = useRef<RepoActionType>();
  const setActions = (proTableActions: ActionType) => {
    actions.current = {
      ...proTableActions,
      deleteRecord: (row:any) => {
        async function deleteFromRepo () {
          await repo.delete(row.id);
          notification.success({
            message: 'Record deleted',
            description: `Record with id ${row.id} has been deleted succesfully`
          });
        }
        const modal = Modal.confirm({
          title: 'Delete record',
          content: `Do you want to delete the record with id ${row.id}?`,
          onOk: () => {
            modal.update(prevConfig => ({
              ...prevConfig,
              confirmLoading: true
            }));
            deleteFromRepo();
            proTableActions.reload();
          }
        });
      }
    };
    if (typeof actionRef === 'function') {
      actionRef(actions.current);
    } else if (actionRef) {
      actionRef.current = actions.current;
    }
  };

  // augment / build columns from schema (and add delete action)
  useEffect(() => {
    async function buildColumns () {
      const schema = await repo.getSchema();
      console.log(schema);
      const augmentedColumns = augmentColumns(schema, columns);
      if (!augmentedColumns.some(column => column.key === 'actions')) {
        augmentedColumns.push({
          key: 'actions',
          title: 'Aktionen',
          valueType: 'option',
          render: (text: any, record: any) => {
            return (
            <>
              <Space size='middle'>
              {onEditRecord && (
                  <Button
                    size='small'
                    onClick={() => onEditRecord(record.id)}
                  >
                    Bearbeiten
                  </Button>
              )}
                <Button
                  danger
                  size='small'
                  onClick={() => actions.current?.deleteRecord(record)}
                >
                  Löschen
                </Button>
              </Space>
            </>
            );
          }
        });
      }
      setAugmentedColumns(augmentedColumns);
    }
    buildColumns();
  }, []);

  // fetches data in format expected by antd ProTable component
  async function fetchData (params: any, sorter?: Record<string, SortOrder>): Promise<any> {
    let ordering = '';
    if (sorter) {
      for (const prop in sorter) {
        // TODO handle multi property ordering
        ordering = (sorter[prop] === 'descend' ? '-' : '') + prop;
      }
    }
    console.log('Fetching', params);
    const filters:any = {};
    for (const prop in params) {
      // 'current' and 'pageSize' are reserved names in antd ProTable (and cannot be used for filtering)
      if (prop !== 'current' && prop !== 'pageSize') {
        // TODO respect backend filtering capabilities
        filters[`filter[${prop}.icontains]`] = params[prop];
      }
    }
    const queryParams = {
      page: params.current,
      pageSize: params.pageSize,
      ordering: ordering,
      filters: filters
    };
    const response = await repo.findAll(queryParams);
    const records = response.data?.data === undefined ? [] : response.data?.data;
    const data: any = [];
    if (Array.isArray(records)) {
      records.forEach((record: any) => {
        const row = {
          key: record.id,
          id: record.id,
          ...record.attributes
        };
        data.push(row);
      });
    }
    const dataSource = {
      current: response.data?.meta.pagination.page,
      data: data,
      pageSize: params.pageSize,
      success: true,
      total: response.data?.meta.pagination.count
    };
    return dataSource;
  }

  return (
    <>{ augmentedColumns.length > 0 && (<ProTable
        request={fetchData}
        columns={augmentedColumns}
        scroll={{ x: true }}
        headerTitle={repo.displayName}
        actionRef={setActions}
        toolBarRender={onAddRecord
          ? () => [
          <Button
            type='primary'
            key='primary'
            onClick={() => {
              navigate(onAddRecord as string);
            }}
          >
            <PlusOutlined />Neu
          </Button>
            ]
          : () => []}
        search={{
          layout: 'vertical'
        }}
    />)}</>
  );
};

export default RepoTable;
