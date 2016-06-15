from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils.deconstruct import deconstructible
import string
import random


def generate_token(size=40, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def subclass_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images_<subsec>/<meal>_<filename>
    return 'images_{0}/{1}_{2}'.format(instance.meal.subsec.link, instance.meal.link, filename)

alphanumeric = RegexValidator(r'^[0-9a-zA-Z_-]*$', 'Latin only')
phone_regexp = RegexValidator(regex=r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$',
                            message="Wrong number")


class Section(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название раздела')
    link = models.CharField(max_length=50, verbose_name='Ссылка', validators=[alphanumeric], unique=True,
                            primary_key=True, help_text='Название для использования в ссылках')
    img = models.ImageField(upload_to='sec_img', verbose_name='Изображение раздела')
    descr = models.TextField(verbose_name='Описание', default='')
    keywords = models.CharField(max_length=300, verbose_name='Ключевые слова', help_text='Для поисковиков', default='')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'


class SubSection(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название подраздела')
    sec = models.ForeignKey(Section, related_name='subsecs', verbose_name='Подраздел для')
    link = models.CharField(max_length=70, verbose_name='Ссылка', validators=[alphanumeric], unique=True,
                            primary_key=True, help_text='Название для использования в ссылках')
    img = models.ImageField(upload_to='subsec_img', verbose_name='Изображение подраздела')
    descr = models.TextField(verbose_name='Описание', default='')
    keywords = models.CharField(max_length=300, verbose_name='Ключевые слова', help_text='Для поисковиков', default='')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Подраздел'
        verbose_name_plural = 'Подразделы'


class Meal(models.Model):
    title = models.CharField(max_length=150, verbose_name='Название блюда')
    price = models.PositiveSmallIntegerField(verbose_name='Цена', default=0)
    weight = models.CharField(max_length=70, verbose_name='Вес', help_text='Вес блюда в граммах')
    subsec = models.ForeignKey(SubSection, related_name='meals', verbose_name='Подраздел')
    link = models.CharField(max_length=80, verbose_name='Ссылка', validators=[alphanumeric], unique=True,
                            primary_key=True, help_text='Название для использования в ссылках')
    descr = models.TextField(verbose_name='Описание', default='')
    keywords = models.CharField(max_length=300, verbose_name='Ключевые слова', help_text='Для поисковиков', default='')

    add_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def s_ingredients(self):
        if self.ingredients.all():
            return ', '.join(map(str, self.ingredients.all()))
        return ''

    class Meta:
        ordering = ['-add_date']
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'


class MealImage(models.Model):
    meal = models.ForeignKey(Meal, related_name='imgs', verbose_name='Блюдо', on_delete=models.CASCADE)
    img = models.ImageField(upload_to=subclass_directory_path, verbose_name='Изображение')
    descr = models.TextField(verbose_name='Описание', null=True, blank=True)

    def __str__(self):
        return str(self.meal) + " Фото #" + str(self.id)

    def image_tag(self):
        return '%s<br><img src="%s" width="100" height="100" />' % (str(self), self.img.url)

    image_tag.short_description = 'Превью изображения'
    image_tag.allow_tags = True

    def url(self):
        return self.img.url

    class Meta:
        verbose_name = 'Изображение блюда'
        verbose_name_plural = 'Изображение блюд'


class InfoType(models.Model):
    type = models.CharField(max_length=80, verbose_name='Тип информации')

    def __str__(self):
        return self.type


class MealInfo(models.Model):
    meal = models.ForeignKey(Meal, verbose_name='Блюдо', related_name='info')
    info_type = models.ForeignKey(InfoType, verbose_name='Тип информации')
    value = models.CharField(max_length=200, verbose_name='Информация')

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = 'Информация о блюде'
        verbose_name_plural = 'Информация о блюдах'


class IngredientType(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название типа')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип ингредиентов'
        verbose_name_plural = 'Типы ингредиентов'


class Ingredient(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')
    descr = models.TextField(verbose_name='Описание', default='')
    inside = models.ManyToManyField(Meal, related_name='ingredients', verbose_name='Содержится в')
    type = models.ForeignKey(IngredientType, related_name='ingredients', verbose_name='Тип ингредиента')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


@deconstructible
class State(models.Model):
    text = models.CharField(max_length=60, verbose_name='Статус')
    details = models.CharField(max_length=600, verbose_name='Подробнее', help_text='Более детальное описание статуса')

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Статус'
        verbose_name_plural = 'Статусы заказов'


class Cart(models.Model):
    owner = models.ForeignKey(User, verbose_name='Покупатель', related_name='carts', blank=True, null=True)
    creation_date = models.DateTimeField(auto_now=True)
    meals = models.ManyToManyField(Meal, verbose_name='Заказ', through='CartMeal')
    token = models.CharField(max_length=40, verbose_name='Токен корзины для сессий', default=generate_token)
    archive = models.BooleanField(verbose_name='Заказ оформлен', default=False)

    status = models.ForeignKey('State', verbose_name='Статус заказа', related_name='carts',
                               default=State.objects.get_or_create(text='Ожидается',
                                                                    details='Заказ не оформлен')[0]
                               )

    contact = models.CharField(max_length=20, null=True, default='', verbose_name='Контактные данные')

    def __str__(self):
        return 'Заказ #' + str(self.id)

    def meals_list(self):
        return '\n'.join([str(x.meal) + "\t" + str(x.amount) + " шт." for x in self.cartmeal_set.all()])

    meals_list.__name__ = 'Блюда'

    def mealprices(self):
        return '\n'.join([str(x.meal) + "\t" + str(x.amount) + " шт.\t" + str(x.sum()) + " ₽" for x in
                          self.cartmeal_set.all()])

    def meal_count(self):
        s = 0
        for cart_meal in self.cartmeal_set.all():
            s += cart_meal.amount
        return s

    meal_count.__name__ = 'Количество блюд'

    def sum_price(self):
        price = 0
        for cart_meal in self.cartmeal_set.all():
            price += cart_meal.sum()
        return price

    sum_price.__name__ = 'Сумма заказа'

    def model_owner(self):
        if not self.owner:
            return 'Неавторизованный пользователь'
        return self.owner

    model_owner.__name__ = 'Покупатель'

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        ordering = ['-creation_date']


class CartMeal(models.Model):
    amount = models.PositiveSmallIntegerField(default=1, verbose_name='Количество')
    cart = models.ForeignKey(Cart, verbose_name='Корзина')
    meal = models.ForeignKey(Meal, verbose_name='Блюдо')

    def sum(self):
        return self.amount * self.meal.price

    def __str__(self):
        return str(self.meal)

    class Meta:
        verbose_name = 'Блюдо в корзине'
        verbose_name_plural = 'Блюда в корзине'


class Contact(models.Model):
    phone = models.CharField(max_length=20, validators=[phone_regexp], blank=True, verbose_name='Телефон')
    user = models.OneToOneField(User, verbose_name='Пользователь', related_name='phone', blank=True, null=True)
    cart = models.OneToOneField(Cart, verbose_name='Заказ', related_name='phone', null=True, blank=True)

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = 'Контактные данные'
        verbose_name_plural = verbose_name
