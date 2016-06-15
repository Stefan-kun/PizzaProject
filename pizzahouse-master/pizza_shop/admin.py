from django.contrib import admin

from pizza_shop.models import Meal, SubSection, Section, MealImage, Cart, Ingredient, IngredientType


class MealImageInline(admin.StackedInline):
    model = MealImage
    extra = 2
    allow_add = True
    fields = ('image_tag', 'img')
    readonly_fields = ('image_tag',)


class MealModelAdmin(admin.ModelAdmin):
    inlines = [
        MealImageInline,
    ]
    exclude = ['section', ]


class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'status', 'archive')


admin.site.register(Meal, MealModelAdmin)
admin.site.register([Section, SubSection, MealImage, Ingredient, IngredientType])
admin.site.register(Cart, CartAdmin)