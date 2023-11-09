Feature: BackgroundProcess List Endpoint
    As an API client,
    I want to get backgroundprocesses,
    so that I can show progress information of a process.

    Background: Setup base url
        Given I use the endpoint http://localhost:8000/api/notify/background-processes


    Scenario: Can get list of current background processes
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "4"
        Then I expect that response json has an attribute "data.[1].attributes.runningThreadsCount" with value "0"
        Then I expect that response json has an attribute "data.[1].attributes.successedThreadsCount" with value "1"
        Then I expect that response json has an attribute "data.[1].attributes.failedThreadsCount" with value "1"
        Then I expect that response json has an attribute "data.[1].attributes.pendingThreadsCount" with value "0"
        Then I expect that response json has an attribute "data.[1].attributes.progress" with value "100.0"
        Then I expect that response json has an attribute "data.[2].attributes.runningThreadsCount" with value "1"
        Then I expect that response json has an attribute "data.[2].attributes.successedThreadsCount" with value "3"
        Then I expect that response json has an attribute "data.[2].attributes.failedThreadsCount" with value "0"
        Then I expect that response json has an attribute "data.[2].attributes.pendingThreadsCount" with value "0"
        Then I expect that response json has an attribute "data.[2].attributes.progress" with value "81.25"
        Then I expect that response json has an attribute "data.[3].attributes.runningThreadsCount" with value "2"
        Then I expect that response json has an attribute "data.[3].attributes.successedThreadsCount" with value "3"
        Then I expect that response json has an attribute "data.[3].attributes.failedThreadsCount" with value "0"
        Then I expect that response json has an attribute "data.[3].attributes.pendingThreadsCount" with value "1"
        Then I expect that response json has an attribute "data.[3].attributes.progress" with value "50.0"

    Scenario: Can filter by process_type
        Given I set a queryparam "filter[processType.icontains]" with value "process 2"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by description
        Given I set a queryparam "filter[description.icontains]" with value "description 2"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"

    Scenario: Can filter by phase
        Given I set a queryparam "filter[phase.icontains]" with value "failed"
        When I send the request with GET method
        Then I expect the response status is 200
        Then I expect that response json has an attribute "meta.pagination.count" with value "1"
