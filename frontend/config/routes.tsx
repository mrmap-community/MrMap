﻿import { CrownOutlined, HeartOutlined, SmileOutlined } from '@ant-design/icons';
import type { MenuDataItem } from '@ant-design/pro-layout';
//@ts-ignore
import React from 'react';
const IconMap = {
  smile: <SmileOutlined />,
  heart: <HeartOutlined />,
  crown: <CrownOutlined />,
};

export const loopMenuItem = (menus: MenuDataItem[]): MenuDataItem[] =>
  menus.map(({ icon, routes, ...item }) => ({
    ...item,
    icon: icon && IconMap[icon as string],
    routes: routes && loopMenuItem(routes),
  }));

const defaultMenus = [
  {
    path: '/user',
    layout: false,
    routes: [
      {
        path: '/user',
        routes: [
          {
            name: 'login',
            path: '/user/login',
            component: './user/Login',
          },
        ],
      },
      {
        component: './404',
      },
    ],
  },
  {
    path: '/welcome',
    name: 'welcome',
    icon: 'smile',
    component: './Welcome',
  },
  {
    path: '/registry',
    name: 'registry',
    icon: 'database',
    routes: [
      {
        name: 'wms',
        path: '/registry/wms',
        component: './registry/WmsTable',
      },
      {
        path: '/registry/wms/:id/security',
        component: './registry/WmsSecuritySettings',
        hideInMenu: true,
        routes: [{ path: 'rules' }, { path: 'rules/:ruleId/edit' }, { path: 'rules/add' }],
      },
      {
        name: 'wfs',
        path: '/registry/wfs',
        component: './registry/WfsTable',
      },
      {
        name: 'csw',
        path: '/registry/csw',
        component: './registry/CswTable',
      },
      {
        name: 'datasets',
        path: '/registry/datasets',
        component: './registry/DatasetTable',
      },
      {
        name: 'layers',
        path: '/registry/layers',
        component: './registry/LayerTable',
      },
      {
        name: 'featuretypes',
        path: '/registry/featuretypes',
        component: './registry/FeatureTypeTable',
      },
      {
        name: 'maps',
        path: '/registry/maps',
        component: './registry/MapTable',
      },
      {
        path: '/registry/maps/add',
        component: './registry/MapContextEditor',
      },
      {
        path: '/registry/maps/:id/edit',
        component: './registry/MapContextEditor',
      },
    ],
  },
  {
    path: '/',
    redirect: '/welcome',
  },
  {
    component: './404',
  },
];

export default defaultMenus;
