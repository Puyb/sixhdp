# -*- coding: utf-8 -*-
from inscriptions.models import Equipe, Equipier
from django.contrib import admin

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
    list_display = ['categorie', 'nom', 'club', 'gerant_email', 'paiement_complet', 'dossier_complet', 'nombre', 'date']
    list_display_links = ['categorie', 'nom', 'club', ]
    list_filter = ['categorie', 'dossier_complet', 'nombre', 'date']
    ordering = ['-date', ]
    inlines = [ EquipierInlineMini ]

    fieldsets = (
        (None, { 'fields': (('nom', 'club'), ('categorie', 'nombre'), ('paiement', 'prix', 'paiement_info'), 'dossier_complet', 'commentaires') }),
        (u'Gérant', { 'classes': ('collapse', 'collapsed'), 'fields': (('gerant_nom', 'gerant_prenom'), 'gerant_adresse1', 'gerant_adress2', ('gerant_ville', 'gerant_code_postal'), 'gerant_pays', 'gerant_email', 'gerant_telephone') }),
    )


#admin.site.register(Equipe, EquipeAdmin)
admin.site.register(Equipe, EquipeAdminMini)
