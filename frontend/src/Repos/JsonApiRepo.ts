import Cookies from 'js-cookie';
import OpenAPIClientAxios, { AxiosResponse, OpenAPIClient } from 'openapi-client-axios';

export const JsonApiMimeType = 'application/vnd.api+json';

export type JsonApiResponse = AxiosResponse<JsonApiDocument | null>

export interface JsonApiDocument {
    data?: JsonApiPrimaryData[] | JsonApiPrimaryData;
    errors?: JsonApiErrorObject;
    meta?: any;
    links?: any;
}

export interface JsonApiErrorObject {
  id: string;
  links: any; // TODO: add JsonApiLinkObject
  status: string;
  code: string;
  title: string;
  detail: string;
  source: string;
}

export interface JsonApiPrimaryData {
    type: string;
    id: string;
    links: any; // TODO: add JsonApiLinkObject
    attributes: any;
    relationships: any;
}

export interface QueryParams {
    page: number;
    pageSize: number;
    ordering?: string;
    filters?: any;
}

export class JsonApiRepo {
    private static apiInstance: OpenAPIClientAxios;

    private static clientInstance: OpenAPIClient;

    protected readonly resourcePath: string;

    readonly displayName: string;

    constructor (resourcePath: string, displayName: string) {
      this.resourcePath = resourcePath;
      this.displayName = displayName;
    }

    static async getClientInstance (): Promise<OpenAPIClient> {
      if (!this.clientInstance) {
        this.clientInstance = await (await this.getApiInstance()).getClient();
      }
      return this.clientInstance;
    }

    static async getApiInstance (): Promise<OpenAPIClientAxios> {
      if (!this.apiInstance) {
        if (process.env.REACT_APP_REST_API_SCHEMA_URL === undefined) {
          throw new Error('Environment variable REACT_APP_REST_API_SCHEMA_URL is undefined.');
        }
        if (process.env.REACT_APP_REST_API_BASE_URL === undefined) {
          throw new Error('Environment variable REACT_APP_REST_API_BASE_URL is undefined.');
        }
        this.apiInstance = new OpenAPIClientAxios({
          definition: process.env.REACT_APP_REST_API_SCHEMA_URL,
          axiosConfigDefaults: {
            baseURL: process.env.REACT_APP_REST_API_BASE_URL
          }
        });
        try {
          await this.apiInstance.init();
        } catch (err) {
          console.error(err);
        }
      }
      return this.apiInstance;
    }

    async getResourceSchema (): Promise<any> {
      const client = await JsonApiRepo.getClientInstance();
      const op = client.api.getOperation('List' + this.resourcePath);
      if (!op) {
        return [];
      }
      const response: any = op.responses[200];
      if (!response) {
        return [];
      }
      const mimeType = response.content['application/vnd.api+json'];
      if (!mimeType) {
        return [];
      }
      return mimeType.schema;
    }

    async getQueryParams (): Promise<any> {
      const client = await JsonApiRepo.getClientInstance();
      const op = client.api.getOperation('List' + this.resourcePath);
      if (!op) {
        return [];
      }
      const params:any = {};
      op.parameters?.forEach((element: any) => {
        params[element.name] = element;
      });
      return params;
    }

    async findAll (queryParams?: QueryParams): Promise<JsonApiResponse> {
      const client = await JsonApiRepo.getClientInstance();
      // TODO why does Parameters<UnknownParamsObject> not work?
      let jsonApiParams: any;
      if (queryParams) {
        jsonApiParams = {
          'page[number]': queryParams.page,
          'page[size]': queryParams.pageSize,
          ...queryParams.filters
        };
        if (queryParams.ordering) {
          jsonApiParams.sort = queryParams.ordering;
        }
      }
      return await client['List' + this.resourcePath](jsonApiParams);
    }

    async get (id: string): Promise<JsonApiResponse> {
      const client = await JsonApiRepo.getClientInstance();
      return await client['retrieve' + this.resourcePath + '{id}/'](id, {}, {
        headers: { 'Content-Type': JsonApiMimeType }
      });
    }

    async delete (id: string): Promise<JsonApiResponse> {
      const client = await JsonApiRepo.getClientInstance();
      return await client['destroy' + this.resourcePath + '{id}/'](id, {}, {
        headers: { 'Content-Type': JsonApiMimeType, 'X-CSRFToken': Cookies.get('csrftoken') }
      });
    }

    // eslint-disable-next-line
    async add (type: string, attributes: any, relationships?: any): Promise<JsonApiResponse> {
      const client = await JsonApiRepo.getClientInstance();

      // TODO: make relationships optional
      return await client['create' + this.resourcePath](undefined, {
        data: {
          type: type,
          attributes: {
            ...attributes
          },
          relationships: {
            ...relationships
          }
        }
      }, {
        headers: { 'Content-Type': JsonApiMimeType, 'X-CSRFToken': Cookies.get('csrftoken') }
      });
    }

    async partialUpdate (
      id: string,
      type: string,
      attributes: Record<string, unknown>,
      relationships?: Record<string, unknown>
    ): Promise<JsonApiResponse> {
      const client = await JsonApiRepo.getClientInstance();
      // TODO: make relationships optional
      return await client['partial_update' + this.resourcePath + '{id}/'](id, {
        data: {
          type: type,
          id: id,
          attributes: {
            ...attributes
          },
          relationships: {
            ...relationships
          }
        }
      }, {
        headers: { 'Content-Type': JsonApiMimeType, 'X-CSRFToken': Cookies.get('csrftoken') }
      });
    }
}

export default JsonApiRepo;
