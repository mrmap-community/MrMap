
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

/**
 * Setter for the session storage
 */
function setSessionValue(key, value){
    window.sessionStorage.setItem(key, value);
}
/**
 * Getter for the session storage
 *      using the parameter 'remove', the key-value pair will be deleted afterwards
 */
function getSessionValue(key, remove){
    var item = window.sessionStorage.getItem(key);
    if(remove){
        window.sessionStorage.removeItem(key);
    }
    return item;
}

function findSessionValuesLike(substring){
    var items = window.sessionStorage;
    var retArr = [];
    for(i = 0; i < items.length; i++){
        if(items.key(i).includes(substring)){
            retArr.push(getSessionValue(items.key(i)));
        }
    }
    return retArr;
}

function findSessionKeysLike(substring){
    var items = window.sessionStorage;
    var retArr = [];
    for(i = 0; i < items.length; i++){
        if(items.key(i).includes(substring)){
            retArr.push(items.key(i));
        }
    }
    return retArr;
}

function removeSessionKeysLike(substring){
    var items = window.sessionStorage;
    for(i = 0; i < items.length; i++){
        if(items.key(i).includes(substring)){
            getSessionValue(items.key(i), true);
        }
    }
}


function toggleCollapsibleSymbol(elem){
    var src = elem.attr("src");
    var toggle = elem.attr("data-toggle");
    elem.attr("src", toggle);
    elem.attr("data-toggle", src);
}

function checkRedirect(data){
    if(data["redirect"] !== null){
        window.open(data["redirect"], "_self");
    }
}

function toggleNavigationMenu(elem){
    elem.toggleClass("open");
    elem.stop(true, true).slideToggle("medium");
}

function toggleOverlay(html){
    var overlay = $("#overlay");
    if(overlay.is(":visible")){
        overlay.html(html);
    }
    overlay.toggleClass("show");
}

function replaceButtonWithSpinner(button){
}

function changeOverlayContent(html){
    var overlay = $("#overlay");
    overlay.html(html);
}


function editEntity(id, entity){
    $.ajax({
        url: rootUrl + "/" + entity + "/edit/" + id,
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        data: {},
        type: 'get',
        dataType: 'json'
    }).done(function(data){
        var html = data["html"];
        toggleOverlay(html);
    }).always(function(data){
        checkRedirect(data);
    });
}

function updateEntity(id, entity){
    $.ajax({
        url: rootUrl + "/" + entity + "/update/register-form/" + id,
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        data: {},
        type: 'get',
        dataType: 'json'
    }).done(function(data){
        var html = data["html"];
        toggleOverlay(html);

    }).always(function(data){
        checkRedirect(data);
    });
}

function addEntity(entity){
    $.ajax({
        url: rootUrl + "/" + entity + "/new/register-form",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        data: {},
        type: 'get',
        dataType: 'json',
    }).done(function(data){
        var html = data["html"];
        toggleOverlay(html);
    }).always(function(data){
        checkRedirect(data);
    });
}


function removeEntity(id, confirmed, entity){
    $.ajax({
        url: rootUrl + "/" + entity + "/remove?id=" + id + "&confirmed=" + confirmed,
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        type: 'get',
        dataType: 'json'
    }).done(function(data){
        var html = data["html"];
        toggleOverlay(html);
    }).always(function(data){
        checkRedirect(data);
    });
}

$(document).on("click", "#eeImg", function(){
    toggleOverlay("");
    // restore rotation
    var elem = $("#ee-trggr");
    elem.css({"transform": "rotate(0deg)"});
});


$(document).ready(function(){
    // hide messages after 10 seconds automatically
    setTimeout(function(){
        var msg = $(".messages");
        if(msg.is(":visible")){
            $(".messages").click();
        }
    }, 5000);

    var eeRotation = 0;

    $("#ee-trggr").mousemove(function(event){
        var element = $(this);
        // check if ctrl key is pressed
        eeRotation += 2;
        element.css({"transform": "rotate(" + eeRotation +"deg)"});
        if(eeRotation == 360){
            var eeSound = $("#ee-audio")[0];
            var img = $("<img/>").attr("src", "/static/images/mr_map.png")
            .attr("class", "rotating-image")
            .attr("style", "object-fit: contain;")
            .attr("id", "eeImg");
            toggleOverlay(img);
            eeSound.addEventListener("ended", function(){
                // remove overlay
                if($("#overlay").hasClass("show")){
                    toggleOverlay("");
                }
            });
            eeSound.play();
            eeRotation = 0;
        }
    });

    $("#navbar-logo").mouseleave(function(){
        var elem = $(this);
        eeRotation = 0;
        elem.css({"transform": "rotate(" + eeRotation +"deg)"});
    });


    $(".navigation-menu").on("mouseover",function(){
        var list = $(this).find(".navigation-element-list");
        if(!list.hasClass("open")){
            toggleNavigationMenu(list);
        }
    });

    $(".navigation-menu").on("mouseleave",function(){
        var elem = $(this).find(".navigation-element-list");
        if(elem.hasClass("open")){
            toggleNavigationMenu(elem);
        }
    });

    $(".messages").on("click", function(){
        var elem = $(this);
        elem.slideToggle();
    });

    $(".delete-container").click(function(){
        var id = $(this).attr("data-parent");
        // call remove form, but indicate that the remove process was not confirmed yet by the user
        var entity = $(this).attr("typeof");
        removeEntity(id, false, entity);
    });

    $("#edit-button, #change-pw-button").click(function(){
        var id = $(this).attr("data-parent");
        // call remove form, but indicate that the remove process was not confirmed yet by the user
        var entity = $(this).attr("typeof");
        if(entity.includes('user')){
            id = "";
        }
        editEntity(id, entity);
    });

    $(".add-button").click(function(){
        // call remove form, but indicate that the remove process was not confirmed yet by the user
        var entity = $(this).attr("typeof");
        addEntity(entity);
    });

    $("html").click(function(){
        var langMenu = $("#current-lang");
        if(langMenu.hasClass("open")){
            langMenu.click();
        }
    });

    $("#current-lang").click(function(event){
        event.stopPropagation();
        var elem = $(this);
        elem.toggleClass("open");
        $("#lang-selector").slideToggle();
    });


    $(".lang-item").click(function(){
        var elem = $(this);
        var val = elem.attr("data-value");
        // activate selected language via ajax call
        $.ajax({
            url: "/i18n/setlang/",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
            data: {
                'language': val
            },
            type: 'post',
            dataType: 'json',
            success: function(data) {
                location.reload();
            },
            timeout: 10000,
            error: function(jqXHR, textStatus, errorThrown){
                if(textStatus === "timeout"){
                    console.log("A timeout occured.");
                }
            }
        })

    });

    $(function () {
      $('[data-toggle="tooltip"]').tooltip();
    })

});

function toggleBusyState( form ) {
  // get status message references
  const busyStateItems = form.querySelectorAll('.submit_btn_txt, .submit_btn_spinner');

  // Show busy state
  busyStateItems.forEach(function(item) {
    if ( item.classList.contains('d-none') ){
        item.classList.remove("d-none");
    } else {
        item.classList.add("d-none");
    }
  });

  // toggle disable state of all form elements to prevent further input
  Array.from(form.elements).forEach(function(field) {
    if ( field.disabled ) {
        field.disabled = false
    } else {
        field.disabled = true
    }
  });
}


function submitAsync( event, is_modal = false ) {
  const submitter = event.submitter;

  // Store reference to form and modal to make later code easier to read
  const form = event.target;
  const exchangeContainer = form.querySelector("div").closest(".modal-fetched-content")

  var formData = new FormData(form);
  if (submitter.name != ""){
    formData.append(submitter.name, "");
  }
  // Post data using the Fetch API
  fetch(form.action, {
      method: form.method,
      body: formData,
      redirect: 'manual'
    }).then(response => {
        if(response.ok) {
            return response;
        } else {
            throw Error(`Request rejected with status ${response.status}`);
        }
    }).then(response => {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json().then(data => {
              // process your JSON data further
              if ( data.hasOwnProperty('data') ){
                if ( is_modal ) {
                    const modal = form.querySelector("div").closest(".modal")
                    $('#' + modal.id).modal('hide');
                }
                // todo: this should be fetched by a websocket
                document.querySelector("#body-content").insertAdjacentHTML('beforebegin', data.alert);
              } else {
                throw Error(`Response has no data attribute`);
              }
            });
        } else {
            return response.text().then(text => {
                // There is still a html content to render
                exchangeContainer.innerHTML = text;
                $('[data-toggle="tooltip"]').tooltip();
            });
        }
    }).catch(err => {
        if ( is_modal ) {
            const modal = form.querySelector("div").closest(".modal")
            $('#' + modal.id).modal('hide');
            exchangeContainer.innerHTML = "";
        }
        toggleBusyState( form );
        console.log(err);
    });

  toggleBusyState( form );

  // Prevent the default form submit
  event.preventDefault();
}

// adds auto submitting functionality to submit if a auto submit tagged item becomes changes
function isFormUpdateEventHandler( event ){
    const form = event.target.closest("form");
    const isFormUpdate = document.createElement("input");
    isFormUpdate.type = "hidden";
    isFormUpdate.name = "is_form_update";
    isFormUpdate.value = 'True'
    form.appendChild(isFormUpdate);
    form.querySelectorAll('[type=submit]')[0].click();
}

// adds formset delete form functionality to the frontend

function markFormAsDelete( submitter ){

    const formDeleteCheckbox = document.querySelector(submitter.dataset.target);
    const parentContainer = document.querySelector(submitter.dataset.parent);
    formDeleteCheckbox.value = "on";
    parentContainer.classList.add("d-none");

}
