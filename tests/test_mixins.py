"""
Test mixins for trampoline.
"""
from django.test.utils import override_settings

from elasticsearch_dsl import Index

from trampoline.mixins import ESIndexableMixin

from tests.base import BaseTestCase
from tests.models import Token


class TestMixins(BaseTestCase):

    def setUp(self):
        super(TestMixins, self).setUp()
        self.doc_type = Token.get_es_doc_type()
        self.index = Index(self.doc_type._doc_type.index)
        self.index.doc_type(self.doc_type)
        self.index.create()
        self.refresh()

    def tearDown(self):
        super(TestMixins, self).tearDown()
        self.index.delete()

    def test_is_indexable(self):
        self.assertTrue(ESIndexableMixin().is_indexable())

    def test_get_indexable_queryset(self):
        self.assertQuerysetEqual(
            Token.get_indexable_queryset(),
            Token.objects.all()
        )

    def test_get_es_doc(self):
        token = Token(name='token')
        self.assertIsNone(token.get_es_doc())
        token.save()
        self.assertIsNotNone(token.get_es_doc())

    def test_es_index(self):
        # Asynchronous call.
        token = Token.objects.create(name='not_indexable')
        self.assertDocDoesntExist(token)
        token.es_index()
        self.assertDocExists(token)

        # Synchronous call.
        token = Token.objects.create(name='not_indexable')
        self.assertDocDoesntExist(token)
        token.es_index(async=False)
        self.assertDocExists(token)

    def test_es_delete(self):
        # Asynchronous call.
        token = Token.objects.create(name='token')
        self.assertDocExists(token)
        token.es_delete()
        self.assertDocDoesntExist(Token, token.pk)

        # Synchronous call.
        token = Token.objects.create(name='token')
        self.assertDocExists(token)
        token.es_delete(async=False)
        self.assertDocDoesntExist(Token, token.pk)

    def test_save(self):
        token = Token(name='token')

        with override_settings(TRAMPOLINE={'OPTIONS': {'disabled': True}}):
            token.save()
            self.assertDocDoesntExist(token)

        token.save()
        doc = token.get_es_doc()
        self.assertEqual(doc.name, 'token')
        self.assertEqual(doc._id, str(token.pk))

        # Update model and synchronise doc.
        token.name = 'kento'
        token.save()
        doc = token.get_es_doc()
        self.assertEqual(doc.name, 'kento')

        # Instance is not indexable.
        token = Token.objects.create(name='not_indexable')
        self.assertDocDoesntExist(token)

    def test_delete(self):
        token = Token.objects.create(name='token')
        token_id = token.pk
        self.assertDocExists(token)

        with override_settings(TRAMPOLINE={'OPTIONS': {'disabled': True}}):
            token.delete()
            self.assertDocExists(Token, token_id)

        token.save()
        token_id = token.pk
        token.delete()
        self.assertDocDoesntExist(Token, token_id)
