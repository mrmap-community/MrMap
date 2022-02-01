import { ApiOutlined, GithubOutlined } from '@ant-design/icons';
import { Layout, Space } from 'antd';
import React, { useState } from 'react';
import { BrowserRouter as Router, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import './App.css';
import { Dashboard } from './Components/Dashboard/Dashboard';
import { MapContext } from './Components/MapContextForm/MapContext';
import MapContextTable from './Components/MapContextTable/MapContextTable';
import DatasetMetadataTable from './Components/Metadata/DatasetMetadataTable';
import { NavBar } from './Components/NavBar/NavBar';
import FeatureTypeTable from './Components/OgcService/FeatureTypeTable';
import LayerTable from './Components/OgcService/LayerTable';
import OgcServiceAdd from './Components/OgcService/OgcServiceAdd';
import WfsTable from './Components/OgcService/WfsTable';
import { PageNotFound } from './Components/PageNotFound/PageNotFound';
import { TaskProgressList } from './Components/Task/TaskProgress';
import { Login } from './Components/Users/Auth/Login';
import { Logout } from './Components/Users/Auth/Logout';
import { WmsSecuritySettings } from './Components/WmsSecuritySettings/WmsSecuritySettings';
import WmsTable from './Components/WmsTable/WmsTable';
import { useAuth } from './Hooks/useAuth';
import logo from './logo.png';
import WebFeatureServiceRepo from './Repos/WfsRepo';
import WebMapServiceRepo from './Repos/WmsRepo';


const { Content, Footer, Sider } = Layout;

function RequireAuth ({ children }:{ children: JSX.Element }) {
  const auth = useAuth();
  const location = useLocation();
  if (!auth || !auth.userId) {
    // store location so login page can forward to original page
    return <Navigate to='/login' state={{ from: location }} />;
  }
  return children;
}

export default function App (): JSX.Element {
  const swaggerUiUrl = '/swagger-ui/';

  const [collapsed, setCollapsed] = useState(false);

  const onCollapse = (_collapsed: boolean) => {
    setCollapsed(_collapsed);
  };

  return (
    <Router>
      <Routes>
        <Route
          path='/login'
          element={<Login />}
        />
        <Route
          path='/logout'
          element={<Logout />}
        />
        <Route
          path='/'
          element={
            <RequireAuth>
              <Layout style={{ minHeight: '100vh' }}>
                <Sider
                  collapsible
                  collapsed={collapsed}
                  onCollapse={onCollapse}>
                  <div className='logo'>
                    <img
                      src={logo}
                      alt='Mr. Map Logo'
                    >
                    </img>
                  </div>
                  <NavBar />
                </Sider>
                <Layout className='site-layout'>
                  <Content style={{ margin: '0 16px' }}>
                    <div
                      className='site-layout-background'
                      style={{ padding: 24, minHeight: 360 }}
                    >
                      <Outlet />
                    </div>
                  </Content>
                  <Footer style={{ textAlign: 'center' }}>
                    <Space>
                      <a href={swaggerUiUrl}><ApiOutlined /> OpenAPI</a>
                      <a href='https://github.com/mrmap-community/mrmap'><GithubOutlined /> GitHub</a>
                    </Space>
                  </Footer>
                </Layout>
              </Layout>
            </RequireAuth>
          }
        >
          <Route
            path='/notify'
            element={<TaskProgressList />}
          />
          <Route
            path='/'
            element={<Dashboard />}
          />
          <Route
            path='/registry/services/wms'
            element={<WmsTable />}
          />
          <Route
            path='/registry/services/wms/add'
            element={<OgcServiceAdd repo={new WebMapServiceRepo()} />}
          />
          <Route
            path='/registry/services/wms/:id/security'
            element={<WmsSecuritySettings />}
          />
          <Route
            path='/registry/services/wfs'
            element={<WfsTable />}
          />
          <Route
            path='/registry/services/wfs/add'
            element={<OgcServiceAdd repo={new WebFeatureServiceRepo()} />}
          />
          <Route
            path='/registry/layers'
            element={<LayerTable />}
          />
          <Route
            path='/registry/featuretypes'
            element={<FeatureTypeTable />}
          />
          <Route
            path='/registry/dataset-metadata'
            element={<DatasetMetadataTable />}
          />
          <Route
            path='/registry/mapcontexts'
            element={<MapContextTable />}
          />
          <Route
            path='/registry/mapcontexts/add'
            element={<MapContext />}
          />
          <Route
            path='/registry/mapcontexts/:id/edit'
            element={<MapContext />}
            // @ts-ignore
            exact
          />
          <Route
            path='*'
            element={<PageNotFound/>}
          />
        </Route>
      </Routes>
    </Router>
  );
}
