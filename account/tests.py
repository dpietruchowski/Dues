from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Account, Funds, Beneficiary, Due, Notification
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


class NotificationTestCaseManager:
    def __init__(self):
        self.test_case = TestCase()
        self.message = "Default message"
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
        users = [1, 2]
        for key in users:
            create_account(key)
        self.funds = Funds.objects.create(
            owner=get_account(1),
            purpose='TestParty',
            purpose_price=10.0
        )
        self.due = Due.objects.create(
            funds=self.funds,
            account=get_account(1),
            for_account=get_account(2),
            amount=20
        )

    def assert_equal(self, first, second):
        self.test_case.assertEqual(first, second)

    def notify(self, user):
        account = get_account(user)
        account.send_notification(self.due, self.message)

    def notify_back(self, notification_tuple, is_accepted):
        account1 = get_account(notification_tuple[0])
        account2 = get_account(notification_tuple[1])
        notification_queryset = Notification.objects.filter(
            from_account=account1,
            to_account=account2,
            due=self.due,
        )
        self.assert_equal(notification_queryset.exists(), True)
        self.assert_equal(notification_queryset.count(), 1)
        notification = notification_queryset.first()
        notification.send_back(self.message, is_accepted)

    def validate_notifications(self, expected_notifications):
        self.assert_equal(Notification.objects.all().count(), len(expected_notifications))
        for notification_tuple in expected_notifications:
            type = notification_tuple[0]
            from_account = get_account(notification_tuple[1])
            to_account = get_account(notification_tuple[2])
            seen = notification_tuple[3]
            self.validate_notification(type, from_account, to_account, seen)

    def validate_notification(self, type, from_account, to_account, seen):
        notification_queryset = Notification.objects.filter(
            from_account=from_account,
            to_account=to_account,
            due=self.due,
        )
        self.assert_equal(notification_queryset.exists(), True)
        self.assert_equal(notification_queryset.count(), 1)
        notification = notification_queryset.first()
        self.assert_equal(notification.type, int(type))
        self.assert_equal(notification.seen, seen)

class NotificationTestCase(TestCase):
    def setUp(self):
        self.manager = NotificationTestCaseManager()

    def test_1_notify(self):
        self.manager.notify(1)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False)
        ])
        pass

    def test_2_notify(self):
        self.manager.notify(2)
        self.manager.validate_notifications([
            (Notification.Type.UNPAID, 2, 1, False)
        ])
        pass

    def test_1_notify_twice(self):
        self.manager.notify(1)
        self.manager.notify(1)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False)
        ])
        pass

    def test_2_notify_twice(self):
        self.manager.notify(2)
        self.manager.notify(2)
        self.manager.validate_notifications([
            (Notification.Type.UNPAID, 2, 1, False)
        ])
        pass

    def test_2_accept(self):
        self.manager.notify(1)
        self.manager.notify_back((1, 2), True)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False),
            (Notification.Type.ACCEPTED, 2, 1, False)
        ])
        pass

    def test_2_decline(self):
        self.manager.notify(1)
        self.manager.notify_back((1, 2), False)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False),
            (Notification.Type.DECLINED, 2, 1, False)
        ])
        pass

    def test_2_accept_twice(self):
        self.manager.notify(1)
        self.manager.notify_back((1, 2), True)
        self.manager.notify_back((1, 2), True)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False),
            (Notification.Type.ACCEPTED, 2, 1, False)
        ])
        pass

    def test_2_accept_1_notify(self):
        self.manager.notify(1)
        self.manager.notify_back((1, 2), True)
        self.manager.notify(1)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False),
            (Notification.Type.ACCEPTED, 2, 1, False)
        ])
        pass

    def test_2_decline_1_notify(self):
        self.manager.notify(1)
        self.manager.notify_back((1, 2), False)
        self.manager.notify(1)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False),
            (Notification.Type.DECLINED, 2, 1, False)
        ])
        pass

    def test_2_decline_1_notify_accept(self):
        self.manager.notify(1)
        self.manager.notify_back((1, 2), False)
        self.manager.notify(1)
        self.manager.notify_back((1, 2), True)
        self.manager.validate_notifications([
            (Notification.Type.PAID, 1, 2, False),
            (Notification.Type.ACCEPTED, 2, 1, False)
        ])
        pass
