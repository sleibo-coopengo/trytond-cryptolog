# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
import os

import unittest

import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
import xmlrpc.client

from trytond.modules.currency.tests import create_currency

from trytond.pool import Pool


class ElectronicSignatureTestCase(ModuleTestCase):
    'Module Test Case'
    module = 'cryptolog'

    def _init_all(self):
        self.pool = Pool()
        self.subscriber = self._init_subscriber()
        self.company = self._init_company()
        self.signature_credential = self._init_signature_credential()
        self.signature_configuration = self._init_signature_configuration()
        self.signature = self._init_signature()
        self.id_docs = self._init_id_docs()
        self._update_company()
        self.id_type = 'id_card_fr'

    def _init_subscriber(self):
        Party = self.pool.get('party.party')
        subscriber = Party()
        subscriber.name = 'Berthier'
        subscriber.first_name = 'Corinne'
        subscriber.is_person = True
        subscriber.gender = 'female'
        subscriber.birth_date = datetime.datetime(1965, 12, 6, 8, 5)
        subscriber.save()

        ContactMechanism = self.pool.get('party.contact_mechanism')
        ContactMechanism.create([{
                                'party': subscriber.id,
                                'type': 'email',
                                'value': 'corinne.bertier@coopengo.com',
                                }])

        return subscriber

    def _init_company(self):
        Company = self.pool.get('company.company')
        company = Company()
        company.party = self.subscriber
        company.currency = create_currency('EUR')
        company.signature_configurations = []
        company.signature_credentials = []
        company.save()
        return company

    def _init_signature_credential(self):
        SignatureCredential = self.pool.get('document.signature.credential')
        signature_credential = SignatureCredential()
        signature_credential.company = self.company
        signature_credential.provider = 'cryptolog'
        signature_credential.provider_url = 'https://sign.test.cryptolog.com/ra/rpc/'
        signature_credential.username = 'test.coopengo@universign.com'
        signature_credential.password = 'EGC0S50W'
        signature_credential.save()
        return signature_credential

    def _init_signature_configuration(self):
        SignatureConfiguration = self.pool.get('document.signature.configuration')
        signature_configuration = SignatureConfiguration()
        signature_configuration.company = self.company
        signature_configuration.level = 'certified'
        signature_configuration.handwritten_signature = 'never'
        signature_configuration.send_email_to_sign = True
        signature_configuration.send_signed_docs_by_email = True
        signature_configuration.save()
        return signature_configuration

    def _init_signature(self):
        Signature = self.pool.get('document.signature')
        signature = Signature()
        signature.provider_credential = self.signature_credential
        signature.save()
        return signature

    def _update_company(self):
        self.company.signature_configurations = [self.signature_configuration.id]
        self.company.signature_credentials = [self.signature_credential.id]
        self.company.save()

    def _init_id_docs(self, id_docs_path=None):
        id_docs = []
        if not id_docs_path:
            id_docs_path = ('CNI-FR-TEST-RECTO.jpg',
                'CNI-FR-TEST-VERSO.jpg')
        file_path = os.path.join(os.path.dirname(__file__), 'id_documents/')
        for id_doc_path in id_docs_path:
            with open(os.path.join(file_path, id_doc_path), 'rb') as id_doc:
                id_docs.append(xmlrpc.client.Binary(id_doc.read()))
        return id_docs

    @with_transaction()
    def test001_cni_OK(self):
        self._init_all()
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertEqual(res, 1)

    @with_transaction()
    def test002_cni_KO_bad_firstname(self):
        self._init_all()
        self.subscriber.first_name = 'Bad firstname'
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertEqual(res, 2)

    @with_transaction()
    def test003_cni_KO_bad_birthdate(self):
        self._init_all()
        self.subscriber.birth_date = datetime.datetime(1966, 12, 6, 8, 5)
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertEqual(res, 2)

    @with_transaction()
    def test004_cni_KO_bad_id_docs(self):
        self._init_all()
        self.id_docs = self._init_id_docs(id_docs_path=('CNI2-RECTO.jpg',
            'CNI-FR-TEST-RECTO.jpg'))
        with Transaction().set_context(company=self.company):
            res = self.signature.validate_electronic_identity(
                self.signature.provider_credential, self.subscriber,
                self.id_docs, self.id_type)
            self.assertEqual(res, 2)

    """@with_transaction()
    def test005_match_account(self):
        self._init_all()
        with Transaction().set_context(company=self.company):
            res = self.signature.check_match_account(self.subscriber)
            self.assertEqual(res, 2)"""


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ElectronicSignatureTestCase))
    return suite
