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

    @with_transaction()
    def test_universign_with_id_documents(self):
        'Test Universign'
        pool = Pool()

        Party = pool.get('party.party')
        subscriber = Party()
        subscriber.name = 'Bertier'
        subscriber.first_name = 'Corinne'
        #subscriber.first_name = 'Xun'
        subscriber.is_person = True
        subscriber.gender = 'female'
        subscriber.birth_date = datetime.datetime(1965, 12, 6, 8, 5)
        subscriber.phone = '0612345678'
        subscriber.mobile = '0612345678'
        subscriber.all_addresses = ['home, sweet home']
        subscriber.save()

        ContactMechanism = pool.get('party.contact_mechanism')
        ContactMechanism.create([{
                                'party': subscriber.id,
                                'type': 'email',
                                'value': 'corinne.bertier@coopengo.com',
                                }])

        Company = pool.get('company.company')
        company = Company()
        company.party = subscriber
        company.currency = create_currency('EUR')
        company.signature_configurations = []
        company.signature_credentials = []
        company.save()

        SignatureCredential = pool.get('document.signature.credential')
        signature_credential = SignatureCredential()
        signature_credential.company = company
        signature_credential.provider = 'cryptolog'
        #signature_credential.provider_url = 'https://sign.test.cryptolog.com/sign/rpc/'
        signature_credential.provider_url = 'https://sign.test.cryptolog.com/ra/rpc/'
        signature_credential.username = 'test.coopengo@universign.com'
        signature_credential.password = 'EGC0S50W'
        signature_credential.save()

        SignatureConfiguration = pool.get('document.signature.configuration')
        signature_configuration = SignatureConfiguration()
        signature_configuration.company = company
        signature_configuration.level = 'certified'
        signature_configuration.handwritten_signature = 'never'
        signature_configuration.send_email_to_sign = True
        signature_configuration.send_signed_docs_by_email = True
        signature_configuration.save()

        company.signature_configurations = [signature_configuration.id]
        company.signature_credentials = [signature_credential.id]
        company.save()

        Signature = pool.get('document.signature')
        signature = Signature()
        signature.provider_credential = signature_credential
        signature.save()

        id_type = 'id_card_fr'
        id_docs = []
        id_docs_path = ('CNI-FR-TEST-RECTO.jpg',
            'CNI-FR-TEST-VERSO.jpg')
        #id_docs_path = ('My_dog.jpg', 'Push_van_cat.jpg')

        module_file = __file__
        module_tests_folder = os.path.dirname(module_file)

        file_path = os.path.join(module_tests_folder, 'id_documents/')

        for id_doc_path in id_docs_path:
            with open(os.path.join(file_path, id_doc_path), 'rb') as id_doc:
                id_docs.append(xmlrpc.client.Binary(id_doc.read()))

        with Transaction().set_context(company=company):
            res = signature.validate_electronic_identity1(subscriber, id_docs, id_type)

        self.assertTrue(res)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ElectronicSignatureTestCase))
    return suite
