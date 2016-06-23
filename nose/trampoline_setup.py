"""
Nose plugin to setup trampoline.
"""
import os

from django.apps import apps
from django.core.management import call_command

from nose.plugins import Plugin


class TrampolineSetup(Plugin):
    name = 'trampoline-setup'

    def options(self, parser, env=os.environ):
        super(TrampolineSetup, self).options(parser, env=env)

    def configure(self, options, conf):
        super(TrampolineSetup, self).configure(options, conf)

    def prefix_index_name(self, index_name):
        return u"{}{}".format(
            self.trampoline_config.test_prefix,
            index_name
        )

    def create_indices(self):
        for index_name in self.trampoline_config.indices:
            target_name = self.prefix_index_name(index_name)
            call_command(
                'es_create_index',
                index_name=index_name,
                target_name=target_name,
                verbosity=0
            )

    def patch_doc_types(self, index_name):
        for model in self.trampoline_config.get_index_models(index_name):
            doc_type_cls = model.get_es_doc_type()
            doc_type_cls._doc_type.index = (
                self.prefix_index_name(doc_type_cls._doc_type.index)
            )

    def delete_indices(self):
        for index_name in self.trampoline_config.indices:
            index_name = self.prefix_index_name(index_name)
            call_command(
                'es_delete_index',
                index_name=index_name,
                no_verification=True,
                verbosity=0
            )

    def begin(self):
        self.trampoline_config = apps.get_app_config('trampoline')
        if not self.trampoline_config.is_disabled:
            for index_name in self.trampoline_config.indices:
                self.patch_doc_types(index_name)

    def beforeTest(self, test):
        if not self.trampoline_config.is_disabled:
            self.create_indices()

    def afterTest(self, test):
        if not self.trampoline_config.is_disabled:
            self.delete_indices()
