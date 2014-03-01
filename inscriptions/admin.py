# -*- coding: utf-8 -*-
from inscriptions.models import *
from django.contrib import admin

HELP_TEXT = """
<ul>
    <li>
        Réception d'un chèque : 
        <ol>
            <li>saisissez le montant du chèque dans la case 'Paiement reçu'.</li>
            <li>Au besoin, vous pouvez saisir une information complétentaire dans la case 'Détails'</li>
        </ol>
    </li>
    <li>
        Réception d'un certificat médical :
        <ol>
            <li>Identifier à quel équipier il se rapporte</li>
            <li>Vérifiez s'il a été émis après le 4 août 2012 et s'il autorise la pratique du roller en compétition</li>
            <li>Modifiez la case 'Certificat ou licence valide' de 'Inconnu' à 'Oui' ou 'Non' selon le cas</li>
        </ol>
    </li>
    <li>
        Réception d'une licence FFRS :
        <ol>
            <li>Identifier à quel équipier il se rapporte</li>
            <li>Vérifiez qu'elle est en cours de validité et qu'elle comporte la mention 'competition'</li>
            <li>Modifiez la case 'Certificat ou licence valide' de 'Inconnu' à 'Oui' ou 'Non' selon le cas</li>
        </ol>
    </li>
    <li>
        Réception d'une autorisation parentale :
        <ol>
            <li>Identifier à quel équipier il se rapporte</li>
            <li>Vérifiez qu'elle est valide</li>
            <li>Modifiez la case 'Autorisation parentale' de 'Inconnu' à 'Oui' ou 'Non' selon le cas</li>
        </ol>
    </li>
    <li>
        Réception d'une attestation entreprise ou étudiant :
        <ol>
            <li>Identifier à quel équipier il se rapporte</li>
            <li>Vérifiez qu'il est valide</li>
            <li>Modifiez la case 'Justificatif' de 'Inconnu' à 'Oui' ou 'Non' selon le cas</li>
        </ol>
    </li>
</ul>
<p>Au besoin, vous pouvez saisir des informations complémentaires dans la case 'commentaires'.</p>
<p>Une fois terminer, cliquer sur le bouton 'Enregistrer' en bas de page.</p>
<p>En cas de difficultés, contacter Stéphane au 06 72 80 65 98 ou par <a href="mailto:stephane.puybareau@6hdeparis.fr">mail</a>.</p>
"""

class EquipierInline(admin.StackedInline):
    model = Equipier
    extra = 0
    max_num = 5
    readonly_fields = [ 'nom', 'prenom', 'sexe', 'adresse1', 'adresse2', 'ville', 'code_postal', 'pays', 'email', 'date_de_naissance', 'autorisation', 'justificatif', 'num_licence', 'piece_jointe', 'piece_jointe2', 'age']
    fieldsets = (
        (None, { 'fields': (('nom', 'prenom', 'sexe'), ) }),
        (u'Coordonnées', { 'classes': ('collapse', 'collapsed'), 'fields': ('adresse1', 'adresse2', ('ville', 'code_postal'), 'pays', 'email') }),
        (None, { 'classes': ('wide', ), 'fields': (('date_de_naissance', 'age', ), ('autorisation_valide', 'autorisation'), ('justificatif', 'num_licence', ), ('piece_jointe_valide', 'piece_jointe'), ('piece_jointe2_valide', 'piece_jointe2')) }),
    )

class EquipeAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = super(EquipeAdmin, self).queryset(request)
        courses = request.user.profile.course.all()
        if len(courses):
            qs = qs.filter(course__in=courses)
        return qs
    class Media:
        css = {"all": ("admin.css",)}
        js  = ('/vars.js', 'prototype.js', 'admin.js', )
    readonly_fields = [ 'id', 'nom', 'club', 'gerant_nom', 'gerant_prenom', 'gerant_adresse1', 'gerant_adress2', 'gerant_ville', 'gerant_code_postal', 'gerant_pays', 'gerant_email', 'gerant_telephone', 'categorie', 'nombre', 'prix', 'date', 'password']
    list_display = ['id', 'categorie', 'nom', 'club', 'gerant_email', 'date', 'nombre2', 'paiement_complet2', 'documents_manquants2', 'verifier2', 'dossier_complet_auto2']
    list_display_links = ['id', 'categorie', 'nom', 'club', ]
    list_filter = ['categorie', 'dossier_complet', 'nombre', 'date']
    ordering = ['-date', ]
    inlines = [ EquipierInline ]

    fieldsets = (
        ("Instructions", { 'description': HELP_TEXT, 'classes': ('collapse', 'collapsed'), 'fields': () }),
        (None, { 'fields': (('id', 'nom', 'club'), ('categorie', 'nombre'), ('paiement', 'prix', 'paiement_info'), 'commentaires')}),
        (u'Gérant', { 'classes': ('collapse', 'collapsed'), 'fields': (('gerant_nom', 'gerant_prenom'), 'gerant_adresse1', 'gerant_adress2', ('gerant_ville', 'gerant_code_postal'), 'gerant_pays', 'gerant_email', 'gerant_telephone', 'password') }),
        ("Autre", { 'description': '<div id="autre"></div>', 'classes': ('collapse', 'collapsed'), 'fields': () }),

    )
    actions = []
    search_fields = ('id', 'nom', 'club', 'gerant_nom', 'gerant_prenom', 'equipier__nom', 'equipier__prenom')
    list_per_page = 500

    def documents_manquants2(self):
        return (len(self.licence_manquantes()) + len(self.certificat_manquantes()) + len(self.autorisation_manquantes())) or ''
    documents_manquants2.short_description = u'✉'

    def verifier2(self):
        return self.verifier() and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u''
    verifier2.allow_tags = True
    verifier2.short_description = 'V'

    def paiement_complet2(self):
        return self.paiement_complet() and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
    paiement_complet2.allow_tags = True
    paiement_complet2.short_description = '€'
    
    def nombre2(self):
        return self.nombre
    nombre2.short_description = u'☺'

    def dossier_complet2(self):
        return self.dossier_complet and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
    dossier_complet2.allow_tags = True
    dossier_complet2.short_description = mark_safe(u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""")

    def dossier_complet_auto2(self):
        auto = self.dossier_complet_auto()
        if auto:
            return u"""<img alt="None" src="/static/admin/img/icon-yes.gif">"""
        if auto == False:
            return u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
        return u""
    dossier_complet_auto2.allow_tags = True
    dossier_complet_auto2.short_description = mark_safe(u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""")


from django.contrib.admin.models import LogEntry
from django.utils.html import escape
from django.utils.safestring import mark_safe
class LogAdmin(admin.ModelAdmin):
    """Create an admin view of the history/log table"""
    list_display = ('action_time','user','content_type','modified_object','change_message','is_addition','is_change','is_deletion')
    list_filter = ['action_time','user','content_type']
    ordering = ('-action_time',)
    readonly_fields = [ 'user','content_type','object_id','object_repr','action_flag','change_message']
    #We don't want people changing this historical record:
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        #returning false causes table to not show up in admin page :-(
        #I guess we have to allow changing for now
        return True
    def has_delete_permission(self, request, obj=None):
        return False
    def modified_object(self, obj=None):
        if not obj:
            return ''
        return mark_safe(u'<a href="/admin/%s">%s</a>' % (
            obj.get_admin_url(),
            escape(obj.object_repr)
        ))
    modified_object.allow_tags = True
admin.site.register(LogEntry, LogAdmin)


#admin.site.disable_action('delete_selected')
admin.site.register(Equipe, EquipeAdmin)


class CourseAdmin(admin.ModelAdmin):
    pass
admin.site.register(Course, CourseAdmin)


class CategorieAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = super(CategorieAdmin, self).queryset(request)
        courses = request.user.profile.course.all()
        if len(courses):
            qs = qs.filter(course__in=courses)
        return qs
    pass
admin.site.register(Categorie, CategorieAdmin)


class TemplateMailAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = super(EquipeAdmin, self).queryset(request)
        courses = request.user.profile.course.all()
        if len(courses):
            qs = qs.filter(course__in=courses)
        return qs
    list_display = ('sujet', )
admin.site.register(TemplateMail, TemplateMailAdmin)


from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile

class UserProfileAdmin(UserAdmin):
    inlines = [ UserProfileInline, ]

admin.site.register(User, UserProfileAdmin)
