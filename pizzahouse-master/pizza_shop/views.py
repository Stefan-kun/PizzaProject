import operator
from functools import reduce

from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import deprecate_current_app
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, render_to_response, resolve_url
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from paypal.standard.forms import PayPalPaymentsForm

from pizza_shop.forms import UserRegForm, ContactForm
from pizza_shop.models import Meal, Section, SubSection, Cart, CartMeal, State
from pizzaproject import settings


def get_cart(request):
    found = False

    if request.session.get('cart_token', ''):
        cart = Cart.objects.filter(token=request.session['cart_token']).latest('creation_date')
        if cart.archive is False and (
                (request.user.is_authenticated() and cart.owner == request.user) or request.user.is_anonymous()):
            found = True
    elif request.user.is_authenticated() and request.user.carts.filter(archive=False).all():
            cart = request.user.carts.filter(archive=False).latest('creation_date')
            found = True
    if not found:
        cart = Cart()
        if request.user.is_authenticated():
            cart.owner = request.user
        cart.save()
    request.session['cart_token'] = cart.token
    return cart


def menu(request):
    reg_form = UserRegForm()
    phone_form = ContactForm()
    return {
        'sects': Section.objects.all(),
        'cart': get_cart(request),
        'form': AuthenticationForm(),
        'phone_form': phone_form,
        'reg_form': reg_form,
    }


def index(request):
    meals = Meal.objects.order_by('?').all()[:9]
    return render(request, 'index.html', {'meals': meals, 'title': 'Главная'})


def section(request, link):
    sec = get_object_or_404(Section, link=link)
    objs = []
    for ss in sec.subsecs.all():
        objs.extend(ss.meals.all())
    paginator = Paginator(objs, 24)  # Show 24 meals per page

    page = request.GET.get('page')
    try:
        meals = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        meals = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        meals = paginator.page(paginator.num_pages)
    context = {'meals': meals,
               'section': sec,
               'title': str(sec),
               }
    return render(request, 'section.html', context)


def subsection(request, link, sublink):
    subsec = get_object_or_404(SubSection, link=sublink)
    objs = subsec.meals.all()
    paginator = Paginator(objs, 24)  # Show 24 meals per page

    page = request.GET.get('page')
    try:
        meals = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        meals = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        meals = paginator.page(paginator.num_pages)
    context = {'meals': meals,
               'subsection': subsec,
               'title': str(subsec.sec) + str(subsec),
               }
    return render(request, 'subsection.html', context)


def meal(request, link, sublink, meal_link):
    meal = get_object_or_404(Meal, link=meal_link)
    try:
        in_cart = get_cart(request).cartmeal_set.get(meal=meal).amount
    except Exception:
        in_cart = 0
    rand_meals = Meal.objects.exclude(link=meal.link).order_by('?')[:3]
    return render(request, 'show.html', {'meal': meal,
                                         'meals': rand_meals,
                                         'section': meal.subsec.sec,
                                         'subsection': meal.subsec,
                                         'in_cart': in_cart,
                                         'title': str(meal),
                                         })


def about(request):
    return render(request, 'about.html', {'title': 'Информация'})


def ajax_handler(request):
    if request.is_ajax():
        req_type = request.POST.get('type')
        if req_type == 'add' or req_type == 'set':
            cart = get_cart(request)
            try:
                _meal = Meal.objects.get(link=request.POST.get('meal'))
            except Meal.DoesNotExist:
                return HttpResponse("ERROR")

            try:
                cart_meal = cart.cartmeal_set.get(meal=_meal)
            except CartMeal.DoesNotExist:
                cart_meal = CartMeal.objects.create(cart=cart, meal=_meal, amount=0)
            if req_type == 'set':
                amount = request.POST.get('amount')
                if amount:
                    cart_meal.amount = int(amount)
            else:
                cart_meal.amount += 1
            cart_meal.save()
            cart.save()
            return HttpResponse(render_to_string('ajax/cart_meal.html', {'cart_meal': cart_meal}))

        elif req_type == 'del':
            cart = get_cart(request)
            try:
                _meal = Meal.objects.get(link=request.POST.get('meal'))
                cart_meal = cart.cartmeal_set.get(meal=_meal)
                cart_meal.delete()
                cart.save()
            except Meal.DoesNotExist or CartMeal.DoesNotExist:
                pass
            return HttpResponse('OK')

        elif req_type == 'search':
            wordlist = request.POST.get('meal').split()
            w = list()
            for word in wordlist:
                w.append(Q(title__icontains=word.strip()))
            meals = Meal.objects.filter(reduce(operator.or_, w))
            return HttpResponse(render_to_string('search_output.html', {'meals': meals}))

    return HttpResponse('ERROR')


@login_required
def account(request):
    old_orders = request.user.carts.filter(archive=True)
    return render(request, 'account.html', {'orders': old_orders, 'title': 'Ваш Профиль'})


def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    if request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/profile')

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserRegForm(data=request.POST)
        profile_form = ContactForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save()
            profile.user = user
            profile.save()

            new_user = authenticate(email=user_form.cleaned_data['email'], password=user_form.cleaned_data['password'])
            login(request, new_user)
            if request.session.get('cart_token', ''):
                cart = get_cart(request)
                cart.owner = user
                cart.save()
            next_page = request.GET.get('next')
            if next_page:
                return HttpResponseRedirect(next_page)
            else:
                return HttpResponseRedirect('/accounts/profile')

                # Invalid form or forms - mistakes or something else?
                # Print problems to the terminal.
                # They'll also be shown to the user.
                # else:
                #     print(user_form.errors, profile_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserRegForm()
        profile_form = ContactForm()

    # Render the template depending on the context.
    return render_to_response(
        'registration/login.html',
        {'userregform': user_form,
         'contactform': profile_form,
         'registered': registered,
         'title': 'Авторизация'
         },
        context)


def get_order(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/register')
    # if request.session.get('cart_token', '') != '':
    try:
        cart = request.user.carts.filter(archive=False, token=request.session['cart_token']).latest('creation_date')
        # print(cart.status)
        cart.archive = True
        cart.status = State.objects.get_or_create(text='Не оплачен', details='Оплатите заказ')[0]
        cart.save()
    except Cart.DoesNotExist:
        pass
    request.session['cart_token'] = ''
    return HttpResponseRedirect('/accounts/')


@deprecate_current_app
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_user(request, template_name='registration/login.html',
               redirect_field_name=REDIRECT_FIELD_NAME,
               authentication_form=AuthenticationForm,
               extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.POST.get(redirect_field_name,
                                   request.GET.get(redirect_field_name, ''))

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            login(request, form.get_user())

            if request.session.get('cart_token', ''):
                cart = get_cart(request)
                cart.owner = form.get_user()
                cart.save()

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        'title': 'Авторизация',
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)


def logout_user(request):
    try:
        request.user.carts.filter(archive=False, token=request.session['cart_token']).latest('creation_date').delete()
        request.session['cart_token'] = ''
        logout(request)
    except Exception:
        pass
    return HttpResponseRedirect('/')


@csrf_exempt
def paypal_success(request, cart):
    if request.method == 'post':
        curr_cart = Cart.objects.get(id=cart)
        curr_cart.status = State.objects.get_or_create(text='Оплачено', details='Спасибо за покупку')[0]
        curr_cart.save()
    return HttpResponseRedirect('/accounts/')


@login_required
def paypal_pay(request, cart):
    """
    Page where we ask user to pay with paypal.
    """
    curr_cart = Cart.objects.get(id=cart)
    paypal_dict = {
        "business": "hikka228-facilitator_api1.bk.ru",
        "amount": curr_cart.sum_price,
        "currency_code": "RUB",
        "item_name": "products",
        "invoice": cart,
        "notify_url": reverse('paypal-ipn'),
        "return_url": "http://localhost:8000/payment/success/" + cart,
        "cancel_return": "http://localhost:8000/payment/cart/" + cart,
        "custom": str(request.user)
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form, "paypal_dict": paypal_dict}
    return render(request, "payment.html", context)
