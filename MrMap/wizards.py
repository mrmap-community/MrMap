from collections import OrderedDict

from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse, resolve
from django.utils.html import format_html
from formtools.wizard.views import SessionWizardView
from MrMap.utils import get_theme
from users.helper import user_helper
from django.utils.translation import gettext_lazy as _


class MrMapWizard(SessionWizardView):
    template_name = "sceletons/modal-wizard-form.html"
    messages = []
    ignore_uncomitted_forms = False

    def __init__(self, ignore_uncomitted_forms=False, *args, **kwargs):
        super(MrMapWizard, self).__init__(*args, **kwargs)
        self.ignore_uncomitted_forms = ignore_uncomitted_forms

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({'id_modal': self.kwargs['id_modal'],
                        'modal_title': self.kwargs['title'],
                        'THEME': get_theme(user_helper.get_user(self.request)),
                        'action_url': reverse('editor:dataset-metadata-wizard-instance',
                                              args=(self.kwargs['current_view'], self.kwargs.get('instance_id')))
                        if 'instance_id' in self.kwargs else reverse('editor:dataset-metadata-wizard-new',
                                                                     args=(self.kwargs['current_view'],)),
                        'show_modal': True,
                        'fade_modal': True,
                        'current_view': self.kwargs['current_view'],
                        })

        if bool(self.storage.data['step_data']):
            # this wizard is not new, prevent from bootstrap modal fading
            context.update({'fade_modal': False, })

        return context

    def render(self, form=None, **kwargs):
        form = form or self.get_form()
        context = self.get_context_data(form=form, **kwargs)
        context['wizard'].update({'messages': self.messages})
        context['wizard'].update({'ignore_uncomitted_forms': self.ignore_uncomitted_forms})

        rendered_wizard = render_to_string(request=self.request,
                                           template_name=self.template_name,
                                           context=context)
        view_function = resolve(reverse(f"{self.kwargs['current_view']}", ))
        rendered_view = view_function.func(request=self.request, rendered_wizard=rendered_wizard)
        return rendered_view

    def render_goto_step(self, goto_step, **kwargs):
        # 1. save current form, we doesn't matter for validation for now.
        # If the wizard is done, he will perform validation for each.
        current_form = self.get_form(data=self.request.POST, files=self.request.FILES)
        self.storage.set_step_data(self.steps.current,
                                   self.process_step(current_form))
        self.storage.set_step_files(self.steps.current, self.process_step_files(current_form))

        if self.storage.current_step == goto_step and self.request.POST[f"{current_form.prefix}-is_form_update"] == 'True':
            return self.render(current_form)

        # ToDo: call super().render_goto_step instead to write duplicate code
        self.storage.current_step = goto_step
        next_form = self.get_form(
            data=self.storage.get_step_data(self.steps.current),
            files=self.storage.get_step_files(self.steps.current))

        return self.render(next_form)

    def process_step(self, form):
        self.messages = []
        # ToDo: check if save button was hitted
        if self.ignore_uncomitted_forms and 'wizard_save' in self.request.POST:
            uncomitted_forms = []
            for form_key in self.get_form_list():
                form_obj = self.get_form(
                    step=form_key,
                    data=self.storage.get_step_data(form_key),
                    files=self.storage.get_step_files(form_key)
                )
                # x.1. self.get_form_list(): get the unbounded forms
                if not form_obj.is_bound and form_key != self.steps.current:
                    uncomitted_forms.append(form_key)
            # x.4. if no unbounded form has required fields then remove them from the form_list
            for uncomitted_form in uncomitted_forms:
                self.form_list.pop(uncomitted_form)
            # set current commited form as last form
            self.form_list.move_to_end(self.steps.current)
        return self.get_form_step_data(form)

    def get_form_kwargs(self, step):
        return {'instance_id': self.kwargs['instance_id'] if 'instance_id' in self.kwargs else None,
                'request': self.request, }
