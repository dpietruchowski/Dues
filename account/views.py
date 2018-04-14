from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
import json
from . import models
from . import forms as myforms
import pdb


@login_required(login_url='login')
def account(request):
    acc = models.Account.objects.get(user=request.user.id)
    dues = acc.get_due_list()

    dues_page = []
    for username, due_list in dues.items():
        for funds_id, amount in due_list.items():
            dues_page.append((username, funds_id, amount))

    paginator = Paginator(dues_page, 6)
    page = request.GET.get('page')
    dues_page = paginator.get_page(page)

    dues = {}
    for username, funds_id, amount in dues_page.object_list:
        if username in dues:
            dues[username].update({funds_id: amount})
        else:
            dues.update({username: {funds_id: amount}})

    return render(
        request,
        'account/account.html',
        {'dues': dues,
         "dues_page": dues_page,
         'account_value': acc.get_value(),
         'user_name': request.user.username}
    )


@login_required(login_url='login')
def funds(request, pk):
    funds = get_object_or_404(models.Funds, pk=pk)
    return render(
        request,
        'account/funds.html',
        {'funds': funds}
    )


@login_required(login_url='login')
def myfunds(request):
    acc = models.Account.objects.get(user=request.user.id)
    paginator = Paginator(acc.funds_set.all(), 8)
    page = request.GET.get('page')
    funds = paginator.get_page(page)
    return render(
        request,
        'account/myfunds.html',
        {"myfunds": funds}
    )


@login_required(login_url='login')
def history(request):
    acc = models.Account.objects.get(user=request.user.id)
    paginator = Paginator(acc.get_history_funds(), 10)
    page = request.GET.get('page')
    history_funds = paginator.get_page(page)
    return render(
        request,
        'account/history.html',
        {"history_funds": history_funds}
    )

def post_funds(request, BeneficiaryFormSet, pk):
    form = myforms.FundsForm(request.POST)
    formset = BeneficiaryFormSet(request.POST)
    valid = False
    beneficiaries = {}
    if formset.is_valid() and form.is_valid():
        valid = True
        purpose = form.cleaned_data['purpose']
        purpose_price = form.cleaned_data['purpose_price']
        for f in formset:
            account = f.cleaned_data['account_id']
            contribution = f.cleaned_data['contribution']
            beneficiaries.update({account: contribution})
    else:
        for f in formset:
            if not f.is_valid():
                print(f.errors)

    if valid:
        if pk is None:
            funds = models.Funds.objects.create(
                owner=models.Account.objects.get(user=request.user),
                purpose=purpose,
                purpose_price=purpose_price
            )
        else:
            funds = models.Funds.objects.get(pk=pk)
        funds_manager = models.FundsManager(funds)
        funds_manager.update(
            purpose=purpose,
            purpose_price=purpose_price
        )
        funds_manager.update_beneficiaries(beneficiaries)
        return HttpResponse("YEAH UDALO SIE!!")

    return HttpResponse("dupa nie udalo sie")

@login_required(login_url='login')
def edit_funds(request, pk):
    BeneficiaryFormSet = forms.formset_factory(myforms.BeneficiaryForm, extra=0)
    if request.method == 'POST':
        return post_funds(request, BeneficiaryFormSet, pk)
    else:
        funds = models.Funds.objects.get(pk=pk)
        account = models.Account.objects.get(user=request.user)
        if account != funds.owner:
            return HttpResponse("Nie masz uprawnien do edytowania tej skladki")
        form = myforms.FundsForm(initial={
            'purpose': funds.purpose,
            'purpose_price': funds.purpose_price
        })
        beneficiaries_form_set = []
        for beneficiary in funds.beneficiaries.all():
            beneficiaries_form_set.append({
                'account_id': beneficiary.account.user.username,
                'contribution': beneficiary.contribution
            })
        print(beneficiaries_form_set)
        formset = BeneficiaryFormSet(initial=beneficiaries_form_set)
    return render(request, 'account/edit_funds.html', {
        'form': form,
        'formset': formset,
        'sum_of_contribution': funds.sum_of_contribution,
        'owner': request.user.username
    })

@login_required(login_url='login')
def new_funds(request):
    BeneficiaryFormSet = forms.formset_factory(myforms.BeneficiaryForm, extra=0)
    if request.method == 'POST':
        return post_funds(request, BeneficiaryFormSet, None)
    formset = BeneficiaryFormSet()
    form = myforms.FundsForm()
    return render(request, 'account/edit_funds.html', {
        'form': form,
        'formset': formset,
        'sum_of_contribution': 0,
        'owner': request.user.username
    })

@login_required(login_url='login')
def delete_funds(request, pk):
    account = models.Account.objects.get(user=request.user)
    funds = models.Funds.objects.get(pk=pk)
    if account != funds.owner:
        return HttpResponse("Nie masz uprawnien do edytowania tej skladki")
    funds_manager = models.FundsManager(funds)
    funds_manager.delete_funds()
    return HttpResponse("Udalo sie usunales skladke( id : " + str(pk) + " )")


@login_required(login_url='login')
def accounts(request):
    results = []
    if request.method == "GET":
        if u'query' in request.GET:
            value = request.GET[u'query']
            model_results = User.objects.filter(username__icontains=value)
            results = [x.username for x in model_results]
    return JsonResponse(json.dumps(results), safe=False)


@login_required(login_url='login')
def new_notify(request):
    response = {
        "new_notifications": 0,
        "message": "Nie ma nowej notyfikacji"
    }
    if request.method == "GET":
        acc = models.Account.objects.get(user=request.user.id)
        new_notifications = acc.notifications_received.filter(seen=False)
        if new_notifications.exists():
            response["new_notifications"] = new_notifications.count()
            response["message"] = "Sa nowe notyfikacje"
    return JsonResponse(json.dumps(response), safe=False)

@login_required(login_url='login')
def notify(request):
    response = {
        "success": False,
        "message": "Nie udalo sie stworzyc notyfikacji"
    }
    if request.method == "GET":
        if u'due_id' in request.GET:
            due_id = request.GET[u'due_id']
            acc = models.Account.objects.get(user=request.user)
            due = models.Due.objects.get(pk=int(due_id))
            sent = acc.send_notification(due)
            if sent is not None:
                response["success"] = True
                response["message"] = "Notyfikacja stworzona pomyslnie"
    return JsonResponse(json.dumps(response), safe=False)

@login_required(login_url='login')
def notifications(request):
    acc = models.Account.objects.get(user=request.user.id)
    paginator = Paginator(
        acc.notifications_received.all().order_by("-latest_date", "-latest_datetime"),
        10
    )
    page = request.GET.get('page')
    notifications_received = paginator.get_page(page)
    for notification in acc.notifications_received.filter(seen=False):
        notification.seen = True
        notification.save()
    return render(
        request,
        'account/notification.html',
        {"new_notify_class": "new_notify",
         "notifications": notifications_received,
         "notification_types": dict(models.Notification.Type.__members__)}
    )
    pass
