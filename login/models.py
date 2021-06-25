from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.models import SetUpModel


class Usuario(SetUpModel, AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Obrigatório, 150 caracteres ou menos. Letras, digitos e @/./+/-/ apenas.'),
        validators=[username_validator],
        error_messages={
            'unique': _("Este usuário já existe!"),
        },
    )
    nome = models.CharField(_('nome'), max_length=150, blank=True)
    email = models.EmailField(_('endereco de email'), blank=True, unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Define se o usuário pode acessar o site do admin'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Define se o usuário está ativo ou não'
        ),
    )

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        db_table = 'usuario'

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = str(self.nome)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.nome

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def save(self, *args, **kwargs):
        try:
            identify_hasher(self.password)
        except ValueError:
            self.set_password(self.password)
        super(Usuario, self).save(*args, **kwargs)
