"use strict";
/* globals COURSE, INSTANCE, CATEGORIES, UPDATE, STAFF, CHECK_URL, I18N */
/* globals Prototype, $, $$, $F, $R, Form, Event, Ajax */

if(![].map)
    Array.prototype.map = function(fn) {
        var r = [];
        for(var i = 0; i < this.length; i++)
            r.push(fn(this[i], i));
        return r;
    };

var actual_part = 0;

function age(a) {
    return function(eq) {
        var b = COURSE.YEAR - parseFloat(eq.date_de_naissance_year);
        if(b !== a) return b > a;
        if(parseFloat(eq.date_de_naissance_month) !== COURSE.MONTH)
            return parseFloat(eq.date_de_naissance_month) < COURSE.MONTH;
        return parseFloat(eq.date_de_naissance_day) <= COURSE.DAY;
    };
}

function check_date(data, k) {
    var d = new Date(parseFloat(data[k + '_year']), parseFloat(data[k + '_month']) - 1, parseFloat(data[k + '_day']));
    return d.getFullYear()  === parseFloat(data[k + '_year'])  && 
            d.getMonth() + 1 === parseFloat(data[k + '_month']) &&
            d.getDate()       === parseFloat(data[k + '_day'])   ? d : undefined;
}

function serialize() {
    $$('input, select').each(function(e) {
        e.disabled = false;
    });
    var data = Form.serialize(document.body, true);
    if(!STAFF) {
        if(new Date() >= COURSE.CLOSE_DATE || COURSE.EQUIPIERS_COUNT >= COURSE.MAX_EQUIPIERS) {
            $$('input, select').each(function(e) {
                if(e.type !== 'file' && e.type !== 'button' && e.type !== 'submit' && e.type !== 'radio' && !/num_licence$/.test(e.name))
                    e.disabled = true;
            });
        }
    }
    data.equipiers = [{}, {}, {}, {}, {}];
    data.nombre = parseFloat(data.nombre);
    for(var k in data)
        if(/^form-\d-/.test(k) && parseFloat(k.substr(5)) < data.nombre)
            data.equipiers[parseFloat(k.substr(5))][k.substr(7)] = data[k];
    data.nombre_h = data.equipiers.filter(function(i) { return i.sexe === 'H'; }).length;
    data.nombre_f = data.equipiers.filter(function(i) { return i.sexe === 'F'; }).length;
    return data;
}

function disable_form_if_needed() {
    if(new Date() >= COURSE.CLOSE_DATE || COURSE.EQUIPIERS_COUNT >= COURSE.MAX_EQUIPIERS && !STAFF) {
        $$('input, select').each(function(e) {
            if(e.type !== 'file' && e.type !== 'button' && e.type !== 'submit' && e.type !== 'radio' && !/num_licence$/.test(e.name))
                e.disabled = true;
        });
    }
}

function check_nom(wait) {
    new Ajax.Request(CHECK_URL, {
        parameters: { nom: $F('id_nom'), id: INSTANCE.ID },
        asynchronous: !wait,
        onSuccess: function(r) {
            if(r.responseText !== '0')
                $('nom_erreur').update(gettext("Ce nom d'équipe est déjà utilisé !"));
            else
                $('nom_erreur').update("");

        }
    });
}

function check_step(data) {
    // check values
    var ok = true;
    var prefix = 'id_';
    var test_data = data;
    var tests;
    var message = '';
    if(!actual_part) {
        tests = {
            nom:                function(k) { check_nom(true); return /^.+$/i.test(this.nom) && $('nom_erreur').innerHTML === ''; },
            gerant_nom:         /^.+$/i,
            gerant_prenom:      /^.+$/i,
            gerant_ville:       /^.+$/i,
            gerant_code_postal: /^[0-9]{4,6}$/i,
            gerant_email:       /^[a-z0-9+\-\._]+@([a-z0-9\-_]+\.)+[a-z]{2,5}$/i,
            nombre:             function(k) {
                var nombre = this.nombre;
                if(CATEGORIES.filter(function(categorie) {
                    return categorie.min_equipiers <= nombre && nombre <= categorie.max_equipiers;
                }).length === 0) {
                    message += gettext("Désolé, il n'y a plus de place dans ces catégories. Changez le nombre de participants.") + '\n';
                    return false;
                }
                return true;
            },
            gerant_telephone:   /^\+?[0-9]{10,15}$/i

        };
    } else {
        tests = {
            nom:                /^.+$/i,
            prenom:             /^.+$/i,
            sexe:               /^[HF]$/,
            ville:              /^.+$/i,
            code_postal:        /^[0-9]{4,6}$/i,
            email:              /^[a-z0-9+\-\._]+@([a-z0-9\-_]+\.)+[a-z]{2,5}$/i,
            date_de_naissance:  function(k) { return check_date(this, k) && age(COURSE.MIN_AGE)(this); },
            num_licence:        function(k) { return this.justificatif !== 'licence' || /^[0-9]{3,9}$/i.test(this[k]); }
        };
        prefix = 'id_form-' + (actual_part - 1) + '-';
        test_data = data.equipiers[actual_part - 1];
    }
    for(var k in tests) {
        if(tests[k].test ? tests[k].test(test_data[k]) : tests[k].call(test_data, k)) {
            $(prefix + k).setStyle({ background: 'white' });
        } else {
            ok = false;
            $(prefix + k).setStyle({ background: '#ff6666' });
        }
    }
    if(!ok) {
        return alert(message + gettext('Veuillez corriger les champs en rouge.'));
    }
    return ok;
}

function setup_categories(data) {
    // filter
    var actual_categories = CATEGORIES.filter(function(c) {
        return c.min_equipiers <= data.nombre && data.nombre <= c.max_equipiers
            && data.equipiers.filter(age(c.min_age)).length === data.nombre
            && ((c.sexe === 'H' && data.nombre === data.nombre_h) ||
                (c.sexe === 'F' && data.nombre === data.nombre_f) ||
                (c.sexe === 'HX' && data.nombre_f >= 1) ||
                (c.sexe === 'FX' && data.nombre_h >= 1) ||
                (c.sexe === 'X' && data.nombre_f >0 && data.nombre_h > 0))
            && c.valid(data);
    });
    
    if(actual_categories.length === 0) {
        $('button_prev').click();
        alert(gettext("Votre équipe n'est éligible dans aucune des catégories proposées pour cette compétition. Veuillez vous référer au réglement de la course disponible sur le site pour voir les critères de chaque catégorie."));
        return false;
    }

    // generate html
    $('catwrapper').innerHTML = actual_categories.map(function(c) {
        return '<input type="radio" value="#{id}" name="categorie" id="id_categorie_id-#{id}"><label for="id_categorie-#{id}">#{label} - #{prix} €</label><br />'.interpolate(c);
    }).join('');

    disable_form_if_needed();

    // install handlers
    $$('input[name=categorie]').invoke('observe', 'change', function(event) {
        var categorie = $$('input[name=categorie]').filter(function(e) { return e.checked; })[0].value;
        var d = CATEGORIES.filter(function(c) { return c.code === categorie; })[0];
        $('id_prix').value = d.prix;
        $$('.justif_supp').invoke('hide');
        if(d.show)
            $('justif_' + d.code).show();
    });

    // select the categorie
    if(UPDATE) {
        if(!$('id_categorie-' + INSTANCE.CATEGORIE))
            alert(gettext("Vos modifications impliquent un changement de catégorie. Veuillez sélectionner la nouvelle catégorie."));
        else
            $('id_categorie-' + INSTANCE.CATEGORIE).checked = true;
    } else {
        $$('input[name=categorie]')[0].checked = true;
        $('id_prix').value = actual_categories[0].prix;
    }

    return true;
}

function setup_extra_justif() {
    for(var i = 1; i < actual_part; i++) {
        var n = $F('id_form-' + (i - 1) + '-prenom') + ' ' + $F('id_form-' + (i - 1) + '-nom');
        $$('#justif_FMX', '#justif_EPX').each(function(e) {
            var tr = e.down('tr', i - 1);
            tr.show();
            tr.down().update(n);
        });
    }
}

Event.observe(window, 'load', function() {
    $('id_categorie').remove();
    for(var i = 0; i < 5; i++) {
        $('id_form-' + i + '-date_de_naissance_day').up().id = 'id_form-' + i + '-date_de_naissance';
    }
    //$('id_password').up().insert('<br /><input type="password" id="id_password2" />');

    $$('select[name*=naissance]').invoke('observe', 'change', function(event) {
        var data = serialize();
        var n = event.element().name.split('-')[1];
        if(age(18)(data.equipiers[n])) {
            $('id_form-' + n + '-autorisation').up('tr').hide();
            if($('tr-autorisation-warning'))
                $('tr-autorisation-warning').remove();
        } else {
            var e = $('id_form-' + n + '-autorisation').up('tr').show();
            if(!$('tr-autorisation-warning'))
                e.insert({
                    after: new Element('tr', { id: 'tr-autorisation-warning' })
                            .insert(new Element('td', { colspan: 2 })
                            .update(gettext("Si vous le pouvez, scannez l'autorisation et ajoutez la en pièce jointe (formats PDF ou JPEG).") + "<br />" + gettext("Vous pourrez aussi la télécharger plus tard, ou l'envoyer par courrier (<a href=\"http://www.6hdeparis.fr/wp-content/uploads/2013/03/autorisation_parentale.pdf\" target=\"_blank\">modèle</a>).")))
                });
        }
    
    });
    $$('input[name*=licence]').each(function(e) {
        var tr = e.up('tr');
        var id = e.id.split('-').slice(0, 2).join('-');
        tr.hide()
            .next().hide();
        var handler = function() {
            if($(id + '-justificatif_1').checked) {
                tr.show()
                    .next().show().down('label').update(gettext('Licence') + ':');
                tr.next(1).show();
            }
            if($(id + '-justificatif_2').checked) {
                tr.hide()
                    .next().show().down('label').update(gettext('Certificat médical') + ':');
                tr.next(1).show();
            }
        };
        $(id + '-justificatif_0').up('li').remove();
        $(id + '-justificatif_1').observe(Prototype.Browser.IE ? 'click' : 'change', handler);
        $(id + '-justificatif_2').observe(Prototype.Browser.IE ? 'click' : 'change', handler);
        $(id + '-justificatif_1').up('tr').next(1).insert({after: e.up('table').down('tr:last') });
        handler();
    });
    $$('input[name*=parent]').each(function(e) {
        var tr = e.up('tr').hide();
        $('justif_FMX').down('table').insert(tr);
    });
    $$('input[name*=jointe2]').each(function(e) {
        var tr = e.up('tr').hide();
        $('justif_EPX').down('table').insert(tr);
    });

    disable_form_if_needed();

    var nom_timeout;
    $('id_nom')
        .insert({ after: new Element('div', { id: 'nom_erreur' }) })
        .observe('keydown', function(event) {
            if(nom_timeout) clearTimeout(nom_timeout);
            nom_timeout = setTimeout(check_nom, 500);
        });



    $('part0').down('input').focus();

    $('button_prev').observe('click', function(event) {
        $$('.parts').invoke('hide');
        actual_part--;
        $('part' + actual_part).show();
        $('part' + actual_part).down('input').focus();
        $('button_next').show();
        $('button_submit').hide();
        if(!actual_part) event.element().hide();
    });


    $('button_next').observe('click', function(event) {
        var data = serialize();
        if(!check_step(data)) {
            return;
        }

        // change page
        $('button_prev').show();
        $$('.parts').invoke('hide');
        actual_part++;
        if(actual_part > parseInt($F('id_nombre'))) {
            // last page
            $('partlast').show();
            try {
                $('partlast').down('input').focus();
            } catch(e) {}

            if(setup_categories(data)) {

                setup_extra_justif();

                $('button_next').hide();
                $('id_form-TOTAL_FORMS').value = actual_part - 1;
                $('button_submit').show();
            }
        } else {
            $('part' + actual_part).show();
            $('part' + actual_part).down('input').focus();
            if(age(18)(data.equipiers[actual_part - 1]))
                $('id_form-' + (actual_part - 1) + '-autorisation').up('tr').hide();
            if(actual_part === 1) {
                $$('[name*=gerant_]').each(function(element) {
                    var element2 = $('id_form-0-' + element.name.substr('gerant_'.length));
                    if(element2) {
                        element2.setValue(element.getValue());
                    }
                });
            }
        }
    });



    $('button_submit').observe('mousedown', function(event) {
        $R(actual_part, 5).each(function(i) { $('part' + i).remove(); });
        var categorie = $$('input[name=categorie]').filter(function(e) { return e.checked; })[0].value;
        $('id_prix').value = CATEGORIES.filter(function(c) { return c.id === categorie; })[0].prix;
        if(!categorie) {
            event.stop();
            alert(gettext('Vous devez choisir une catégorie'));
        }
        if(!$('id_conditions').checked) {
            event.stop();
            alert(gettext('Vous devez accépter le règlement de la compétition'));
        }
        $$('input, select').each(function(e) {
            e.disabled = false;
        });
    });
});

if(!UPDATE) {
    if(new Date() >= COURSE.CLOSE_DATE) {
        alert("Désolé, les inscriptions sont fermées. Il n'est plus possible de s'incrire à la course");
        location.href = COURSE.URL;
    } else if(COURSE.EQUIPIERS_COUNT >= COURSE.MAX_EQUIPIERS) {
        alert("Désolé, la course est complete, il n'y a plus de place disponible.");
        location.href = COURSE.URL;
    }
}



