Feature: WebMapService List Endpoint
    As an API client,
    I want to search for web map services,
    so that I can find relevant map content.

    Background: Setup baseurl, content-type and payload
        Given I use the endpoint http://localhost:8000/api/registry/wms

    Scenario: Can retrieve list as anonymous user
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "2"
        Then I expect that "13" queries where made

    Scenario: Can search by title
        Given I set a queryparam "filter[search]" with value "WMS1"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can search by abstract
        Given I set a queryparam "filter[search]" with value "wms1 abstract"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can search by keywords
        Given I set a queryparam "filter[search]" with value "meteorology"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by title
        Given I set a queryparam "filter[title.icontains]" with value "WMS1"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by abstract
        Given I set a queryparam "filter[abstract.icontains]" with value "wms1 abstract"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by bbox
        Given I set a queryparam "filter[bboxLatLon.contains]" with value "{'type': 'Polygon', 'coordinates': [[[7.062835693359375, 50.043911679834615], [7.568206787109375, 50.043911679834615], [7.568206787109375, 50.39451208023374], [7.062835693359375, 50.39451208023374], [7.062835693359375, 50.043911679834615]]]}"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    # Scenario: Can include layers
    #     Given I set a queryparam "include" with value "layers"
    #     When I send the request with GET method
    #     Then I expect the response status is 200
    #     Then I expect that response json has an attribute "included.[0].type" with value "Layer"
    #     Then I expect that "14" queries where made

    Scenario: Can include keywords
        Given I set a queryparam "include" with value "keywords"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "Keyword"

    Scenario: Can include operationUrls
        Given I set a queryparam "include" with value "operationUrls"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "WebMapServiceOperationUrl"

    Scenario: Can include serviceContact
        Given I set a queryparam "include" with value "serviceContact"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "MetadataContact"

    Scenario: Can include metadataContact
        Given I set a queryparam "include" with value "metadataContact"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "MetadataContact"

    Scenario: Can include createdBy
        Given I set a queryparam "include" with value "createdBy"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "User"

    Scenario: Can include lastModifiedBy
        Given I set a queryparam "include" with value "lastModifiedBy"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "User"