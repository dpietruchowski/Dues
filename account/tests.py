from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Account, Funds, Beneficiary
import pdb

from collections import defaultdict

def get_username(number):
    return 'TestUser' + str(number)


def get_user(number):
    return User.objects.get(username=get_username(number))


def get_account(number):
    return Account.objects.get(user=get_user(number))


class NewFundsTestCase:
    def __init__(self, purpose_price, users):
        self.test_case = TestCase()
        self.purpose_price = purpose_price

        def create_account(number):
            account = Account(
                user=User.objects.create_user(
                    get_username(number),
                    'asd@dom.pl',
                    'qwerty12'
                )
            )
            account.save()
            return account

        for key in users:
            create_account(key)
        Funds.objects.create(
            owner=get_account(1),
            purpose='TestParty',
            purpose_price=self.purpose_price
        )

    def assert_equal(self, first, second):
        self.test_case.assertEqual(first, second)

    def add_beneficiaries(self, input_beneficiaries):
        funds = Funds.objects.get(owner=get_account(1))
        for key, value in input_beneficiaries.items():
            funds.add_beneficiary(get_account(key), value)

    def set_beneficiaries(self, input_beneficiaries):
        funds = Funds.objects.get(owner=get_account(1))
        for key, value in input_beneficiaries.items():
            funds.set_beneficiary(get_account(key), value)

    def delete_beneficiaries(self, input_beneficiaries):
        funds = Funds.objects.get(owner=get_account(1))
        for key in input_beneficiaries:
            funds.delete_beneficiary(get_account(key))

    def validate_beneficiaries(self, expected_beneficiaries):
        funds = Funds.objects.get(owner=get_account(1))
        beneficiaries = funds.beneficiaries
        self.assert_equal(len(expected_beneficiaries), beneficiaries.count())
        for key, value in expected_beneficiaries.items():
            beneficiary = beneficiaries.filter(
                account=get_account(key)
            )
            self.assert_equal(beneficiary.exists(), True)
            self.assert_equal(beneficiary.count(), 1)
            beneficiary = beneficiary.first()
            self.assert_equal(beneficiary.contribution,  round(Decimal(value), 2))
            self.assert_equal(beneficiary.funds, funds)

    def update(self, input_dues):
        funds = Funds.objects.get(owner=get_account(1))
        funds.update()
        funds = Funds.objects.get(owner=get_account(1))
        if not input_dues:
            self.assert_equal(funds.dues.exists(), False)
       # pdb.set_trace()
        expected_dues_count = 0;
        for key, due_list in input_dues.items():
            expected_dues_count += len(due_list)
            for for_account, amount in due_list:
                due = funds.dues.filter(
                    account=get_account(key)
                ).filter(
                    for_account=get_account(for_account)
                )
                self.assert_equal(due.exists(), True)
                self.assert_equal(due.count(), 1)
                due = due.first()
                self.assert_equal(due.amount, round(Decimal(amount), 2))
                self.assert_equal(due.is_paid, False)
        self.assert_equal(funds.dues.count(), expected_dues_count)


class NewFundsTestCase1(TestCase):
    def setUp(self):
        self.funds_testcase = NewFundsTestCase(
            users={1, 2, 3},
            purpose_price=10
        )

    def test_add_beneficiary1(self):
        self.funds_testcase.add_beneficiaries({1: 2.5, 2: 7.5, 3: 0})
        self.funds_testcase.validate_beneficiaries({1: 2.5, 2: 7.5, 3: 0})
        self.funds_testcase.update({3: [(2, 3.33)], 1: [(2, 0.83)]})
        pass

    def test_add_beneficiary2(self):
        self.funds_testcase.add_beneficiaries({1: 10, 2: 0, 3: 0})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0, 3: 0})
        self.funds_testcase.update({2: [(1, 3.33)], 3: [(1, 3.33)]})
        pass

    def test_add_beneficiary3(self):
        self.funds_testcase.add_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.update({2: [(1, 5)]})
        pass

    def test_add_beneficiary4(self):
        self.funds_testcase.add_beneficiaries({1: 2.5, 2: 7.5})
        self.funds_testcase.validate_beneficiaries({1: 2.5, 2: 7.5})
        self.funds_testcase.update({1: [(2, 2.5)]})
        pass

    def test_add_beneficiary5(self):
        self.funds_testcase.add_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.update({})
        pass

    def test_add_beneficiary6(self):
        self.funds_testcase.add_beneficiaries({1: 5})
        self.funds_testcase.validate_beneficiaries({1: 5})
        self.funds_testcase.update({})
        self.funds_testcase.add_beneficiaries({2: 5})
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.update({})
        self.funds_testcase.add_beneficiaries({3: 0})
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5, 3: 0})
        self.funds_testcase.update({3: [(1, 1.67), (2, 1.66)]})
        pass

class EditFundsTestCase(TestCase):
    def setUp(self):
        self.funds_testcase = NewFundsTestCase(
            users={1, 2, 3},
            purpose_price=10
        )

    def test_set_beneficiary1(self):
        self.funds_testcase.add_beneficiaries({1: 2.5, 2: 7.5, 3: 0})
        self.funds_testcase.validate_beneficiaries({1: 2.5, 2: 7.5, 3: 0})
        self.funds_testcase.update({3: [(2, 3.33)], 1: [(2, 0.83)]})
        self.funds_testcase.set_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5, 3: 0})
        self.funds_testcase.update({3: [(2, 1.67), (1, 1.67)]})
        pass

    def test_set_beneficiary2(self):
        self.funds_testcase.add_beneficiaries({1: 10, 2: 0, 3: 0})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0, 3: 0})
        self.funds_testcase.update({2: [(1, 3.33)], 3: [(1, 3.33)]})
        self.funds_testcase.set_beneficiaries({3: 10})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0, 3: 10})
        self.funds_testcase.update({2: [(1, 3.33),  (3, 3.33)]})
        pass

    def test_set_beneficiary3(self):
        self.funds_testcase.add_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.update({2: [(1, 5)]})
        self.funds_testcase.set_beneficiaries({1: 0, 2: 10})
        self.funds_testcase.validate_beneficiaries({1: 0, 2: 10})
        self.funds_testcase.update({1: [(2, 5)]})
        pass

    def test_set_beneficiary4(self):
        self.funds_testcase.add_beneficiaries({1: 2.5, 2: 7.5})
        self.funds_testcase.validate_beneficiaries({1: 2.5, 2: 7.5})
        self.funds_testcase.update({1: [(2, 2.5)]})
        self.funds_testcase.set_beneficiaries({1: 7.5, 2: 7.5})
        self.funds_testcase.validate_beneficiaries({1: 7.5, 2: 7.5})
        self.funds_testcase.update({})
        pass

    def test_set_beneficiary5(self):
        self.funds_testcase.add_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.update({})
        self.funds_testcase.set_beneficiaries({1: 0})
        self.funds_testcase.validate_beneficiaries({1: 0, 2: 5})
        self.funds_testcase.update({1: [(2, 2.5)]})
        pass

class EditFundsTestCase2(TestCase):
    def setUp(self):
        self.funds_testcase = NewFundsTestCase(
            users={1, 2, 3},
            purpose_price=10
        )

    def test_add_beneficiary1(self):
        self.funds_testcase.add_beneficiaries({1: 2.5, 2: 7.5, 3: 0})
        self.funds_testcase.validate_beneficiaries({1: 2.5, 2: 7.5, 3: 0})
        self.funds_testcase.update({3: [(2, 3.33)], 1: [(2, 0.83)]})
        self.funds_testcase.delete_beneficiaries([1, 2])
        self.funds_testcase.validate_beneficiaries({3: 0})
        self.funds_testcase.update({})
        pass

    def test_add_beneficiary2(self):
        self.funds_testcase.add_beneficiaries({1: 10, 2: 0, 3: 0})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0, 3: 0})
        self.funds_testcase.update({2: [(1, 3.33)], 3: [(1, 3.33)]})
        self.funds_testcase.delete_beneficiaries([3])
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.update({2: [(1, 5)]})
        pass

    def test_add_beneficiary3(self):
        self.funds_testcase.add_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.validate_beneficiaries({1: 10, 2: 0})
        self.funds_testcase.update({2: [(1, 5)]})
        self.funds_testcase.delete_beneficiaries([1, 2])
        self.funds_testcase.validate_beneficiaries({})
        self.funds_testcase.update({})
        pass

    def test_add_beneficiary4(self):
        self.funds_testcase.add_beneficiaries({1: 2.5, 2: 7.5})
        self.funds_testcase.validate_beneficiaries({1: 2.5, 2: 7.5})
        self.funds_testcase.update({1: [(2, 2.5)]})
        self.funds_testcase.delete_beneficiaries([1])
        self.funds_testcase.validate_beneficiaries({2: 7.5})
        self.funds_testcase.update({})
        self.funds_testcase.delete_beneficiaries([2])
        self.funds_testcase.validate_beneficiaries({})
        self.funds_testcase.update({})
        pass

    def test_add_beneficiary5(self):
        self.funds_testcase.add_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.update({})
        self.funds_testcase.delete_beneficiaries([3])
        self.funds_testcase.validate_beneficiaries({1: 5, 2: 5})
        self.funds_testcase.update({})
        pass
