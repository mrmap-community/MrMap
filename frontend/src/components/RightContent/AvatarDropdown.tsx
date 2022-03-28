import { LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons';
import { Avatar, Menu, message, Spin } from 'antd';
import { stringify } from 'querystring';
import React, { useEffect } from 'react';
import { useOperationMethod } from 'react-openapi-client/useOperationMethod';
import { history, useIntl, useModel } from 'umi';
import HeaderDropdown from '../HeaderDropdown';
import styles from './index.less';

export type GlobalHeaderRightProps = {
  menu?: boolean;
};


const AvatarDropdown: React.FC<GlobalHeaderRightProps> = ({ menu }) => {
  const intl = useIntl();
  const { initialState, setInitialState } = useModel('@@initialState');
  const [
    deleteLogin,
    { loading: deleteLoginLoading, error: deleteLoginError, response: deleteLoginResponse , api: deleteLoginApi},
  ] = useOperationMethod('deleteLogout');

  useEffect(() => {
    if (deleteLoginResponse && deleteLoginResponse.status === 200){
      setInitialState((s: any) => ({ ...s, currentUser: undefined }));
      const { query = {}, pathname } = history.location;
      const { redirect } = query;
      // Note: There may be security issues, please note
      if (window.location.pathname !== '/user/login' && !redirect) {
        setTimeout(() => {
          history.replace({
            pathname: '/user/login',
            search: stringify({
              redirect: pathname,
            }),
          });
        });
      }
      const defaultLoginSuccessMessage = intl.formatMessage({
        id: 'pages.logout.success',
        defaultMessage: 'Logout succesful！',
      });
      message.success(defaultLoginSuccessMessage);
    }
  }, [deleteLoginResponse, intl, setInitialState]);

  useEffect(() => {
    if (deleteLoginError){
      const defaultLoginFailureMessage = intl.formatMessage({
        id: 'pages.logout.failure',
        defaultMessage: 'Logout failed, please try again!',
      });
      message.error(defaultLoginFailureMessage);
    }
  }, [deleteLoginError, intl]);

  const loading = (
    <span className={`${styles.action} ${styles.account}`}>
      <Spin
        size="small"
        style={{
          marginLeft: 8,
          marginRight: 8,
        }}
      />
    </span>
  );

  if (deleteLoginLoading || !initialState || !initialState.currentUser?.data?.attributes?.username) {
    return loading;
  }

  const menuHeaderDropdown = (
    <Menu className={styles.menu} selectedKeys={[]}>
      {menu && (
        <Menu.Item key="center">
          <UserOutlined />
          User information
        </Menu.Item>
      )}
      {menu && (
        <Menu.Item key="settings">
          <SettingOutlined />
          User settings
        </Menu.Item>
      )}
      {menu && <Menu.Divider />}

      <Menu.Item key="logout" onClick={
        () => {
          deleteLogin();
        }
        }>
        <LogoutOutlined />
        Log out
      </Menu.Item>
    </Menu>
  );
  return (
    <HeaderDropdown overlay={menuHeaderDropdown}>
      <span className={`${styles.action} ${styles.account}`}>
        <Avatar
          size="small"
          className={styles.avatar}
          src={initialState.currentUser?.data?.attributes?.avatar}
          alt="avatar"
        />
        <span className={`${styles.name} anticon`}>{initialState.currentUser?.data?.attributes?.username}</span>
      </span>
    </HeaderDropdown>
  );
};

export default AvatarDropdown;
