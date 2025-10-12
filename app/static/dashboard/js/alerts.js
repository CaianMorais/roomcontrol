export function showAlert(title, text, icon, timer = false, time = 1000) {
    const options = {
        title: title,
        text: text,
        icon: icon
    };
    
    if (timer) {
        ;
        options.timer = time;
        options.timerProgressBar = true;
        options.didOpen = () => {
            Swal.showLoading();
        };
        options.willClose = () => {
            clearInterval(options.timerInterval);
        };
    } else {
        options.showCancelButton = true;
        options.confirmButtonColor = "#3085d6";
        options.cancelButtonColor = "#d33";
        options.confirmButtonText = "Confirmar";
        options.cancelButtonText = "Não";
    }

    return Swal.fire(options);
}