Feature: MapContext Rendering Layer
    As a User, 
    I want to configure the rendering behaviour of a layer, 
    So that the rendering configuration is part of the mapcontext.

  Background: Open mapcontext add page
    Given the base url is "https://localhost:8000"
    Given I open the site "/registry/mapcontexts/add"

  Scenario: Successful configure mapcontext layer tree
    When I set "mapcontext " to the inputfield "//*[@id='id_title']"
    When I set "short example of a mapcontext" to the inputfield "//*[@id='id_abstract']"
    When I click on the button "//button[@id='j1_1']//*[contains(@title, 'Add Folder')]"


    When I click on the button "//button[@type='submit']"
    Then I expect that element "//*[text()[contains(.,'Successfully signed in.')]]" does exist

