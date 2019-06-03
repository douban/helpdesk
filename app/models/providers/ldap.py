# coding: utf-8


class LdapProviderMixin:
    def get_user_email_from_ldap(self, user):
        """if LDAP not configured or can't get email, return None
        """
        return None
