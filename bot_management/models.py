from django.db import models
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _


class BotUser(models.Model):
    LANGUAGE_CHOICES = [
        ('uz', 'O\'zbekcha'),
        ('qq', 'Qaraqalpaqsha'),
    ]
    
    telegram_id = models.BigIntegerField(unique=True, verbose_name=_("Telegram ID"))
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Username"))
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Имя"))
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Фамилия"))
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Номер телефона"))
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='uz', verbose_name=_("Язык"))
    instagram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Instagram аккаунт"))
    is_subscribed_instagram = models.BooleanField(default=False, verbose_name=_("Подписан на Instagram"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    
    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} (@{self.username})" if self.username else f"User {self.telegram_id}"
    
    class Meta:
        verbose_name = _("Пользователь бота")
        verbose_name_plural = _("Пользователи бота")


class Branch(models.Model):
    name_uz = models.CharField(max_length=200, verbose_name=_("Название (Узбекский)"))
    name_qq = models.CharField(max_length=200, verbose_name=_("Название (Каракалпакский)"))
    address_uz = models.TextField(verbose_name=_("Адрес (Узбекский)"))
    address_qq = models.TextField(verbose_name=_("Адрес (Каракалпакский)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активный"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    
    def get_name(self, language='uz'):
        return self.name_uz if language == 'uz' else self.name_qq
    
    def get_address(self, language='uz'):
        return self.address_uz if language == 'uz' else self.address_qq
    
    def __str__(self) -> str:
        return self.name_uz
    
    class Meta:
        verbose_name = _("Филиал")
        verbose_name_plural = _("Филиалы")
        ordering = ['name_uz']


class Receipt(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Ожидает')),
        ('approved', _('Одобрен')),
        ('rejected', _('Отклонен')),
    ]
    
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='receipts', verbose_name=_("Пользователь"))
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='receipts', verbose_name=_("Филиал"))
    file = models.FileField(
        upload_to='receipts/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        verbose_name=_("Файл чека")
    )
    file_size = models.PositiveIntegerField(verbose_name=_("Размер файла"))  # in bytes
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name=_("Статус"))
    rejection_reason = models.TextField(blank=True, null=True, verbose_name=_("Причина отклонения"))
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата отправки"))
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Дата обработки"))
    
    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Receipt from {self.user} at {self.branch} - {self.status}"
    
    class Meta:
        verbose_name = _("Чек")
        verbose_name_plural = _("Чеки")
        ordering = ['-submitted_at']


class BotSettings(models.Model):
    instagram_profile_url = models.URLField(
        default="https://instagram.com/",
        help_text=_("Ссылка на Instagram профиль, на который пользователи должны подписаться"),
        verbose_name=_("Instagram профиль")
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    
    def __str__(self):
        return "Настройки бота"
    
    class Meta:
        verbose_name = _("Настройки бота")
        verbose_name_plural = _("Настройки бота")
