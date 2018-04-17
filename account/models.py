from datetime import date
from math import fabs
from decimal import Decimal
from enum import Enum

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import pdb


class Account(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def get_value(self):
        dues = self.get_due_list()
        value = 0
        for due_user, due_amounts in dues.items():
            for funds_id, amount in due_amounts.items():
                value += amount[1]
        return value

    def get_due_from_list(self, due_list):
        for due in self.dues_from.all():
            if due.is_paid:
                continue
            key = due.account.user.username
            amount = 1 * due.amount
            funds_id = due.funds.id
            if key in due_list:
                due_list[key].update({funds_id: (due.pk, amount)})
            else:
                due_list.update({key: {funds_id: (due.pk, amount)}})
        return due_list

    def get_due_for_list(self, due_list):
        for due in self.dues.all():
            if due.is_paid:
                continue
            key = due.for_account.user.username
            amount = -1 * due.amount
            funds_id = due.funds.id
            if key in due_list:
                due_list[key].update({funds_id: (due.pk, amount)})
            else:
                due_list.update({key: {funds_id: (due.pk, amount)}})
        return due_list

    def get_due_list(self):
        dues = self.get_due_for_list({})
        dues.update(self.get_due_from_list(dues))
        return dues;

    def get_history_funds(self):
        funds = [];
        for as_beneficiary in self.as_beneficiaries.all():
            funds.append(as_beneficiary.funds)
        return funds

    def accept_notification(self, due):
        if due in self.dues_from.all():
            return due.send_accept("Ok. Zaakceptowałem.")
        else:
            return None

    def decline_notification(self, due):
        if due in self.dues_from.all():
            return due.send_decline("Pieniądze nie wpłyneły na moje konto.")
        else:
            return None

    def send_notification(self, due):
        if due in self.dues.all():
            return due.send_paid("Spłaciłem dług. Proszę usuń go.")
        elif due in self.dues_from.all():
            return due.send_unpaid("Proszę spłać dług")
        else:
            return None


class FundsManager:
    def __init__(self, funds):
        self.funds = funds

    def update(self, purpose, purpose_price):
        self.funds.purpose = purpose
        self.funds.purpose_price = purpose_price
        self.funds.save()

    def update_beneficiaries(self, account_dict):
        old_beneficiaries = set()
        new_beneficiaries = set()
        for beneficiary in self.funds.beneficiaries.all():
            old_beneficiaries.update({beneficiary.account})

        for username, contribution in account_dict.items():
            user = User.objects.get(username=username)
            account = Account.objects.get(user=user)
            new_beneficiaries.update({account})
            self.funds.update_beneficiary(account, contribution)

        for account in old_beneficiaries.difference(new_beneficiaries):
            self.funds.delete_beneficiary(account)

        self.funds.update()

    def delete_funds(self):
        for due in self.funds.dues.all():
            due.delete()
        for beneficiary in self.funds.beneficiaries.all():
            beneficiary.delete()
        self.funds.delete()


class Funds(models.Model):
    owner = models.ForeignKey(Account, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=130)
    purpose_price = models.DecimalField(
        decimal_places=2,
        max_digits=15
    )
    sum_of_contribution = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0
    )
    date = models.DateField(default=date.today)
    datetime = models.DateTimeField(default=timezone.now)

    def update_beneficiary(self, account, contribution):
        if self.beneficiaries.filter(account=account).exists():
            self.set_beneficiary(account, contribution)
        else:
            self.add_beneficiary(account, contribution)

    def add_beneficiary(self, account, contribution):
        self.sum_of_contribution += Decimal(contribution)
        self.beneficiaries.create(
            account=account,
            contribution=contribution
        )
        self.save()

    def delete_beneficiary(self, account):
        beneficiary = self.beneficiaries.filter(account=account).first()
        if not beneficiary:
            return
        self.sum_of_contribution -= beneficiary.contribution
        beneficiary.delete()

    def set_beneficiary(self, account, contribution):
        beneficiary = self.beneficiaries.filter(account=account).first()
        self.sum_of_contribution -= beneficiary.contribution
        self.sum_of_contribution += Decimal(contribution)
        beneficiary.contribution = Decimal(contribution)
        beneficiary.save()
        self.save()

    def update(self):
        self.dues.all().delete()
        if self.beneficiaries.count() == 0:
            return
        due_per_person = self.sum_of_contribution / self.beneficiaries.count()
        due_per_person = round(due_per_person, 2)
        creditors = self.beneficiaries.filter(contribution__gte=due_per_person)
        debtors = self.beneficiaries.filter(contribution__lt=due_per_person)
        if not debtors:
            return
        it_debtors = iter(debtors.order_by('-contribution'))
        debtor = next(it_debtors)
        debtor_contribution = debtor.contribution
        for creditor in creditors.order_by('contribution'):
            creditor_contribution = creditor.contribution
            while fabs(creditor_contribution - due_per_person) > 0.03:
                if debtor_contribution == due_per_person:
                    debtor = next(it_debtors)
                    debtor_contribution = debtor.contribution
                amount = due_per_person - debtor_contribution
                if amount > creditor_contribution - due_per_person:
                    amount = creditor_contribution - due_per_person
                due = self.dues.\
                    filter(account=debtor.account).\
                    filter(for_account=creditor.account)
                if not due:
                    created_due = self.dues.create(
                        account=debtor.account,
                        for_account=creditor.account,
                        amount=amount
                    )
                else:
                    due = due.first()
                    due.amount = amount
                    due.save()
                creditor_contribution -= amount
                debtor_contribution += amount


class Beneficiary(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="as_beneficiaries"
    )
    funds = models.ForeignKey(
        Funds,
        on_delete=models.CASCADE,
        related_name="beneficiaries"
    )
    contribution = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0
    )

    def get_info(self):
        return {
            "account": self.account.user.username,
            "funds": self.funds.id,
            "contribution": self.contribution,
        }

    def __str__(self):
        return '(%s:%s$%s)' % (self.account.pk, self.funds.pk, self.contribution)


class Due(models.Model):
    funds = models.ForeignKey(
        Funds,
        on_delete=models.CASCADE,
        related_name="dues"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="dues"
    )
    for_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="dues_from"
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        default=0
    )
    is_paid = models.BooleanField(default=False)

    def get_notification(self):
        notification = self.notification_set.filter(
            from_account=self.account,
            to_account=self.for_account
        )
        if notification.exists():
            notification = notification.first()
        else:
            notification = self.notification_set.create(
                type=Notification.Type.PAID,
                from_account=self.account,
                to_account=self.for_account,
                message=""
            )
        return notification

    def get_notification_back(self):
        notification = self.notification_set.filter(
            from_account=self.for_account,
            to_account=self.account
        )
        if notification.exists():
            notification = notification.first()
            notification.type = type
        else:
            notification = self.notification_set.create(
                type=Notification.Type.UNPAID,
                from_account=self.for_account,
                to_account=self.account,
                message=""
            )
        return notification

    def send_paid(self, message):
        notification = self.get_notification()
        notification.send(message, Notification.Type.PAID)
        return notification

    def send_unpaid(self, message):
        notification = self.get_notification_back()
        notification.send(message, Notification.Type.UNPAID)
        return notification

    def send_accept(self, message):
        notification = self.get_notification_back()
        notification.send(message, Notification.Type.ACCEPTED)
        self.is_paid = True
        self.save()
        return notification

    def send_decline(self, message):
        notification = self.get_notification_back()
        notification.send(message, Notification.Type.DECLINED)
        return notification


class Notification(models.Model):
    class Type(Enum):
        PAID = 0
        UNPAID = 1
        ACCEPTED = 2
        DECLINED = 3

        @classmethod
        def choices(cls):
            return tuple((x.name, x.value) for x in cls)

        def __int__(self):
            return self.value

    type = models.IntegerField(choices=Type.choices())
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="notifications_sent"
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="notifications_received"
    )
    due = models.ForeignKey(
        Due,
        on_delete=models.CASCADE
    )
    latest_date = models.DateField(default=date.today)
    latest_datetime = models.DateTimeField(default=timezone.now)
    date = models.DateField(default=date.today)
    datetime = models.DateTimeField(default=timezone.now)
    message = models.CharField(max_length=130)
    seen = models.BooleanField(default=False)
    answered = models.BooleanField(default=False)

    def send(self, message, type):
        self.latest_date = date.today()
        self.latest_datetime = timezone.now()
        self.message = message
        self.type = type
        self.seen = False
        self.answered = False
        self.save()

    def __str__(self):
        return '(%s%s:%s->%s)' % (self.due, self.Type(self.type).name, self.from_account.pk, self.to_account.pk)