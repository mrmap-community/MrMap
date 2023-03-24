Feature: Featuretype List Endpoint
    As an API client,
    I want to search for featuretype,
    so that I can find relevant map content.

    Background: Setup baseurl, content-type and payload
        Given I use the endpoint http://localhost:8000/api/v1/registry/featuretypes/

    Scenario: Can retrieve list as anonymous user
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "5"
        Then I expect that "8" queries where made

    Scenario: Can search by title
        Given I set a queryparam "filter[search]" with value "wfs1-node1"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can search by abstract
        Given I set a queryparam "filter[search]" with value "wfs1-node1"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can search by keywords
        Given I set a queryparam "filter[search]" with value "meteorology"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by title
        Given I set a queryparam "filter[title.icontains]" with value "wfs1-node1"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by abstract
        Given I set a queryparam "filter[abstract.icontains]" with value "wfs1-node1"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by bbox
        Given I set a queryparam "filter[bboxLatLon.contains]" with value "{'type': 'Polygon', 'coordinates': [[[7.062835693359375, 50.043911679834615], [7.568206787109375, 50.043911679834615], [7.568206787109375, 50.39451208023374], [7.062835693359375, 50.39451208023374], [7.062835693359375, 50.043911679834615]]]}"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "4"

    Scenario: Can include service
        Given I set a queryparam "include" with value "service"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "WebFeatureService"

    Scenario: Can include keywords
        Given I set a queryparam "include" with value "keywords"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[0].type" with value "Keyword"

    Scenario: Can include service.operationUrls
        Given I set a queryparam "include" with value "service.operationUrls"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "included.[3].type" with value "WebFeatureServiceOperationUrl"

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