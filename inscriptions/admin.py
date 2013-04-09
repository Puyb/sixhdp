# -*- coding: utf-8 -*-
from inscriptions.models import Equipe, Equipier
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

class EquipeAdmin(admin.ModelAdmin):
    #exclude = [ 'password', ]
    list_display = ['categorie', 'nom', 'club', 'gerant_email', 'paiement', 'dossier_complet', 'nombre', 'date']
    list_display_links = ['categorie', 'nom', 'club', ]
    list_filter = ['categorie', 'paiement', 'dossier_complet', 'nombre', 'date']
    ordering = ['-date', ]
    inlines = [ EquipierInline ]

class EquipierInlineMini(admin.StackedInline):
    model = Equipier
    extra = 0
    max_num = 5
    readonly_fields = [ 'nom', 'prenom', 'sexe', 'adresse1', 'adresse2', 'ville', 'code_postal', 'pays', 'email', 'date_de_naissance', 'autorisation', 'justificatif', 'num_licence', 'piece_jointe', 'piece_jointe2', ]
    fieldsets = (
        (None, { 'fields': (('nom', 'prenom', 'sexe'), ) }),
        (u'Coordonnées', { 'classes': ('collapse', 'collapsed'), 'fields': ('adresse1', 'adresse2', ('ville', 'code_postal'), 'pays', 'email') }),
        (None, { 'classes': ('wide', ), 'fields': (('date_de_naissance',), ('autorisation_valide', 'autorisation'), ('justificatif', 'num_licence', ), ('piece_jointe_valide', 'piece_jointe'), ('piece_jointe2_valide', 'piece_jointe2')) }),
    )

class EquipeAdminMini(admin.ModelAdmin):
    class Media:
        css = {"all": ("admin.css",)}
        js  = ('/vars.js', 'prototype.js', 'admin.js', )
    exclude = [ 'password', ]
    readonly_fields = [ 'id', 'nom', 'club', 'gerant_nom', 'gerant_prenom', 'gerant_adresse1', 'gerant_adress2', 'gerant_ville', 'gerant_code_postal', 'gerant_pays', 'gerant_email', 'gerant_telephone', 'categorie', 'nombre', 'prix', 'date', ]
    list_display = ['id', 'categorie', 'nom', 'club', 'gerant_email', 'paiement_complet2', 'dossier_complet2', 'nombre2', 'date']
    list_display_links = ['id', 'categorie', 'nom', 'club', ]
    list_filter = ['categorie', 'dossier_complet', 'nombre', 'date']
    ordering = ['-date', ]
    inlines = [ EquipierInlineMini ]

    fieldsets = (
            ("Instructions", { 'description': HELP_TEXT, 'classes': ('collapse', 'collapsed'), 'fields': () }),
            (None, { 'fields': (('id', 'nom', 'club'), ('categorie', 'nombre'), ('paiement', 'prix', 'paiement_info'), 'dossier_complet', 'commentaires')}),
        (u'Gérant', { 'classes': ('collapse', 'collapsed'), 'fields': (('gerant_nom', 'gerant_prenom'), 'gerant_adresse1', 'gerant_adress2', ('gerant_ville', 'gerant_code_postal'), 'gerant_pays', 'gerant_email', 'gerant_telephone') }),
    )
    actions = []
    search_fields = ('id', 'nom', 'club', 'gerant_nom', 'gerant_prenom', 'equipier__nom', 'equipier__prenom')


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


admin.site.disable_action('delete_selected')
#admin.site.register(Equipe, EquipeAdmin)
admin.site.register(Equipe, EquipeAdminMini)
