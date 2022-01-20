import { Key } from "antd/lib/table/interface";
import LayerGroup from "ol/layer/Group";
import { ReactNode } from "react";
import { JsonApiResponse } from "../../Repos/JsonApiRepo";
import { TreeNodeType } from "../Shared/FormFields/TreeFormField/TreeFormFieldTypes";

type OlWMSServerType = 'ESRI' | 'GEOSERVER' | 'MAPSERVER' | 'QGIS';

export interface CreateLayerOpts {
  url: string;
  version: '1.1.0' | '1.1.1' | '1.3.0';
  format: 'image/jpeg' | 'image/png';
  layers: string;
  visible: boolean;
  serverType: OlWMSServerType;
  layerId?: string | number;
  legendUrl: string;
  title: string;
  description?: string;
  properties: Record<string, string>;
  extent?: any[]
}

export interface LayerTreeProps {
  // map: OlMap
  layerGroup?: LayerGroup;
  asyncTree?: boolean;
  addLayerDispatchAction?:(
    nodeAttributes: any,
    newNodeParent?: string | number | null | undefined) =>
    Promise<JsonApiResponse> | void;
  removeLayerDispatchAction?: (nodeToRemove: TreeNodeType) => Promise<JsonApiResponse> | void;
  editLayerDispatchAction?: (nodeId:number|string, nodeAttributesToUpdate: any) => Promise<JsonApiResponse> | void;
  dragLayerDispatchAction?: (nodeBeingDraggedInfo: any) => Promise<JsonApiResponse> | void;
  selectLayerDispatchAction?: (selectedKeys: Key[], info: any) => void;
  layerAttributeForm?: ReactNode;
}
