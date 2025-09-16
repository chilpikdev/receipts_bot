from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django import forms
from .models import BotUser, Branch, Receipt, BotSettings
from .notifications import notify_user_sync
import asyncio
from django.contrib import messages


class RejectReceiptForm(forms.Form):
    """Form for rejecting receipts with reason"""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 50}),
        max_length=500,
        required=True,
        label="Причина отклонения",
        help_text="Пожалуйста, укажите причину отклонения (максимум 500 символов)"
    )


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'full_name', 'username', 'phone_number', 'instagram_username', 'language', 'is_subscribed_instagram', 'created_at']
    list_filter = ['language', 'is_subscribed_instagram', 'created_at']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name', 'phone_number', 'instagram_username']
    readonly_fields = ['telegram_id', 'created_at', 'updated_at']
    
    def full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}" if obj.first_name or obj.last_name else 'Нет имени'
    full_name.short_description = 'Полное имя'
    
    fieldsets = (
        ('Информация Telegram', {
            'fields': ('telegram_id', 'username', 'first_name', 'last_name')
        }),
        ('Контактная информация', {
            'fields': ('phone_number', 'instagram_username')
        }),
        ('Настройки', {
            'fields': ('language', 'is_subscribed_instagram')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name_uz', 'name_qq', 'is_active', 'receipts_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name_uz', 'name_qq', 'address_uz', 'address_qq']
    
    def receipts_count(self, obj):
        return obj.receipts.count()
    receipts_count.short_description = 'Количество чеков'
    
    fieldsets = (
        ('Названия филиалов', {
            'fields': ('name_uz', 'name_qq')
        }),
        ('Адреса', {
            'fields': ('address_uz', 'address_qq')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        })
    )


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_info', 'branch_name', 'status_display', 'file_link', 'file_size_mb', 'submitted_at', 'action_buttons']
    list_filter = ['status', 'submitted_at', 'branch']
    search_fields = ['user__telegram_id', 'user__username', 'user__first_name', 'branch__name_uz']
    readonly_fields = ['user', 'branch', 'file', 'file_size', 'submitted_at', 'processed_at', 'file_preview']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:receipt_id>/approve/', self.admin_site.admin_view(self.approve_receipt), name='approve_receipt'),
            path('<int:receipt_id>/reject/', self.admin_site.admin_view(self.reject_receipt), name='reject_receipt'),
        ]
        return custom_urls + urls
    
    def user_info(self, obj):
        user_link = reverse('admin:bot_management_botuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', user_link, obj.user)
    user_info.short_description = 'Пользователь'
    
    def branch_name(self, obj):
        return obj.branch.name_uz
    branch_name.short_description = 'Филиал'
    
    def status_display(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745', 
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return 'No file'
    file_link.short_description = 'Файл'
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / 1024 / 1024:.2f} MB" if obj.file_size else 'Unknown'
    file_size_mb.short_description = 'Размер файла'
    
    def action_buttons(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_receipt', args=[obj.id])
            reject_url = reverse('admin:reject_receipt', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" style="background-color: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Одобрить</a>'
                '<a class="button" href="{}" style="background-color: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Отклонить</a>',
                approve_url, reject_url
            )
            return f'Already {obj.get_status_display()}'
    action_buttons.short_description = 'Действия'
    
    def file_preview(self, obj):
        if obj.file:
            if obj.file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;"/>', obj.file.url)
            else:
                return format_html('<a href="{}" target="_blank">Download {}</a>', obj.file.url, obj.file.name)
        return 'No file'
    file_preview.short_description = 'Предпросмотр файла'
    
    def approve_receipt(self, request, receipt_id):
        """Approve a single receipt"""
        receipt = get_object_or_404(Receipt, id=receipt_id)
        
        if receipt.status != 'pending':
            messages.error(request, f"Receipt is already {receipt.status}")
            return HttpResponseRedirect('../')
        
        # Update receipt status
        receipt.status = 'approved'
        receipt.processed_at = timezone.now()
        receipt.save()
        
        # Send notification to user
        try:
            success = notify_user_sync(
                user_telegram_id=receipt.user.telegram_id,
                receipt_id=receipt.id,
                status='approved',
                user_language=receipt.user.language
            )
            if success:
                messages.success(request, f"Receipt #{receipt.id} approved and user notified successfully!")
            else:
                messages.warning(request, f"Receipt #{receipt.id} approved but failed to notify user.")
        except Exception as e:
            messages.warning(request, f"Receipt #{receipt.id} approved but notification failed: {e}")
        
        return HttpResponseRedirect('../')
    
    def reject_receipt(self, request, receipt_id):
        """Reject a single receipt with reason"""
        receipt = get_object_or_404(Receipt, id=receipt_id)
        
        if receipt.status != 'pending':
            messages.error(request, f"Receipt is already {receipt.status}")
            return HttpResponseRedirect('../')
        
        if request.method == 'POST':
            form = RejectReceiptForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data['reason']
                
                # Update receipt status
                receipt.status = 'rejected'
                receipt.rejection_reason = reason
                receipt.processed_at = timezone.now()
                receipt.save()
                
                # Send notification to user
                try:
                    success = notify_user_sync(
                        user_telegram_id=receipt.user.telegram_id,
                        receipt_id=receipt.id,
                        status='rejected',
                        user_language=receipt.user.language,
                        rejection_reason=reason
                    )
                    if success:
                        messages.success(request, f"Receipt #{receipt.id} rejected and user notified successfully!")
                    else:
                        messages.warning(request, f"Receipt #{receipt.id} rejected but failed to notify user.")
                except Exception as e:
                    messages.warning(request, f"Receipt #{receipt.id} rejected but notification failed: {e}")
                
                return HttpResponseRedirect('../')
        else:
            form = RejectReceiptForm()
        
        context = {
            'title': f'Reject Receipt #{receipt.id}',
            'receipt': receipt,
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/receipt_reject.html', context)
    
    actions = ['bulk_approve_receipts', 'bulk_reject_receipts']
    
    def bulk_approve_receipts(self, request, queryset):
        """Bulk approve multiple receipts"""
        pending_receipts = queryset.filter(status='pending')
        count = 0
        notification_failures = 0
        
        for receipt in pending_receipts:
            receipt.status = 'approved'
            receipt.processed_at = timezone.now()
            receipt.save()
            count += 1
            
            # Try to notify user
            try:
                success = notify_user_sync(
                    user_telegram_id=receipt.user.telegram_id,
                    receipt_id=receipt.id,
                    status='approved',
                    user_language=receipt.user.language
                )
                if not success:
                    notification_failures += 1
            except Exception:
                notification_failures += 1
        
        if count > 0:
            message = f"Successfully approved {count} receipts."
            if notification_failures > 0:
                message += f" {notification_failures} notification(s) failed."
            messages.success(request, message)
        else:
            messages.warning(request, "No pending receipts to approve.")
    
    bulk_approve_receipts.short_description = "Одобрить выбранные чеки"
    
    def bulk_reject_receipts(self, request, queryset):
        """Bulk reject multiple receipts (without individual reasons)"""
        pending_receipts = queryset.filter(status='pending')
        count = 0
        notification_failures = 0
        
        for receipt in pending_receipts:
            receipt.status = 'rejected'
            receipt.rejection_reason = "Bulk rejection - contact admin for details"
            receipt.processed_at = timezone.now()
            receipt.save()
            count += 1
            
            # Try to notify user
            try:
                success = notify_user_sync(
                    user_telegram_id=receipt.user.telegram_id,
                    receipt_id=receipt.id,
                    status='rejected',
                    user_language=receipt.user.language,
                    rejection_reason=receipt.rejection_reason
                )
                if not success:
                    notification_failures += 1
            except Exception:
                notification_failures += 1
        
        if count > 0:
            message = f"Successfully rejected {count} receipts."
            if notification_failures > 0:
                message += f" {notification_failures} notification(s) failed."
            messages.success(request, message)
        else:
            messages.warning(request, "No pending receipts to reject.")
    
    bulk_reject_receipts.short_description = "Отклонить выбранные чеки"
    
    fieldsets = (
        ('Информация о чеке', {
            'fields': ('user', 'branch', 'status')
        }),
        ('Информация о файле', {
            'fields': ('file_preview', 'file', 'file_size')
        }),
        ('Обработка', {
            'fields': ('rejection_reason', 'submitted_at', 'processed_at')
        })
    )


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ['instagram_profile_url', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance of BotSettings
        return not BotSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of BotSettings
        return False
    
    fieldsets = (
        ('Настройки Instagram', {
            'fields': ('instagram_profile_url',),
            'description': 'Настройте URL профиля Instagram, на который пользователи должны подписаться.'
        }),
    )


# Custom admin site configuration
admin.site.site_header = "Администрирование бота чеков"
admin.site.site_title = "Админ чеков"
admin.site.index_title = "Добро пожаловать в администрирование бота чеков"
