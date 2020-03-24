"""
Author: Michel Peltriaux
Organization: Spatial data infrastructure Rhineland-Palatinate, Germany
Contact: michel.peltriaux@vermkv.rlp.de
Created on: 08.05.19

"""
import json

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect

from MapSkinner.messages import SESSION_TIMEOUT, NO_PERMISSION, LOGOUT_FORCED, SERVICE_NOT_FOUND
from MapSkinner.responses import BackendAjaxResponse
from MapSkinner.settings import ROOT_URL
from service.models import Metadata, ProxyLog
from structure.models import Permission
from users.helper import user_helper


def check_session(function):
    """ Checks whether the user's session is valid or not

    Args:
        function: The decorated function
    Returns:
         The function
    """
    def wrap(request, *args, **kwargs):
        if user_helper.is_session_expired(request):

            messages.add_message(request, messages.INFO, SESSION_TIMEOUT)

            if request.environ.get("HTTP_X_REQUESTED_WITH", None) is not None:
                # this is an ajax call -> redirect user to login page if the session isn't valid anymore
                last_page = request.META.get("HTTP_REFERER", "").replace(request._current_scheme_host, "")
                request.session["next"] = last_page
                return BackendAjaxResponse(html="", redirect=ROOT_URL).get_response()
            else:
                # save last path so the user can be redirected after a successful login
                request.session["next"] = request.path
                return redirect("login")

        user = user_helper.get_user(user_id=request.session.get("user_id"))

        if user is None:
            if request.session.get("user_id", None) is not None:
                del request.session["user_id"]
            messages.add_message(request, messages.ERROR, LOGOUT_FORCED)

            return redirect("login")
        return function(request=request, user=user, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def check_permission(permission_needed: Permission):
    """ Checks whether the user has the required permission for the requested action

    Args:
        permission_needed (Permission): The permission object that defines which permissions are needed
    Returns:
         The function
    """
    def method_wrap(function):
        def wrap(request, *args, **kwargs):
            user = user_helper.get_user(request)
            user_permissions = user.get_permissions()
            perm_needed = permission_needed.get_permission_list()
            for perm in perm_needed:
                if perm not in user_permissions:
                    messages.add_message(request, messages.ERROR, NO_PERMISSION)
                    return redirect(request.META.get("HTTP_REFERER"))
            return function(request=request, *args, **kwargs)

        wrap.__doc__ = function.__doc__
        wrap.__name__ = function.__name__
        return wrap
    return method_wrap


def log_proxy(function):
    """ Checks whether the metadata has a logging proxy configuration and adds another log record

    Args:
        md (Metadata): The requested metadata
    Returns:
        The function
    """
    def wrap(request, *args, **kwargs):
        user = user_helper.get_user(request=request)
        try:
            md = Metadata.objects.get(id=kwargs["id"])
        except ObjectDoesNotExist:
            return HttpResponse(status=404, content=SERVICE_NOT_FOUND)
        user_id = None
        if user is not None:
            user_id = user

        uri = request.path
        post_body = {}
        if request.method.lower() == "post":
            post_body = request.POST.dict()
        elif request.method.lower() == "get":
            uri += "?" + request.environ.get("QUERY_STRING")
        post_body = json.dumps(post_body)

        proxy_log = None
        if md.use_proxy_uri and md.log_proxy_access:
            proxy_log = ProxyLog(
                metadata=md,
                uri=uri,
                post_body=post_body,
                user=user_id
            )
            proxy_log.save()
        return function(request=request, proxy_log=proxy_log, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap