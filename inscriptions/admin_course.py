# -*- coding: utf-8 -*-
from inscriptions.models import *
from django.contrib import admin
from django.core.mail import EmailMessage
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import Template, Context
from django.template import RequestContext
from django.conf.urls import patterns


class CourseAdminSite(admin.sites.AdminSite):
    def login(self, request):
        user = request.user
        if user.is_authenticated() and user.is_active and not self.has_permission(request) and request.META['REQUEST_METHOD'] == 'GET':
            return self.display_login_form(request, _("You're not allowed to access this part of the site. Please contact your site adminstrator."))
        return super(CourseAdminSite, self).login(request)

    def has_permission(self, request):
        if not request.user.is_authenticated():
            return False
        if request.path.endswith('/logout/'):
            return True
        if request.user.is_superuser:
            return True
        course_uid = request.COOKIES['course_uid']
        return request.user.profile.course.filter(uid=course_uid)


site = CourseAdminSite(name='course')

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
        course_uid = request.COOKIES['course_uid']
        qs = qs.filter(course__uid=course_uid)
        return qs
    class Media:
        css = {"all": ("admin.css",)}
        js  = ('admin/equipe.js', )
    readonly_fields = [ 'id', 'nom', 'club', 'gerant_nom', 'gerant_prenom', 'gerant_adresse1', 'gerant_adress2', 'gerant_ville', 'gerant_code_postal', 'gerant_pays', 'gerant_email', 'gerant_telephone', 'categorie', 'nombre', 'prix', 'date', 'password']
    list_display = ['numero', 'categorie', 'nom', 'club', 'gerant_email', 'date', 'nombre2', 'paiement_complet2', 'documents_manquants2', 'verifier2', 'dossier_complet_auto2']
    list_display_links = ['numero', 'categorie', 'nom', 'club', ]
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

    def documents_manquants2(self, obj):
        return (len(obj.licence_manquantes()) + len(obj.certificat_manquantes()) + len(obj.autorisation_manquantes())) or ''
    documents_manquants2.short_description = u'✉'

    def verifier2(self, obj):
        return obj.verifier() and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u''
    verifier2.allow_tags = True
    verifier2.short_description = 'V'

    def paiement_complet2(self, obj):
        return obj.paiement_complet() and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
    paiement_complet2.allow_tags = True
    paiement_complet2.short_description = '€'
    
    def nombre2(self, obj):
        return obj.nombre
    nombre2.short_description = u'☺'

    def dossier_complet2(self, obj):
        return obj.dossier_complet and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
    dossier_complet2.allow_tags = True
    dossier_complet2.short_description = mark_safe(u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""")

    def dossier_complet_auto2(self, obj):
        auto = obj.dossier_complet_auto()
        if auto:
            return u"""<img alt="None" src="/static/admin/img/icon-yes.gif">"""
        if auto == False:
            return u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
        return u""
    dossier_complet_auto2.allow_tags = True
    dossier_complet_auto2.short_description = mark_safe(u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""")

    def get_urls(self):
        urls = super(EquipeAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^(?P<id>\d+)/send/(?P<template>.*)/$', self.send_mail),
            (r'^(?P<id>\d+)/autre/$', self.autre),
        )
        return my_urls + urls

    def send_mail(self, request, id, template):
        instance = get_object_or_404(Equipe, id=id)

        if request.method == 'POST':
            msg = EmailMessage(request.POST['subject'], request.POST['message'], request.POST['sender'], [ request.POST['mail'] ])
            msg.content_subtype = "html"
            msg.send()
            messages.add_message(request, messages.INFO, u'Message envoyé à %s' % (request.POST['mail'], ))
            return redirect('/admin/inscriptions/equipe/%s/' % (instance.id, ))


        mail = get_object_or_404(TemplateMail, id=template)
        sujet = Template(mail.sujet).render(Context({ "course": instance.course, "instance": instance, }))
        message = Template(mail.message).render(Context({ "course": instance.course, "instance": instance, }))

        return render_to_response('admin/equipe/send_mail.html', RequestContext(request, {
            'message': message,
            'sender': instance.course.email_contact,
            'mail': instance.gerant_email,
            'subject': sujet,
        }))

    def autre(self, request, id):
        instance = get_object_or_404(Equipe, id=id)
        return render_to_response('admin/equipe/autre.html', RequestContext(request, {
            "templates": instance.course.templatemail_set.all(),
            "instance": instance,
        }));



#main_site.disable_action('delete_selected')
site.register(Equipe, EquipeAdmin)

class MaCourse(Course):
    class Meta:
        verbose_name = "Course"
        proxy = True
class CourseAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = super(CourseAdmin, self).queryset(request)
        course_uid = request.COOKIES['course_uid']
        qs = qs.filter(uid=course_uid)
        return qs
    pass
site.register(MaCourse, CourseAdmin)


class CategorieAdmin(admin.ModelAdmin):
    class Media:
        js  = ('admin/categorie.js', )
    def queryset(self, request):
        qs = super(CategorieAdmin, self).queryset(request)
        course_uid = request.COOKIES['course_uid']
        qs = qs.filter(course__uid=course_uid)
        return qs
    list_display = ('code', 'nom', 'min_equipiers', 'max_equipiers', 'min_age', 'sexe', )
site.register(Categorie, CategorieAdmin)


class TemplateMailAdmin(admin.ModelAdmin):
    class Media:
        js  = ('http://tinymce.cachefly.net/4.0/tinymce.min.js', 'admin/templatemail.js', )
    def queryset(self, request):
        qs = super(TemplateMailAdmin, self).queryset(request)
        course_uid = request.COOKIES['course_uid']
        qs = qs.filter(course__uid=course_uid)
        return qs
    list_display = ('nom', 'sujet', )
site.register(TemplateMail, TemplateMailAdmin)



