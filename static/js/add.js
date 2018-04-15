let isForm = false
function toogleForm() {
    console.log(isForm)
    if(isForm){
        $('#form').show();
        $('#show-form_button').hide();
        isForm = false
    } else {
        $('#form').hide();
        $('#show-form_button').show();
        isForm = true
    }
}
toogleForm()
$('.add-container').draggable();
