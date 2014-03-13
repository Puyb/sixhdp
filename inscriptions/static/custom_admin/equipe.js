django.jQuery(function() {
    var $ = django.jQuery;
    if(!$('#equipe_form').length) return;

    $('.field-piece_jointe p', '.field-piece_jointe2 p', '.field-autorisation p').each(function() {
        if(this.textContent == '')
            this.innerHTML = 'Aucun fichier joint';
        else
            this.innerHTML = '<a href="/uploads/' + this.textContent + '" target="_blank">' + this.textContent + '</a>';
    });

    if($('.field-categorie p')[0].textContent != 'EPX')
        $('.field-piece_jointe2').hide();

    if($('.field-categorie p')[0].textContent != 'FMX')
        $('.field-parent').hide();

    $('.add-row, .delete').remove();

    $('.field-age>p').each(function() {
        if(parseFloat(this.textContent) >= 18) {
            $(this).parents('.form-row').next().hide();
        }
    
    });

    $.get('autre/', function(data) {
        $('#autre').html(data);
    });

});


