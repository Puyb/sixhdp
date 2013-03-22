Event.observe(window, 'load', function() {
    if(!$('equipe_form')) return;

    $$('.field-piece_jointe p', '.field-piece_jointe2 p', '.field-autorisation p').each(function(p) {
        if(p.textContent == '')
            p.innerHTML = 'Aucun fichier joint';
        else
            p.innerHTML = '<a href="/uploads/' + p.textContent + '" target="_blank">' + p.textContent + '</a>';
    });

    if($$('.field-categorie p')[0].textContent != 'EPX')
        $$('.field-piece_jointe2').invoke('hide');

    if($$('.field-categorie p')[0].textContent != 'FMX')
        $$('.field-parent').invoke('hide');

    $$('.add-row, .delete').invoke('remove');

    $$('.field-date_de_naissance p').each(function(p) {
        var d = p.textContent.split(' ');
        console.log(d);
        d[1] = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'].indexOf(d[1]);
        d = d.collect(parseFloat);
        console.log(d);
        var date_de_naissance= new Date(d[2], d[1], d[0]);

        today = new Date(YEAR, MONTH - 1, DAY)

        birthday = new Date(YEAR, d[1], d[0]);
        if(birthday.getDay() != d[0])
            birthday = new Date(YEAR, d[1], d[0] - 1);

        var age = today.getFullYear() - date_de_naissance.getFullYear() - (birthday > today ? 1 : 0)


        p.up().addClassName('field-box field-date_de_naissance');
        p.up().insert({after: '<div class="field-box">' +
            '<label class="inline">Age pendant la course:</label>' +
            '<p>' + age + ' ans</p>' +
            '</div>' })
        if(age > 18) {
            p.up('.form-row').next().hide();
        }
    
    });


});


