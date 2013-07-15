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

    $$('.field-age>p').each(function(p) {

        console.log(p.textContent)
        if(parseFloat(p.textContent) >= 18) {

            p.up('.form-row').next().hide();
        }
    
    });

    $('autre').innerHTML = '<a href="/' + $$('.field-id p')[0].textContent + '/done/">Lien de paiement</a><br />' +
                           '<a href="/' + $$('.field-id p')[0].textContent + '/' + $$('.field-password p')[0].textContent + '/">Lien de modification</a><br />'+
                           '<a href="/' + $$('.field-id p')[0].textContent + '/send/">Envoyer une relance</a><br />';

});


