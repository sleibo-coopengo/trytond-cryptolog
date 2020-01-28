# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
import os

import unittest

import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import ModuleTestCase, with_transaction, DB_NAME
import xmlrpc.client

from trytond.modules.currency.tests import create_currency

from trytond.pool import Pool


class ElectronicSignatureTestCase(ModuleTestCase):
    'Module Test Case'
    module = 'cryptolog'

    def custom_setup(self):
        self.pool = Pool()
        self._init_subscriber()
        self._init_company()
        self._init_signature_credential()
        self._init_signature_configuration()
        self._init_signature()
        self._init_id_docs()
        self._update_company()

    def _init_subscriber(self):
        Party = self.pool.get('party.party')
        self.subscriber = Party()
        self.subscriber.name = 'Berthier'
        self.subscriber.first_name = 'Corinne'
        self.subscriber.is_person = True
        self.subscriber.gender = 'female'
        self.subscriber.birth_date = datetime.datetime(1965, 12, 6, 8, 5)
        self.subscriber.save()

        ContactMechanism = self.pool.get('party.contact_mechanism')
        ContactMechanism.create([{
                                'party': self.subscriber.id,
                                'type': 'email',
                                'value': 'corinne.bertier@coopengo.com',
                                }])

    def _init_company(self):
        Company = self.pool.get('company.company')
        self.company = Company()
        self.company.party = self.subscriber
        self.company.currency = create_currency('EUR')
        self.company.signature_configurations = []
        self.company.signature_credentials = []
        self.company.save()

    def _init_signature_credential(self):
        SignatureCredential = self.pool.get('document.signature.credential')
        self.signature_credential = SignatureCredential()
        self.signature_credential.company = self.company
        self.signature_credential.provider = 'cryptolog'
        self.signature_credential.provider_url = \
            'https://sign.test.cryptolog.com/ra/rpc/'
        self.signature_credential.username = 'test.coopengo@universign.com'
        self.signature_credential.password = 'EGC0S50W'
        self.signature_credential.save()

    def _init_signature_configuration(self):
        SignatureConfiguration = self.pool.get(
            'document.signature.configuration')
        self.signature_configuration = SignatureConfiguration()
        self.signature_configuration.company = self.company
        self.signature_configuration.level = 'certified'
        self.signature_configuration.handwritten_signature = 'never'
        self.signature_configuration.send_email_to_sign = True
        self.signature_configuration.send_signed_docs_by_email = True
        self.signature_configuration.save()

    def _init_signature(self):
        Signature = self.pool.get('document.signature')
        self.signature = Signature()
        self.signature.provider_credential = self.signature_credential
        self.signature.save()

    def _update_company(self):
        self.company.signature_configurations = [
            self.signature_configuration.id]
        self.company.signature_credentials = [self.signature_credential.id]
        self.company.save()

    def _init_id_docs(self, id_docs_path=None):
        self.id_docs = []
        if not id_docs_path:
            id_docs_path = ('CNI-FR-TEST-RECTO.jpg', 'CNI-FR-TEST-VERSO.jpg')
        self.id_type = 'id_card_fr'
        file_path = os.path.join(os.path.dirname(__file__), 'id_documents/')
        for id_doc_path in id_docs_path:
            with open(os.path.join(file_path, id_doc_path), 'rb') as id_doc:
                self.id_docs.append(xmlrpc.client.Binary(id_doc.read()))

    @with_transaction()
    def test001_cni_OK(self):
        self.custom_setup()
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertTrue(res)

    @with_transaction()
    def test002_cni_KO_bad_firstname(self):
        self.custom_setup()
        self.subscriber.first_name = 'Bad firstname'
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertFalse(res)

    @with_transaction()
    def test003_cni_KO_bad_birthdate(self):
        self.custom_setup()
        self.subscriber.birth_date = datetime.datetime(1966, 12, 6, 8, 5)
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertFalse(res)

    @with_transaction()
    def test004_cni_KO_bad_id_docs(self):
        self.custom_setup()
        self._init_id_docs(id_docs_path=('CNI2-RECTO.jpg',
            'CNI-FR-TEST-RECTO.jpg'))
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertFalse(res)

    """@with_transaction()
    def test005_match_account(self):
        self.custom_setup()
        with Transaction().set_context(company=self.company):
            res = self.signature.check_match_account(self.subscriber)
            self.assertEqual(res, 2)"""


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            ElectronicSignatureTestCase))
    return suite
